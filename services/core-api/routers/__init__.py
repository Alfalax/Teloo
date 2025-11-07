"""
TeLOO V3 Core API Routers
API endpoints and route handlers
"""

from .admin import router as admin_router

__all__ = [
    "admin_router",
]