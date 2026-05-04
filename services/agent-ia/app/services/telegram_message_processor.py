"""
Telegram message processor
Adapts Telegram messages to work with existing NLP pipeline
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime

from app.core.redis import redis_manager
from app.services.telegram_service import telegram_service
from app.services.conversation_service import conversation_service
from app.services.nlp_service import nlp_service
from app.services.solicitud_service import solicitud_service
from app.services.context_manager import get_context_manager
from app.models.telegram import ProcessedTelegramMessage
from app.models.whatsapp import ProcessedMessage  # Reuse WhatsApp model for compatibility
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


def normalize_city_name(city_name: str) -> str:
    """
    Normaliza el nombre de la ciudad para búsqueda insensible a tildes.
    
    Args:
        city_name: Nombre de la ciudad a normalizar
    
    Returns:
        Nombre de la ciudad normalizado
    """
    import unicodedata
    
    # Convertir a mayúsculas y remover tildes
    normalized = unicodedata.normalize('NFD', city_name.upper())
    normalized = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
    
    return normalized


class TelegramMessageProcessor:
    """Process Telegram messages using existing NLP pipeline"""
    
    def __init__(self):
        self.queue_key = "telegram:message_queue"
    
    async def process_queued_messages(self):
        """Process messages from the Telegram queue"""
        try:
            while True:
                # Get message from queue (blocking with timeout)
                message_data = await redis_manager.brpop(self.queue_key, timeout=5)
                
                if message_data:
                    _, message_json = message_data
                    message_dict = json.loads(message_json)
                    
                    # Convert to ProcessedTelegramMessage
                    telegram_message = ProcessedTelegramMessage(
                        message_id=message_dict["message_id"],
                        chat_id=message_dict["chat_id"],
                        user_id=message_dict["user_id"],
                        username=message_dict.get("username"),
                        timestamp=datetime.fromisoformat(message_dict["timestamp"]),
                        message_type=message_dict["message_type"],
                        text_content=message_dict.get("text_content"),
                        media_file_id=message_dict.get("media_file_id"),
                        media_type=message_dict.get("media_type")
                    )
                    
                    await self.process_message(telegram_message)
                
        except Exception as e:
            logger.error(f"Error processing queued Telegram messages: {e}")
    
    async def process_message(self, telegram_message: ProcessedTelegramMessage) -> Dict[str, Any]:
        """
        Process a single Telegram message with context-aware interpretation
        
        Args:
            telegram_message: Processed Telegram message
            
        Returns:
            Dict with processing result
        """
        try:
            logger.info(f"Processing Telegram message {telegram_message.message_id} from chat {telegram_message.chat_id}")
            
            # Use chat_id as unique identifier
            user_id = str(telegram_message.chat_id)
            phone_number = f"+tg{telegram_message.chat_id}"
            
            # Get context manager
            context_mgr = get_context_manager()
            
            # Save user message to history
            if telegram_message.text_content:
                await context_mgr.add_message(user_id, "user", telegram_message.text_content)
            
            # Interpret message with context using GPT-4
            interpretation = None
            if telegram_message.text_content:
                interpretation = await context_mgr.interpret_with_context(user_id, telegram_message.text_content)
                logger.info(f"🎯 Intent: {interpretation.get('intent')} - {interpretation.get('action')}")
            
            # Convert Telegram message to WhatsApp-compatible format
            whatsapp_message = await self._convert_to_whatsapp_format(telegram_message)
            
            # Get or create conversation context
            conversation = await conversation_service.get_or_create_conversation(phone_number)
            
            # Handle based on interpreted intent
            if interpretation and interpretation.get('intent') == 'cancel':
                # User wants to cancel current operation
                await context_mgr.clear_pending_action(user_id)
                
                # Clear conversation history so NEXT message starts fresh
                await context_mgr.clear_history(user_id)
                
                # Clear draft from Redis
                draft_key = f"solicitud_draft:{telegram_message.chat_id}"
                await redis_manager.delete(draft_key)
                
                await telegram_service.send_message(
                    telegram_message.chat_id,
                    "✅ Entendido, he cancelado todo.\n\nSi cambias de opinión y necesitas repuestos, solo escríbeme. ¡Estoy aquí para ayudarte!"
                )
                return {"success": True, "action": "cancelled"}
            
            elif interpretation and interpretation.get('intent') == 'respond_offers':
                # User is responding to offers
                return await self._handle_evaluation_response(telegram_message, conversation)
            
            elif interpretation and interpretation.get('intent') == 'correct_data':
                # User is correcting data in draft
                return await self._handle_data_correction(telegram_message, conversation, interpretation, user_id)
            
            # Check if this is a response to an evaluation result (fallback)
            elif telegram_message.text_content and await self._is_evaluation_response(telegram_message.text_content, conversation):
                return await self._handle_evaluation_response(telegram_message, conversation)
            
            # Process as new solicitud or continuation
            return await self._handle_solicitud_message(telegram_message, conversation, whatsapp_message)
            
        except Exception as e:
            logger.error(f"Error processing Telegram message {telegram_message.message_id}: {e}")
            return {
                "success": False,
                "error": "Error interno procesando mensaje",
                "details": str(e)
            }
    
    async def _convert_to_whatsapp_format(self, telegram_message: ProcessedTelegramMessage) -> ProcessedMessage:
        """
        Convert Telegram message to WhatsApp format for compatibility
        
        This allows us to reuse all existing NLP, conversation, and solicitud logic
        """
        # Download media if present
        media_url = None
        if telegram_message.media_file_id:
            try:
                # Get file URL from Telegram
                media_url = await telegram_service.get_file(telegram_message.media_file_id)
                logger.info(f"Media URL obtained: {media_url}")
            except Exception as e:
                logger.error(f"Error getting media URL: {e}")
        
        # Create WhatsApp-compatible message
        return ProcessedMessage(
            message_id=telegram_message.message_id,
            from_number=f"+tg{telegram_message.chat_id}",  # Use chat_id as phone
            timestamp=telegram_message.timestamp,
            message_type=telegram_message.message_type,
            text_content=telegram_message.text_content,
            media_url=media_url,
            media_type=telegram_message.media_type
        )
    
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
    
    async def _handle_evaluation_response(self, telegram_message: ProcessedTelegramMessage, conversation) -> Dict[str, Any]:
        """Handle client response to evaluation results"""
        try:
            logger.info(f"Handling evaluation response from chat {telegram_message.chat_id}")
            
            # Call Core API to process client response
            import httpx
            from app.core.config import settings
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.core_api_url}/v1/solicitudes/{conversation.solicitud_id}/respuesta-cliente",
                    json={
                        "respuesta_texto": telegram_message.text_content,
                        "usar_nlp": True  # ALWAYS use AI to interpret responses (handles typos, variations, natural language)
                    },
                    headers={
                        "X-Service-API-Key": str(settings.service_api_key or ""),
                        "X-Service-Name": str(settings.service_name or "agent-ia")
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success"):
                        # Send success message via Telegram
                        response_message = result.get("mensaje", "Respuesta procesada correctamente")
                        await telegram_service.send_message(telegram_message.chat_id, response_message)
                        
                        # Clear solicitud_id from conversation
                        await conversation_service.clear_solicitud_id(f"+tg{telegram_message.chat_id}")
                        
                        logger.info(f"Evaluation response processed: {result.get('tipo_respuesta')}")
                        return result
                    else:
                        error_msg = result.get("error", "Error procesando respuesta")
                        await telegram_service.send_message(telegram_message.chat_id, error_msg)
                        return result
                else:
                    error_msg = "Error procesando respuesta del cliente"
                    await telegram_service.send_message(telegram_message.chat_id, error_msg)
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling evaluation response: {e}")
            error_msg = "Lo siento, hubo un error procesando tu respuesta. ¿Podrías intentar de nuevo?"
            await telegram_service.send_message(telegram_message.chat_id, error_msg)
            return {
                "success": False,
                "error": "Error procesando respuesta de evaluación",
                "details": str(e)
            }
    
    async def _handle_data_correction(
        self, 
        telegram_message: ProcessedTelegramMessage,
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
                whatsapp_message = await self._convert_to_whatsapp_format(telegram_message)
                return await self._handle_solicitud_message(telegram_message, conversation, whatsapp_message)
            
            # Extract field and value from interpretation
            field = interpretation.get('extracted_data', {}).get('field')
            value = interpretation.get('extracted_data', {}).get('value')
            
            if not field or not value:
                # Can't determine what to correct
                await telegram_service.send_message(
                    telegram_message.chat_id,
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
            await telegram_service.send_message(telegram_message.chat_id, response)
            
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
        telegram_message: ProcessedTelegramMessage,
        conversation,
        whatsapp_message: ProcessedMessage,
    ) -> Dict[str, Any]:
        """Handle message as part of solicitud creation process."""
        try:
            logger.info(f"Handling solicitud message from chat {telegram_message.chat_id}")

            import httpx
            from app.core.config import settings
            from app.services.solicitud_bot_flow import run_solicitud_flow

            try:
                from app.services.solicitud_bot_flow import run_solicitud_flow

                message_content = telegram_message.text_content or ""
                draft_key = f"solicitud_draft:{telegram_message.chat_id}"
                ciudad_invalida_key = f"ciudad_invalida:{telegram_message.chat_id}"

                async def send_fn(msg: str) -> None:
                    await telegram_service.send_message(telegram_message.chat_id, msg)

                # --- COMANDOS ESPECIALES ---
                comando = message_content.strip().lower()

                if comando in ["/start", "/inicio"]:
                    welcome = (
                        "👋 ¡Hola! Soy el asistente de *TeLOO*.\n\n"
                        "Te ayudo a conseguir los mejores repuestos para tu vehículo al mejor precio.\n\n"
                        "Para crear tu solicitud, contame:\n"
                        "🔧 ¿Qué repuestos necesitás?\n"
                        "🚗 Marca, modelo y año de tu vehículo\n"
                        "📍 Tu ciudad\n"
                        "👤 Tu nombre y teléfono\n\n"
                        "Podés enviarme un *mensaje de voz* o texto. ¡Como prefieras! 😊\n\n"
                        "💡 Tip: si en algún momento querés empezar de nuevo, escribí /reiniciar"
                    )
                    await telegram_service.send_message(telegram_message.chat_id, welcome)
                    return {"success": True, "action": "welcome_sent"}

                elif comando in ["/reiniciar", "/cancelar", "/empezar", "/nuevo"]:
                    draft_key = f"solicitud_draft:{telegram_message.chat_id}"
                    await redis_manager.delete(draft_key)
                    
                    help_msg = "🔄 Conversación reiniciada.\n\n"
                    help_msg += "Envíame la información de tu solicitud:\n"
                    help_msg += "• Puedes enviar un audio\n"
                    help_msg += "• O un mensaje de texto con:\n"
                    help_msg += "  - Tu nombre y teléfono\n"
                    help_msg += "  - Repuestos que necesitas\n"
                    help_msg += "  - Marca, modelo y año del vehículo\n"
                    help_msg += "  - Tu ciudad"
                    
                    await telegram_service.send_message(telegram_message.chat_id, help_msg)
                    
                    return {
                        "success": True,
                        "action": "conversation_restarted"
                    }
                
                # /ayuda - Mostrar comandos disponibles
                elif comando in ["/ayuda", "/help", "/comandos"]:
                    help_msg = "🤖 *Comandos disponibles:*\n\n"
                    help_msg += "📝 *Para crear solicitud:*\n"
                    help_msg += "• Envía un audio con tu información\n"
                    help_msg += "• O escribe los datos directamente\n\n"
                    help_msg += "🔄 *Comandos útiles:*\n"
                    help_msg += "• /reiniciar - Empezar de nuevo\n"
                    help_msg += "• /cancelar - Cancelar solicitud actual\n"
                    help_msg += "• /ayuda - Ver este mensaje\n\n"
                    help_msg += "💡 *Tip:* Puedes hablar naturalmente, no necesitas comandos específicos."
                    
                    await telegram_service.send_message(telegram_message.chat_id, help_msg)
                    
                    return {
                        "success": True,
                        "action": "help_shown"
                    }
                
                # Procesar audio/voz con Whisper
                if whatsapp_message.media_url and whatsapp_message.media_type in ["voice", "audio"] and not getattr(telegram_message, "_audio_processed", False):
                    logger.info(f"Processing audio/voice from URL: {whatsapp_message.media_url}")

                    
                    try:
                        # Descargar el archivo de audio desde Telegram
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            audio_response = await client.get(whatsapp_message.media_url)
                            if audio_response.status_code == 200:
                                audio_content = audio_response.content
                                logger.info(f"Audio file downloaded: {len(audio_content)} bytes")
                                
                                # Transcribir directamente con Whisper adapter
                                from app.services.llm.whisper_adapter import whisper_adapter
                                
                                # Llamar directamente al API de Whisper con los bytes
                                transcription = await whisper_adapter._call_whisper_api(audio_content)
                                
                                if transcription:
                                    logger.info(f"Audio transcribed successfully: {transcription[:100]}...")
                                    message_content = transcription
                                    
                                    # Get extraction from audio (Using LLM for better results)
                                    extracted_data = await nlp_service.extract_solicitud_data(transcription)
                                    
                                    # PASO CRÍTICO: Si ya existe un draft, fusionar los datos nuevos con los viejos
                                    # Esto evita que el bot "olvide" lo que ya se le envió (ej. teléfono o ciudad)
                                    existing_draft = await redis_manager.get_json(f"solicitud_draft:{telegram_message.chat_id}")
                                    if existing_draft:
                                        logger.info(f"🔄 Merging audio extraction with existing draft for {telegram_message.chat_id}")
                                        
                                        # Fusionar cliente (nombre, teléfono, ciudad)
                                        # Si el audio no trajo datos de cliente, usar los del draft
                                        if not extracted_data.get("cliente") or not any(extracted_data["cliente"].values()):
                                            extracted_data["cliente"] = existing_draft.get("cliente", {})
                                        else:
                                            # Hay datos nuevos, pero completar los que falten con los del draft
                                            for field in ["nombre", "telefono", "ciudad", "ciudad_display"]:
                                                if not extracted_data["cliente"].get(field) and existing_draft.get("cliente", {}).get(field):
                                                    extracted_data["cliente"][field] = existing_draft["cliente"][field]
                                        
                                        # Fusionar vehículo (marca, línea, año)
                                        if not extracted_data.get("vehiculo") or not any(extracted_data["vehiculo"].values()):
                                            extracted_data["vehiculo"] = existing_draft.get("vehiculo", {})
                                        else:
                                            for field in ["marca", "linea", "anio"]:
                                                if not extracted_data["vehiculo"].get(field) and existing_draft.get("vehiculo", {}).get(field):
                                                    extracted_data["vehiculo"][field] = existing_draft["vehiculo"][field]
                                        
                                        # Fusionar repuestos
                                        if not extracted_data.get("repuestos") and existing_draft.get("repuestos"):
                                            extracted_data["repuestos"] = existing_draft["repuestos"]
                                        
                                        # Preservar metadatos del draft (municipio_id, etc.)
                                        for key in ["_municipio_id", "_departamento", "_status"]:
                                            if key in existing_draft and key not in extracted_data:
                                                extracted_data[key] = existing_draft[key]

                                    # Guardar en Redis ANTES de llamar recursivamente
                                    await redis_manager.set_json(f"solicitud_draft:{telegram_message.chat_id}", extracted_data, ttl=3600)
                                    
                                    # Marcar como procesado y re-lanzar como texto
                                    telegram_message.text_content = transcription
                                    telegram_message._audio_processed = True
                                    whatsapp_message.media_url = None # Evitar re-procesar audio
                                    
                                    return await self._handle_solicitud_message(telegram_message, conversation, whatsapp_message)

                                else:
                                    logger.warning(f"Audio transcription returned empty")
                                    message_content = "Audio recibido pero no se pudo transcribir"
                            else:
                                logger.error(f"Failed to download audio: HTTP {audio_response.status_code}")
                    except Exception as e:
                        logger.error(f"Error processing audio: {e}")
                
                # Procesar Excel
                elif whatsapp_message.media_url and whatsapp_message.media_type == "document":
                    logger.info(f"Processing Excel file from URL: {whatsapp_message.media_url}")
                    
                    try:
                        # Descargar el archivo desde Telegram
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            file_response = await client.get(whatsapp_message.media_url)
                            if file_response.status_code == 200:
                                file_content = file_response.content
                                logger.info(f"Excel file downloaded: {len(file_content)} bytes")
                                
                                # Procesar con file_processor directamente
                                from app.services.file_processor import file_processor
                                file_result = await file_processor._process_excel(file_content, message_content)
                                
                                # Verificar si se extrajeron repuestos (ya sea en repuestos o extracted_entities)
                                repuestos_list = file_result.repuestos or file_result.extracted_entities.get("repuestos", [])
                                
                                if repuestos_list and len(repuestos_list) > 0:
                                    # Usar los repuestos extraídos del Excel
                                    logger.info(f"Excel processed successfully: {len(repuestos_list)} repuestos found")
                                    message_content = f"{message_content}\n\nRepuestos del Excel:\n"
                                    for rep in repuestos_list:
                                        nombre = rep.get('nombre', rep.get('name', 'Sin nombre'))
                                        cantidad = rep.get('cantidad', rep.get('quantity', 1))
                                        message_content += f"- {nombre} (cantidad: {cantidad})\n"
                                else:
                                    logger.warning(f"Excel processing completed but no repuestos found. Missing fields: {file_result.missing_fields}")
                            else:
                                logger.error(f"Failed to download Excel: HTTP {file_response.status_code}")
                    except Exception as e:
                        logger.error(f"Error processing Excel file: {e}")
                
                # Delegate the full conversation flow to the shared module
                return await run_solicitud_flow(
                    message_content=message_content,
                    draft_key=draft_key,
                    ciudad_invalida_key=ciudad_invalida_key,
                    send_fn=send_fn,
                    settings=settings,
                )

                # NOTE: everything below this line is unreachable — kept temporarily
                # until the shared flow has been verified in production.
                existing_draft = await redis_manager.get_json(draft_key)
                user_confirmed = False
                extracted_data = None
                if False and existing_draft:  # dead — flow handled by run_solicitud_flow above
                    pass  # SIEMPRE ANALIZAR INTENCIÓN CUANDO HAY DRAFT
                # Esto asegura que siempre pida confirmación antes de crear
                if existing_draft:
                    logger.info(f"Draft exists for chat {telegram_message.chat_id}, analyzing user intent with GPT-4")
                    
                    # Preparar contexto del draft actual para GPT-4
                    draft_context = {
                        "cliente": existing_draft.get("cliente", {}),
                        "vehiculo": existing_draft.get("vehiculo", {}),
                        "repuestos": existing_draft.get("repuestos", [])
                    }
                    
                    # Obtener el último mensaje del bot para contexto (si existe)
                    last_bot_message = existing_draft.get("_last_bot_message", "")
                    
                    # Agregar información sobre el último repuesto agregado (útil para correcciones de cantidad)
                    last_repuesto_added = None
                    if existing_draft.get("repuestos"):
                        last_repuesto_added = existing_draft["repuestos"][-1].get("nombre", "")
                    
                    # Usar GPT-4 para entender la intención del usuario
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        intent_response = await client.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                            json={
                                "model": "gpt-4o-mini",
                                "messages": [{
                                    "role": "system",
                                    "content": """Analiza el mensaje del usuario y determina su intención. Responde SOLO con un JSON válido.

