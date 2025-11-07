"""
TeLOO V3 Analytics Service
Métricas, dashboards y reportes del sistema con 34 KPIs
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import components
from app.core.database import init_db, close_db
from app.core.redis import redis_manager
from app.services.event_collector import event_collector
from app.services.scheduler import analytics_scheduler
from app.services.mv_scheduler import mv_scheduler
from app.routers import dashboards, materialized_views, alerts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("Iniciando Analytics Service...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Base de datos inicializada")
        
        # Connect to Redis
        await redis_manager.connect()
        logger.info("Redis conectado")
        
        # Start event collector in background
        asyncio.create_task(event_collector.start())
        logger.info("Event Collector iniciado")
        
        # Initialize and start scheduler for batch jobs
        await analytics_scheduler.initialize()
        await analytics_scheduler.start()
        logger.info("Analytics Scheduler iniciado")
        
        # Start materialized views scheduler
        await mv_scheduler.start()
        logger.info("Materialized Views Scheduler iniciado")
        
        # Initialize alert manager with default alerts
        from app.services.alert_manager import alert_manager
        await alert_manager.initialize_default_alerts()
        logger.info("Alert Manager inicializado con alertas por defecto")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Cerrando Analytics Service...")
        
        # Stop event collector
        await event_collector.stop()
        
        # Stop scheduler
        await analytics_scheduler.shutdown()
        
        # Stop materialized views scheduler
        await mv_scheduler.stop()
        
        # Close connections
        await redis_manager.disconnect()
        await close_db()
        
        logger.info("Analytics Service cerrado")

# Create FastAPI app
app = FastAPI(
    title="TeLOO V3 Analytics",
    description="Métricas, dashboards y reportes del sistema con 34 KPIs",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(dashboards.router)
app.include_router(materialized_views.router)
app.include_router(alerts.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "TeLOO V3 Analytics",
        "version": "3.0.0",
        "status": "running",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": [
            "Event Collection (Redis pub/sub)",
            "Real-time Metrics Calculation", 
            "Dashboard Generation",
            "KPI Caching",
            "Alert System with Email/Slack Notifications",
            "Configurable Alert Thresholds",
            "Automatic Alert Monitoring (every 5 minutes)",
            "Alert History and Audit Trail",
            "Batch Jobs for Complex Metrics",
            "Scheduled Analytics Processing",
            "Materialized Views for Historical KPIs",
            "Automatic Daily Refresh (1 AM)"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Basic health check
        components = {
            "database": "unknown",
            "redis": "unknown",
            "event_collector": "unknown",
            "scheduler": "unknown",
            "alert_system": "unknown"
        }
        
        # Check database connection
        try:
            from tortoise import connections
            conn = connections.get("default")
            if conn:
                components["database"] = "connected"
        except:
            components["database"] = "disconnected"
        
        # Check Redis connection
        try:
            components["redis"] = "connected" if redis_manager.redis_client else "disconnected"
        except:
            components["redis"] = "disconnected"
        
        # Check event collector
        try:
            components["event_collector"] = "running" if event_collector.running else "stopped"
        except:
            components["event_collector"] = "error"
        
        # Check scheduler
        try:
            scheduler_status = analytics_scheduler.get_job_status()
            components["scheduler"] = scheduler_status.get('status', 'unknown')
        except:
            components["scheduler"] = "error"
        
        # Check alert system
        try:
            from app.models.metrics import AlertaMetrica
            active_alerts_count = await AlertaMetrica.filter(activa=True).count()
            components["alert_system"] = f"active ({active_alerts_count} alerts)"
        except:
            components["alert_system"] = "error"
        
        return {
            "status": "healthy",
            "service": "analytics",
            "version": "3.0.0",
            "components": components
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "analytics",
            "version": "3.0.0",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )