"""
Script para probar el fix del bug de escalamiento
"""
import asyncio
from tortoise import Tortoise
from datetime import datetime, timezone, timedelta

async def test_fix():
    # Conectar a la base de datos
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_v3",
        modules={"models": ["services.core-api.models.solicitud", "services.core-api.models.oferta", "services.core-api.models.user"]}
    )
    
    from models.solicitud import Solicitud
    from models.oferta import Oferta
    from models.enums import EstadoSolicitud
    
    print("\n" + "="*80)
    print("🧪 TEST: Verificando fix del bug de escalamiento")
    print("="*80 + "\n")
    
    # Buscar solicitudes en nivel 4 con ofertas incompletas
    solicitudes_nivel_4 = await Solicitud.filter(
        estado=EstadoSolicitud.ABIERTA,
        nivel_actual=4
    ).all()
    
    print(f"📊 Solicitudes en nivel 4: {len(solicitudes_nivel_4)}")
    
    for solicitud in solicitudes_nivel_4:
        ofertas = await Oferta.filter(solicitud_id=solicitud.id).all()
        
        # Contar ofertas completas
        ofertas_completas = 0
        for oferta in ofertas:
            await oferta.fetch_related('detalles')
            repuestos_solicitados = await solicitud.repuestos.all()
            total_repuestos = len(repuestos_solicitados)
            repuestos_cubiertos = len(set([detalle.repuesto_solicitado_id for detalle in oferta.detalles]))
            if repuestos_cubiertos == total_repuestos:
                ofertas_completas += 1
        
        print(f"\n📋 Solicitud: {str(solicitud.id)[:8]}...")
        print(f"   Nivel actual: {solicitud.nivel_actual}")
        print(f"   Ofertas totales: {len(ofertas)}")
        print(f"   Ofertas completas: {ofertas_completas}")
        print(f"   Ofertas mínimas deseadas: {solicitud.ofertas_minimas_deseadas}")
        print(f"   Tiempo desde escalamiento: {(datetime.now(timezone.utc) - solicitud.fecha_escalamiento).total_seconds() / 60:.1f} minutos")
        
        # Verificar qué debería pasar con el nuevo código
        if ofertas_completas >= solicitud.ofertas_minimas_deseadas:
            print(f"   ✅ DEBERÍA: Evaluar (tiene ofertas completas suficientes)")
        else:
            print(f"   ✅ DEBERÍA: Escalar a nivel 5 (ofertas insuficientes)")
    
    print("\n" + "="*80)
    print("✅ Test completado")
    print("="*80 + "\n")
    
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(test_fix())
