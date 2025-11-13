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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create FastAPI app
app = FastAPI(
    title="TeLOO V3 Core API",
    description="Motor central del sistema - gestión de solicitudes, ofertas, evaluación y escalamiento",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

# Initialize database
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
    """Health check endpoint"""
    scheduler_status = scheduler_service.get_job_status()
    return {
        "status": "healthy",
        "service": "core-api",
        "version": "3.0.0",
        "scheduler": scheduler_status
    }



@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize database with default data
        from services.init_service import InitService
        await InitService.initialize_default_data()
        
        # Initialize scheduler
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        await scheduler_service.initialize(redis_url)
        await scheduler_service.start()
        logging.info("Scheduler service started successfully")
    except Exception as e:
        logging.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await scheduler_service.shutdown()
        logging.info("Scheduler service shutdown successfully")
    except Exception as e:
        logging.error(f"Error shutting down scheduler service: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )