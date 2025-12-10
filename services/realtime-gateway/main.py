"""
TeLOO V3 Realtime Gateway Service
Comunicación WebSocket en tiempo real con Socket.IO y Redis
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.socket_manager import socket_manager
from app.redis_client import redis_client
from app.event_listener import event_listener

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting Realtime Gateway Service...")
    
    try:
        # Connect to Redis
        await redis_client.connect()
        
        # Start event listener
        await event_listener.start()
        
        logger.info("Realtime Gateway Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start service: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Realtime Gateway Service...")
    
    try:
        # Stop event listener
        await event_listener.stop()
        
        # Disconnect from Redis
        await redis_client.disconnect()
        
        logger.info("Realtime Gateway Service shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="TeLOO V3 Realtime Gateway",
    description="Comunicación WebSocket en tiempo real con Socket.IO y Redis",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO app
socket_app = socketio.ASGIApp(
    socket_manager.sio,
    other_asgi_app=app,
    socketio_path='/socket.io'
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "TeLOO V3 Realtime Gateway",
        "version": "3.0.0",
        "status": "running",
        "environment": settings.environment,
        "websocket_path": "/socket.io"
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
    
    health_status = {
        "status": "healthy",
        "service": "realtime-gateway",
        "version": "3.0.0",
        "timestamp": None,
        "checks": {}
    }
    
    all_healthy = True
    
    # Check Redis connection
    try:
        await redis_client.client.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        all_healthy = False
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }
    
    # Check WebSocket server
    try:
        connected_count = await socket_manager.get_connected_users_count()
        health_status["checks"]["websocket"] = {
            "status": "healthy",
            "message": f"WebSocket server operational ({connected_count} connections)"
        }
    except Exception as e:
        health_status["checks"]["websocket"] = {
            "status": "degraded",
            "message": f"WebSocket check failed: {str(e)}"
        }
    
    # Check event listener
    try:
        listener_running = event_listener.running if hasattr(event_listener, 'running') else True
        health_status["checks"]["event_listener"] = {
            "status": "healthy" if listener_running else "degraded",
            "message": "Event listener running" if listener_running else "Event listener stopped"
        }
    except Exception as e:
        health_status["checks"]["event_listener"] = {
            "status": "degraded",
            "message": f"Event listener check failed: {str(e)}"
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
        await redis_client.client.ping()
        
        # Check event listener is running
        listener_running = event_listener.running if hasattr(event_listener, 'running') else True
        if not listener_running:
            raise Exception("Event listener not running")
        
        return JSONResponse(
            content={
                "status": "ready",
                "service": "realtime-gateway",
                "checks": {
                    "redis": "ready",
                    "websocket": "ready",
                    "event_listener": "ready"
                }
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "not_ready",
                "service": "realtime-gateway",
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
        "service": "realtime-gateway",
        "version": "3.0.0"
    }


@app.get("/stats")
async def get_stats():
    """Get connection statistics"""
    return {
        "connected_users": await socket_manager.get_connected_users_count(),
        "admins_connected": await socket_manager.get_connected_users_by_role('ADMIN'),
        "advisors_connected": await socket_manager.get_connected_users_by_role('ADVISOR'),
        "clients_connected": await socket_manager.get_connected_users_by_role('CLIENT')
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=settings.port,
        reload=True if settings.environment == "development" else False,
        log_level=settings.log_level.lower()
    )