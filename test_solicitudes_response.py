import asyncio
import sys
sys.path.insert(0, 'services/core-api')

from services.solicitudes_service import SolicitudesService
from models.enums import EstadoSolicitud

async def test():
    # Get asesor ID from database
    from models.user import Asesor
    asesor = await Asesor.all().first()
    
    if not asesor:
        print("No asesor found")
        return
    
    print(f"Testing with asesor_id: {asesor.id}")
    
    # Get solicitudes
    result = await SolicitudesService.get_solicitudes_paginated(
        page=1,
        page_size=10,
        estado=EstadoSolicitud.ABIERTA,
        user_rol="ASESOR",
        asesor_id=asesor.id
    )
    
    print(f"\nTotal solicitudes: {result['total']}")
    
    if result['items']:
        first = result['items'][0]
        print(f"\nPrimera solicitud:")
        print(f"  ID: {first['id']}")
        print(f"  Estado: {first['estado']}")
        print(f"  Mi oferta: {first.get('mi_oferta')}")
        
        if first.get('mi_oferta'):
            print(f"    - Oferta ID: {first['mi_oferta']['id']}")
            print(f"    - Monto: {sum(d['precio_unitario'] * d['cantidad'] for d in first['mi_oferta']['detalles'])}")
            print(f"    - Detalles: {len(first['mi_oferta']['detalles'])}")

if __name__ == "__main__":
    from tortoise import Tortoise
    
    async def run():
        await Tortoise.init(
            db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_v3",
            modules={"models": ["models.user", "models.solicitud", "models.oferta", "models.geografia", "models.analytics"]}
        )
        await test()
        await Tortoise.close_connections()
    
    asyncio.run(run())
