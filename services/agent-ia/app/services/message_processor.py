"""
Service for processing WhatsApp messages
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.redis import redis_manager
from app.services.conversation_service import conversation_service
from app.services.nlp_service import nlp_service
from app.services.solicitud_service import solicitud_service
from app.services.results_service import results_service
from app.services.whatsapp_service import whatsapp_service
from app.models.whatsapp import ProcessedMessage

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Service for processing WhatsApp messages"""
    
    def __init__(self):
        self.response_keywords = {
            "accept": ["si", "sí", "yes", "acepto", "aceptar", "ok", "vale", "bueno"],
            "reject": ["no", "rechazo", "rechazar", "nada", "cancel", "cancelar"],
            "details": ["detalles", "detalle", "info", "información", "mas info", "más info", "explicar"]
        }
    
    async def process_queued_messages(self):
        """Process messages from the Redis queue"""
        try:
            while True:
                # Get message from queue (blocking with timeout)
                queue_key = "whatsapp:message_queue"
                message_data = await redis_manager.brpop(queue_key, timeout=5)
                
                if message_data:
                    _, message_json = message_data
                    message_dict = json.loads(message_json)
                    
                    # Convert to ProcessedMessage
                    message = ProcessedMessage(
                        message_id=message_dict["message_id"],
                        from_number=message_dict["from_number"],
                        timestamp=datetime.fromisoformat(message_dict["timestamp"]),
                        message_type=message_dict["message_type"],
                        text_content=message_dict["text_content"],
                        media_url=message_dict["media_url"],
                        media_type=message_dict["media_type"],
                        context_message_id=message_dict["context_message_id"]
                    )
                    
                    await self.process_message(message)
                
        except Exception as e:
            logger.error(f"Error processing queued messages: {e}")
    
    async def process_message(self, message: ProcessedMessage) -> Dict[str, Any]:
        """
        Process a single WhatsApp message
        
        Args:
            message: Processed message from WhatsApp
            
        Returns:
            Dict with processing result
        """
        try:
            logger.info(f"Processing message {message.message_id} from {message.from_number}")
            
            # Skip non-text messages for now
            if message.message_type != "text" or not message.text_content:
                logger.info(f"Skipping non-text message {message.message_id}")
                return {"success": True, "action": "skipped", "reason": "non_text_message"}
            
            # Get or create conversation context
            conversation = await conversation_service.get_or_create_conversation(message.from_number)
            
            # Check if this is a response to an evaluation result
            if await self._is_evaluation_response(message.text_content, conversation):
                return await self._handle_evaluation_response(message, conversation)
            
            # Process as new solicitud or continuation
            return await self._handle_solicitud_message(message, conversation)
            
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}")
            return {
                "success": False,
                "error": "Error interno procesando mensaje",
                "details": str(e)
            }
    
    async def _is_evaluation_response(self, text: str, conversation) -> bool:
        """Check if message is a response to evaluation results"""
        try:
            # Check if conversation has a pending solicitud
            if not conversation.solicitud_id:
                return False
            
            # Check if text matches response keywords
            text_lower = text.lower().strip()
            
            for category, keywords in self.response_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking evaluation response: {e}")
            return False
    
    async def _handle_evaluation_response(self, message: ProcessedMessage, conversation) -> Dict[str, Any]:
        """Handle client response to evaluation results"""
        try:
            logger.info(f"Handling evaluation response from {message.from_number}")
            
            # Process the response
            result = await results_service.handle_client_response(
                message.from_number,
                message.text_content,
                conversation.solicitud_id
            )
            
            if result["success"]:
                # Clear solicitud_id from conversation if accepted or rejected
                if result["action"] in ["accepted", "rejected"]:
                    await conversation_service.clear_solicitud_id(message.from_number)
                
                logger.info(f"Evaluation response processed: {result['action']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling evaluation response: {e}")
            return {
                "success": False,
                "error": "Error procesando respuesta de evaluación",
                "details": str(e)
            }
    
    async def _handle_solicitud_message(self, message: ProcessedMessage, conversation) -> Dict[str, Any]:
        """Handle message as part of solicitud creation process"""
        try:
            logger.info(f"Handling solicitud message from {message.from_number}")
            
            # Add message to conversation
            await conversation_service.add_message_to_conversation(
                message.from_number,
                message.text_content,
                "user"
            )
            
            # Process with NLP service
            nlp_result = await nlp_service.process_message(
                message.text_content,
                conversation,
                message.media_url,
                message.media_type
            )
            
            if not nlp_result["success"]:
                # Send error message to user
                error_msg = "Lo siento, no pude procesar tu mensaje. ¿Podrías intentar de nuevo?"
                await whatsapp_service.send_text_message(message.from_number, error_msg)
                return nlp_result
            
            processed_data = nlp_result["processed_data"]
            
            # Check if we have enough information to create solicitud
            if processed_data.is_complete:
                # Create solicitud
                solicitud_result = await solicitud_service.crear_solicitud_desde_whatsapp(
                    processed_data,
                    conversation
                )
                
                if solicitud_result["success"]:
                    # Store solicitud_id in conversation for future responses
                    await conversation_service.set_solicitud_id(
                        message.from_number,
                        solicitud_result["solicitud_id"]
                    )
                    
                    logger.info(f"Solicitud created: {solicitud_result['solicitud_id']}")
                else:
                    # Send error message
                    error_msg = f"Error creando solicitud: {solicitud_result['error']}"
                    await whatsapp_service.send_text_message(message.from_number, error_msg)
                
                return solicitud_result
            else:
                # Request missing information
                missing_info_msg = await self._generate_missing_info_message(processed_data)
                await whatsapp_service.send_text_message(message.from_number, missing_info_msg)
                
                return {
                    "success": True,
                    "action": "info_requested",
                    "missing_fields": processed_data.missing_fields
                }
                
        except Exception as e:
            logger.error(f"Error handling solicitud message: {e}")
            return {
                "success": False,
                "error": "Error procesando mensaje de solicitud",
                "details": str(e)
            }
    
    async def _generate_missing_info_message(self, processed_data) -> str:
        """Generate message requesting missing information"""
        try:
            missing_fields = processed_data.missing_fields
            
            if "repuestos" in missing_fields:
                return """¡Hola! 👋 

Para ayudarte a encontrar los mejores repuestos, necesito que me digas:

🔧 **¿Qué repuestos necesitas?**
Por ejemplo: "pastillas de freno", "filtro de aceite", "amortiguadores"

También sería útil si me dices:
🚗 Marca y modelo de tu vehículo
📅 Año del vehículo
📍 Tu ciudad

¡Envíame esta información y te busco las mejores ofertas! 😊"""
            
            missing_info = []
            
            if "vehiculo.marca" in missing_fields:
                missing_info.append("🚗 Marca del vehículo (ej: Toyota, Chevrolet)")
            
            if "vehiculo.anio" in missing_fields:
                missing_info.append("📅 Año del vehículo")
            
            if "cliente.ciudad" in missing_fields:
                missing_info.append("📍 Tu ciudad")
            
            if missing_info:
                info_list = "\n".join([f"• {info}" for info in missing_info])
                return f"""Para completar tu solicitud, necesito la siguiente información:

{info_list}

¡Envíame estos datos y te busco las mejores ofertas! 😊"""
            
            return "¡Perfecto! Estoy procesando tu solicitud. Te responderé en un momento. 😊"
            
        except Exception as e:
            logger.error(f"Error generating missing info message: {e}")
            return "¿Podrías darme más detalles sobre los repuestos que necesitas? 😊"


# Global message processor instance
message_processor = MessageProcessor()