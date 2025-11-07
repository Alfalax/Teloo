"""
Conversation management service
"""

import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from app.models.conversation import (
    ConversationContext, 
    ConversationState, 
    MessageTurn,
    ConversationStats
)
from app.models.whatsapp import ProcessedMessage
from app.models.llm import ProcessedData
from app.core.redis import redis_manager
from app.core.config import settings
from app.services.nlp_service import nlp_service
from app.services.whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing WhatsApp conversations"""
    
    def __init__(self):
        self.conversation_ttl = settings.conversation_ttl_hours * 3600
        self.max_turns = settings.max_conversation_turns
        self.conversation_key_prefix = "conversation"
    
    async def gestionar_conversacion(self, telefono: str, mensaje: ProcessedMessage) -> Tuple[ConversationContext, str]:
        """
        Main conversation management function
        
        Args:
            telefono: Phone number (normalized)
            mensaje: Processed WhatsApp message
            
        Returns:
            Tuple of (conversation_context, response_message)
        """
        try:
            # Get or create conversation context
            conversation = await self.get_conversation_context(telefono)
            
            # Process the message with NLP
            processed_data = await nlp_service.procesar_mensaje_whatsapp(mensaje)
            
            # Add user turn to conversation
            user_turn = MessageTurn(
                message_id=mensaje.message_id,
                timestamp=mensaje.timestamp,
                from_user=True,
                content=mensaje.text_content or "",
                message_type=mensaje.message_type,
                processed_data=processed_data
            )
            conversation.add_turn(user_turn)
            
            # Update accumulated data
            await self._update_accumulated_data(conversation, processed_data)
            
            # Determine next action and generate response
            response_message = await self._determine_next_action(conversation)
            
            # Add system response turn
            system_turn = MessageTurn(
                message_id=f"system_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                from_user=False,
                content=response_message,
                message_type="text"
            )
            conversation.add_turn(system_turn)
            
            # Save conversation context
            await self.save_conversation_context(conversation)
            
            return conversation, response_message
            
        except Exception as e:
            logger.error(f"Error managing conversation for {telefono}: {e}")
            
            # Return error response
            error_response = "Disculpa, hubo un error procesando tu mensaje. ¿Podrías intentar de nuevo?"
            return await self.get_conversation_context(telefono), error_response
    
    async def get_conversation_context(self, telefono: str) -> ConversationContext:
        """Get or create conversation context"""
        try:
            conversation_key = f"{self.conversation_key_prefix}:{telefono}"
            data = await redis_manager.get(conversation_key)
            
            if data:
                conversation_dict = json.loads(data)
                conversation = ConversationContext(**conversation_dict)
                
                # Check if conversation is still valid (not expired)
                if datetime.now() - conversation.last_activity > timedelta(hours=settings.conversation_ttl_hours):
                    logger.info(f"Conversation for {telefono} expired, creating new one")
                    conversation = ConversationContext(phone_number=telefono)
                
                return conversation
            else:
                # Create new conversation
                conversation = ConversationContext(phone_number=telefono)
                return conversation
                
        except Exception as e:
            logger.error(f"Error getting conversation context for {telefono}: {e}")
            return ConversationContext(phone_number=telefono)
    
    async def save_conversation_context(self, conversation: ConversationContext):
        """Save conversation context to Redis"""
        try:
            conversation_key = f"{self.conversation_key_prefix}:{conversation.phone_number}"
            
            # Convert to dict for JSON serialization
            conversation_dict = conversation.model_dump()
            
            await redis_manager.set(
                conversation_key,
                json.dumps(conversation_dict, default=str),
                ttl=self.conversation_ttl
            )
            
        except Exception as e:
            logger.error(f"Error saving conversation context: {e}")
    
    async def _update_accumulated_data(self, conversation: ConversationContext, processed_data: ProcessedData):
        """Update accumulated data from processed message"""
        try:
            # Merge repuestos
            if processed_data.repuestos:
                for new_repuesto in processed_data.repuestos:
                    # Check if repuesto already exists
                    existing = False
                    for existing_repuesto in conversation.accumulated_repuestos:
                        if existing_repuesto.get("nombre", "").lower() == new_repuesto.get("nombre", "").lower():
                            # Update existing repuesto with new information
                            existing_repuesto.update(new_repuesto)
                            existing = True
                            break
                    
                    if not existing:
                        conversation.accumulated_repuestos.append(new_repuesto)
            
            # Merge vehiculo data
            if processed_data.vehiculo:
                if not conversation.accumulated_vehiculo:
                    conversation.accumulated_vehiculo = {}
                
                for key, value in processed_data.vehiculo.items():
                    if value:  # Only update if new value is not None/empty
                        conversation.accumulated_vehiculo[key] = value
            
            # Merge cliente data
            if processed_data.cliente:
                if not conversation.accumulated_cliente:
                    conversation.accumulated_cliente = {}
                
                for key, value in processed_data.cliente.items():
                    if value:  # Only update if new value is not None/empty
                        conversation.accumulated_cliente[key] = value
            
            # Ensure phone number is set
            if not conversation.accumulated_cliente:
                conversation.accumulated_cliente = {}
            conversation.accumulated_cliente["telefono"] = conversation.phone_number
            
            # Update completeness
            await self._calculate_completeness(conversation)
            
        except Exception as e:
            logger.error(f"Error updating accumulated data: {e}")
    
    async def _calculate_completeness(self, conversation: ConversationContext):
        """Calculate conversation completeness"""
        try:
            missing_fields = []
            total_fields = 6  # repuestos, vehiculo.marca, vehiculo.anio, cliente.nombre, cliente.ciudad, cliente.telefono
            complete_fields = 0
            
            # Check repuestos
            if not conversation.accumulated_repuestos:
                missing_fields.append("repuestos")
            else:
                complete_fields += 1
            
            # Check vehiculo
            if not conversation.accumulated_vehiculo:
                missing_fields.extend(["vehiculo.marca", "vehiculo.anio"])
            else:
                if conversation.accumulated_vehiculo.get("marca"):
                    complete_fields += 1
                else:
                    missing_fields.append("vehiculo.marca")
                
                if conversation.accumulated_vehiculo.get("anio"):
                    complete_fields += 1
                else:
                    missing_fields.append("vehiculo.anio")
            
            # Check cliente
            if not conversation.accumulated_cliente:
                missing_fields.extend(["cliente.nombre", "cliente.ciudad", "cliente.telefono"])
            else:
                if conversation.accumulated_cliente.get("nombre"):
                    complete_fields += 1
                else:
                    missing_fields.append("cliente.nombre")
                
                if conversation.accumulated_cliente.get("ciudad"):
                    complete_fields += 1
                else:
                    missing_fields.append("cliente.ciudad")
                
                # Phone is always set from conversation
                complete_fields += 1
            
            conversation.missing_fields = missing_fields
            conversation.completeness_score = complete_fields / total_fields
            
        except Exception as e:
            logger.error(f"Error calculating completeness: {e}")
            conversation.completeness_score = 0.0
    
    async def _determine_next_action(self, conversation: ConversationContext) -> str:
        """Determine next action and generate response"""
        try:
            # Check if we have enough information to create solicitud
            if conversation.completeness_score >= 0.7:  # 70% complete
                if conversation.state != ConversationState.SOLICITUD_CREATED:
                    # Ready to create solicitud
                    conversation.state = ConversationState.CREATING_SOLICITUD
                    return await self._generate_confirmation_message(conversation)
                else:
                    # Solicitud already created, provide status
                    return await self._generate_status_message(conversation)
            
            # Need more information
            conversation.state = ConversationState.GATHERING_INFO
            return await self._generate_clarification_message(conversation)
            
        except Exception as e:
            logger.error(f"Error determining next action: {e}")
            return "¿Podrías proporcionar más detalles sobre los repuestos que necesitas?"
    
    async def _generate_confirmation_message(self, conversation: ConversationContext) -> str:
        """Generate confirmation message before creating solicitud"""
        try:
            message_parts = ["Perfecto! He recopilado la siguiente información:"]
            
            # Add repuestos
            if conversation.accumulated_repuestos:
                repuestos_list = []
                for repuesto in conversation.accumulated_repuestos:
                    nombre = repuesto.get("nombre", "repuesto")
                    cantidad = repuesto.get("cantidad", 1)
                    if cantidad > 1:
                        repuestos_list.append(f"• {cantidad}x {nombre}")
                    else:
                        repuestos_list.append(f"• {nombre}")
                
                message_parts.append(f"\n*Repuestos:*\n" + "\n".join(repuestos_list))
            
            # Add vehiculo
            if conversation.accumulated_vehiculo:
                vehiculo = conversation.accumulated_vehiculo
                vehiculo_str = f"{vehiculo.get('marca', '')} {vehiculo.get('linea', '')} {vehiculo.get('anio', '')}".strip()
                message_parts.append(f"\n*Vehículo:* {vehiculo_str}")
            
            # Add cliente
            if conversation.accumulated_cliente:
                cliente = conversation.accumulated_cliente
                cliente_parts = []
                if cliente.get("nombre"):
                    cliente_parts.append(f"Nombre: {cliente['nombre']}")
                if cliente.get("ciudad"):
                    cliente_parts.append(f"Ciudad: {cliente['ciudad']}")
                
                if cliente_parts:
                    message_parts.append(f"\n*Cliente:* {', '.join(cliente_parts)}")
            
            message_parts.append("\n¿Confirmas que la información es correcta? Responde *SÍ* para buscar ofertas o *NO* para hacer correcciones.")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error generating confirmation message: {e}")
            return "¿Confirmas que quieres buscar ofertas con la información proporcionada?"
    
    async def _generate_clarification_message(self, conversation: ConversationContext) -> str:
        """Generate message asking for missing information"""
        try:
            # Get questions for missing information
            questions = []
            
            if "repuestos" in conversation.missing_fields:
                questions.append("¿Qué repuestos necesitas?")
            
            if "vehiculo.marca" in conversation.missing_fields:
                questions.append("¿Cuál es la marca de tu vehículo?")
            elif "vehiculo.anio" in conversation.missing_fields:
                questions.append("¿De qué año es tu vehículo?")
            
            if "cliente.nombre" in conversation.missing_fields:
                questions.append("¿Cuál es tu nombre?")
            elif "cliente.ciudad" in conversation.missing_fields:
                questions.append("¿En qué ciudad te encuentras?")
            
            if not questions:
                return "¿Hay algo más que quieras agregar sobre los repuestos que necesitas?"
            
            # Return first question
            return questions[0]
            
        except Exception as e:
            logger.error(f"Error generating clarification message: {e}")
            return "¿Podrías proporcionar más información sobre tu solicitud?"
    
    async def _generate_status_message(self, conversation: ConversationContext) -> str:
        """Generate status message for existing solicitud"""
        if conversation.solicitud_id:
            return f"Tu solicitud #{conversation.solicitud_id} está siendo procesada. Te notificaremos cuando tengamos ofertas disponibles."
        else:
            return "Estamos procesando tu solicitud. Te contactaremos pronto con las mejores ofertas."
    
    async def validate_completitud(self, conversation: ConversationContext) -> bool:
        """Validate if conversation has enough information to create solicitud"""
        try:
            # Must have at least one repuesto
            if not conversation.accumulated_repuestos:
                return False
            
            # Must have vehicle brand
            if not conversation.accumulated_vehiculo or not conversation.accumulated_vehiculo.get("marca"):
                return False
            
            # Must have client phone (always available) and preferably city
            if not conversation.accumulated_cliente or not conversation.accumulated_cliente.get("telefono"):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating completeness: {e}")
            return False
    
    async def get_conversation_stats(self) -> ConversationStats:
        """Get conversation statistics"""
        try:
            # This would typically query a database or aggregate Redis data
            # For now, return basic stats
            
            stats = ConversationStats(
                total_conversations=0,
                active_conversations=0,
                completed_conversations=0,
                avg_turns_per_conversation=0.0,
                avg_completion_time_minutes=0.0,
                completion_rate=0.0
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return ConversationStats()
    
    async def close_conversation(self, telefono: str, reason: str = "completed"):
        """Close a conversation"""
        try:
            conversation = await self.get_conversation_context(telefono)
            conversation.state = ConversationState.CLOSED
            conversation.updated_at = datetime.now()
            
            await self.save_conversation_context(conversation)
            
            logger.info(f"Conversation closed for {telefono}: {reason}")
            
        except Exception as e:
            logger.error(f"Error closing conversation for {telefono}: {e}")
    
    async def get_active_conversations(self) -> List[ConversationContext]:
        """Get list of active conversations"""
        try:
            # This would typically scan Redis keys or query a database
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting active conversations: {e}")
            return []
    
    async def get_or_create_conversation(self, telefono: str) -> ConversationContext:
        """Get or create conversation (alias for get_conversation_context)"""
        return await self.get_conversation_context(telefono)
    
    async def add_message_to_conversation(self, telefono: str, content: str, from_user_type: str):
        """Add a message to the conversation"""
        try:
            conversation = await self.get_conversation_context(telefono)
            
            turn = MessageTurn(
                message_id=f"{from_user_type}_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                from_user=(from_user_type == "user"),
                content=content,
                message_type="text"
            )
            
            conversation.add_turn(turn)
            await self.save_conversation_context(conversation)
            
        except Exception as e:
            logger.error(f"Error adding message to conversation: {e}")
    
    async def set_solicitud_id(self, telefono: str, solicitud_id: str):
        """Set solicitud ID for conversation"""
        try:
            conversation = await self.get_conversation_context(telefono)
            conversation.solicitud_id = solicitud_id
            conversation.state = ConversationState.SOLICITUD_CREATED
            await self.save_conversation_context(conversation)
            
        except Exception as e:
            logger.error(f"Error setting solicitud ID: {e}")
    
    async def clear_solicitud_id(self, telefono: str):
        """Clear solicitud ID from conversation"""
        try:
            conversation = await self.get_conversation_context(telefono)
            conversation.solicitud_id = None
            conversation.state = ConversationState.COMPLETED
            await self.save_conversation_context(conversation)
            
        except Exception as e:
            logger.error(f"Error clearing solicitud ID: {e}")


# Global conversation service instance
conversation_service = ConversationService()