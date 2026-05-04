"""
WhatsApp message processor
Adapts WhatsApp messages to work with existing NLP pipeline
Based on proven Telegram implementation
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.redis import redis_manager
from app.services.whatsapp_service import whatsapp_service
from app.services.conversation_service import conversation_service
from app.services.context_manager import get_context_manager
from app.models.whatsapp import ProcessedMessage
from app.services.bot_prompts import ERR_TECHNICAL, ERR_AUDIO_TRANSCRIPTION, MSG_CANCELLED
import httpx
import os

logger = logging.getLogger(__name__)

# Core API URL
CORE_API_URL = os.getenv("CORE_API_URL", "http://core-api:8000")


def format_repuestos_list(repuestos: list, max_items: int = 7) -> str:
    """
    Formatea la lista de repuestos para mostrar al usuario.
    Si hay más de max_items, muestra solo la cantidad total.
    
    Args:
        repuestos: Lista de repuestos
        max_items: Número máximo de items a mostrar en detalle (default: 7)
    
    Returns:
        String formateado con la lista de repuestos
    """
    if not repuestos:
        return "🔧 Repuestos: Ninguno\n"
    
    num_repuestos = len(repuestos)
    
    if num_repuestos > max_items:
        # Mostrar solo cantidad total
        return f"🔧 Repuestos: {num_repuestos} items en total\n"
    else:
        # Mostrar detalle completo
        result = "🔧 Repuestos:\n"
        for rep in repuestos:
            result += f"• {rep.get('cantidad', 1)}x {rep['nombre']}\n"
        return result


class WhatsAppMessageProcessor:
    """Process WhatsApp messages using existing NLP pipeline"""
    
    def __init__(self):
        self.queue_key = "whatsapp:message_queue"
    
    async def process_queued_messages(self):
        """Process messages from the WhatsApp queue"""
        try:
            while True:
                # Get message from queue (blocking with timeout)
                message_data = await redis_manager.brpop(self.queue_key, timeout=5)
                
                if message_data:
                    _, message_json = message_data
                    message_dict = json.loads(message_json)
                    
                    # Convert to ProcessedMessage
                    whatsapp_message = ProcessedMessage(
                        message_id=message_dict["message_id"],
                        from_number=message_dict["from_number"],
                        timestamp=datetime.fromisoformat(message_dict["timestamp"]),
                        message_type=message_dict["message_type"],
                        text_content=message_dict.get("text_content"),
                        media_url=message_dict.get("media_url"),
                        media_type=message_dict.get("media_type"),
                        context_message_id=message_dict.get("context_message_id")
                    )
                    
                    await self.process_message(whatsapp_message)
                
        except Exception as e:
            logger.error(f"Error processing queued WhatsApp messages: {e}")
    
    async def _transcribe_whatsapp_audio(self, whatsapp_message: ProcessedMessage) -> Optional[str]:
        """Download and transcribe a WhatsApp voice/audio message using Whisper."""
        media_id = whatsapp_message.media_url  # stored as media_id at ingest time
        if not media_id:
            return None
        try:
            media_url = await whatsapp_service.get_media_url(media_id)
            if not media_url:
                logger.warning(f"Could not resolve media URL for id {media_id}")
                return None
            audio_bytes = await whatsapp_service.download_media(media_url)
            if not audio_bytes:
                logger.warning(f"Empty audio download for {media_id}")
                return None
            from app.services.llm.whisper_adapter import whisper_adapter
            transcription = await whisper_adapter._call_whisper_api(audio_bytes)
            if transcription:
                logger.info(f"WhatsApp audio transcribed ({len(audio_bytes)} bytes): {transcription[:80]}...")
            return transcription
        except Exception as e:
            logger.error(f"Error transcribing WhatsApp audio: {e}")
            return None

    async def process_message(self, whatsapp_message: ProcessedMessage) -> Dict[str, Any]:
        """
        Process a single WhatsApp message with context-aware interpretation

        Args:
            whatsapp_message: Processed WhatsApp message

        Returns:
            Dict with processing result
        """
        try:
            logger.info(f"Processing WhatsApp message {whatsapp_message.message_id} from {whatsapp_message.from_number}")

            # Transcribe audio/voice before any intent detection
            if whatsapp_message.media_type in ("voice", "audio") and whatsapp_message.media_url:
                transcription = await self._transcribe_whatsapp_audio(whatsapp_message)
                if transcription:
                    whatsapp_message.text_content = transcription
                    whatsapp_message.media_url = None  # avoid re-processing
                else:
                    await whatsapp_service.send_text_message(
                        whatsapp_message.from_number,
                        ERR_AUDIO_TRANSCRIPTION,
                    )
                    return {"success": False, "action": "audio_transcription_failed"}

            # Use phone number as unique identifier
            user_id = whatsapp_message.from_number
            phone_number = whatsapp_message.from_number
            
            # Get context manager
            context_mgr = get_context_manager()
            
            # Save user message to history
            if whatsapp_message.text_content:
                await context_mgr.add_message(user_id, "user", whatsapp_message.text_content)
            
            # Interpret message with context using GPT-4
            interpretation = None
            if whatsapp_message.text_content:
                interpretation = await context_mgr.interpret_with_context(user_id, whatsapp_message.text_content)
                logger.info(f"🎯 Intent: {interpretation.get('intent')} - {interpretation.get('action')}")
            
            # Get or create conversation context
            conversation = await conversation_service.get_or_create_conversation(phone_number)
            
            # Handle based on interpreted intent
            if interpretation and interpretation.get('intent') == 'cancel':
                await context_mgr.clear_pending_action(user_id)
                await redis_manager.delete(f"solicitud_draft:whatsapp:{whatsapp_message.from_number}")
                await redis_manager.delete(f"ciudad_invalida:whatsapp:{whatsapp_message.from_number}")
                
                await whatsapp_service.send_text_message(
                    whatsapp_message.from_number,
                    MSG_CANCELLED,
                )
                return {"success": True, "action": "cancelled"}
            
            elif interpretation and interpretation.get('intent') == 'respond_offers':
                # User is responding to offers
                return await self._handle_evaluation_response(whatsapp_message, conversation)
            
            elif interpretation and interpretation.get('intent') == 'correct_data':
                # Route through solicitud flow — the LLM handles corrections naturally
                return await self._handle_solicitud_message(whatsapp_message, conversation)
            
            # Check if this is a response to an evaluation result (fallback)
            elif whatsapp_message.text_content and await self._is_evaluation_response(whatsapp_message.text_content, conversation):
                return await self._handle_evaluation_response(whatsapp_message, conversation)
            
            # Process as new solicitud or continuation
            return await self._handle_solicitud_message(whatsapp_message, conversation)
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp message {whatsapp_message.message_id}: {e}")
            return {
                "success": False,
                "error": "Error interno procesando mensaje",
                "details": str(e)
            }
    
    async def _is_evaluation_response(self, text: str, conversation) -> bool:
        """
        Check if message is a response to evaluation results
        
        ALWAYS returns True if there's a solicitud_id, so we use AI to interpret the response.
        This handles typos, variations, and natural language better than keyword matching.
        """
        try:
            # If there's a solicitud_id, treat it as a potential evaluation response
            # Let the AI decide what the user meant
            if conversation.solicitud_id:
                logger.info(f"Message will be processed as evaluation response (solicitud_id: {conversation.solicitud_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking evaluation response: {e}")
            return False
    
    async def _handle_evaluation_response(self, whatsapp_message: ProcessedMessage, conversation) -> Dict[str, Any]:
        """Handle client response to evaluation results"""
        try:
            logger.info(f"Handling evaluation response from {whatsapp_message.from_number}")
            
            # Call Core API to process client response
            from app.core.config import settings
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.core_api_url}/v1/solicitudes/{conversation.solicitud_id}/respuesta-cliente",
                    json={
                        "respuesta_texto": whatsapp_message.text_content,
                        "usar_nlp": True  # ALWAYS use AI to interpret responses (handles typos, variations, natural language)
                    },
                    headers={
                        "X-Service-API-Key": settings.service_api_key,
                        "X-Service-Name": "agent-ia"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success"):
                        # Send success message via WhatsApp
                        response_message = result.get("mensaje", "Respuesta procesada correctamente")
                        await whatsapp_service.send_text_message(whatsapp_message.from_number, response_message)
                        
                        # Clear solicitud_id from conversation
                        await conversation_service.clear_solicitud_id(whatsapp_message.from_number)
                        
                        logger.info(f"Evaluation response processed: {result.get('tipo_respuesta')}")
                        return result
                    else:
                        error_msg = result.get("error", "Error procesando respuesta")
                        await whatsapp_service.send_text_message(whatsapp_message.from_number, error_msg)
                        return result
                else:
                    error_msg = "Error procesando respuesta del cliente"
                    await whatsapp_service.send_text_message(whatsapp_message.from_number, error_msg)
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    }
            
        except Exception as e:
            logger.error(f"Error handling evaluation response: {e}")
            error_msg = "Lo siento, hubo un error procesando tu respuesta. ¿Podrías intentar de nuevo?"
            await whatsapp_service.send_text_message(whatsapp_message.from_number, error_msg)
            return {
                "success": False,
                "error": "Error procesando respuesta de evaluación",
                "details": str(e)
            }
    
    async def _handle_data_correction(
        self, 
        whatsapp_message: ProcessedMessage,
        conversation,
        interpretation: Dict,
        user_id: str
    ) -> Dict[str, Any]:
        """Handle data correction in draft solicitud"""
        try:
            logger.info(f"🔧 Handling data correction for user {user_id}")
            
            context_mgr = get_context_manager()
            pending = await context_mgr.get_pending_actions(user_id)
            
            if not pending or pending.get('type') != 'creating_request':
                # No draft to correct, process normally
                logger.info("No draft found, processing as normal message")
                return await self._handle_solicitud_message(whatsapp_message, conversation)
            
            # Extract field and value from interpretation
            field = interpretation.get('extracted_data', {}).get('field')
            value = interpretation.get('extracted_data', {}).get('value')
            
            if not field or not value:
                # Can't determine what to correct
                await whatsapp_service.send_text_message(
                    whatsapp_message.from_number,
                    "No entendí qué dato quieres corregir. Por favor especifica (ej: 'telefono 3001234567')"
                )
                return {"success": False, "error": "Could not determine correction"}
            
            # Update draft
            draft = pending.get('data', {}).get('draft', {})
            
            if field == 'telefono':
                draft['telefono'] = value
            elif field == 'nombre':
                draft['nombre_cliente'] = value
            elif field == 'ciudad':
                draft['ciudad'] = value
            
            # Save updated draft
            pending['data']['draft'] = draft
            await context_mgr.set_pending_action(user_id, 'creating_request', pending['data'])
            
            # Show updated summary
            response = await self._format_draft_summary(draft)
            await whatsapp_service.send_text_message(whatsapp_message.from_number, response)
            
            logger.info(f"✅ Data corrected: {field} = {value}")
            
            return {"success": True, "action": "data_corrected"}
            
        except Exception as e:
            logger.error(f"Error handling data correction: {e}")
            return {"success": False, "error": str(e)}
    
    async def _format_draft_summary(self, draft: Dict) -> str:
        """Format draft summary for display"""
        missing = []
        if not draft.get('repuestos'): missing.append("repuestos")
        if not draft.get('marca'): missing.append("marca del vehículo")
        if not draft.get('anio'): missing.append("año del vehículo")
        if not draft.get('nombre_cliente'): missing.append("nombre del cliente")
        if not draft.get('telefono'): missing.append("teléfono del cliente")
        if not draft.get('ciudad'): missing.append("ciudad")
        
        if missing:
            return f"🤔 Para crear tu solicitud necesito la siguiente información:\n" + \
                   "\n".join([f"❌ {m}" for m in missing]) + \
                   "\n\n📝 Por favor envíame la información que falta."
        
        # All data complete
        response = "✅ Perfecto, actualicé la información:\n\n"
        response += f"👤 Cliente: {draft.get('nombre_cliente', 'N/A')}\n"
        response += f"📞 Teléfono: {draft.get('telefono', 'N/A')}\n"
        response += f"📍 Ciudad: {draft.get('ciudad', 'N/A')}\n"
        response += f"🚗 Vehículo: {draft.get('marca', 'N/A')} {draft.get('modelo', '')} {draft.get('anio', '')}\n\n"
        response += format_repuestos_list(draft.get('repuestos', []))
        response += "\n¿Ahora sí está todo correcto?"
        
        return response
    
    async def _handle_solicitud_message(
        self,
        whatsapp_message: ProcessedMessage,
        conversation,
    ) -> Dict[str, Any]:
        """Handle message as part of solicitud creation process."""
        try:
            from app.core.config import settings
            from app.services.solicitud_bot_flow import run_solicitud_flow

            phone = whatsapp_message.from_number
            message_content = whatsapp_message.text_content or ""

            # Welcome detection — short greeting with no draft in progress
            _GREETINGS = {
                "hola", "hello", "hi", "buenas", "buenos días", "buenas tardes",
                "buenas noches", "buen dia", "buen día", "ola", "hey",
            }
            draft_key = f"solicitud_draft:whatsapp:{phone}"
            existing_draft = await redis_manager.get_json(draft_key)

            if not existing_draft and message_content.lower().strip() in _GREETINGS:
                welcome = (
                    "👋 ¡Hola! Soy el asistente de *TeLOO*.\n\n"
                    "Te ayudo a conseguir los mejores repuestos para tu vehículo al mejor precio.\n\n"
                    "Para crear tu solicitud, contame:\n"
                    "🔧 ¿Qué repuestos necesitás?\n"
                    "🚗 Marca, modelo y año de tu vehículo\n"
                    "📍 Tu ciudad\n"
                    "👤 Tu nombre y teléfono\n\n"
                    "_Podés enviarme un mensaje de voz o texto. ¡Como prefieras!_ 😊"
                )
                await whatsapp_service.send_text_message(phone, welcome)
                return {"success": True, "action": "welcome_sent"}

            async def send_fn(msg: str) -> None:
                await whatsapp_service.send_text_message(phone, msg)

            async def send_buttons_fn(body_text: str, buttons: list) -> None:
                await whatsapp_service.send_interactive_buttons(phone, body_text, buttons)

            result = await run_solicitud_flow(
                message_content=message_content,
                draft_key=draft_key,
                ciudad_invalida_key=f"ciudad_invalida:whatsapp:{phone}",
                send_fn=send_fn,
                settings=settings,
                send_buttons_fn=send_buttons_fn,
            )

            # When the bot is waiting for user input, offer a cancel button
            WAITING_ACTIONS = {
                "info_requested",
                "invalid_phone_detected",
                "ciudad_validation_pending",
                "year_requested",
            }
            if result.get("action") in WAITING_ACTIONS:
                await send_buttons_fn(
                    "¿Querés cancelar la solicitud?",
                    [
                        {"id": "cancel_solicitud", "title": "Cancelar"},
                        {"id": "restart_solicitud", "title": "Empezar de nuevo"},
                    ],
                )

            return result

        except Exception as e:
            logger.error(f"Error handling WhatsApp solicitud message: {e}")
            await whatsapp_service.send_text_message(
                whatsapp_message.from_number,
                ERR_TECHNICAL,
            )
            return {"success": False, "error": str(e)}


# Global WhatsApp message processor instance
whatsapp_message_processor = WhatsAppMessageProcessor()
