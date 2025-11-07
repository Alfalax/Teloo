"""
Database configuration for TeLOO V3 Core API
"""

from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI
import os


# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://teloo_user:teloo_password@localhost:5432/teloo_v3")
# Convert postgresql:// to postgres:// for Tortoise ORM compatibility
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgres://", 1)

TORTOISE_ORM = {
    "connections": {
        "default": DATABASE_URL
    },
    "apps": {
        "models": {
            "models": [
                "models.user",
                "models.solicitud", 
                "models.oferta",
                "models.geografia",
                "models.analytics"
            ],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "America/Bogota"
}


def init_db(app: FastAPI):
    """Initialize database with FastAPI app"""
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    )


async def init_db_standalone():
    """Initialize database for standalone usage"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db():
    """Close database connections"""
    await Tortoise.close_connections()