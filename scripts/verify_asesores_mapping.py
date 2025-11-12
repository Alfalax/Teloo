#!/usr/bin/env python3
"""
Script para verificar el mapeo de asesores a municipios
y corregir casos problemáticos manualmente
"""
import asyncio
import asyncpg
import os
from typing import List, Dict

async def verify_mapping():
    """Verifica el estado del mapeo de asesores a municipios"""
    
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USER', 'teloo_user'),
        password=os.getenv('DB_PASSWORD', 'teloo_password'),
        database=os.getenv('DB_NAME', 'teloo_v3')
    )
    
    try:
        print("=" * 80)
        print("VERIFICACIÓN DE MAPEO: ASESORES → MUNICIPIOS")
        print("=" * 80)
        
        # 1. Estadísticas generales
        stats = await conn.fetch("""
            SELECT 
                estado,
                COUNT(*) as total,
                COUNT(municipio_id) as mapeados,
                COUNT(*) - COUNT(municipio_id) as sin_mapear
            FROM asesores
            GROUP BY estado
            ORDER BY estado
        """)
        
        print("\n📊 ESTADÍSTICAS POR ESTADO:")
        print("-" * 80)
        for row in stats:
            print(f"  {row['estado']:15} | Total: {row['total']:4} | Mapeados: {row['mapeados']:4} | Sin mapear: {row['sin_mapear']:4}")
        
        # 2. Asesores activos sin mapear
        unmapped = await conn.fetch("""
            SELECT 
                ciudad,
                departamento,
                COUNT(*) as total_asesores,
                STRING_AGG(DISTINCT id::text, ', ') as ejemplos
            FROM asesores
            WHERE municipio_id IS NULL AND estado = 'ACTIVO'
            GROUP BY ciudad, departamento
            ORDER BY total_asesores DESC
        """)
        
        if unmapped:
            print("\n⚠️  ASESORES ACTIVOS SIN MAPEAR:")
            print("-" * 80)
            for row in unmapped:
                print(f"  {row['ciudad']:25} | {row['departamento']:20} | {row['total_asesores']:3} asesores")
                print(f"    Ejemplos: {row['ejemplos'][:100]}")
            
            # 3. Intentar encontrar coincidencias cercanas
            print("\n🔍 BUSCANDO COINCIDENCIAS CERCANAS:")
            print("-" * 80)
            for row in unmapped:
                ciudad = row['ciudad']
                matches = await conn.fetch("""
                    SELECT 
                        municipio,
                        departamento,
                        codigo_divipola,
                        similarity(municipio, $1) as sim
                    FROM municipios
                    WHERE similarity(municipio, $1) > 0.3
                    ORDER BY sim DESC
                    LIMIT 3
                """, ciudad)
                
                if matches:
                    print(f"\n  '{ciudad}' podría ser:")
                    for match in matches:
                        print(f"    - {match['municipio']:30} ({match['departamento']:20}) [Similitud: {match['sim']:.2f}]")
        else:
            print("\n✅ TODOS LOS ASESORES ACTIVOS ESTÁN MAPEADOS CORRECTAMENTE")
        
        # 4. Verificar distribución geográfica
        print("\n📍 DISTRIBUCIÓN GEOGRÁFICA (Top 10 ciudades):")
        print("-" * 80)
        distribution = await conn.fetch("""
            SELECT 
                m.municipio,
                m.departamento,
                m.hub_logistico,
                COUNT(a.id) as total_asesores
            FROM asesores a
            JOIN municipios m ON a.municipio_id = m.id
            WHERE a.estado = 'ACTIVO'
            GROUP BY m.municipio, m.departamento, m.hub_logistico
            ORDER BY total_asesores DESC
            LIMIT 10
        """)
        
        for row in distribution:
            print(f"  {row['municipio']:25} | {row['departamento']:20} | Hub: {row['hub_logistico']:15} | {row['total_asesores']:3} asesores")
        
        # 5. Verificar hubs logísticos
        print("\n🚚 DISTRIBUCIÓN POR HUB LOGÍSTICO:")
        print("-" * 80)
        hubs = await conn.fetch("""
            SELECT 
                m.hub_logistico,
                COUNT(DISTINCT a.id) as total_asesores,
                COUNT(DISTINCT m.id) as municipios_cubiertos
            FROM asesores a
            JOIN municipios m ON a.municipio_id = m.id
            WHERE a.estado = 'ACTIVO'
            GROUP BY m.hub_logistico
            ORDER BY total_asesores DESC
        """)
        
        for row in hubs:
            print(f"  {row['hub_logistico']:20} | {row['total_asesores']:3} asesores | {row['municipios_cubiertos']:3} municipios")
        
        # 6. Verificar áreas metropolitanas
        print("\n🏙️  ASESORES EN ÁREAS METROPOLITANAS:")
        print("-" * 80)
        metros = await conn.fetch("""
            SELECT 
                m.area_metropolitana,
                COUNT(DISTINCT a.id) as total_asesores,
                COUNT(DISTINCT m.id) as municipios_cubiertos
            FROM asesores a
            JOIN municipios m ON a.municipio_id = m.id
            WHERE a.estado = 'ACTIVO' 
                AND m.area_metropolitana IS NOT NULL 
                AND m.area_metropolitana != 'NO'
            GROUP BY m.area_metropolitana
            ORDER BY total_asesores DESC
        """)
        
        for row in metros:
            print(f"  {row['area_metropolitana']:30} | {row['total_asesores']:3} asesores | {row['municipios_cubiertos']:3} municipios")
        
        print("\n" + "=" * 80)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify_mapping())
