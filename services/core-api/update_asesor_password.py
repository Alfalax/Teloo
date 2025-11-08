#!/usr/bin/env python3
"""Script para actualizar contraseña de asesor"""

import asyncio
import os
from tortoise import Tortoise
from models.user import Usuario
from services.auth_service import AuthService

async def update_password():
    DATABASE_URL = os.getenv("DATABASE_URL", "postgres://teloo_user:teloo_password@localhost:5432/teloo_v3")
    
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={'models': ['models.user', 'models.solicitud', 'models.oferta', 'models.geografia', 'models.analytics']}
    )
    
    try:
        # Actualizar asesor1
        asesor = await Usuario.get(email="asesor1@teloo.com")
        new_password = "asesor123"
        asesor.password_hash = AuthService.get_password_hash(new_password)
        await asesor.save()
        
        print(f"✅ Contraseña actualizada para: asesor1@teloo.com")
        print(f"   Nueva contraseña: {new_password}")
        
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(update_password())
