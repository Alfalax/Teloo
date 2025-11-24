"""
Telegram webhook endpoints
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Optional

from app.models.telegram import TelegramUpdate
from app.services.telegram_service import telegram_service
from app.services.rate_limiter import rate_limiter
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/telegram", tags=["telegram"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


async def check_rate_limit(request: Request):
    """Rate limiting dependency"""
    client_ip = get_client_ip(request)
    
    rate_limit_info = await rate_limiter.is_rate_limited(client_ip)
    
    if rate_limit_info.is_limited:
        logger.warning(f"Rate limit exceeded for IP {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Too many requests.",
            headers={
                "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(rate_limit_info.window_start.timestamp()) + 60)
            }
        )
    
    return rate_limit_info


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    update: TelegramUpdate,
    rate_limit_info = Depends(check_rate_limit)
):
    """
    Telegram webhook endpoint for receiving updates
    
    This endpoint receives webhook notifications from Telegram when:
    - A message is sent to the bot
    - A message is edited
    """
    try:
        client_ip = get_client_ip(request)
        logger.info(f"Telegram webhook received from IP {client_ip}, update_id={update.update_id}")
        
        # Extract message from update
        message = telegram_service.extract_message_from_update(update)
        
        if message:
            logger.info(f"Processing message {message.message_id} from chat {message.chat_id}")
            
            # Queue message for asynchronous processing
            queued = await telegram_service.queue_message_for_processing(message)
            
            if not queued:
                logger.error(f"Failed to queue message {message.message_id}")
        else:
            logger.info("No message found in update")
        
        # Always return 200 to Telegram to acknowledge receipt
        return {
            "ok": True,
            "status": "received",
            "update_id": update.update_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        # Return 200 to prevent Telegram retries for processing errors
        return {
            "ok": True,
            "status": "error",
            "message": "Internal processing error"
        }


@router.get("/status")
async def telegram_status():
    """Get Telegram bot status and configuration"""
    try:
        webhook_info = await telegram_service.get_webhook_info()
        
        return {
            "service": "Telegram Bot",
            "status": "active",
            "bot_token_configured": bool(settings.telegram_bot_token),
            "webhook_info": webhook_info.get("result", {}) if webhook_info.get("ok") else None
        }
    except Exception as e:
        logger.error(f"Error getting Telegram status: {e}")
        return {
            "service": "Telegram Bot",
            "status": "error",
            "error": str(e)
        }


@router.post("/set-webhook")
async def set_telegram_webhook(webhook_url: str):
    """
    Set Telegram webhook URL
    
    Args:
        webhook_url: Public HTTPS URL for webhook (e.g., https://yourdomain.com/v1/telegram/webhook)
    """
    try:
        success = await telegram_service.set_webhook(webhook_url)
        
        if success:
            return {
                "ok": True,
                "message": f"Webhook set to {webhook_url}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to set webhook")
            
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete-webhook")
async def delete_telegram_webhook():
    """Delete Telegram webhook"""
    try:
        success = await telegram_service.delete_webhook()
        
        if success:
            return {
                "ok": True,
                "message": "Webhook deleted"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete webhook")
            
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