DATOS ACTUALES:
""" + json.dumps(draft_context, ensure_ascii=False) + """

ÚLTIMO REPUESTO AGREGADO:
""" + (last_repuesto_added if last_repuesto_added else "Ninguno") + """

ÚLTIMO MENSAJE DEL BOT:
""" + last_bot_message + """

CONTEXTO: Si el usuario menciona cantidades ("las 2", "son 3") después de una pregunta sobre cantidades,
actualiza la cantidad del ÚLTIMO REPUESTO AGREGADO (el que aparece al final de la lista).

FORMATO DE RESPUESTA:
{
  "intent": "confirm" | "reject" | "correct" | "question",
  "answer": "respuesta a la pregunta (solo si intent es question)",
  "updated_data": {
    "cliente": {"nombre": "...", "telefono": "...", "ciudad": "..."},
    "vehiculo": {"marca": "...", "linea": "...", "anio": "..."},
    "repuestos": [{"nombre": "...", "cantidad": 1}]
  }
}

INTENCIONES:
- "confirm": Usuario confirma que todo está bien SIN mencionar cambios
  Ejemplos: "sí", "ok", "perfecto", "todo bien", "correcto", "así está", "confirmar", "adelante", "está bien",
            "aprobado", "aprobada", "esta bien aprobada", "está bien aprobado", "listo", "dale", "de acuerdo",
            "conforme", "excelente", "genial", "bien", "muy bien", "todo correcto", "todo ok"
  NO ES CONFIRMACIÓN: "serían las 2" (menciona cantidad), "sí, pero..." (tiene corrección)

