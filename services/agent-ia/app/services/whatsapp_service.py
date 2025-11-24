"""
WhatsApp service for handling webhook and sending messages
"""

import hmac
import hashlib
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.redis import redis_manager
from app.models.whatsapp import (
    WhatsAppWebhook, 
    ProcessedMessage, 
    WhatsAppOutgoingMessage,
    WhatsAppMessage
)
from app.services.llm.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for WhatsApp integration with circuit breaker and retry logic"""
    
    def __init__(self):
        self.api_url = f"{settings.whatsapp_api_url}/{settings.whatsapp_api_version}"
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token
        self.verify_token = settings.whatsapp_verify_token
        self.webhook_secret = settings.whatsapp_webhook_secret
        
        # Circuit breaker for WhatsApp API
        self.circuit_breaker = CircuitBreaker(
            provider_name="whatsapp_api",
            failure_threshold=3,
            timeout_seconds=300  # 5 minutes
        )
        
        # HTTP client for API calls
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
        )
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff
    
    async def _retry_with_exponential_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"WhatsApp API call failed after {self.max_retries + 1} attempts: {e}")
                    break
                
                # Calculate delay with exponential backoff
                delay = self.base_delay * (2 ** attempt)
                logger.warning(f"WhatsApp API call failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
            except Exception as e:
                # Non-retryable errors
                logger.error(f"Non-retryable error in WhatsApp API call: {e}")
                raise e
        
        # If we get here, all retries failed
        raise last_exception
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify WhatsApp webhook signature"""
        if not settings.webhook_signature_verification:
            return True
        
        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def extract_message_from_webhook(self, webhook: WhatsAppWebhook) -> Optional[ProcessedMessage]:
        """Extract message data from WhatsApp webhook"""
        try:
            for entry in webhook.entry:
                for change in entry.changes:
                    if change.field == "messages":
                        value = change.value
                        
                        # Get messages array
                        messages = value.get("messages", [])
                        if not messages:
                            continue
                        
                        # Process first message
                        message_data = messages[0]
                        message = WhatsAppMessage(**message_data)
                        
                        # Extract text content
                        text_content = None
                        media_url = None
                        media_type = None
                        
                        if message.type == "text" and message.text:
                            text_content = message.text.get("body", "")
                        elif message.type == "image" and message.image:
                            media_url = message.image.get("id")
                            media_type = "image"
                            text_content = message.image.get("caption", "")
                        elif message.type == "audio" and message.audio:
                            media_url = message.audio.get("id")
                            media_type = "audio"
                        elif message.type == "document" and message.document:
                            media_url = message.document.get("id")
                            media_type = "document"
                            text_content = message.document.get("caption", "")
                        elif message.type == "voice" and message.voice:
                            media_url = message.voice.get("id")
                            media_type = "voice"
                        
                        # Get context if reply
                        context_message_id = None
                        if message.context:
                            context_message_id = message.context.get("id")
                        
                        return ProcessedMessage(
                            message_id=message.id,
                            from_number=message.from_,
                            timestamp=datetime.fromtimestamp(int(message.timestamp)),
                            message_type=message.type,
                            text_content=text_content,
                            media_url=media_url,
                            media_type=media_type,
                            context_message_id=context_message_id
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting message from webhook: {e}")
            return None
    
    async def queue_message_for_processing(self, message: ProcessedMessage) -> bool:
        """Queue message for asynchronous processing"""
        try:
            # Create queue entry
            queue_entry = {
                "message_id": message.message_id,
                "from_number": message.from_number,
                "timestamp": message.timestamp.isoformat(),
                "message_type": message.message_type,
                "text_content": message.text_content,
                "media_url": message.media_url,
                "media_type": message.media_type,
                "context_message_id": message.context_message_id,
                "queued_at": datetime.now().isoformat()
            }
            
            # Add to Redis queue
            queue_key = "whatsapp:message_queue"
            await redis_manager.lpush(queue_key, json.dumps(queue_entry))
            
            logger.info(f"Queued message {message.message_id} for processing")
            return True
            
        except Exception as e:
            logger.error(f"Error queuing message {message.message_id}: {e}")
            return False
    
    async def send_text_message(
        self, 
        to_number: str, 
        text: str,
        reply_to_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send text message via WhatsApp API with circuit breaker and retry logic
        
        Args:
            to_number: Recipient phone number
            text: Message text
            reply_to_message_id: Message ID to reply to (optional)
            
        Returns:
            API response dict with 'ok' status
        """
        try:
            # Check circuit breaker
            if not await self.circuit_breaker.is_available():
                logger.error(f"WhatsApp API circuit breaker is OPEN, cannot send message to {to_number}")
                return {"ok": False, "error": "Circuit breaker open"}
            
            async def _send_message():
                message = WhatsAppOutgoingMessage(
                    to=to_number,
                    type="text",
                    text={"body": text}
                )
                
                url = f"{self.api_url}/{self.phone_number_id}/messages"
                
                response = await self.client.post(
                    url,
                    json=message.model_dump()
                )
                
                if response.status_code == 200:
                    return response
                else:
                    # Raise HTTPStatusError for retry logic
                    response.raise_for_status()
            
            # Execute with circuit breaker and retry logic
            response = await self.circuit_breaker.call_with_circuit_breaker(
                self._retry_with_exponential_backoff,
                _send_message
            )
            
            logger.info(f"Message sent successfully to {to_number}")
            return {"ok": True, "result": response.json()}
                
        except Exception as e:
            logger.error(f"Error sending message to {to_number}: {e}")
            return {"ok": False, "error": str(e)}
    
    async def send_template_message(self, to_number: str, template_name: str, parameters: list = None) -> bool:
        """Send template message via WhatsApp API with circuit breaker and retry logic"""
        try:
            # Check circuit breaker
            if not await self.circuit_breaker.is_available():
                logger.error(f"WhatsApp API circuit breaker is OPEN, cannot send template message to {to_number}")
                return False
            
            async def _send_template():
                template_data = {
                    "name": template_name,
                    "language": {"code": "es"}
                }
                
                if parameters:
                    template_data["components"] = [
                        {
                            "type": "body",
                            "parameters": [{"type": "text", "text": param} for param in parameters]
                        }
                    ]
                
                message = WhatsAppOutgoingMessage(
                    to=to_number,
                    type="template",
                    template=template_data
                )
                
                url = f"{self.api_url}/{self.phone_number_id}/messages"
                
                response = await self.client.post(
                    url,
                    json=message.model_dump()
                )
                
                if response.status_code == 200:
                    return response
                else:
                    response.raise_for_status()
            
            # Execute with circuit breaker and retry logic
            response = await self.circuit_breaker.call_with_circuit_breaker(
                self._retry_with_exponential_backoff,
                _send_template
            )
            
            logger.info(f"Template message sent successfully to {to_number}")
            return True
                
        except Exception as e:
            logger.error(f"Error sending template message to {to_number}: {e}")
            return False
    
    async def get_media_url(self, media_id: str) -> Optional[str]:
        """Get media URL from WhatsApp API"""
        try:
            url = f"{self.api_url}/{media_id}"
            
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("url")
            else:
                logger.error(f"Failed to get media URL for {media_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting media URL for {media_id}: {e}")
            return None
    
    async def download_media(self, media_url: str) -> Optional[bytes]:
        """Download media content from WhatsApp"""
        try:
            response = await self.client.get(media_url)
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Failed to download media: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global WhatsApp service instance
whatsapp_service = WhatsAppService()