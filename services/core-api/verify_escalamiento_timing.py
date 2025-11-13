import asyncio
import asyncpg
from datetime import datetime, timezone

async def verificar_escalamiento():
    """Verificar el historial de escalamiento de la solicitud problemática"""
    
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='teloo_user',
        password='teloo_password',
        database='teloo_v3'
    )
    
    solicitud_id = '2544d0dc-3f2d-46b3-a444-c9a755192ad9'
    
    # Obtener datos de la solicitud
    solicitud = await conn.fetchrow("""
        SELECT 
            id,
            nivel_actual,
            estado,
            created_at,
            updated_at,
            fecha_escalamiento,
            ofertas_minimas_deseadas
        FROM solicitudes 
        WHERE id = $1
    """, solicitud_id)
    
    print("=" * 80)
    print("ANÁLISIS DE TIEMPOS DE ESCALAMIENTO")
    print("=" * 80)
    print(f"\nSolicitud ID: {solicitud['id']}")
    print(f"Estado final: {solicitud['estado']}")
    print(f"Nivel final: {solicitud['nivel_actual']}")
    print(f"Ofertas mínimas deseadas: {solicitud['ofertas_minimas_deseadas']}")
    
    print(f"\n📅 TIMESTAMPS:")
    print(f"  Creada:              {solicitud['created_at']}")
    print(f"  Última escalamiento: {solicitud['fecha_escalamiento']}")
    print(f"  Actualizada:         {solicitud['updated_at']}")
    
    # Calcular tiempos
    tiempo_total = (solicitud['updated_at'] - solicitud['created_at']).total_seconds() / 60
    tiempo_en_ultimo_nivel = (solicitud['updated_at'] - solicitud['fecha_escalamiento']).total_seconds() / 60
    
    print(f"\n⏱️  DURACIÓN:")
    print(f"  Tiempo total: {tiempo_total:.1f} minutos")
    print(f"  Tiempo en último nivel: {tiempo_en_ultimo_nivel:.1f} minutos")
    
    # Contar ofertas
    ofertas = await conn.fetch("""
        SELECT 
            o.id,
            o.created_at,
            COUNT(DISTINCT od.repuesto_solicitado_id) as repuestos_cubiertos
        FROM ofertas o
        LEFT JOIN ofertas_detalle od ON o.id = od.oferta_id
        WHERE o.solicitud_id = $1
        GROUP BY o.id, o.created_at
        ORDER BY o.created_at
    """, solicitud_id)
    
    total_repuestos = await conn.fetchval("""
        SELECT COUNT(*) FROM repuestos_solicitados WHERE solicitud_id = $1
    """, solicitud_id)
    
    print(f"\n📊 OFERTAS RECIBIDAS: {len(ofertas)} ofertas")
    print(f"   Total repuestos solicitados: {total_repuestos}")
    
    ofertas_completas = 0
    for i, oferta in enumerate(ofertas, 1):
        es_completa = oferta['repuestos_cubiertos'] == total_repuestos
        if es_completa:
            ofertas_completas += 1
        tiempo_desde_creacion = (oferta['created_at'] - solicitud['created_at']).total_seconds() / 60
        print(f"   Oferta {i}: {oferta['repuestos_cubiertos']}/{total_repuestos} repuestos - "
              f"{'COMPLETA ✅' if es_completa else 'PARCIAL'} - "
              f"Recibida a los {tiempo_desde_creacion:.1f} min")
    
    print(f"\n   Ofertas completas (100%): {ofertas_completas}")
    print(f"   Ofertas parciales: {len(ofertas) - ofertas_completas}")
    
    # Análisis del problema
    print(f"\n🔍 ANÁLISIS:")
    print(f"   Configuración: Escalar cada 2 minutos")
    print(f"   Esperado: Nivel 1→2→3→4→5 en ~8 minutos (4 escalamientos × 2 min)")
    print(f"   Real: Se quedó {tiempo_en_ultimo_nivel:.1f} minutos en el último nivel")
    print(f"   Problema: {'❌ NO escaló correctamente' if tiempo_en_ultimo_nivel > 3 else '✅ Escaló correctamente'}")
    
    if ofertas_completas < solicitud['ofertas_minimas_deseadas']:
        print(f"\n   ⚠️  No había ofertas completas suficientes ({ofertas_completas} < {solicitud['ofertas_minimas_deseadas']})")
        print(f"   ✅ Debería haber continuado escalando")
        print(f"   ❌ Pero se quedó {tiempo_en_ultimo_nivel:.1f} minutos sin escalar")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(verificar_escalamiento())
