"""
Telegram Long Polling Service
Para pruebas locales sin necesidad de VPS o webhooks
"""
import asyncio
import logging
from typing import Optional
import httpx

from app.core.config import settings
from app.services.telegram_message_processor import TelegramMessageProcessor

logger = logging.getLogger(__name__)


class TelegramPollingService:
    """
    Servicio de Long Polling para Telegram
    Permite recibir mensajes sin necesidad de webhook público
    """
    
    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.message_processor = TelegramMessageProcessor()
        self.offset = 0
        self.timeout = 30  # Timeout de polling en segundos
        self.running = False
        
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(self.timeout + 10))
        
        logger.info("TelegramPollingService initialized")
    
    async def start(self):
        """Iniciar el servicio de polling"""
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not configured")
            return
        
        # Inicializar Redis
        try:
            from app.core.redis import redis_manager
            await redis_manager.connect()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Continuing without conversation memory.")
        
        self.running = True
        logger.info("🚀 Starting Telegram Long Polling...")
        logger.info(f"Bot Token: {self.bot_token[:10]}...")
        
        # Obtener info del bot
        bot_info = await self.get_bot_info()
        if bot_info:
            logger.info(f"✅ Bot connected: @{bot_info.get('username')}")
            logger.info(f"   Name: {bot_info.get('first_name')}")
        
        # Iniciar loop de polling
        await self.polling_loop()
    
    async def stop(self):
        """Detener el servicio de polling"""
        self.running = False
        await self.client.aclose()
        logger.info("Telegram polling stopped")
    
    async def get_bot_info(self) -> Optional[dict]:
        """Obtener información del bot"""
        try:
            response = await self.client.get(f"{self.api_url}/getMe")
            if response.status_code == 200:
                data = response.json()
                return data.get("result")
            else:
                logger.error(f"Failed to get bot info: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return None
    
    async def polling_loop(self):
        """Loop principal de polling"""
        logger.info("📡 Polling loop started. Waiting for messages...")
        
        while self.running:
            try:
                # Obtener actualizaciones
                updates = await self.get_updates()
                
                if updates:
                    logger.info(f"📨 Received {len(updates)} update(s)")
                    
                    # Procesar cada actualización
                    for update in updates:
                        await self.process_update(update)
                        
                        # Actualizar offset para no recibir el mismo mensaje
                        self.offset = update.get("update_id", 0) + 1
                
            except asyncio.CancelledError:
                logger.info("Polling loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(5)  # Esperar antes de reintentar
    
    async def get_updates(self) -> list:
        """Obtener actualizaciones de Telegram"""
        try:
            params = {
                "offset": self.offset,
                "timeout": self.timeout,
                "allowed_updates": ["message", "callback_query"]
            }
            
            response = await self.client.get(
                f"{self.api_url}/getUpdates",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])
                else:
                    logger.error(f"Telegram API error: {data}")
                    return []
            else:
                logger.error(f"HTTP error {response.status_code}: {response.text}")
                return []
                
        except httpx.TimeoutException:
            # Timeout es normal en long polling
            return []
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []
    
    async def process_update(self, update: dict):
        """Procesar una actualización de Telegram"""
        try:
            update_id = update.get("update_id")
            
            # Procesar mensaje
            if "message" in update:
                message = update["message"]
                chat_id = message.get("chat", {}).get("id")
                user = message.get("from", {})
                username = user.get("username", "unknown")
                
                # Log del mensaje recibido
                if "text" in message:
                    logger.info(f"💬 Text from @{username}: {message['text'][:50]}...")
                elif "voice" in message:
                    logger.info(f"🎤 Voice message from @{username}")
                elif "audio" in message:
                    logger.info(f"🎵 Audio from @{username}")
                elif "photo" in message:
                    logger.info(f"📷 Photo from @{username}")
                elif "document" in message:
                    logger.info(f"📄 Document from @{username}")
                
                # Procesar mensaje con IA
                from app.services.telegram_message_processor import telegram_message_processor
                from app.models.telegram import ProcessedTelegramMessage
                from datetime import datetime
                
                # Determinar tipo de mensaje y file_id
                media_file_id = None
                media_type = None
                caption = message.get("caption")
                
                if "voice" in message:
                    media_file_id = message["voice"].get("file_id")
                    media_type = "voice"
                elif "audio" in message:
                    media_file_id = message["audio"].get("file_id")
                    media_type = "audio"
                elif "photo" in message:
                    media_file_id = message["photo"][-1].get("file_id") if message["photo"] else None
                    media_type = "photo"
                elif "document" in message:
                    media_file_id = message["document"].get("file_id")
                    media_type = "document"
                
                # Crear mensaje procesado
                telegram_msg = ProcessedTelegramMessage(
                    message_id=str(message.get("message_id")),
                    chat_id=str(chat_id),
                    user_id=str(user.get("id")),
                    username=username,
                    timestamp=datetime.now(),
                    message_type="text" if "text" in message and not media_file_id else "media",
                    text_content=message.get("text") or caption,
                    media_file_id=media_file_id,
                    media_type=media_type
                )
                
                # Procesar con IA
                await telegram_message_processor.process_message(telegram_msg)
            
            # Procesar callback query (botones)
            elif "callback_query" in update:
                callback = update["callback_query"]
                logger.info(f"🔘 Callback: {callback.get('data')}")
                # Aquí puedes manejar callbacks de botones
                
        except Exception as e:
            logger.error(f"Error processing update {update.get('update_id')}: {e}", exc_info=True)
    
    async def send_message(self, chat_id: int, text: str, **kwargs):
        """Enviar mensaje a un chat"""
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                **kwargs
            }
            
            response = await self.client.post(
                f"{self.api_url}/sendMessage",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent to {chat_id}")
                return response.json()
            else:
                logger.error(f"Failed to send message: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None


# Instancia global
polling_service = TelegramPollingService()


# Entry point para ejecutar el servicio
if __name__ == "__main__":
    import sys
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Ejecutar servicio
    try:
        asyncio.run(polling_service.start())
    except KeyboardInterrupt:
        logger.info("🛑 Telegram polling stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