- "reject": Usuario rechaza TODO y quiere empezar de nuevo (SOLO rechazos totales y explícitos)
  Ejemplos: "no, todo mal", "empecemos de nuevo", "borra todo", "cancela todo", "nada está bien", "quiero cancelar"
  NO ES RECHAZO: "no" (solo), "no, es la izquierda" (es corrección), "no viene el par?" (es pregunta)
  IMPORTANTE: Si el usuario solo dice "no" sin más contexto, usa "correct" para que el bot pregunte qué quiere corregir

- "question": Usuario hace una pregunta o pide aclaración (NO quiere borrar nada)
  Ejemplos: "¿las pastillas vienen 1 o el par?", "¿cuánto demora?", "¿puedo agregar más?", 
            "¿tienen disponibilidad?", "¿el precio incluye envío?", "¿cómo funciona?"
  Responde la pregunta en "answer" basándote en el contexto y mantén los datos sin cambios

- "correct": Usuario quiere corregir o agregar algo específico
  Ejemplos: "el teléfono es 3006515619", "los amortiguadores son delanteros", 
            "agrega pastillas traseras", "el modelo es Zontes 310", "serían las 2", "son 3 unidades"

REGLAS IMPORTANTES:
1. Si el mensaje tiene "?" o palabras como "viene", "vienen", "puedo", "cómo", "cuánto" → probablemente es "question"
2. Si menciona números/cantidades ("las 2", "3 unidades", "el par") → es "correct", NO "confirm"
3. Si el último mensaje del bot fue una pregunta y el usuario responde con datos → es "correct"
4. Si dice "no" pero está corrigiendo algo específico → es "correct", NO "reject"
5. Solo usa "reject" si el usuario quiere borrar TODO y empezar de nuevo
6. Para "question": genera una respuesta útil en "answer" y NO modifiques los datos

Si intent es "correct":
1. Copia TODOS los datos actuales a "updated_data"
2. Modifica SOLO los campos que el usuario menciona
3. Para repuestos: si menciona "derecha" o "izquierda", actualiza el nombre del repuesto específico
4. Si dice "agregar" o "también necesito", AGREGA el repuesto a la lista existente
5. IMPORTANTE - Correcciones de cantidad:
   - Si el último mensaje del bot fue una pregunta sobre cantidades (ej: "¿vienen 1 o el par?")
   - Y el usuario responde con un número (ej: "las 2", "entonces las 2", "serían 2")
   - Identifica el repuesto mencionado en la pregunta del bot (busca en el último mensaje)
   - Busca en los repuestos actuales el que contiene "pastillas" y fue agregado más recientemente
   - Actualiza su cantidad a 2

Usuario: "los amortiguadores son delanteros"
→ intent: "correct", busca "amortiguadores traseros" y cámbialo a "amortiguadores delanteros"

