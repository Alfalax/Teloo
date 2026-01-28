"""
TeLOO V3 Agent IA Service
Interfaz conversacional con clientes vía WhatsApp usando múltiples proveedores LLM
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.redis import redis_manager
from app.routers import webhooks
from app.services.whatsapp_service import whatsapp_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Agent IA Service...")
    
    try:
        # Connect to Redis
        await redis_manager.connect()
        logger.info("Connected to Redis successfully")
        
        # Start client notification listener in background
        import asyncio
        from app.services.client_notification_listener import client_notification_listener
        
        listener_task = asyncio.create_task(client_notification_listener.start_listening())
        logger.info("Client notification listener started")
        
        # Start Telegram Service
        telegram_task = None
        if settings.telegram_enabled and settings.telegram_bot_token:
            if settings.telegram_mode == "webhook" and settings.telegram_webhook_url:
                from app.services.telegram_service import telegram_service
                from app.services.telegram_message_processor import telegram_message_processor
                
                # Start queue processor in background
                telegram_task = asyncio.create_task(telegram_message_processor.process_queued_messages())
                logger.info("⚙️ Telegram queue processor started (Webhook Mode)")
                
                # Register webhook
                webhook_url = f"{settings.telegram_webhook_url}/v1/telegram/webhook"
                success = await telegram_service.set_webhook(webhook_url, secret_token=settings.telegram_webhook_secret)
                if success:
                    logger.info(f"✅ Telegram Webhook registered: {webhook_url}")
                else:
                    logger.error("❌ Failed to register Telegram Webhook")
            else:
                from app.services.telegram_polling import polling_service
                telegram_task = asyncio.create_task(polling_service.start())
                logger.info("🚀 Telegram polling service started (Development Mode)")
        else:
            logger.info("Telegram service disabled or token not configured")
        
        logger.info("Agent IA Service started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Agent IA Service: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down Agent IA Service...")
        
        # Cancel listener task
        if 'listener_task' in locals():
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass
        
        # Cancel telegram task
        if 'telegram_task' in locals() and telegram_task:
            telegram_task.cancel()
            try:
                await telegram_task
            except asyncio.CancelledError:
                pass
            logger.info("Telegram polling stopped")
        
        # Close connections
        await redis_manager.disconnect()
        await whatsapp_service.close()
        
        logger.info("Agent IA Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Interfaz conversacional con clientes vía WhatsApp usando múltiples proveedores LLM",
    version=settings.version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Configure CORS
import os
import json

environment = os.getenv("ENVIRONMENT", settings.environment)
cors_origins_env = os.getenv("BACKEND_CORS_ORIGINS")
if cors_origins_env:
    try:
        origins = json.loads(cors_origins_env)
    except Exception:
        origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"] if environment == "production" else ["*"]
allow_headers = ["Authorization", "Content-Type", "X-Requested-With"] if environment == "production" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
)

# Include routers
app.include_router(webhooks.router)

# Import and include results router
from app.routers import results
app.include_router(results.router)

# Import and include Telegram router
from app.routers import telegram
app.include_router(telegram.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint with dependency checks
    Returns 200 if all critical dependencies are healthy
    Returns 503 if any critical dependency is unhealthy
    """
    from fastapi import status
    from fastapi.responses import JSONResponse
    from datetime import datetime
    import httpx
    
    health_status = {
        "status": "healthy",
        "service": "agent-ia",
        "version": settings.version,
        "environment": settings.environment,
        "timestamp": None,
        "checks": {}
    }
    
    all_healthy = True
    
    # Check Redis connection
    try:
        if redis_manager.redis_client:
            await redis_manager.redis_client.ping()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        else:
            all_healthy = False
            health_status["checks"]["redis"] = {
                "status": "unhealthy",
                "message": "Redis client not initialized"
            }
    except Exception as e:
        all_healthy = False
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }
    
    # Check Core API connection
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.core_api_url}/health/live")
            if response.status_code == 200:
                health_status["checks"]["core_api"] = {
                    "status": "healthy",
                    "message": "Core API reachable"
                }
            else:
                health_status["checks"]["core_api"] = {
                    "status": "degraded",
                    "message": f"Core API returned status {response.status_code}"
                }
    except Exception as e:
        health_status["checks"]["core_api"] = {
            "status": "degraded",
            "message": f"Core API unreachable: {str(e)}"
        }
    
    # Check WhatsApp service status
    try:
        whatsapp_configured = bool(settings.whatsapp_access_token and settings.whatsapp_phone_number_id)
        health_status["checks"]["whatsapp"] = {
            "status": "healthy" if whatsapp_configured else "not_configured",
            "message": "WhatsApp credentials configured" if whatsapp_configured else "WhatsApp not configured"
        }
    except Exception as e:
        health_status["checks"]["whatsapp"] = {
            "status": "degraded",
            "message": f"WhatsApp check failed: {str(e)}"
        }
    
    # Set overall status
    health_status["timestamp"] = datetime.utcnow().isoformat()
    health_status["status"] = "healthy" if all_healthy else "unhealthy"
    
    # Return appropriate status code
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=health_status, status_code=status_code)

@app.get("/health/ready")
async def readiness_check():
    """
    Readiness probe - checks if service is ready to accept traffic
    Used by Kubernetes/Docker to determine if container is ready
    """
    from fastapi import status
    from fastapi.responses import JSONResponse
    
    try:
        # Check Redis is accessible
        if redis_manager.redis_client:
            await redis_manager.redis_client.ping()
        else:
            raise Exception("Redis client not initialized")
        
        return JSONResponse(
            content={
                "status": "ready",
                "service": "agent-ia",
                "checks": {
                    "redis": "ready"
                }
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "not_ready",
                "service": "agent-ia",
                "error": str(e)
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

@app.get("/health/live")
async def liveness_check():
    """
    Liveness probe - checks if service is alive
    Used by Kubernetes/Docker to determine if container should be restarted
    This is a lightweight check that only verifies the application is running
    """
    return {
        "status": "alive",
        "service": "agent-ia",
        "version": settings.version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug
    )
