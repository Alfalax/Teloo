#!/usr/bin/env python3
"""
Script definitivo para crear usuario administrador
"""

import asyncio
import os
import bcrypt
from tortoise import Tortoise

async def create_admin_user():
    # Configurar conexión a la base de datos
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
        # Importar modelos
        from models.user import Usuario
        from models.enums import RolUsuario, EstadoUsuario
        
        # Eliminar usuario existente si existe
        existing = await Usuario.filter(email="admin@teloo.com").first()
        if existing:
            await existing.delete()
            print("Usuario existente eliminado")
        
        # Crear hash de contraseña
        password = "admin123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Crear usuario admin
        admin_user = await Usuario.create(
            email="admin@teloo.com",
            password_hash=password_hash,
            nombre="Administrador",
            apellido="TeLOO",
            telefono="+573001234567",
            rol=RolUsuario.ADMIN,
            estado=EstadoUsuario.ACTIVO
        )
        
        print(f"✅ Usuario administrador creado exitosamente!")
        print(f"   Email: {admin_user.email}")
        print(f"   ID: {admin_user.id}")
        print(f"   Rol: {admin_user.rol}")
        print(f"   Estado: {admin_user.estado}")
        print(f"   Contraseña: {password}")
        
        # Verificar que la contraseña funciona
        verification = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        print(f"   Verificación de contraseña: {'✅ OK' if verification else '❌ FALLO'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(create_admin_user())