Usuario: "agrega pastillas de freno traseras"
→ intent: "correct", AGREGA el nuevo repuesto a la lista existente
"""
                                }, {
                                    "role": "user",
                                    "content": message_content
                                }],
                                "temperature": 0.1
                            }
                        )
                    
                    if intent_response.status_code == 200:
                        intent_result = intent_response.json()
                        intent_text = intent_result["choices"][0]["message"]["content"]
                        
                        try:
                            intent_data = json.loads(intent_text)
                            intent = intent_data.get("intent")
                            
                            # Usuario CONFIRMA - crear solicitud INMEDIATAMENTE
                            if intent == "confirm":
                                logger.info(f"User confirmed solicitud (natural language) - creating immediately")
                                
                                # Preparar datos para creación (saltar validación porque ya fue validado antes)
                                extracted_data = existing_draft
                                # Limpiar campos internos
                                if "_status" in extracted_data:
                                    del extracted_data["_status"]
                                if "_last_bot_message" in extracted_data:
                                    del extracted_data["_last_bot_message"]
                                
                                # Eliminar draft de Redis
                                await redis_manager.delete(draft_key)
                                
                                # SALTAR DIRECTAMENTE A LA CREACIÓN - no volver a validar
                                # El código de creación está después de la línea 1087
                                # Necesitamos extraer las variables necesarias
                                vehiculo = extracted_data.get("vehiculo", {})
                                cliente = extracted_data.get("cliente", {})
                                
                                # Validar año antes de proceder
                                raw_anio = str(vehiculo.get("anio", "")).strip()
                                if not raw_anio.isdigit() or int(raw_anio) < 1980 or int(raw_anio) > 2026:
                                    logger.warning(f"⚠️ Año de vehículo inválido o ausente: '{raw_anio}'")
                                    # Guardar draft de nuevo para no perder nada
                                    await redis_manager.set_json(draft_key, existing_draft, ttl=3600)
                                    await telegram_service.send_message(
                                        telegram_message.chat_id, 
                                        "✅ He guardado los datos, pero me falta saber el **año del vehículo** (ej: 2022) para poder crear la solicitud.\n\nPor favor, dime el año."
                                    )
                                    return {"success": True, "action": "year_requested"}
                                
                                anio_val = int(raw_anio)
                                
                                # Preparar repuestos
                                repuestos_formatted = []
                                for rep in extracted_data["repuestos"]:
                                    repuestos_formatted.append({
                                        "nombre": rep["nombre"],
                                        "cantidad": rep.get("cantidad", 1),
                                        "marca_vehiculo": vehiculo.get("marca", "N/A"),
                                        "linea_vehiculo": vehiculo.get("linea", "N/A") if vehiculo.get("linea") else "N/A",
                                        "anio_vehiculo": anio_val,
                                        "observaciones": rep.get("observaciones", "")
                                    })
                                
                                # Normalizar teléfono
                                telefono_original = cliente["telefono"].strip()
                                logger.info(f"📞 Teléfono original: '{telefono_original}'")
                                telefono = telefono_original.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                                logger.info(f"📞 Teléfono limpio: '{telefono}' (longitud: {len(telefono)})")
                                
                                if not telefono.startswith("+57"):
                                    if telefono.startswith("57"):
                                        telefono = "+" + telefono
                                    elif telefono.startswith("3"):
                                        telefono = "+57" + telefono
                                    else:
                                        telefono = "+57" + telefono
                                
                                logger.info(f"📞 Teléfono normalizado: '{telefono}' (longitud: {len(telefono)})")
                                
                                # Preparar datos del cliente
                                cliente_payload = {
                                    "nombre": cliente["nombre"],
                                    "telefono": telefono
                                }
                                if cliente.get("email"):
                                    cliente_payload["email"] = cliente["email"]
                                
                                # Usar datos de ciudad ya validados del draft
                                municipio_id = extracted_data.get("_municipio_id")
                                departamento = extracted_data.get("_departamento")
                                ciudad_display = extracted_data["cliente"].get("ciudad_display", cliente["ciudad"])
                                
                                # Limpiar ciudad para guardar en BD
                                from app.services.solicitud_service import limpiar_ciudad
                                ciudad_para_bd = cliente["ciudad"]
                                if " - " in ciudad_para_bd:
                                    ciudad_para_bd = ciudad_para_bd.split(" - ")[0].strip()
                                ciudad_normalizada = limpiar_ciudad(ciudad_para_bd)
                                
                                solicitud_payload = {
                                    "cliente": cliente_payload,
                                    "municipio_id": municipio_id,
                                    "ciudad_origen": ciudad_normalizada,
                                    "departamento_origen": departamento,
                                    "repuestos": repuestos_formatted
                                }
                                
                                logger.info(f"📤 Payload a enviar: {json.dumps(solicitud_payload, indent=2, ensure_ascii=False)}")
                                
                                # Llamar al endpoint seguro del bot
                                async with httpx.AsyncClient(timeout=30.0) as api_client:
                                    api_response = await api_client.post(
                                        f"{settings.core_api_url}/v1/solicitudes/services/bot",
                                        json=solicitud_payload,
                                        headers={
                                            "X-Service-Name": str(settings.service_name or "agent-ia"),
                                            "X-Service-API-Key": str(settings.service_api_key or "")
                                        }
                                    )
                                
                                if api_response.status_code == 201:
                                    solicitud_result = api_response.json()
                                    solicitud_id = solicitud_result["id"]
                                    
                                    logger.info(f"✅ Solicitud created: {solicitud_id}")
                                    
                                    # Enviar confirmación
                                    response_msg = f"✅ Solicitud creada exitosamente!\n\n"
                                    response_msg += f"📋 Número: {solicitud_id[:8]}...\n\n"
                                    response_msg += f"👤 Cliente: {cliente['nombre']}\n"
                                    response_msg += f"📞 Teléfono: {telefono}\n"
                                    response_msg += f"📍 Ciudad: {ciudad_display}\n\n"
                                    response_msg += f"🚗 Vehículo: {vehiculo.get('marca', '')} {vehiculo.get('linea', '')} {vehiculo.get('anio', '')}\n\n"
                                    response_msg += f"🔧 Repuestos:\n"
                                    response_msg += format_repuestos_list(extracted_data["repuestos"])
                                    response_msg += "\n\n🔍 Estamos buscando las mejores ofertas para ti. Te notificaremos cuando tengamos propuestas disponibles.\n\n"
                                    response_msg += "¡Gracias por usar TeLOO! 🚗"
                                    
                                    await telegram_service.send_message(telegram_message.chat_id, response_msg)
                                    
                                    return {
                                        "success": True,
                                        "action": "solicitud_created",
                                        "solicitud_id": solicitud_id
                                    }
                                else:
                                    error_msg = f"❌ Error creando solicitud: {api_response.status_code}\n\n"
                                    error_msg += "Por favor intenta de nuevo más tarde."
                                    await telegram_service.send_message(telegram_message.chat_id, error_msg)
                                    
                                    return {
                                        "success": False,
                                        "error": f"API error: {api_response.status_code}"
                                    }
                            
                            # Usuario RECHAZA TODO - cancelar completamente
                            elif intent == "reject":
                                logger.info(f"User rejected everything - cancelling (natural language)")
                                await redis_manager.delete(draft_key)
                                
                                # Clear pending actions
                                context_mgr = get_context_manager()
                                user_id = f"+tg{telegram_message.chat_id}"
                                await context_mgr.clear_pending_action(user_id)
                                
                                cancel_msg = "✅ Entendido, he cancelado todo.\n\n"
                                cancel_msg += "Si cambias de opinión y necesitas repuestos, solo escríbeme. ¡Estoy aquí para ayudarte!"
                                
                                await telegram_service.send_message(telegram_message.chat_id, cancel_msg)
                                
                                return {
                                    "success": True,
                                    "action": "cancelled"
                                }
                            
                            # Usuario HACE UNA PREGUNTA - responder y mantener datos
                            elif intent == "question":
                                logger.info(f"User asked a question (natural language)")
                                answer = intent_data.get("answer", "")
                                
                                if not answer:
                                    answer = "Entiendo tu pregunta. Los datos que tengo registrados están correctos según lo que me compartiste."
                                
                                # Responder la pregunta
                                question_msg = f"💬 {answer}\n\n"
                                question_msg += "📋 Resumen actual:\n"
                                question_msg += f"👤 Cliente: {existing_draft['cliente']['nombre']}\n"
                                question_msg += f"📞 Teléfono: {existing_draft['cliente']['telefono']}\n"
                                question_msg += f"📍 Ciudad: {existing_draft['cliente']['ciudad']}\n\n"
                                vehiculo = existing_draft.get("vehiculo", {})
                                question_msg += f"🚗 Vehículo: {vehiculo.get('marca', '')} {vehiculo.get('linea', '')} {vehiculo.get('anio', '')}\n\n"
                                question_msg += format_repuestos_list(existing_draft["repuestos"])
                                question_msg += "\n¿Está todo correcto o necesitas ajustar algo?"
                                
                                # Guardar el mensaje del bot para contexto futuro
                                existing_draft["_last_bot_message"] = question_msg
                                await redis_manager.set_json(draft_key, existing_draft, ttl=3600)
                                
                                await telegram_service.send_message(telegram_message.chat_id, question_msg)
                                
                                return {
                                    "success": True,
                                    "action": "question_answered"
                                }
                            
                            # Usuario CORRIGE algo específico
                            elif intent == "correct":
                                logger.info(f"User wants to correct specific fields (natural language)")
                                updated_data = intent_data.get("updated_data", {})
                                
                                # Detectar si el usuario solo dijo "no" sin especificar qué corregir
                                message_lower = message_content.lower().strip()
                                if message_lower in ["no", "nop", "nope", "nel", "no está bien", "no esta bien"]:
                                    # Preguntar qué quiere corregir
                                    await telegram_service.send_message(
                                        telegram_message.chat_id,
                                        "Entiendo. ¿Qué información quieres corregir?\n\n"
                                        "Puedes decirme, por ejemplo:\n"
                                        "• La ciudad es Amagá\n"
                                        "• El teléfono es 3001234567\n"
                                        "• Agrega pastillas traseras\n"
                                        "• El año es 2019"
                                    )
                                    return {
                                        "success": True,
                                        "action": "correction_requested"
                                    }
                                
                                # Aplicar correcciones FUSIONANDO datos (no reemplazando)
                                if updated_data and "cliente" in updated_data and updated_data["cliente"]:
                                    # Fusionar cliente: solo actualizar campos que vienen en updated_data
                                    for key, value in updated_data["cliente"].items():
                                        if value:  # Solo actualizar si el valor no está vacío
                                            existing_draft["cliente"][key] = value
                                
                                if updated_data and "vehiculo" in updated_data and updated_data["vehiculo"]:
                                    # Fusionar vehículo: solo actualizar campos que vienen en updated_data
                                    if "vehiculo" not in existing_draft:
                                        existing_draft["vehiculo"] = {}
                                    for key, value in updated_data["vehiculo"].items():
                                        if value:  # Solo actualizar si el valor no está vacío
                                            existing_draft["vehiculo"][key] = value
                                
                                if updated_data and "repuestos" in updated_data and updated_data["repuestos"]:
                                    # Solo reemplazar repuestos si vienen datos nuevos
                                    if updated_data["repuestos"]:
                                        existing_draft["repuestos"] = updated_data["repuestos"]
                                
                                # Validar ciudad antes de mostrar resumen
                                cliente = existing_draft.get("cliente", {})
                                from app.services.solicitud_service import limpiar_ciudad
                                ciudad_para_validar = cliente.get("ciudad", "")
                                # Si la ciudad tiene formato "CIUDAD - DEPARTAMENTO", extraer solo la ciudad
                                if " - " in ciudad_para_validar:
                                    ciudad_para_validar = ciudad_para_validar.split(" - ")[0].strip()
                                ciudad_normalizada = limpiar_ciudad(ciudad_para_validar)
                                
                                # Buscar municipio en la base de datos
                                logger.info(f"🔍 Validating city at: {settings.core_api_url}/v1/solicitudes/services/municipio")
                                async with httpx.AsyncClient(timeout=10.0) as geo_client:
                                    geo_response = await geo_client.get(
                                        f"{settings.core_api_url}/v1/solicitudes/services/municipio",
                                        params={"ciudad": ciudad_normalizada},
                                        headers={
                                            "X-Service-Name": str(settings.service_name or "agent-ia"),
                                            "X-Service-API-Key": str(settings.service_api_key or "")
                                        }
                                    )
                                
                                if geo_response.status_code == 200:
                                    # Ciudad válida - obtener departamento
                                    municipio_data = geo_response.json()
                                    departamento = municipio_data["departamento"]
                                    ciudad_display = f"{ciudad_normalizada.title()} - {departamento}"
                                    
                                    # Guardar datos validados en el draft
                                    existing_draft["cliente"]["ciudad_display"] = ciudad_display
                                    existing_draft["_municipio_id"] = municipio_data["id"]
                                    existing_draft["_departamento"] = departamento
                                else:
                                    # Ciudad no válida - usar ciudad original sin departamento
                                    ciudad_display = cliente.get("ciudad", "")
                                
                                # Validar teléfono ANTES de mostrar resumen
                                telefono_original = existing_draft['cliente']['telefono']
                                telefono_limpio = telefono_original.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                                
                                # Remover +57 si existe para contar solo los dígitos
                                telefono_validar = telefono_limpio
                                if telefono_validar.startswith("+57"):
                                    telefono_validar = telefono_validar[3:]
                                elif telefono_validar.startswith("57"):
                                    telefono_validar = telefono_validar[2:]
                                
                                # Validar que tenga exactamente 10 dígitos
                                if len(telefono_validar) != 10 or not telefono_validar.isdigit():
                                    # Teléfono inválido - pedir corrección
                                    logger.info(f"Invalid phone '{telefono_original}' detected in correction")
                                    
                                    help_msg = f"⚠️ El teléfono '{telefono_original}' no es válido.\n\n"
                                    help_msg += "📱 Por favor, envíame un teléfono colombiano completo con 10 dígitos.\n\n"
                                    help_msg += "Ejemplo: 3001234567"
                                    
                                    await telegram_service.send_message(telegram_message.chat_id, help_msg)
                                    
                                    return {
                                        "success": True,
                                        "action": "invalid_phone_in_correction"
                                    }
                                
                                # Teléfono válido - mostrar limpio
                                telefono_display = telefono_limpio
                                
                                # Mostrar resumen actualizado con ciudad validada y teléfono limpio
                                confirmation_msg = "✅ Perfecto, actualicé la información:\n\n"
                                confirmation_msg += f"👤 Cliente: {existing_draft['cliente']['nombre']}\n"
                                confirmation_msg += f"📞 Teléfono: {telefono_display}\n"
                                confirmation_msg += f"📍 Ciudad: {ciudad_normalizada.title()}\n\n"
                                vehiculo = existing_draft.get("vehiculo", {})
                                confirmation_msg += f"🚗 Vehículo: {vehiculo.get('marca', '')} {vehiculo.get('linea', '')} {vehiculo.get('anio', '')}\n\n"
                                confirmation_msg += f"🔧 Repuestos:\n"
                                # Usar función helper para formatear repuestos
                                confirmation_msg += format_repuestos_list(existing_draft["repuestos"])
                                confirmation_msg = confirmation_msg.rstrip('\n')  # Remover salto de línea extra
                                confirmation_msg += "\n¿Ahora sí está todo correcto?"
                                
                                # Guardar draft actualizado con el último mensaje del bot para contexto
                                existing_draft["_status"] = "pending_confirmation"
                                existing_draft["_last_bot_message"] = confirmation_msg
                                await redis_manager.set_json(draft_key, existing_draft, ttl=3600)
                                
                                await telegram_service.send_message(telegram_message.chat_id, confirmation_msg)
                                
                                return {
                                    "success": True,
                                    "action": "correction_applied"
                                }
                        
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse intent from GPT-4")
                            # Si falla, asumir que quiere corregir y procesar normalmente
                            existing_draft["_status"] = "correcting"
                            await redis_manager.set_json(draft_key, existing_draft, ttl=3600)
                
                # Si el usuario confirmó, saltar todo el procesamiento y ir directo a creación
                if not user_confirmed:
                    # Si existe draft y el mensaje parece ser solo un teléfono
                    # NO volver a extraer todo, solo actualizar el teléfono
                    import re
                    # Extraer solo números del mensaje
                    solo_numeros = re.sub(r'\D', '', message_content)
                    
                    es_solo_telefono = (
                        existing_draft is not None and 
                        existing_draft.get("_status") != "correcting" and  # No si está corrigiendo
                        len(message_content.strip()) <= 30 and  # Mensaje corto
                        len(solo_numeros) == 10 and  # Exactamente 10 dígitos
                        solo_numeros.startswith("3")  # Número celular colombiano
                    )
                    
                    if es_solo_telefono:
                        logger.info(f"Detected phone-only message '{solo_numeros}', updating draft without re-extraction")
                        # Solo actualizar el teléfono en el draft existente
                        if "cliente" not in existing_draft:
                            existing_draft["cliente"] = {}
                        existing_draft["cliente"]["telefono"] = solo_numeros
                        extracted_data = existing_draft
                    else:
                        # Llamar a OpenAI para extraer información
                        try:
                            async with httpx.AsyncClient(timeout=30.0) as client:
                                response = await client.post(
                                    "https://api.openai.com/v1/chat/completions",
                                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                                    json={
                                        "model": "gpt-4o-mini",
                                        "messages": [{
                                            "role": "system",
                                            "content": """Extrae información del mensaje y responde SOLO con JSON válido (sin markdown):
{
  "repuestos": [{"nombre": "kit de arrastre", "cantidad": 1}],
  "vehiculo": {"marca": "", "linea": "", "anio": ""},
  "cliente": {"telefono": "", "nombre": "", "ciudad": ""}
}

