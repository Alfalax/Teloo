"""
TeLOO V3 Files Service
Gestión de archivos Excel con validación, antivirus y almacenamiento en MinIO
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.minio_client import minio_client
from app.antivirus import antivirus_scanner
from app.routers import files

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
    logger.info("Starting Files Service...")
    
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # Connect to MinIO
        minio_client.connect()
        
        # Connect to ClamAV (if enabled)
        antivirus_scanner.connect()
        
        logger.info("Files Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start service: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Files Service...")
    logger.info("Files Service shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="TeLOO V3 Files Service",
    description="Gestión de archivos Excel con validación, antivirus y almacenamiento en MinIO",
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

# Include routers
app.include_router(files.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "TeLOO V3 Files Service",
        "version": "3.0.0",
        "status": "running",
        "environment": settings.environment,
        "features": {
            "max_file_size_mb": settings.max_file_size_mb,
            "allowed_extensions": settings.allowed_extensions_list,
            "antivirus_enabled": settings.clamav_enabled
        }
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
        "service": "files",
        "version": "3.0.0",
        "timestamp": None,
        "checks": {}
    }
    
    all_healthy = True
    
    # Check MinIO connection
    try:
        if minio_client.client:
            # Try to list buckets to verify connection
            buckets = minio_client.client.list_buckets()
            health_status["checks"]["minio"] = {
                "status": "healthy",
                "message": f"MinIO connection successful ({len(buckets)} buckets)"
            }
        else:
            all_healthy = False
            health_status["checks"]["minio"] = {
                "status": "unhealthy",
                "message": "MinIO client not initialized"
            }
    except Exception as e:
        all_healthy = False
        health_status["checks"]["minio"] = {
            "status": "unhealthy",
            "message": f"MinIO connection failed: {str(e)}"
        }
    
    # Check ClamAV status (if enabled)
    if settings.clamav_enabled:
        try:
            clamav_version = antivirus_scanner.get_version()
            if clamav_version:
                health_status["checks"]["clamav"] = {
                    "status": "healthy",
                    "message": f"ClamAV operational (version: {clamav_version})"
                }
            else:
                health_status["checks"]["clamav"] = {
                    "status": "degraded",
                    "message": "ClamAV not responding"
                }
        except Exception as e:
            health_status["checks"]["clamav"] = {
                "status": "degraded",
                "message": f"ClamAV check failed: {str(e)}"
            }
    else:
        health_status["checks"]["clamav"] = {
            "status": "disabled",
            "message": "ClamAV antivirus scanning is disabled"
        }
    
    # Check upload directory
    try:
        if os.path.exists(settings.upload_dir) and os.access(settings.upload_dir, os.W_OK):
            health_status["checks"]["upload_dir"] = {
                "status": "healthy",
                "message": f"Upload directory accessible: {settings.upload_dir}"
            }
        else:
            health_status["checks"]["upload_dir"] = {
                "status": "degraded",
                "message": f"Upload directory not writable: {settings.upload_dir}"
            }
    except Exception as e:
        health_status["checks"]["upload_dir"] = {
            "status": "degraded",
            "message": f"Upload directory check failed: {str(e)}"
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
        # Check MinIO is accessible
        if not minio_client.client:
            raise Exception("MinIO client not initialized")
        
        # Try to list buckets
        minio_client.client.list_buckets()
        
        # Check upload directory is writable
        if not os.access(settings.upload_dir, os.W_OK):
            raise Exception("Upload directory not writable")
        
        return JSONResponse(
            content={
                "status": "ready",
                "service": "files",
                "checks": {
                    "minio": "ready",
                    "upload_dir": "ready"
                }
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "not_ready",
                "service": "files",
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
        "service": "files",
        "version": "3.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True if settings.environment == "development" else False,
        log_level=settings.log_level.lower()
    )