"""
NLP Service for processing WhatsApp messages
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models.whatsapp import ProcessedMessage
from app.models.llm import ProcessedData, ComplexityLevel
from app.services.llm.llm_provider_service import llm_provider_service
from app.core.redis import redis_manager

logger = logging.getLogger(__name__)


class NLPService:
    """Service for processing WhatsApp messages with NLP"""
    
    def __init__(self):
        self.processing_queue_key = "whatsapp:message_queue"
        self.processed_queue_key = "whatsapp:processed_queue"
    
    async def procesar_mensaje_whatsapp(self, mensaje: ProcessedMessage) -> ProcessedData:
        """
        Main function to process WhatsApp message with multi-LLM strategy
        
        This function implements the complete NLP processing pipeline:
        1. Analyzes message complexity automatically
        2. Routes to appropriate LLM provider based on complexity
        3. Implements fallback cascade: regex → Deepseek → Gemini → OpenAI → Anthropic → basic
        4. Extracts structured data (repuestos, vehiculo, cliente)
        5. Returns processed data with confidence scores and metrics
        
        Complexity levels:
        - Level 1 (Simple): Deepseek/Ollama - short, direct messages
        - Level 2 (Complex): Gemini - long messages, multiple parts, slang
        - Level 3 (Structured): OpenAI GPT-4 - Excel, PDFs, structured documents
        - Level 4 (Multimedia): Anthropic Claude - audio, images, videos
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing WhatsApp message {mensaje.message_id} from {mensaje.from_number}")
            
            # Prepare content for processing
            text_content = mensaje.text_content or ""
            image_url = None
            audio_url = None
            document_url = None
            
            # Handle different message types for multimedia content
            if mensaje.message_type == "image" and mensaje.media_url:
                image_url = mensaje.media_url
                logger.info(f"Processing image content: {mensaje.media_url}")
            elif mensaje.message_type in ["audio", "voice"] and mensaje.media_url:
                audio_url = mensaje.media_url
                logger.info(f"Processing audio content: {mensaje.media_url}")
            elif mensaje.message_type == "document" and mensaje.media_url:
                document_url = mensaje.media_url
                logger.info(f"Processing document content: {mensaje.media_url}")
            
            # Add comprehensive context information
            context = {
                "message_id": mensaje.message_id,
                "from_number": mensaje.from_number,
                "message_type": mensaje.message_type,
                "timestamp": mensaje.timestamp.isoformat(),
                "context_message_id": mensaje.context_message_id,
                "has_media": bool(mensaje.media_url),
                "media_type": mensaje.media_type,
                "processing_start": start_time.isoformat()
            }
            
            # Process with multi-LLM provider service
            # This automatically handles:
            # - Complexity analysis
            # - Provider selection based on complexity
            # - Circuit breaker protection
            # - Retry with exponential backoff
            # - Fallback cascade
            # - Metrics collection
            processed_data = await llm_provider_service.process_content(
                text=text_content,
                image_url=image_url,
                audio_url=audio_url,
                document_url=document_url,
                context=context
            )
            
            # Calculate total processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            processed_data.processing_time_ms = processing_time
            
            # Enhance processed data with additional context
            if processed_data.cliente and not processed_data.cliente.get("telefono"):
                processed_data.cliente["telefono"] = mensaje.from_number
            
            # Log comprehensive processing result
            logger.info(
                f"Message {mensaje.message_id} processed successfully: "
                f"provider={processed_data.provider_used}, "
                f"complexity={processed_data.complexity_level}, "
                f"confidence={processed_data.confidence_score:.2f}, "
                f"complete={processed_data.is_complete}, "
                f"time={processing_time}ms, "
                f"repuestos_found={len(processed_data.repuestos)}, "
                f"has_vehicle={bool(processed_data.vehiculo)}, "
                f"has_client={bool(processed_data.cliente)}"
            )
            
            # Log missing fields for debugging
            if processed_data.missing_fields:
                logger.info(f"Missing fields for message {mensaje.message_id}: {processed_data.missing_fields}")
            
            return processed_data
            
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Error processing WhatsApp message {mensaje.message_id}: {e}")
            logger.error(f"Message content: {mensaje.text_content[:200]}..." if mensaje.text_content else "No text content")
            
            # Return comprehensive fallback result
            fallback_data = ProcessedData(
                repuestos=[],
                vehiculo=None,
                cliente={"telefono": mensaje.from_number},
                provider_used="error_fallback",
                complexity_level="simple",
                confidence_score=0.0,
                processing_time_ms=processing_time,
                raw_text=mensaje.text_content or "",
                is_complete=False,
                missing_fields=["repuestos", "vehiculo", "cliente"]
            )
            
            # Try basic regex extraction as last resort
            try:
                if mensaje.text_content:
                    regex_result = await self.extract_entities_from_text(mensaje.text_content)
                    if regex_result.get("repuestos"):
                        fallback_data.repuestos = regex_result["repuestos"]
                        fallback_data.provider_used = "regex_fallback"
                        fallback_data.confidence_score = 0.3
                        logger.info(f"Regex fallback extracted {len(regex_result['repuestos'])} repuestos")
            except Exception as regex_error:
                logger.error(f"Regex fallback also failed: {regex_error}")
            
            return fallback_data
    
    async def process_queued_messages(self, max_messages: int = 10) -> int:
        """
        Process messages from the queue with conversation management
        
        This function runs periodically to process queued WhatsApp messages
        and manages conversations with context and state tracking
        """
        processed_count = 0
        
        try:
            for _ in range(max_messages):
                # Get message from queue
                message_data = await redis_manager.rpop(self.processing_queue_key)
                if not message_data:
                    break
                
                try:
                    # Parse message
                    message_dict = json.loads(message_data)
                    mensaje = ProcessedMessage(
                        message_id=message_dict["message_id"],
                        from_number=message_dict["from_number"],
                        timestamp=datetime.fromisoformat(message_dict["timestamp"]),
                        message_type=message_dict["message_type"],
                        text_content=message_dict.get("text_content"),
                        media_url=message_dict.get("media_url"),
                        media_type=message_dict.get("media_type"),
                        context_message_id=message_dict.get("context_message_id")
                    )
                    
                    # Process message with conversation management
                    await self._process_message_with_conversation(mensaje)
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing queued message: {e}")
                    logger.error(f"Message data: {message_data}")
                    continue
            
            if processed_count > 0:
                logger.info(f"Processed {processed_count} queued messages")
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing message queue: {e}")
            return processed_count
    
    async def _process_message_with_conversation(self, mensaje: ProcessedMessage):
        """
        Process message with full conversation management
        
        This integrates NLP processing with conversation state management
        """
        try:
            # Import conversation service here to avoid circular imports
            from app.services.conversation_service import conversation_service
            
            # Manage conversation and get response
            conversation, response_message = await conversation_service.gestionar_conversacion(
                mensaje.from_number, 
                mensaje
            )
            
            # Send response back to user
            if response_message:
                from app.services.whatsapp_service import whatsapp_service
                await whatsapp_service.send_text_message(mensaje.from_number, response_message)
                
                logger.info(f"Sent response to {mensaje.from_number}: {response_message[:100]}...")
            
            # Check if conversation is complete and ready for solicitud creation
            if conversation.completeness_score >= 0.8 and conversation.state.value in ["creating_solicitud", "complete"]:
                await self._create_solicitud_from_conversation(conversation)
            
        except Exception as e:
            logger.error(f"Error processing message with conversation: {e}")
            # Send error message to user
            try:
                from app.services.whatsapp_service import whatsapp_service
                await whatsapp_service.send_text_message(
                    mensaje.from_number, 
                    "Disculpa, hubo un error procesando tu mensaje. ¿Podrías intentar de nuevo?"
                )
            except:
                pass  # Don't fail if we can't send error message
    
    async def _create_solicitud_from_conversation(self, conversation):
        """
        Create solicitud from complete conversation data
        
        This function integrates with the Core API to create a solicitud
        """
        try:
            # Import here to avoid circular imports
            from app.services.solicitud_service import solicitud_service
            
            # Check if solicitud already created
            if conversation.solicitud_id:
                logger.info(f"Solicitud {conversation.solicitud_id} already exists for {conversation.phone_number}")
                return
            
            # Create solicitud data
            solicitud_data = {
                "cliente": conversation.accumulated_cliente,
                "vehiculo": conversation.accumulated_vehiculo,
                "repuestos": conversation.accumulated_repuestos,
                "conversation_id": f"conv_{conversation.phone_number}_{int(conversation.created_at.timestamp())}"
            }
            
            # Create solicitud via Core API
            solicitud_id = await solicitud_service.create_solicitud_from_whatsapp(solicitud_data)
            
            if solicitud_id:
                # Update conversation with solicitud ID
                conversation.solicitud_id = solicitud_id
                conversation.state = "solicitud_created"
                
                # Save updated conversation
                from app.services.conversation_service import conversation_service
                await conversation_service.save_conversation_context(conversation)
                
                logger.info(f"Created solicitud {solicitud_id} from conversation {conversation.phone_number}")
                
                # Send confirmation to user
                from app.services.whatsapp_service import whatsapp_service
                await whatsapp_service.send_text_message(
                    conversation.phone_number,
                    f"¡Perfecto! Tu solicitud #{solicitud_id} ha sido creada. "
                    "Estamos buscando las mejores ofertas para ti. Te notificaremos pronto."
                )
            
        except Exception as e:
            logger.error(f"Error creating solicitud from conversation: {e}")
            # Send error message
            try:
                from app.services.whatsapp_service import whatsapp_service
                await whatsapp_service.send_text_message(
                    conversation.phone_number,
                    "Hubo un problema creando tu solicitud. Nuestro equipo revisará tu caso."
                )
            except:
                pass
    
    async def _queue_processed_message(self, original_message: ProcessedMessage, processed_data: ProcessedData):
        """Queue processed message for conversation management"""
        try:
            processed_entry = {
                "original_message": {
                    "message_id": original_message.message_id,
                    "from_number": original_message.from_number,
                    "timestamp": original_message.timestamp.isoformat(),
                    "message_type": original_message.message_type,
                    "text_content": original_message.text_content
                },
                "processed_data": processed_data.model_dump(),
                "processed_at": datetime.now().isoformat()
            }
            
            await redis_manager.lpush(
                self.processed_queue_key,
                json.dumps(processed_entry)
            )
            
        except Exception as e:
            logger.error(f"Error queuing processed message: {e}")
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            queue_length = await redis_manager.llen(self.processing_queue_key)
            processed_queue_length = await redis_manager.llen(self.processed_queue_key)
            
            # Get provider status
            provider_status = await llm_provider_service.get_provider_status()
            
            return {
                "queue_length": queue_length,
                "processed_queue_length": processed_queue_length,
                "provider_status": provider_status,
                "service_status": "active"
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            return {
                "queue_length": 0,
                "processed_queue_length": 0,
                "service_status": "error",
                "error": str(e)
            }
    
    async def extract_entities_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from text using regex patterns
        
        This is used as a fallback or for simple cases
        """
        try:
            # Use the regex processor from LLM service
            from app.services.llm.llm_provider_service import RegexProcessor
            
            regex_processor = RegexProcessor()
            result = regex_processor.process(text)
            
            return {
                "repuestos": result.repuestos,
                "vehiculo": result.vehiculo,
                "cliente": result.cliente,
                "confidence": result.confidence_score,
                "method": "regex"
            }
            
        except Exception as e:
            logger.error(f"Error extracting entities with regex: {e}")
            return {
                "repuestos": [],
                "vehiculo": None,
                "cliente": None,
                "confidence": 0.0,
                "method": "error"
            }
    
    async def validate_extracted_data(self, processed_data: ProcessedData) -> Dict[str, Any]:
        """
        Validate extracted data quality
        
        Returns validation results and suggestions for improvement
        """
        validation_result = {
            "is_valid": True,
            "issues": [],
            "suggestions": [],
            "completeness_score": 0.0
        }
        
        try:
            # Check repuestos
            if not processed_data.repuestos:
                validation_result["issues"].append("No se encontraron repuestos")
                validation_result["suggestions"].append("Solicitar especificación de repuestos necesarios")
            else:
                # Check if parts have proper names
                for i, repuesto in enumerate(processed_data.repuestos):
                    if not repuesto.get("nombre"):
                        validation_result["issues"].append(f"Repuesto {i+1} sin nombre específico")
                    if len(repuesto.get("nombre", "")) < 3:
                        validation_result["issues"].append(f"Nombre de repuesto {i+1} muy corto")
            
            # Check vehiculo
            if not processed_data.vehiculo:
                validation_result["issues"].append("No se encontró información del vehículo")
                validation_result["suggestions"].append("Solicitar marca, modelo y año del vehículo")
            else:
                vehiculo = processed_data.vehiculo
                if not vehiculo.get("marca"):
                    validation_result["issues"].append("Falta marca del vehículo")
                if not vehiculo.get("anio"):
                    validation_result["issues"].append("Falta año del vehículo")
            
            # Check cliente
            if not processed_data.cliente:
                validation_result["issues"].append("No se encontró información del cliente")
                validation_result["suggestions"].append("Solicitar nombre y ciudad del cliente")
            else:
                cliente = processed_data.cliente
                if not cliente.get("telefono"):
                    validation_result["suggestions"].append("Confirmar número de teléfono")
                if not cliente.get("ciudad"):
                    validation_result["suggestions"].append("Solicitar ciudad del cliente")
            
            # Calculate completeness score
            total_fields = 6  # repuestos, vehiculo.marca, vehiculo.anio, cliente.telefono, cliente.ciudad, cliente.nombre
            complete_fields = 0
            
            if processed_data.repuestos:
                complete_fields += 1
            if processed_data.vehiculo and processed_data.vehiculo.get("marca"):
                complete_fields += 1
            if processed_data.vehiculo and processed_data.vehiculo.get("anio"):
                complete_fields += 1
            if processed_data.cliente and processed_data.cliente.get("telefono"):
                complete_fields += 1
            if processed_data.cliente and processed_data.cliente.get("ciudad"):
                complete_fields += 1
            if processed_data.cliente and processed_data.cliente.get("nombre"):
                complete_fields += 1
            
            validation_result["completeness_score"] = complete_fields / total_fields
            validation_result["is_valid"] = len(validation_result["issues"]) == 0
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating extracted data: {e}")
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Error en validación: {str(e)}")
            return validation_result
    
    async def get_missing_information_questions(self, processed_data: ProcessedData) -> List[str]:
        """
        Generate questions to ask for missing information
        """
        questions = []
        
        try:
            # Check what's missing and generate appropriate questions
            if not processed_data.repuestos:
                questions.append("¿Qué repuestos necesitas para tu vehículo?")
            
            if not processed_data.vehiculo:
                questions.append("¿Cuál es la marca, modelo y año de tu vehículo?")
            else:
                vehiculo = processed_data.vehiculo
                if not vehiculo.get("marca"):
                    questions.append("¿Cuál es la marca de tu vehículo?")
                if not vehiculo.get("linea") and not vehiculo.get("modelo"):
                    questions.append("¿Cuál es el modelo de tu vehículo?")
                if not vehiculo.get("anio"):
                    questions.append("¿De qué año es tu vehículo?")
            
            if not processed_data.cliente:
                questions.append("¿Cuál es tu nombre y en qué ciudad te encuentras?")
            else:
                cliente = processed_data.cliente
                if not cliente.get("nombre"):
                    questions.append("¿Cuál es tu nombre?")
                if not cliente.get("ciudad"):
                    questions.append("¿En qué ciudad te encuentras?")
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return ["¿Podrías proporcionar más detalles sobre los repuestos que necesitas?"]
    
    async def analyze_message_complexity(self, mensaje: ProcessedMessage) -> ComplexityLevel:
        """
        Analyze message complexity for provider selection
        
        This method implements the complexity classification system:
        - Simple: Short messages, common patterns, single parts
        - Complex: Long messages, multiple parts, technical terms, slang
        - Structured: References to Excel, CSV, PDFs, structured data
        - Multimedia: Images, audio, videos, documents
        """
        try:
            # Import the complexity analyzer
            from app.services.llm.llm_router import llm_router
            from app.models.llm import LLMRequest
            
            # Create a request for complexity analysis
            request = LLMRequest(
                text=mensaje.text_content,
                image_url=mensaje.media_url if mensaje.message_type == "image" else None,
                audio_url=mensaje.media_url if mensaje.message_type in ["audio", "voice"] else None,
                document_url=mensaje.media_url if mensaje.message_type == "document" else None,
                complexity_level=ComplexityLevel.SIMPLE  # Will be overridden
            )
            
            complexity = llm_router.analyze_request_complexity(request)
            
            logger.info(f"Message {mensaje.message_id} classified as {complexity.value} complexity")
            return complexity
            
        except Exception as e:
            logger.error(f"Error analyzing message complexity: {e}")
            return ComplexityLevel.SIMPLE
    
    async def get_provider_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for all LLM providers
        """
        try:
            return await llm_provider_service.get_provider_status()
        except Exception as e:
            logger.error(f"Error getting provider stats: {e}")
            return {"error": str(e)}
    
    async def optimize_provider_routing(self) -> bool:
        """
        Optimize provider routing based on recent performance
        """
        try:
            await llm_provider_service.optimize_routing()
            logger.info("Provider routing optimized successfully")
            return True
        except Exception as e:
            logger.error(f"Error optimizing provider routing: {e}")
            return False
    
    async def process_multimedia_content(self, mensaje: ProcessedMessage) -> ProcessedData:
        """
        Specialized processing for multimedia content (images, audio, documents)
        
        This method handles:
        - Image analysis for parts identification
        - Audio transcription and analysis
        - Document extraction (Excel, PDF)
        """
        try:
            logger.info(f"Processing multimedia content: {mensaje.message_type}")
            
            # Route to appropriate multimedia handler
            if mensaje.message_type == "image":
                return await self._process_image_content(mensaje)
            elif mensaje.message_type in ["audio", "voice"]:
                return await self._process_audio_content(mensaje)
            elif mensaje.message_type == "document":
                return await self._process_document_content(mensaje)
            else:
                logger.warning(f"Unsupported multimedia type: {mensaje.message_type}")
                return await self.procesar_mensaje_whatsapp(mensaje)
                
        except Exception as e:
            logger.error(f"Error processing multimedia content: {e}")
            return await self.procesar_mensaje_whatsapp(mensaje)
    
    async def _process_image_content(self, mensaje: ProcessedMessage) -> ProcessedData:
        """Process image content using Anthropic Claude or OpenAI Vision"""
        try:
            # Use the main processing function which will route to appropriate provider
            return await self.procesar_mensaje_whatsapp(mensaje)
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise
    
    async def _process_audio_content(self, mensaje: ProcessedMessage) -> ProcessedData:
        """Process audio content using Anthropic Claude"""
        try:
            # Use the main processing function which will route to appropriate provider
            return await self.procesar_mensaje_whatsapp(mensaje)
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            raise
    
    async def _process_document_content(self, mensaje: ProcessedMessage) -> ProcessedData:
        """Process document content using OpenAI GPT-4"""
        try:
            # Use the main processing function which will route to appropriate provider
            return await self.procesar_mensaje_whatsapp(mensaje)
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise


# Global NLP service instance
nlp_service = NLPService()