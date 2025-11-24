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
                
                # Clear draft from Redis
                from app.core.redis import redis_manager
                draft_key = f"solicitud_draft:{telegram_message.chat_id}"
                await redis_manager.delete(draft_key)
                
                telegram_service = TelegramService()
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
                        "X-Service-API-Key": settings.service_api_key,
                        "X-Service-Name": "agent-ia"
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
        whatsapp_message: ProcessedMessage
    ) -> Dict[str, Any]:
        """Handle message as part of solicitud creation process"""
        try:
            logger.info(f"Handling solicitud message from chat {telegram_message.chat_id}")
            
            # TEMPORAL: Procesamiento simple con OpenAI para pruebas
            # TODO: Reemplazar con sistema WhatsApp completo cuando se implemente
            import httpx
            from app.core.config import settings
            
            try:
                # Si hay archivo adjunto (Excel o Audio), procesarlo primero
                message_content = telegram_message.text_content or ""
                
                # COMANDOS ESPECIALES
                comando = message_content.strip().lower()
                
                # /reiniciar o /cancelar - Limpiar draft y empezar de nuevo
                if comando in ["/reiniciar", "/cancelar", "/empezar", "/nuevo"]:
                    from app.core.redis import redis_manager
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
                if whatsapp_message.media_url and whatsapp_message.media_type in ["voice", "audio"]:
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
                
                # RECUPERAR DRAFT EXISTENTE PRIMERO
                from app.core.redis import redis_manager
                draft_key = f"solicitud_draft:{telegram_message.chat_id}"
                existing_draft = await redis_manager.get_json(draft_key)
                
                # Variables de control
                user_confirmed = False
                extracted_data = None
                
                # SIEMPRE ANALIZAR INTENCIÓN CUANDO HAY DRAFT (con o sin estado pending_confirmation)
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

- "reject": Usuario rechaza TODO y quiere empezar de nuevo (SOLO rechazos totales)
  Ejemplos: "no, todo mal", "empecemos de nuevo", "borra todo", "cancela", "nada está bien"
  NO ES RECHAZO: "no, es la izquierda" (es corrección), "no viene el par?" (es pregunta)

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
   - Actualiza la cantidad de ESE repuesto específico al número mencionado

EJEMPLOS:
Usuario: "¿las pastillas vienen 1 o el par?"
→ intent: "question", answer: "Las pastillas de freno normalmente vienen por par (2 unidades). En tu solicitud tengo las cantidades que mencionaste."

Usuario: "entonces necesito las 2" (después de pregunta sobre "pastillas")
→ intent: "correct"
→ Busca en el último mensaje del bot qué repuesto se mencionó ("pastillas")
→ Busca en los repuestos actuales el que contiene "pastillas" y fue agregado más recientemente
→ Actualiza su cantidad a 2

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
                            
                            # Usuario CONFIRMA - crear solicitud
                            if intent == "confirm":
                                logger.info(f"User confirmed solicitud (natural language)")
                                # Eliminar draft de Redis
                                await redis_manager.delete(draft_key)
                                
                                # Preparar datos para creación (saltar validación porque ya fue validado antes)
                                extracted_data = existing_draft
                                # Limpiar campos internos
                                if "_status" in extracted_data:
                                    del extracted_data["_status"]
                                if "_last_bot_message" in extracted_data:
                                    del extracted_data["_last_bot_message"]
                                
                                # Marcar que el usuario confirmó para saltar el procesamiento de GPT-4
                                user_confirmed = True
                                existing_draft = None
                                # El código continúa después del bloque if existing_draft
                            
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
                                
                                # Aplicar correcciones completas del GPT-4
                                if "cliente" in updated_data:
                                    existing_draft["cliente"] = updated_data["cliente"]
                                if "vehiculo" in updated_data:
                                    existing_draft["vehiculo"] = updated_data["vehiculo"]
                                if "repuestos" in updated_data:
                                    existing_draft["repuestos"] = updated_data["repuestos"]
                                
                                # Mostrar resumen actualizado
                                confirmation_msg = "✅ Perfecto, actualicé la información:\n\n"
                                confirmation_msg += f"👤 Cliente: {existing_draft['cliente']['nombre']}\n"
                                confirmation_msg += f"📞 Teléfono: {existing_draft['cliente']['telefono']}\n"
                                confirmation_msg += f"📍 Ciudad: {existing_draft['cliente']['ciudad']}\n\n"
                                vehiculo = existing_draft.get("vehiculo", {})
                                confirmation_msg += f"� Vehíctulo: {vehiculo.get('marca', '')} {vehiculo.get('linea', '')} {vehiculo.get('anio', '')}\n\n"
                                confirmation_msg += f"�  Repuestos:\n"
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
                if not cliente.get("telefono"):
                    missing_fields.append("teléfono del cliente")
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
                
                    # TODOS LOS DATOS COMPLETOS - PEDIR CONFIRMACIÓN
                    # Mostrar resumen y pedir confirmación
                    confirmation_msg = "📋 Perfecto, aquí está el resumen:\n\n"
                    confirmation_msg += f"👤 Cliente: {cliente['nombre']}\n"
                    confirmation_msg += f"📞 Teléfono: {cliente['telefono']}\n"
                    confirmation_msg += f"📍 Ciudad: {cliente['ciudad']}\n\n"
                    confirmation_msg += f"🚗 Vehículo: {vehiculo.get('marca', '')} {vehiculo.get('linea', '')} {vehiculo.get('anio', '')}\n\n"
                    confirmation_msg += f"� rRepuestos:\n"
                    # Usar función helper para formatear repuestos
                    confirmation_msg += format_repuestos_list(extracted_data["repuestos"])
                    confirmation_msg = confirmation_msg.rstrip('\n')  # Remover salto de línea extra ya que format_repuestos_list incluye el encabezado
                    confirmation_msg += "\n¿Todo está bien o necesitas corregir algo?"
                    
                    # Guardar draft con estado "pending_confirmation" y último mensaje del bot
                    extracted_data["_status"] = "pending_confirmation"
                    extracted_data["_last_bot_message"] = confirmation_msg
                    await redis_manager.set_json(draft_key, extracted_data, ttl=3600)
                    logger.info(f"All data complete for chat {telegram_message.chat_id}, requesting confirmation")
                    
                    await telegram_service.send_message(telegram_message.chat_id, confirmation_msg)
                    
                    return {
                        "success": True,
                        "action": "confirmation_requested"
                    }
                
                # Si llegamos aquí, el usuario YA confirmó - Crear solicitud
                repuestos_formatted = []
                for rep in extracted_data["repuestos"]:
                    repuestos_formatted.append({
                        "nombre": rep["nombre"],
                        "cantidad": rep.get("cantidad", 1),
                        "marca_vehiculo": vehiculo.get("marca", "N/A"),
                        "linea_vehiculo": vehiculo.get("linea", "N/A") if vehiculo.get("linea") else "N/A",
                        "anio_vehiculo": int(vehiculo.get("anio", 2020)),
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
                
                # Buscar municipio_id basado en la ciudad
                # Limpiar ciudad: remover departamentos que las personas suelen agregar
                from app.services.solicitud_service import limpiar_ciudad
                ciudad_normalizada = limpiar_ciudad(cliente["ciudad"])
                
                # Buscar UUID del municipio por nombre usando endpoint seguro
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
                    municipio_data = geo_response.json()
                    municipio_id = municipio_data["id"]
                    departamento = municipio_data["departamento"]
                    ciudad_display = f"{ciudad_normalizada.title()} - {departamento}"
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
                        
                        # Guardar draft con estado de ciudad_invalida para que el usuario pueda corregir
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
                
                solicitud_payload = {
                    "cliente": cliente_payload,
                    "municipio_id": municipio_id,
                    "ciudad_origen": ciudad_normalizada,  # Usar ciudad limpia sin departamento
                    "departamento_origen": departamento,
                    "repuestos": repuestos_formatted
                }
                
                # Llamar al endpoint seguro del bot
                async with httpx.AsyncClient(timeout=30.0) as api_client:
                    api_response = await api_client.post(
                        f"{settings.core_api_url}/v1/solicitudes/services/bot",
                        json=solicitud_payload,
                        headers={
                            "X-Service-Name": settings.service_name,
                            "X-Service-API-Key": settings.service_api_key
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
                logger.error(f"Error processing with OpenAI: {e}")
                error_msg = f"❌ Error procesando tu mensaje: {str(e)}\n\n"
                error_msg += "Por favor, intenta de nuevo o contacta soporte."
                await telegram_service.send_message(telegram_message.chat_id, error_msg)
                return {"success": False, "error": str(e)}
            
            # Código original comentado para producción
            if False:
                # Create solicitud
                solicitud_result = await solicitud_service.crear_solicitud_desde_whatsapp(
                    processed_data,
                    conversation
                )
                
                if solicitud_result["success"]:
                    # Store solicitud_id in conversation
                    await conversation_service.set_solicitud_id(
                        f"+tg{telegram_message.chat_id}",
                        solicitud_result["solicitud_id"]
                    )
                    
                    # Send confirmation
                    confirmation_msg = f"✅ ¡Perfecto! Tu solicitud #{solicitud_result['solicitud_id']} ha sido creada.\n\n"
                    confirmation_msg += "Estamos buscando las mejores ofertas para ti. Te notificaremos pronto. 🚀"
                    await telegram_service.send_message(telegram_message.chat_id, confirmation_msg)
                    
                    logger.info(f"Solicitud created: {solicitud_result['solicitud_id']}")
                else:
                    error_msg = f"❌ Error creando solicitud: {solicitud_result['error']}"
                    await telegram_service.send_message(telegram_message.chat_id, error_msg)
                
                return solicitud_result
            else:
                # Request missing information
                missing_info_msg = await self._generate_missing_info_message(processed_data)
                await telegram_service.send_message(telegram_message.chat_id, missing_info_msg)
                
                return {
                    "success": True,
                    "action": "info_requested",
                    "missing_fields": processed_data.missing_fields
                }
                
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
