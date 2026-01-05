"""
Database configuration for Analytics Service
"""
import os
from tortoise import Tortoise

async def init_db():
    """Initialize database connection"""
    database_url = os.getenv("DATABASE_URL", "postgres://teloo_user:teloo_password@postgres:5432/teloo_v3")
    
    # Configuración de base de datos
    # IMPORTANTE: Analytics usa las tablas existentes creadas por Core API
    # NO crea sus propias tablas, solo se conecta para hacer queries
    DATABASE_CONFIG = {
        "connections": {
            "default": database_url,
        },
        "apps": {
            "models": {
                "models": [
                    # Analytics usa las tablas existentes de Core API
                    # No define modelos propios para evitar conflictos de esquema
                ],
                "default_connection": "default",
            }
        },
        "use_tz": True,
        "timezone": "America/Bogota"
    }
    
    await Tortoise.init(config=DATABASE_CONFIG)
    
    # NO generar schemas - usar tablas existentes de Core API
    # await Tortoise.generate_schemas(safe=True)

async def close_db():
    """Close database connection"""
    try:
        await Tortoise.close_connections()
    except Exception as e:
        # If Tortoise was never initialized, this will fail
        # We can safely ignore this error during shutdown
        pass