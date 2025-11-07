#!/usr/bin/env python3
"""
Script para probar la autenticación
"""

import asyncio
import sys
import os
sys.path.append('services/core-api')

from tortoise import Tortoise
from models.user import Usuario
from services.auth_service import AuthService

async def test_login():
    DATABASE_URL = "postgres://teloo_user:teloo_password@localhost:5432/teloo_v3"
    
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={'models': [
            'models.user', 
            'models.solicitud', 
            'models.oferta', 
            'models.geografia', 
            'models.analytics'
        ]}
    )
    
    try:
        # Buscar usuario
        user = await Usuario.get_or_none(email="admin@teloo.com")
        if not user:
            print("❌ Usuario no encontrado")
            return
            
        print(f"✅ Usuario encontrado: {user.email}")
        print(f"   Nombre: {user.nombre} {user.apellido}")
        print(f"   Rol: {user.rol}")
        print(f"   Estado: {user.estado}")
        print(f"   Hash: {user.password_hash[:50]}...")
        
        # Probar verificación de contraseña
        password = "admin123"
        is_valid = AuthService.verify_password(password, user.password_hash)
        print(f"   Verificación de '{password}': {'✅ VÁLIDA' if is_valid else '❌ INVÁLIDA'}")
        
        # Probar autenticación completa
        auth_user = await AuthService.authenticate_user("admin@teloo.com", password)
        if auth_user:
            print("✅ Autenticación completa: EXITOSA")
        else:
            print("❌ Autenticación completa: FALLIDA")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(test_login())