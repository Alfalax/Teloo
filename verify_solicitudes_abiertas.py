"""
Script para verificar solicitudes abiertas directamente en la BD
"""
import asyncio
import sys
from tortoise import Tortoise

async def verificar_solicitudes():
    """Verificar solicitudes abiertas en la BD"""
    
    # Conectar a la BD
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_v3",
        modules={"models": ["models"]}
    )
    
    from models.solicitud import Solicitud
    from models.enums import EstadoSolicitud
    
    print("=" * 80)
    print("VERIFICACIÓN DE SOLICITUDES ABIERTAS")
    print("=" * 80)
    print()
    
    # Contar todas las solicitudes
    total = await Solicitud.all().count()
    print(f"Total de solicitudes en BD: {total}")
    print()
    
    # Contar por estado
    print("Solicitudes por estado:")
    for estado in EstadoSolicitud:
        count = await Solicitud.filter(estado=estado).count()
        print(f"  {estado.value}: {count}")
    print()
    
    # Mostrar solicitudes abiertas
    abiertas = await Solicitud.filter(estado=EstadoSolicitud.ABIERTA).prefetch_related('cliente', 'repuestos_solicitados')
    
    if abiertas:
        print(f"SOLICITUDES ABIERTAS ({len(abiertas)}):")
        print("-" * 80)
        for sol in abiertas:
            print(f"\nID: {sol.id}")
            print(f"  Código: SOL-{str(sol.id).zfill(3)}")
            print(f"  Estado: {sol.estado.value}")
            print(f"  Cliente: {sol.cliente.nombre if sol.cliente else 'N/A'}")
            print(f"  Ciudad: {sol.ciudad_origen}")
            print(f"  Creada: {sol.created_at}")
            print(f"  Repuestos: {len(sol.repuestos_solicitados)}")
            
            if sol.repuestos_solicitados:
                for rep in sol.repuestos_solicitados:
                    print(f"    - {rep.nombre} ({rep.marca_vehiculo} {rep.linea_vehiculo} {rep.anio_vehiculo})")
    else:
        print("⚠️  NO HAY SOLICITUDES ABIERTAS")
        print()
        print("Las solicitudes creadas pueden tener un estado diferente a 'ABIERTA'")
        print("Verifica el estado de las solicitudes recién creadas.")
    
    print()
    print("=" * 80)
    
    await Tortoise.close_connections()

if __name__ == "__main__":
    try:
        asyncio.run(verificar_solicitudes())
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