REGLAS CRÍTICAS:
- Extrae SOLO la información que el usuario menciona explícitamente
- NO inventes ni asumas datos que no están en el mensaje
- Si el usuario NO menciona marca/modelo/año del vehículo, deja esos campos vacíos ""
- Si el usuario NO menciona nombre/teléfono/ciudad, deja esos campos vacíos ""
- Extrae TODOS los repuestos mencionados (incluyendo los del Excel si están listados)
- TELÉFONO: Los números colombianos tienen 10 dígitos y empiezan con 3. Si ves números separados, júntalos (ej: "300 65 15 619" → "3006515619")
- Responde SOLO el JSON, sin texto adicional

EJEMPLOS:
Mensaje: "necesito kit de arrastre y filtro de aire"
→ {"repuestos": [...], "vehiculo": {"marca": "", "linea": "", "anio": ""}, "cliente": {"telefono": "", "nombre": "", "ciudad": ""}}

Mensaje: "para una Yamaha FZ 2.0 del 2018"
→ {"repuestos": [], "vehiculo": {"marca": "Yamaha", "linea": "FZ 2.0", "anio": "2018"}, "cliente": {"telefono": "", "nombre": "", "ciudad": ""}}"""
                                        }, {
                                            "role": "user",
                                            "content": message_content
                                        }],
                                        "temperature": 0.3
                                    }
                                )
                            
                            if response.status_code == 200:
                                result = response.json()
                                extracted_text = result["choices"][0]["message"]["content"]
                                
                                # Parsear JSON extraído
                                try:
                                    extracted_data = json.loads(extracted_text)
                                    
                                    if existing_draft:
                                        logger.info(f"Found existing draft for chat {telegram_message.chat_id}, merging data")
                                        # Combinar datos: SOLO actualizar campos que están vacíos en el draft
                                        # Esto evita que GPT-4 sobrescriba datos correctos con alucinaciones
                                        
                                        # Repuestos: solo actualizar si el draft NO tiene repuestos
                                        if not existing_draft.get("repuestos") and extracted_data.get("repuestos"):
                                            existing_draft["repuestos"] = extracted_data["repuestos"]
                                        
                                        # Vehículo: solo actualizar campos vacíos
                                        if not existing_draft.get("vehiculo"):
                                            existing_draft["vehiculo"] = {}
                                        if not existing_draft["vehiculo"].get("marca") and extracted_data.get("vehiculo", {}).get("marca"):
                                            existing_draft["vehiculo"]["marca"] = extracted_data["vehiculo"]["marca"]
                                        if not existing_draft["vehiculo"].get("linea") and extracted_data.get("vehiculo", {}).get("linea"):
                                            existing_draft["vehiculo"]["linea"] = extracted_data["vehiculo"]["linea"]
                                        if not existing_draft["vehiculo"].get("anio") and extracted_data.get("vehiculo", {}).get("anio"):
                                            existing_draft["vehiculo"]["anio"] = extracted_data["vehiculo"]["anio"]
                                        
                                        # Cliente: solo actualizar campos vacíos
                                        if not existing_draft.get("cliente"):
                                            existing_draft["cliente"] = {}
                                        if not existing_draft["cliente"].get("nombre") and extracted_data.get("cliente", {}).get("nombre"):
                                            existing_draft["cliente"]["nombre"] = extracted_data["cliente"]["nombre"]
                                        if not existing_draft["cliente"].get("telefono") and extracted_data.get("cliente", {}).get("telefono"):
                                            existing_draft["cliente"]["telefono"] = extracted_data["cliente"]["telefono"]
                                        if not existing_draft["cliente"].get("ciudad") and extracted_data.get("cliente", {}).get("ciudad"):
                                            existing_draft["cliente"]["ciudad"] = extracted_data["cliente"]["ciudad"]
                                        
                                        extracted_data = existing_draft
                                except json.JSONDecodeError as e:
                                    logger.error(f"Failed to parse JSON from GPT-4: {e}")
                                    await telegram_service.send_message(
                                        telegram_message.chat_id,
                                        "❌ Error al procesar tu mensaje. Por favor intenta de nuevo."
                                    )
                                    return {"success": False, "error": "json_parse_error"}
                            else:
                                logger.error(f"OpenAI API returned status {response.status_code}")
                                await telegram_service.send_message(
                                    telegram_message.chat_id,
                                    "❌ Error al procesar tu mensaje. Por favor intenta de nuevo en unos momentos."
                                )
                                return {"success": False, "error": f"openai_status_{response.status_code}"}
                        except Exception as e:
                            logger.error(f"Error calling OpenAI API: {e}")
                            await telegram_service.send_message(
                                telegram_message.chat_id,
                                "❌ Error al procesar tu mensaje. Por favor intenta de nuevo en unos momentos."
                            )
                            return {"success": False, "error": "openai_api_error"}
                
                # Validar que extracted_data existe antes de continuar
                if extracted_data is None:
                    logger.error("extracted_data is None, cannot continue")
                    await telegram_service.send_message(
                        telegram_message.chat_id,
                        "❌ Error al procesar tu mensaje. Por favor intenta de nuevo."
                    )
                    return {"success": False, "error": "no_extracted_data"}
                
                # Limpiar estados internos antes de validar
                if "_status" in extracted_data:
                    del extracted_data["_status"]
                if "_last_bot_message" in extracted_data:
                    del extracted_data["_last_bot_message"]
                
                # Solo validar y pedir confirmación si NO hay draft existente
                # Si hay draft, significa que ya pasó por validación y análisis de intención
                if existing_draft is None:
                    # VALIDAR DATOS OBLIGATORIOS
                    missing_fields = []
                
                # 1. Validar repuestos (obligatorio)
                if not extracted_data.get("repuestos") or len(extracted_data["repuestos"]) == 0:
                    missing_fields.append("repuestos")
                
                # 2. Validar vehículo (obligatorio)
                vehiculo = extracted_data.get("vehiculo", {})
                if not vehiculo.get("marca"):
                    missing_fields.append("marca del vehículo")
                if not vehiculo.get("anio"):
                    missing_fields.append("año del vehículo")
                
                # 3. Validar cliente (obligatorio)
                cliente = extracted_data.get("cliente", {})
                if not cliente.get("nombre"):
                    missing_fields.append("nombre del cliente")
                
                # Validar teléfono: debe existir y tener 10 dígitos
                if not cliente.get("telefono"):
                    missing_fields.append("teléfono del cliente")
                else:
                    # Limpiar teléfono para validar longitud
                    telefono_limpio = cliente["telefono"].replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                    # Remover +57 si existe para contar solo los dígitos
                    if telefono_limpio.startswith("+57"):
                        telefono_limpio = telefono_limpio[3:]
                    elif telefono_limpio.startswith("57"):
                        telefono_limpio = telefono_limpio[2:]
                    
                    # Validar que tenga exactamente 10 dígitos
                    if len(telefono_limpio) != 10 or not telefono_limpio.isdigit():
                        # Teléfono inválido - guardar draft y pedir corrección
                        extracted_data["_status"] = "invalid_phone"
                        await redis_manager.set_json(draft_key, extracted_data, ttl=3600)
                        logger.info(f"Invalid phone '{cliente['telefono']}' for chat {telegram_message.chat_id}")
                        
                        help_msg = f"⚠️ El teléfono '{cliente['telefono']}' no es válido.\n\n"
                        help_msg += "📱 Por favor, envíame un teléfono colombiano completo con 10 dígitos.\n\n"
                        help_msg += "Ejemplo: 3001234567\n\n"
                        help_msg += "✅ Ya tengo guardado:\n"
                        if cliente.get("nombre"):
                            help_msg += f"• Nombre: {cliente['nombre']}\n"
                        if extracted_data.get("repuestos"):
                            help_msg += f"• {len(extracted_data['repuestos'])} repuesto(s)\n"
                        if vehiculo.get("marca"):
                            help_msg += f"• Vehículo: {vehiculo.get('marca', '')} {vehiculo.get('linea', '')}\n"
                        if cliente.get("ciudad"):
                            help_msg += f"• Ciudad: {cliente['ciudad']}\n"
                        
                        await telegram_service.send_message(telegram_message.chat_id, help_msg)
                        
                        return {
                            "success": True,
                            "action": "invalid_phone_detected"
                        }
                
                if not cliente.get("ciudad"):
                    missing_fields.append("ciudad")
                
                # Si faltan datos obligatorios, guardar draft y pedir información
                if missing_fields:
                    # Guardar draft en Redis (expira en 1 hora)
                    await redis_manager.set_json(draft_key, extracted_data, ttl=3600)
                    logger.info(f"Saved draft for chat {telegram_message.chat_id} with {len(missing_fields)} missing fields")
                    
                    help_msg = "🤔 Para crear tu solicitud necesito la siguiente información:\n\n"
                    for field in missing_fields:
                        help_msg += f"❌ {field}\n"
                    
                    # Mostrar lo que ya tenemos
                    if extracted_data.get("repuestos"):
                        help_msg += f"\n✅ Ya tengo: {len(extracted_data['repuestos'])} repuesto(s)\n"
                    if extracted_data.get("vehiculo", {}).get("marca"):
                        help_msg += f"✅ Ya tengo: Vehículo {extracted_data['vehiculo'].get('marca', '')} {extracted_data['vehiculo'].get('linea', '')}\n"
                    
                    help_msg += "\n📝 Por favor envíame la información que falta."
                    
                    await telegram_service.send_message(telegram_message.chat_id, help_msg)
                    
                    return {
                        "success": True,
                        "action": "info_requested",
                        "missing_fields": missing_fields
                    }
                
                # TODOS LOS DATOS COMPLETOS - VALIDAR CIUDAD ANTES DE PEDIR CONFIRMACIÓN
                # Limpiar y validar ciudad
                from app.services.solicitud_service import limpiar_ciudad
                ciudad_normalizada = limpiar_ciudad(cliente["ciudad"])
                
                # Buscar municipio en la base de datos
                async with httpx.AsyncClient(timeout=10.0) as geo_client:
                    geo_response = await geo_client.get(
                        f"{settings.core_api_url}/v1/solicitudes/services/municipio",
                        params={"ciudad": ciudad_normalizada},
                        headers={
                            "X-Service-Name": settings.service_name,
                            "X-Service-API-Key": settings.service_api_key
                        }
                    )
                
                if geo_response.status_code == 200:
                    # Ciudad válida - obtener departamento
                    municipio_data = geo_response.json()
                    departamento = municipio_data["departamento"]
                    ciudad_display = f"{ciudad_normalizada.title()} - {departamento}"
                    
                    # Guardar ciudad_display en el draft para usarla en confirmación
                    extracted_data["cliente"]["ciudad_display"] = ciudad_display
                    extracted_data["_municipio_id"] = municipio_data["id"]
                    extracted_data["_departamento"] = departamento
                    
                    # Limpiar teléfono para mostrar (quitar guiones, espacios, paréntesis)
                    telefono_display = cliente['telefono'].replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                    # Si tiene menos de 10 dígitos, mostrar el original
                    if len(telefono_display) < 10:
                        telefono_display = cliente['telefono']
                    
                    # Mostrar resumen con ciudad validada y teléfono limpio
                    confirmation_msg = "📋 Perfecto, aquí está el resumen:\n\n"
                    confirmation_msg += f"👤 Cliente: {cliente['nombre']}\n"
                    confirmation_msg += f"📞 Teléfono: {telefono_display}\n"
                    confirmation_msg += f"📍 Ciudad: {ciudad_normalizada.title()}\n\n"
                    confirmation_msg += f"🚗 Vehículo: {vehiculo.get('marca', '')} {vehiculo.get('linea', '')} {vehiculo.get('anio', '')}\n\n"
                    confirmation_msg += f"🔧 Repuestos:\n"
                    confirmation_msg += format_repuestos_list(extracted_data["repuestos"])
                    confirmation_msg = confirmation_msg.rstrip('\n')
                    confirmation_msg += "\n¿Todo está bien o necesitas corregir algo?"
                    
                    # Guardar draft con estado "pending_confirmation"
                    extracted_data["_status"] = "pending_confirmation"
                    extracted_data["_last_bot_message"] = confirmation_msg
                    await redis_manager.set_json(draft_key, extracted_data, ttl=3600)
                    logger.info(f"All data complete and city validated for chat {telegram_message.chat_id}, requesting confirmation")
                    
                    await telegram_service.send_message(telegram_message.chat_id, confirmation_msg)
                    
                    return {
                        "success": True,
                        "action": "confirmation_requested"
                    }
                else:
                    # Ciudad no encontrada - verificar si es primera o segunda vez
                    ciudad_invalida_key = f"ciudad_invalida:{telegram_message.chat_id}"
                    ciudad_anterior = await redis_manager.get(ciudad_invalida_key)
                    
                    # Convertir a string si es bytes
                    if ciudad_anterior:
                        if isinstance(ciudad_anterior, bytes):
                            ciudad_anterior = ciudad_anterior.decode('utf-8')
                        ciudad_anterior = ciudad_anterior.upper()
                    
                    if ciudad_anterior and ciudad_anterior == ciudad_normalizada:
                        # Segunda vez con la misma ciudad inválida - informar sin cobertura y borrar draft
                        await redis_manager.delete(draft_key)
                        await redis_manager.delete(ciudad_invalida_key)
                        
                        await telegram_service.send_message(
                            telegram_message.chat_id,
                            f"😔 Entiendo, gracias por verificar.\n\n"
                            f"Lamentablemente, en este momento no tenemos cobertura en {cliente['ciudad']}.\n\n"
                            f"📍 Operamos solo en ciudades donde tenemos asesores registrados.\n\n"
                            f"Si en el futuro necesitas repuestos en otra ciudad donde sí tengamos servicio, "
                            f"con gusto te ayudaré. ¡Estoy aquí cuando me necesites! 😊"
                        )
                        
                        return {"success": False, "error": "sin_cobertura"}
                    else:
                        # Primera vez - pedir verificación y MANTENER el draft
                        await redis_manager.set(ciudad_invalida_key, ciudad_normalizada, ttl=3600)
                        
                        # Guardar draft para que el usuario pueda corregir
                        extracted_data["_status"] = "pending_confirmation"
                        extracted_data["_last_bot_message"] = f"Verificando ciudad '{cliente['ciudad']}'"
                        await redis_manager.set_json(draft_key, extracted_data, ttl=3600)
                        logger.info(f"Draft maintained for chat {telegram_message.chat_id} - waiting for city verification")
                        
                        await telegram_service.send_message(
                            telegram_message.chat_id,
                            f"🤔 No encontré la ciudad '{cliente['ciudad']}' en nuestra base de datos.\n\n"
                            f"¿Podrías verificar el nombre? A veces hay errores de escritura.\n\n"
                            f"Si el nombre es correcto, es posible que aún no tengamos cobertura en esa zona."
                        )
                        
                        return {"success": True, "action": "ciudad_validation_pending"}
                
                # Validar año antes de proceder
                raw_anio = str(vehiculo.get("anio", "")).strip()
                if not raw_anio.isdigit() or int(raw_anio) < 1980 or int(raw_anio) > 2026:
                    logger.warning(f"⚠️ Año de vehículo inválido o ausente en flujo normal: '{raw_anio}'")
                    # Guardar draft para que el usuario pueda corregir
                    await redis_manager.set_json(draft_key, extracted_data, ttl=3600)
                    await telegram_service.send_message(
                        telegram_message.chat_id, 
                        "✅ He guardado los datos, pero me falta saber el **año del vehículo** (ej: 2022) para completar tu solicitud.\n\nPor favor, dime el año."
                    )
                    return {"success": True, "action": "year_requested"}
                
                anio_val = int(raw_anio)

                # Si llegamos aquí, el usuario YA confirmó - Crear solicitud
                repuestos_formatted = []
                for rep in extracted_data["repuestos"]:
                    repuestos_formatted.append({
                        "nombre": rep["nombre"],
                        "cantidad": rep.get("cantidad", 1),
                        "marca_vehiculo": vehiculo.get("marca", "N/A"),
                        "linea_vehiculo": vehiculo.get("linea", "N/A") if vehiculo.get("linea") else "N/A",
                        "anio_vehiculo": anio_val,
                        "observaciones": rep.get("observaciones", "")
                    })
                
                # Normalizar teléfono a formato colombiano +57XXXXXXXXXX
                telefono_original = cliente["telefono"].strip()
                logger.info(f"Teléfono original extraído: '{telefono_original}'")
                
                # Remover espacios, guiones y paréntesis
                telefono = telefono_original.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                logger.info(f"Teléfono después de limpiar: '{telefono}'")
                
                # Si no empieza con +57, agregarlo
                if not telefono.startswith("+57"):
                    if telefono.startswith("57"):
                        telefono = "+" + telefono
                    elif telefono.startswith("3"):  # Número celular colombiano
                        telefono = "+57" + telefono
                    else:
                        telefono = "+57" + telefono
                
                logger.info(f"Teléfono normalizado final: '{telefono}'")
                
                # Validar que tenga 13 caracteres (+57 + 10 dígitos)
                if len(telefono) != 13:
                    # Teléfono inválido - guardar draft sin teléfono y pedir que lo envíe por texto
                    extracted_data["cliente"]["telefono"] = ""  # Limpiar teléfono inválido
                    await redis_manager.set_json(draft_key, extracted_data, ttl=3600)
                    logger.info(f"Saved draft without phone for chat {telegram_message.chat_id}")
                    
                    help_msg = f"⚠️ El teléfono '{telefono_original}' parece incompleto (tiene {len(telefono)-3} dígitos).\n\n"
                    help_msg += "📱 Por favor, envíame tu teléfono completo por TEXTO (no audio) con 10 dígitos.\n\n"
                    help_msg += "Ejemplo: 3001234567\n\n"
                    help_msg += "✅ Ya tengo guardado:\n"
                    if extracted_data.get("cliente", {}).get("nombre"):
                        help_msg += f"• Nombre: {extracted_data['cliente']['nombre']}\n"
                    if extracted_data.get("repuestos"):
                        help_msg += f"• {len(extracted_data['repuestos'])} repuesto(s)\n"
                    if extracted_data.get("vehiculo", {}).get("marca"):
                        help_msg += f"• Vehículo: {extracted_data['vehiculo'].get('marca', '')} {extracted_data['vehiculo'].get('linea', '')}\n"
                    if extracted_data.get("cliente", {}).get("ciudad"):
                        help_msg += f"• Ciudad: {extracted_data['cliente']['ciudad']}\n"
                    
                    await telegram_service.send_message(telegram_message.chat_id, help_msg)
                    
                    return {
                        "success": True,
                        "action": "phone_requested"
                    }
                
                # Preparar datos del cliente (omitir email si no existe)
                cliente_payload = {
                    "nombre": cliente["nombre"],
                    "telefono": telefono
                }
                if cliente.get("email"):
                    cliente_payload["email"] = cliente["email"]
                
                # Usar datos de ciudad ya validados del draft
                municipio_id = extracted_data.get("_municipio_id")
                departamento = extracted_data.get("_departamento")
                ciudad_display = extracted_data["cliente"].get("ciudad_display", cliente["ciudad"])
                
                # Limpiar ciudad para guardar en BD
                # IMPORTANTE: Si ciudad_display tiene formato "CIUDAD - DEPARTAMENTO", extraer solo la ciudad
                from app.services.solicitud_service import limpiar_ciudad
                ciudad_para_bd = cliente["ciudad"]
                if " - " in ciudad_para_bd:
                    # Extraer solo la parte de la ciudad (antes del guión)
                    ciudad_para_bd = ciudad_para_bd.split(" - ")[0].strip()
                ciudad_normalizada = limpiar_ciudad(ciudad_para_bd)
                
                solicitud_payload = {
                    "cliente": cliente_payload,
                    "municipio_id": municipio_id,
                    "ciudad_origen": ciudad_normalizada,  # Usar ciudad limpia sin departamento
                    "departamento_origen": departamento,
                    "repuestos": repuestos_formatted
                }
                
                # Llamar al endpoint seguro del bot
                logger.info(f"📤 Sending request to Core API: {settings.core_api_url}/v1/solicitudes/services/bot")
                async with httpx.AsyncClient(timeout=30.0) as api_client:
                    api_response = await api_client.post(
                        f"{settings.core_api_url}/v1/solicitudes/services/bot",
                        json=solicitud_payload,
                        headers={
                            "X-Service-Name": str(settings.service_name or "agent-ia"),
                            "X-Service-API-Key": str(settings.service_api_key or "")
                        }
                    )
                
                if api_response.status_code == 201:
                    solicitud_result = api_response.json()
                    solicitud_id = solicitud_result["id"]
                    
                    # Limpiar draft de Redis
                    await redis_manager.delete(draft_key)
                    logger.info(f"Draft cleared for chat {telegram_message.chat_id}")
                    
                    # Éxito - Enviar confirmación (sin formato Markdown para evitar errores)
                    response_msg = f"✅ Solicitud creada exitosamente!\n\n"
                    response_msg += f"📋 Número: {solicitud_id[:8]}...\n\n"
                    response_msg += f"👤 Cliente: {cliente['nombre']}\n"
                    response_msg += f"📞 Teléfono: {telefono}\n"
                    response_msg += f"📍 Ciudad: {ciudad_display}\n\n"
                    
                    # Usar función para formatear repuestos (muestra solo cantidad si >7)
                    response_msg += format_repuestos_list(extracted_data["repuestos"])
                    
                    response_msg += f"\nVehículo: {vehiculo.get('marca', '')} "
                    response_msg += f"{vehiculo.get('linea', '')} "
                    response_msg += f"{vehiculo.get('anio', '')}\n\n"
                    response_msg += "🔍 Estamos buscando las mejores ofertas para ti. Te notificaremos pronto."
                    
                    await telegram_service.send_message(telegram_message.chat_id, response_msg)
                    
                    return {
                        "success": True,
                        "action": "solicitud_created",
                        "solicitud_id": solicitud_id
                    }
                else:
                    raise Exception(f"Core API error: {api_response.status_code} - {api_response.text}")
                
            except (json.JSONDecodeError, ValueError) as e:
                # No se pudo parsear - Pedir información clara
                logger.warning(f"Could not parse extracted data: {e}")
                help_msg = "🤔 No pude entender tu mensaje correctamente.\n\n"
                help_msg += "Por favor, envíame la información en este formato:\n\n"
                help_msg += "Soy [tu nombre], mi teléfono es [+57...], necesito [repuestos] para [marca modelo año] en [ciudad]\n\n"
                help_msg += "Ejemplo: _Soy Juan Pérez, mi teléfono es +573001234567, necesito pastillas de freno para Chevrolet Spark 2015 en Bogotá_"
                
                await telegram_service.send_message(telegram_message.chat_id, help_msg)
                
                return {
                    "success": True,
                    "action": "info_requested"
                }
                    
            except Exception as e:
                logger.error(f"❌ Error in Telegram processor logic: {e}")
                error_msg = "Lo siento, hubo un problema técnico procesando tu solicitud.\n\nPor favor, intenta de nuevo en unos minutos."
                await telegram_service.send_message(telegram_message.chat_id, error_msg)
                return {"success": False, "error": str(e)}
            
                
        except Exception as e:
            logger.error(f"Error handling solicitud message: {e}")
            error_msg = "Lo siento, hubo un error procesando tu mensaje. ¿Podrías intentar de nuevo?"
            await telegram_service.send_message(telegram_message.chat_id, error_msg)
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

🔧 *¿Qué repuestos necesitas?*
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


# Global Telegram message processor instance
telegram_message_processor = TelegramMessageProcessor()
