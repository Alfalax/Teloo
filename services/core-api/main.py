"""
TeLOO V3 Core API Service
Motor central del sistema - gestión de solicitudes, ofertas, evaluación y escalamiento
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
import asyncio
import logging
from pathlib import Path
import json

# Import database and routers
from database import init_db
from routers import admin_router
from routers.auth import router as auth_router
from routers.solicitudes import router as solicitudes_router
from routers.ofertas import router as ofertas_router
from routers.asesores import router as asesores_router
from routers.pqr import router as pqr_router
from routers.configuracion import router as configuracion_router
from services.scheduler_service import scheduler_service

# Import logging and middleware
from utils.logger import init_logger, get_logger
from middleware.correlation_middleware import CorrelationMiddleware
from middleware.metrics_middleware import MetricsMiddleware

# Load environment variables
load_dotenv()

# Initialize structured logging
log_level = os.getenv("LOG_LEVEL", "INFO")
environment = os.getenv("ENVIRONMENT", "development")
init_logger("core-api", log_level)
logger = get_logger()

# Create FastAPI app
app = FastAPI(
    title="TeLOO V3 Core API",
    description="Motor central del sistema - gestión de solicitudes, ofertas, evaluación y escalamiento",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# BRUTE FORCE CORS - Manual handling to guarantee headers
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class ForceCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            response = Response()
        else:
            try:
                response = await call_next(request)
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                response = Response(content="Internal Server Error", status_code=500)

        origin = request.headers.get("origin")
        if origin:
            # Permitir cualquier origen de teloo.cloud o localhost
            if ".teloo.cloud" in origin or "localhost" in origin or origin.endswith("teloo.cloud"):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        
        return response

app.add_middleware(ForceCORSMiddleware)

# Metrics and tracing middlewares
app.add_middleware(MetricsMiddleware)
app.add_middleware(CorrelationMiddleware)

# Proxy Headers Middleware - CRITICAL for generating correct HTTPS URLs behind Nginx/Coolify
# This fixes the "Mixed Content" issue where backend returns http:// links for pagination
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Database initialization
init_db(app)



# Include routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(solicitudes_router)
app.include_router(ofertas_router)
app.include_router(asesores_router)
app.include_router(pqr_router)
app.include_router(configuracion_router)

# Mount static files for uploads
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "TeLOO V3 Core API",
        "version": "3.0.0",
        "status": "running",
        "environment": os.getenv("ENVIRONMENT", "development")
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
    from tortoise import connections
    import redis.asyncio as aioredis
    
    health_status = {
        "status": "healthy",
        "service": "core-api",
        "version": "3.0.0",
        "timestamp": None,
        "checks": {}
    }
    
    all_healthy = True
    
    # Check database connection
    try:
        conn = connections.get("default")
        await conn.execute_query("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        all_healthy = False
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
    
    # Check Redis connection
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = aioredis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        await redis_client.close()
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
    
    # Check scheduler status
    try:
        scheduler_status = scheduler_service.get_job_status()
        health_status["checks"]["scheduler"] = {
            "status": "healthy" if scheduler_status.get("status") == "running" else "degraded",
            "message": "Scheduler operational",
            "details": scheduler_status
        }
    except Exception as e:
        health_status["checks"]["scheduler"] = {
            "status": "degraded",
            "message": f"Scheduler check failed: {str(e)}"
        }
    
    # Set overall status
    from datetime import datetime
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
    from tortoise import connections
    
    try:
        # Check database is accessible
        conn = connections.get("default")
        await conn.execute_query("SELECT 1")
        
        # Check scheduler is initialized
        scheduler_status = scheduler_service.get_job_status()
        
        return JSONResponse(
            content={
                "status": "ready",
                "service": "core-api",
                "checks": {
                    "database": "ready",
                    "scheduler": "ready" if scheduler_status.get("status") == "running" else "not_ready"
                }
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "not_ready",
                "service": "core-api",
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
        "service": "core-api",
        "version": "3.0.0"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import Response
    from utils.metrics import get_metrics, get_metrics_content_type
    
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )



@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info(
            "Starting Core API service",
            environment=environment,
            log_level=log_level
        )
        
        # Initialize database with default data
        from services.init_service import InitService
        await InitService.initialize_default_data()
        logger.info("Default data initialized")
        
        # Initialize scheduler
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        await scheduler_service.initialize(redis_url)
        await scheduler_service.start()
        logger.info("Scheduler service started successfully")
        
        logger.info("Core API service started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", error=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Shutting down Core API service")
        await scheduler_service.shutdown()
        logger.info("Scheduler service shutdown successfully")
        logger.info("Core API service shutdown complete")
    except Exception as e:
        logger.error(f"Error shutting down scheduler service: {str(e)}", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
