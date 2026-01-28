"""
Telegram Bot API service
"""

import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.models.telegram import TelegramUpdate, TelegramMessage, ProcessedTelegramMessage

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for interacting with Telegram Bot API"""
    
    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_message(
        self, 
        chat_id: str, 
        text: str,
        parse_mode: str = "Markdown",
        reply_to_message_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send text message to Telegram chat
        
        Args:
            chat_id: Telegram chat ID
            text: Message text (supports Markdown)
            parse_mode: Parse mode (Markdown, HTML, or None)
            reply_to_message_id: Message ID to reply to
            
        Returns:
            API response
        """
        try:
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            if reply_to_message_id:
                payload["reply_to_message_id"] = reply_to_message_id
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"Message sent to chat {chat_id}")
                return result
            else:
                logger.error(f"Failed to send message: {result}")
                return {"ok": False, "error": result.get("description")}
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return {"ok": False, "error": str(e)}
    
    async def send_photo(
        self,
        chat_id: str,
        photo_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send photo to Telegram chat"""
        try:
            url = f"{self.base_url}/sendPhoto"
            
            payload = {
                "chat_id": chat_id,
                "photo": photo_url
            }
            
            if caption:
                payload["caption"] = caption
                payload["parse_mode"] = "Markdown"
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            return {"ok": False, "error": str(e)}
    
    async def get_file(self, file_id: str) -> Optional[str]:
        """
        Get file download URL from Telegram
        
        Args:
            file_id: Telegram file ID
            
        Returns:
            File download URL or None
        """
        try:
            url = f"{self.base_url}/getFile"
            
            response = await self.client.post(url, json={"file_id": file_id})
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                file_path = result["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                return download_url
            else:
                logger.error(f"Failed to get file: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting file: {e}")
            return None
    
    async def download_file(self, file_id: str) -> Optional[bytes]:
        """
        Download file from Telegram
        
        Args:
            file_id: Telegram file ID
            
        Returns:
            File bytes or None
        """
        try:
            file_url = await self.get_file(file_id)
            if not file_url:
                return None
            
            response = await self.client.get(file_url)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return None
    
    async def set_webhook(self, webhook_url: str, secret_token: Optional[str] = None) -> bool:
        """
        Set webhook URL for receiving updates
        
        Args:
            webhook_url: Public HTTPS URL for webhook
            secret_token: Optional secret token for security
            
        Returns:
            Success status
        """
        try:
            url = f"{self.base_url}/setWebhook"
            
            # Clean trailing slashes to avoid // in URL
            webhook_url = webhook_url.rstrip('/')
            
            payload = {
                "url": webhook_url,
                "allowed_updates": ["message", "edited_message"]
            }
            
            if secret_token:
                payload["secret_token"] = secret_token
            
            logger.info(f"Attempting to set Telegram Webhook: {webhook_url}")
            response = await self.client.post(url, json=payload)
            
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"✅ Webhook successfully set to {webhook_url}")
                return True
            else:
                logger.error(f"❌ Failed to set webhook: {result.get('description', 'No description')}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False
    
    async def delete_webhook(self) -> bool:
        """Delete webhook"""
        try:
            url = f"{self.base_url}/deleteWebhook"
            
            response = await self.client.post(url)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                logger.info("Webhook deleted")
                return True
            else:
                logger.error(f"Failed to delete webhook: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """Get current webhook information"""
        try:
            url = f"{self.base_url}/getWebhookInfo"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return {"ok": False, "error": str(e)}
    
    def extract_message_from_update(self, update: TelegramUpdate) -> Optional[ProcessedTelegramMessage]:
        """
        Extract processed message from Telegram update
        
        Args:
            update: Telegram update
            
        Returns:
            Processed message or None
        """
        try:
            telegram_message = update.get_message()
            
            if not telegram_message:
                logger.info("No message in update")
                return None
            
            # Convert to processed message
            processed = ProcessedTelegramMessage.from_telegram_message(telegram_message)
            
            logger.info(
                f"Extracted message: type={processed.message_type}, "
                f"chat_id={processed.chat_id}, "
                f"has_text={bool(processed.text_content)}, "
                f"has_media={bool(processed.media_file_id)}"
            )
            
            return processed
            
        except Exception as e:
            logger.error(f"Error extracting message from update: {e}")
            return None
    
    async def queue_message_for_processing(self, message: ProcessedTelegramMessage) -> bool:
        """
        Queue message for asynchronous processing
        
        Args:
            message: Processed Telegram message
            
        Returns:
            Success status
        """
        try:
            from app.core.redis import redis_manager
            import json
            
            queue_key = "telegram:message_queue"
            
            message_data = {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "user_id": message.user_id,
                "username": message.username,
                "timestamp": message.timestamp.isoformat(),
                "message_type": message.message_type,
                "text_content": message.text_content,
                "media_file_id": message.media_file_id,
                "media_type": message.media_type
            }
            
            await redis_manager.lpush(queue_key, json.dumps(message_data))
            
            logger.info(f"Message {message.message_id} queued for processing")
            return True
            
        except Exception as e:
            logger.error(f"Error queuing message: {e}")
            return False
    
    async def format_offer_message(self, offer_data: Dict[str, Any]) -> str:
        """
        Format offer data as Telegram message
        
        Args:
            offer_data: Offer data from evaluation
            
        Returns:
            Formatted message text
        """
        try:
            # Similar to WhatsApp formatting but with Telegram Markdown
            message_parts = ["🎉 *¡Tenemos ofertas para ti!*\n"]
            
            if offer_data.get("tipo_oferta") == "unica":
                # Single offer
                oferta = offer_data["ofertas"][0]
                message_parts.append(f"💰 *Precio:* ${oferta['precio']:,.0f}")
                message_parts.append(f"⏱️ *Tiempo entrega:* {oferta['tiempo_entrega']} días")
                message_parts.append(f"✅ *Garantía:* {oferta['garantia']} meses")
                message_parts.append(f"🏪 *Proveedor:* {oferta['proveedor']}")
            else:
                # Mixed offer
                message_parts.append("📦 *Oferta mixta de múltiples proveedores:*\n")
                for i, oferta in enumerate(offer_data["ofertas"], 1):
                    message_parts.append(f"\n*Repuesto {i}:* {oferta['repuesto']}")
                    message_parts.append(f"💰 ${oferta['precio']:,.0f}")
                    message_parts.append(f"🏪 {oferta['proveedor']}")
            
            message_parts.append("\n¿Aceptas esta oferta? Responde *SÍ* o *NO*")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error formatting offer message: {e}")
            return "Tenemos ofertas disponibles para ti. ¿Te interesa?"
    
    async def send_document(
        self,
        chat_id: int,
        document: bytes,
        filename: str,
        caption: Optional[str] = None,
        parse_mode: str = "Markdown"
    ) -> Dict[str, Any]:
        """
        Send document (PDF, Excel, etc.) to Telegram chat
        
        Args:
            chat_id: Telegram chat ID
            document: Document content as bytes
            filename: Name of the file
            caption: Optional caption for the document
            parse_mode: Parse mode for caption (Markdown, HTML, or None)
            
        Returns:
            API response
        """
        try:
            url = f"{self.base_url}/sendDocument"
            
            # Prepare multipart form data
            files = {
                'document': (filename, document, 'application/octet-stream')
            }
            
            data = {
                'chat_id': str(chat_id)
            }
            
            if caption:
                data['caption'] = caption
                data['parse_mode'] = parse_mode
            
            response = await self.client.post(url, files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"Document sent to chat {chat_id}: {filename}")
                return result
            else:
                logger.error(f"Failed to send document: {result}")
                return {"ok": False, "error": result.get("description")}
                
        except Exception as e:
            logger.error(f"Error sending Telegram document: {e}")
            return {"ok": False, "error": str(e)}

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global Telegram service instance
telegram_service = TelegramService()
