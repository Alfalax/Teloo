"""
Test script for solicitudes endpoints
Run with: python test_solicitudes_endpoints.py
"""

import asyncio
import sys
from tortoise import Tortoise
from models.solicitud import Solicitud, RepuestoSolicitado
from models.user import Usuario, Cliente
from models.enums import EstadoSolicitud, RolUsuario, EstadoUsuario
from services.solicitudes_service import SolicitudesService


async def init_db():
    """Initialize database connection"""
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_db",
        modules={"models": ["models.solicitud", "models.user", "models.geografia", "models.oferta"]}
    )
    await Tortoise.generate_schemas()


async def test_get_stats():
    """Test get_stats method"""
    print("\n=== Testing get_stats ===")
    try:
        stats = await SolicitudesService.get_stats()
        print(f"✓ Stats retrieved successfully:")
        print(f"  Total: {stats['total']}")
        print(f"  Abiertas: {stats['abiertas']}")
        print(f"  Evaluadas: {stats['evaluadas']}")
        print(f"  Aceptadas: {stats['aceptadas']}")
        print(f"  Rechazadas/Expiradas: {stats['rechazadas_expiradas']}")
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_solicitudes_paginated():
    """Test get_solicitudes_paginated method"""
    print("\n=== Testing get_solicitudes_paginated ===")
    try:
        result = await SolicitudesService.get_solicitudes_paginated(
            page=1,
            page_size=10
        )
        print(f"✓ Solicitudes retrieved successfully:")
        print(f"  Total: {result['total']}")
        print(f"  Page: {result['page']}")
        print(f"  Items: {len(result['items'])}")
        
        if result['items']:
            first = result['items'][0]
            print(f"\n  First item:")
            print(f"    ID: {first['id']}")
            print(f"    Cliente: {first['cliente_nombre']}")
            print(f"    Estado: {first['estado']}")
            print(f"    Repuestos: {first['total_repuestos']}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_create_solicitud():
    """Test create_solicitud method"""
    print("\n=== Testing create_solicitud ===")
    try:
        cliente_data = {
            "nombre": "Juan Pérez Test",
            "telefono": "+573001234567",
            "email": "juan.test@example.com"
        }
        
        repuestos_data = [
            {
                "nombre": "Filtro de aceite",
                "codigo": "FO-123",
                "descripcion": "Filtro de aceite para motor",
                "cantidad": 1,
                "marca_vehiculo": "Toyota",
                "linea_vehiculo": "Corolla",
                "anio_vehiculo": 2020,
                "observaciones": "Urgente",
                "es_urgente": True
            },
            {
                "nombre": "Pastillas de freno",
                "cantidad": 4,
                "marca_vehiculo": "Toyota",
                "linea_vehiculo": "Corolla",
                "anio_vehiculo": 2020,
                "es_urgente": False
            }
        ]
        
        solicitud = await SolicitudesService.create_solicitud(
            cliente_data=cliente_data,
            ciudad_origen="Bogotá",
            departamento_origen="Cundinamarca",
            repuestos=repuestos_data
        )
        
        print(f"✓ Solicitud created successfully:")
        print(f"  ID: {solicitud['id']}")
        print(f"  Cliente: {solicitud['cliente_nombre']}")
        print(f"  Estado: {solicitud['estado']}")
        print(f"  Total repuestos: {solicitud['total_repuestos']}")
        print(f"  Repuestos:")
        for rep in solicitud['repuestos_solicitados']:
            print(f"    - {rep['nombre']} ({rep['marca_vehiculo']} {rep['linea_vehiculo']})")
        
        return solicitud['id']
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_solicitud_by_id(solicitud_id: str):
    """Test get_solicitud_by_id method"""
    print(f"\n=== Testing get_solicitud_by_id ({solicitud_id}) ===")
    try:
        import uuid
        solicitud = await SolicitudesService.get_solicitud_by_id(uuid.UUID(solicitud_id))
        
        if solicitud:
            print(f"✓ Solicitud retrieved successfully:")
            print(f"  ID: {solicitud['id']}")
            print(f"  Cliente: {solicitud['cliente_nombre']}")
            print(f"  Teléfono: {solicitud['cliente_telefono']}")
            print(f"  Estado: {solicitud['estado']}")
            print(f"  Ciudad: {solicitud['ciudad_origen']}")
            print(f"  Total repuestos: {len(solicitud['repuestos_solicitados'])}")
            return True
        else:
            print(f"✗ Solicitud not found")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Solicitudes Service")
    print("=" * 60)
    
    try:
        await init_db()
        print("✓ Database initialized")
        
        # Run tests
        results = []
        
        # Test 1: Get stats
        results.append(await test_get_stats())
        
        # Test 2: Get paginated solicitudes
        results.append(await test_get_solicitudes_paginated())
        
        # Test 3: Create solicitud
        solicitud_id = await test_create_solicitud()
        results.append(solicitud_id is not None)
        
        # Test 4: Get solicitud by ID (if created)
        if solicitud_id:
            results.append(await test_get_solicitud_by_id(solicitud_id))
        
        # Summary
        print("\n" + "=" * 60)
        print(f"Tests completed: {sum(results)}/{len(results)} passed")
        print("=" * 60)
        
        if all(results):
            print("✓ All tests passed!")
            return 0
        else:
            print("✗ Some tests failed")
            return 1
            
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
