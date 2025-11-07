"""
WhatsApp webhook endpoints
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from typing import Optional

from app.models.whatsapp import WhatsAppWebhook
from app.services.whatsapp_service import whatsapp_service
from app.services.rate_limiter import rate_limiter
from app.core.config import settings
from app.core.redis import redis_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers first (for reverse proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
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


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """
    WhatsApp webhook verification endpoint
    
    This endpoint is called by WhatsApp to verify the webhook URL.
    It must return the challenge value if the verify token matches.
    """
    logger.info(f"Webhook verification request: mode={hub_mode}, token={hub_verify_token}")
    
    # Verify the token
    if hub_verify_token != settings.whatsapp_verify_token:
        logger.error(f"Invalid verify token: {hub_verify_token}")
        raise HTTPException(status_code=403, detail="Invalid verify token")
    
    # Verify the mode
    if hub_mode != "subscribe":
        logger.error(f"Invalid hub mode: {hub_mode}")
        raise HTTPException(status_code=400, detail="Invalid hub mode")
    
    logger.info("Webhook verification successful")
    return PlainTextResponse(content=hub_challenge)


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    webhook_data: WhatsAppWebhook,
    rate_limit_info = Depends(check_rate_limit)
):
    """
    WhatsApp webhook endpoint for receiving messages
    
    This endpoint receives webhook notifications from WhatsApp when:
    - A message is sent to the business phone number
    - A message status changes (delivered, read, etc.)
    - Other webhook events occur
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify webhook signature if enabled
        if settings.webhook_signature_verification:
            signature = request.headers.get("X-Hub-Signature-256", "")
            if not whatsapp_service.verify_webhook_signature(body, signature):
                logger.error("Invalid webhook signature")
                raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Log webhook received
        client_ip = get_client_ip(request)
        logger.info(f"WhatsApp webhook received from IP {client_ip}")
        
        # Extract message from webhook
        message = whatsapp_service.extract_message_from_webhook(webhook_data)
        
        if message:
            logger.info(f"Processing message {message.message_id} from {message.from_number}")
            
            # Queue message for asynchronous processing
            queued = await whatsapp_service.queue_message_for_processing(message)
            
            if not queued:
                logger.error(f"Failed to queue message {message.message_id}")
                # Don't return error to WhatsApp - we don't want them to retry
        else:
            logger.info("No message found in webhook (possibly status update)")
        
        # Always return 200 to WhatsApp to acknowledge receipt
        return {
            "status": "received",
            "timestamp": rate_limit_info.window_start.isoformat(),
            "rate_limit": {
                "remaining": settings.rate_limit_per_minute - rate_limit_info.request_count,
                "limit": settings.rate_limit_per_minute
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (rate limiting, auth errors)
        raise
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        # Return 200 to prevent WhatsApp retries for processing errors
        return {
            "status": "error",
            "message": "Internal processing error"
        }


@router.get("/whatsapp/status")
async def webhook_status():
    """Get webhook status and configuration"""
    return {
        "service": "WhatsApp Webhook",
        "status": "active",
        "configuration": {
            "phone_number_id": settings.whatsapp_phone_number_id,
            "api_version": settings.whatsapp_api_version,
            "signature_verification": settings.webhook_signature_verification,
            "rate_limit_per_minute": settings.rate_limit_per_minute
        },
        "queue_info": {
            "queue_length": await redis_manager.llen("whatsapp:message_queue") if redis_manager.redis_client else 0
        }
    }