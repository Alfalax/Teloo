#!/usr/bin/env python3
"""
Script para probar la autenticación del usuario admin
"""

import asyncio
import os
import sys
sys.path.append('services/core-api')

from tortoise import Tortoise
from models.user import Usuario
from services.auth_service import AuthService

async def test_auth():
    # Configurar base de datos
    DATABASE_URL = "postgres://teloo_user:teloo_password@localhost:5432/teloo_v3"
    
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={'models': ['models.user', 'models.solicitud', 'models.oferta', 'models.geografia', 'models.analytics']}
    )
    
    try:
        # Buscar usuario admin
        admin_user = await Usuario.get_or_none(email="admin@teloo.com")
        
        if admin_user:
            print(f"Usuario encontrado: {admin_user.email}")
            print(f"Nombre: {admin_user.nombre} {admin_user.apellido}")
            print(f"Rol: {admin_user.rol}")
            print(f"Estado: {admin_user.estado}")
            print(f"Hash de contraseña: {admin_user.password_hash[:20]}...")
            
            # Probar autenticación
            authenticated_user = await AuthService.authenticate_user("admin@teloo.com", "admin123")
            
            if authenticated_user:
                print("✅ Autenticación exitosa!")
            else:
                print("❌ Autenticación fallida")
                
        else:
            print("❌ Usuario admin no encontrado")
            
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(test_auth())