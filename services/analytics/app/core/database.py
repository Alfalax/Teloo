"""
Database configuration for Analytics Service
"""
import os
from tortoise import Tortoise

async def init_db():
    """Initialize database connection"""
    database_url = os.getenv("DATABASE_URL", "postgres://teloo_user:teloo_password@postgres:5432/teloo_v3")
    
    # Configuración de base de datos
    # IMPORTANTE: Analytics necesita acceso a los modelos del core-api para hacer queries
    DATABASE_CONFIG = {
        "connections": {
            "default": database_url,
        },
        "apps": {
            "models": {
                "models": [
                    # Modelos propios de Analytics
                    "app.models.events",
                    "app.models.metrics",
                    # Modelos del core-api necesarios para queries de métricas
                    # Nota: Solo se usan para lectura, no se modifican
                ],
                "default_connection": "default",
            }
        },
        "use_tz": True,
        "timezone": "America/Bogota"
    }
    
    await Tortoise.init(config=DATABASE_CONFIG)
    
    # Generate schemas solo para modelos de Analytics (safe=True no sobrescribe)
    await Tortoise.generate_schemas(safe=True)

async def close_db():
    """Close database connection"""
    try:
        await Tortoise.close_connections()
    except Exception as e:
        # If Tortoise was never initialized, this will fail
        # We can safely ignore this error during shutdown
        pass