"""
Client Notification Listener for Agent IA
Listens to Redis events for client notifications about winning offers
"""

import logging
import json
import asyncio
from typing import Dict, Any
import httpx

from app.core.redis import redis_manager
from app.services.telegram_service import telegram_service
from app.services.whatsapp_service import whatsapp_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class ClientNotificationListener:
    """Listens to Redis events for client notifications"""
    
    def __init__(self):
        self.core_api_url = settings.core_api_url
        self.channels = [
            'cliente.notificar_ofertas_ganadoras',
            'cliente.recordatorio_ofertas',
            'cliente.timeout_respuesta'
        ]
    
    async def start_listening(self):
        """Start listening to Redis pub/sub channels"""
        try:
            logger.info(f"Starting client notification listener for channels: {self.channels}")
            
            # Get Redis pubsub
            pubsub = redis_manager.redis_client.pubsub()
            
            # Subscribe to channels
            await pubsub.subscribe(*self.channels)
            
            logger.info("✅ Client notification listener started successfully")
            
            # Listen for messages
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        channel = message['channel']
                        data = json.loads(message['data'])
                        
                        logger.info(f"📨 Received event from channel: {channel}")
                        
                        # Route to appropriate handler
                        if channel == 'cliente.notificar_ofertas_ganadoras':
                            await self._handle_ofertas_ganadoras(data)
                        elif channel == 'cliente.recordatorio_ofertas':
                            await self._handle_recordatorio(data)
                        elif channel == 'cliente.timeout_respuesta':
                            await self._handle_timeout(data)
                        
                    except Exception as e:
                        logger.error(f"Error processing message from {message.get('channel')}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error in client notification listener: {e}")
            # Retry after 5 seconds
            await asyncio.sleep(5)
            await self.start_listening()
    
    async def _handle_ofertas_ganadoras(self, data: Dict[str, Any]):
        """
        Handle notification of winning offers to client
        
        Event data:
        {
            "tipo_evento": "cliente.notificar_ofertas_ganadoras",
            "solicitud_id": "uuid",
            "codigo_solicitud": "SOL-ABC123",
            "cliente_telefono": "+573048887561",
            "cliente_nombre": "Fernando Hernández",
            "mensaje": "...",
            "pdf_filename": "Propuesta_SOL-ABC123.pdf",
            "metricas": {...},
            "timeout_horas": 24
        }
        """
        try:
            logger.info(f"📋 Notifying client about winning offers: {data['codigo_solicitud']}")
            
            telefono = data['cliente_telefono']
            mensaje = data['mensaje']
            solicitud_id = data['solicitud_id']
            
            # Determine if it's Telegram or WhatsApp
            is_telegram = telefono.startswith('+tg')
            
            if is_telegram:
                # Extract chat_id from phone number (+tg123456789 -> 123456789)
                chat_id = int(telefono.replace('+tg', ''))
                
                # Save solicitud_id in conversation context for response handling
                from app.services.conversation_service import conversation_service
                await conversation_service.set_solicitud_id(telefono, solicitud_id)
                logger.info(f"💾 Saved solicitud_id {solicitud_id} in conversation context for {telefono}")
                
                # Download PDF from Core API
                pdf_content = await self._download_pdf(solicitud_id)
                
                if pdf_content:
                    # Send PDF via Telegram
                    await telegram_service.send_document(
                        chat_id=chat_id,
                        document=pdf_content,
                        filename=data['pdf_filename'],
                        caption=mensaje
                    )
                    logger.info(f"✅ PDF sent to Telegram chat {chat_id}")
                else:
                    # Send only message if PDF download failed
                    await telegram_service.send_message(chat_id, mensaje)
                    logger.warning(f"⚠️ PDF download failed, sent only message to chat {chat_id}")
            
            else:
                # WhatsApp
                # Save solicitud_id in conversation context for response handling
                from app.services.conversation_service import conversation_service
                await conversation_service.set_solicitud_id(telefono, solicitud_id)
                logger.info(f"💾 Saved solicitud_id {solicitud_id} in conversation context for {telefono}")
                
                # Download PDF from Core API
                pdf_content = await self._download_pdf(solicitud_id)
                
                if pdf_content:
                    # Send PDF via WhatsApp
                    await whatsapp_service.send_document(
                        phone_number=telefono,
                        document=pdf_content,
                        filename=data['pdf_filename'],
                        caption=mensaje
                    )
                    logger.info(f"✅ PDF sent to WhatsApp {telefono}")
                else:
                    # Send only message if PDF download failed
                    await whatsapp_service.send_text_message(telefono, mensaje)
                    logger.warning(f"⚠️ PDF download failed, sent only message to {telefono}")
            
            logger.info(f"✅ Client notified successfully: {data['codigo_solicitud']}")
        
        except Exception as e:
            logger.error(f"Error handling ofertas ganadoras notification: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def _handle_recordatorio(self, data: Dict[str, Any]):
        """
        Handle reminder to client
        
        Event data:
        {
            "tipo_evento": "cliente.recordatorio_ofertas",
            "solicitud_id": "uuid",
            "codigo_solicitud": "SOL-ABC123",
            "cliente_telefono": "+573048887561",
            "mensaje": "...",
            "tipo_recordatorio": "intermedio|final"
        }
        """
        try:
            logger.info(f"⏰ Sending reminder: {data['tipo_recordatorio']} for {data['codigo_solicitud']}")
            
            telefono = data['cliente_telefono']
            mensaje = data['mensaje']
            
            # Determine if it's Telegram or WhatsApp
            is_telegram = telefono.startswith('+tg')
            
            if is_telegram:
                chat_id = int(telefono.replace('+tg', ''))
                await telegram_service.send_message(chat_id, mensaje)
            else:
                await whatsapp_service.send_text_message(telefono, mensaje)
            
            logger.info(f"✅ Reminder sent: {data['tipo_recordatorio']}")
        
        except Exception as e:
            logger.error(f"Error handling reminder: {e}")
    
    async def _handle_timeout(self, data: Dict[str, Any]):
        """
        Handle timeout notification
        
        Event data:
        {
            "tipo_evento": "cliente.timeout_respuesta",
            "solicitud_id": "uuid",
            "codigo_solicitud": "SOL-ABC123",
            "cliente_telefono": "+573048887561",
            "mensaje": "..."
        }
        """
        try:
            logger.info(f"⏰ Sending timeout notification for {data['codigo_solicitud']}")
            
            telefono = data['cliente_telefono']
            mensaje = data['mensaje']
            
            # Determine if it's Telegram or WhatsApp
            is_telegram = telefono.startswith('+tg')
            
            if is_telegram:
                chat_id = int(telefono.replace('+tg', ''))
                await telegram_service.send_message(chat_id, mensaje)
            else:
                await whatsapp_service.send_text_message(telefono, mensaje)
            
            logger.info(f"✅ Timeout notification sent")
        
        except Exception as e:
            logger.error(f"Error handling timeout: {e}")
    
    async def _download_pdf(self, solicitud_id: str) -> bytes:
        """
        Download PDF from Core API
        
        Args:
            solicitud_id: ID of the solicitud
            
        Returns:
            PDF content as bytes or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.core_api_url}/v1/solicitudes/{solicitud_id}/pdf-ofertas",
                    headers={
                        "X-Service-API-Key": settings.service_api_key,
                        "X-Service-Name": "agent-ia"
                    }
                )
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"Failed to download PDF: HTTP {response.status_code}")
                    return None
        
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return None


# Global instance
client_notification_listener = ClientNotificationListener()
