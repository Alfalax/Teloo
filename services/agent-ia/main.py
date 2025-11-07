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
        
        logger.info("Agent IA Service started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Agent IA Service: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down Agent IA Service...")
        
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
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhooks.router)

# Import and include results router
from app.routers import results
app.include_router(results.router)


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
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_status = "connected" if redis_manager.redis_client else "disconnected"
        
        return {
            "status": "healthy",
            "service": "agent-ia",
            "version": settings.version,
            "environment": settings.environment,
            "dependencies": {
                "redis": redis_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "agent-ia",
            "version": settings.version,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug
    )