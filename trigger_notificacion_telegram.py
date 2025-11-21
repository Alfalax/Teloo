"""
Script para forzar notificación de cliente por Telegram
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'core-api'))

from tortoise import Tortoise
from services.notificacion_cliente_service import NotificacionClienteService
from core.redis import get_redis_client


async def main():
    # Initialize database
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_pass@localhost:5432/teloo_v3",
        modules={'models': ['models.solicitud', 'models.user', 'models.oferta']}
    )
    
    # Get Redis client
    redis_client = await get_redis_client()
    
    # Trigger notification
    solicitud_id = "120df700-47fa-493b-9167-2d23ad6660a1"
    
    print(f"🔔 Forzando notificación para solicitud {solicitud_id}...")
    
    result = await NotificacionClienteService.notificar_ofertas_ganadoras(
        solicitud_id=solicitud_id,
        redis_client=redis_client
    )
    
    print(f"\n✅ Resultado:")
    print(f"   Success: {result.get('success')}")
    print(f"   Código: {result.get('codigo_solicitud')}")
    print(f"   Teléfono: {result.get('cliente_telefono')}")
    print(f"   PDF generado: {result.get('pdf_generado')}")
    
    if result.get('error'):
        print(f"   ❌ Error: {result.get('error')}")
    
    # Close connections
    await redis_client.close()
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
