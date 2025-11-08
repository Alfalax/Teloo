"""
Script para verificar la última solicitud creada en la base de datos
"""
import asyncio
import sys
from tortoise import Tortoise
from datetime import datetime

async def verify_last_solicitud():
    # Conectar a la base de datos
    await Tortoise.init(
        db_url='postgres://teloo_user:teloo_password@localhost:5432/teloo_db',
        modules={'models': ['services.core-api.models.solicitud', 'services.core-api.models.user']}
    )
    
    try:
        # Importar modelos
        from services.core_api.models.solicitud import Solicitud, RepuestoSolicitado
        from services.core_api.models.user import Cliente
        
        # Obtener la última solicitud
        solicitud = await Solicitud.all().order_by('-created_at').first().prefetch_related('cliente', 'repuestos_solicitados')
        
        if not solicitud:
            print("❌ No se encontraron solicitudes en la base de datos")
            return
        
        print("=" * 80)
        print("✅ ÚLTIMA SOLICITUD CREADA")
        print("=" * 80)
        print(f"\n📋 INFORMACIÓN GENERAL:")
        print(f"   ID: {solicitud.id}")
        print(f"   Estado: {solicitud.estado}")
        print(f"   Nivel Actual: {solicitud.nivel_actual}")
        print(f"   Creada: {solicitud.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Actualizada: {solicitud.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n👤 INFORMACIÓN DEL CLIENTE:")
        if solicitud.cliente:
            print(f"   Nombre: {solicitud.cliente.nombre}")
            print(f"   Teléfono: {solicitud.cliente.telefono}")
            print(f"   Email: {solicitud.cliente.email or 'N/A'}")
        else:
            print(f"   Cliente ID: {solicitud.cliente_id}")
        
        print(f"\n📍 UBICACIÓN:")
        print(f"   Ciudad: {solicitud.ciudad_origen}")
        print(f"   Departamento: {solicitud.departamento_origen}")
        
        print(f"\n🔧 REPUESTOS SOLICITADOS ({len(solicitud.repuestos_solicitados)}):")
        for i, repuesto in enumerate(solicitud.repuestos_solicitados, 1):
            print(f"\n   {i}. {repuesto.nombre}")
            print(f"      - Código: {repuesto.codigo or 'N/A'}")
            print(f"      - Cantidad: {repuesto.cantidad}")
            print(f"      - Vehículo: {repuesto.marca_vehiculo} {repuesto.linea_vehiculo or ''} ({repuesto.anio_vehiculo})")
            if repuesto.descripcion:
                print(f"      - Descripción: {repuesto.descripcion}")
            if repuesto.observaciones:
                print(f"      - Observaciones: {repuesto.observaciones}")
            if repuesto.es_urgente:
                print(f"      - ⚠️  URGENTE")
        
        if solicitud.metadata_json:
            print(f"\n📊 METADATA:")
            for key, value in solicitud.metadata_json.items():
                print(f"   {key}: {value}")
        
        print("\n" + "=" * 80)
        print("✅ Verificación completada exitosamente")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error al verificar la solicitud: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(verify_last_solicitud())
