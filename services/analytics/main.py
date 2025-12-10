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
    """
    Health check endpoint with dependency checks
    Returns 200 if all critical dependencies are healthy
    Returns 503 if any critical dependency is unhealthy
    """
    from fastapi import status
    from fastapi.responses import JSONResponse
    from datetime import datetime
    from tortoise import connections
    
    health_status = {
        "status": "healthy",
        "service": "analytics",
        "version": "3.0.0",
        "timestamp": None,
        "checks": {}
    }
    
    all_healthy = True
    
    # Check database connection (read replica)
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
    
    # Check event collector
    try:
        collector_running = event_collector.running
        health_status["checks"]["event_collector"] = {
            "status": "healthy" if collector_running else "degraded",
            "message": "Event collector running" if collector_running else "Event collector stopped"
        }
    except Exception as e:
        health_status["checks"]["event_collector"] = {
            "status": "degraded",
            "message": f"Event collector check failed: {str(e)}"
        }
    
    # Check scheduler
    try:
        scheduler_status = analytics_scheduler.get_job_status()
        health_status["checks"]["scheduler"] = {
            "status": "healthy" if scheduler_status.get('status') == 'running' else "degraded",
            "message": "Scheduler operational",
            "details": scheduler_status
        }
    except Exception as e:
        health_status["checks"]["scheduler"] = {
            "status": "degraded",
            "message": f"Scheduler check failed: {str(e)}"
        }
    
    # Check alert system
    try:
        from app.models.metrics import AlertaMetrica
        active_alerts_count = await AlertaMetrica.filter(activa=True).count()
        health_status["checks"]["alert_system"] = {
            "status": "healthy",
            "message": f"Alert system operational with {active_alerts_count} active alerts",
            "active_alerts": active_alerts_count
        }
    except Exception as e:
        health_status["checks"]["alert_system"] = {
            "status": "degraded",
            "message": f"Alert system check failed: {str(e)}"
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
    from tortoise import connections
    
    try:
        # Check database is accessible
        conn = connections.get("default")
        await conn.execute_query("SELECT 1")
        
        # Check Redis is accessible
        if redis_manager.redis_client:
            await redis_manager.redis_client.ping()
        else:
            raise Exception("Redis client not initialized")
        
        # Check event collector is running
        if not event_collector.running:
            raise Exception("Event collector not running")
        
        return JSONResponse(
            content={
                "status": "ready",
                "service": "analytics",
                "checks": {
                    "database": "ready",
                    "redis": "ready",
                    "event_collector": "ready"
                }
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "not_ready",
                "service": "analytics",
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
        "service": "analytics",
        "version": "3.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )