
import asyncio
import os
import logging
from tortoise import Tortoise
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug_script")

async def test_create_user():
    print("--- INICIANDO TEST DE CREACION DE USUARIO ---")
    load_dotenv()
    
    # Obtener URL de BD
    db_url = os.getenv("DATABASE_URL")
    print(f"Conectando a BD: {db_url.split('@')[1] if '@' in db_url else '***'}")

    try:
        # Inicializar Tortoise
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["models.user", "models.solicitud", "models.oferta", "models.geografia"]}
        )
        print("Tortoise inicializado.")
        
        # Importar modelos
        from models.user import Usuario
        from models.enums import RolUsuario, EstadoUsuario
        from services.auth_service import AuthService
        
        print("Modelos importados.")
        
        # Datos de prueba
        email = "test_crash_debug@example.com"
        password = "Teloo2026."
        
        # Hashear password
        print("Intentando hashear password...")
        password_hash = AuthService.get_password_hash(password)
        print(f"Hash generado: {password_hash[:10]}...")
        
        # Crear usuario
        print("Intentando crear usuario en BD...")
        usuario = await Usuario.create(
            email=email,
            password_hash=password_hash,
            nombre="Test",
            apellido="Crash",
            telefono="+573001234567",
            rol=RolUsuario.CLIENT,
            estado=EstadoUsuario.ACTIVO
        )
        print(f"Usuario creado EXITOSAMENTE con ID: {usuario.id}")
        
    except Exception as e:
        print(f"\n!!! CRASH CAPTURADO !!!\nError: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("Cerrando conexiones...")
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(test_create_user())
