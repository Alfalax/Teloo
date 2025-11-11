"""
Script para verificar que las 3 reglas geográficas del escalamiento funcionan correctamente
"""
import asyncio
import sys
sys.path.insert(0, 'services/core-api')

from tortoise import Tortoise
from models.geografia import Municipio
from models.user import Asesor
from models.enums import EstadoAsesor, EstadoUsuario


async def test_reglas_geograficas():
    # Conectar a la base de datos
    await Tortoise.init(
        db_url='postgres://teloo_user:teloo_password@localhost:5432/teloo_v3',
        modules={'models': ['models.user', 'models.geografia', 'models.solicitud', 'models.oferta', 'models.analytics']}
    )
    
    # Ciudad de prueba: COPACABANA, ANTIOQUIA
    ciudad_solicitud = "COPACABANA"
    departamento_solicitud = "ANTIOQUIA"
    
    print(f"\n{'='*80}")
    print(f"VERIFICACIÓN DE REGLAS GEOGRÁFICAS PARA: {ciudad_solicitud}, {departamento_solicitud}")
    print(f"{'='*80}\n")
    
    # Normalizar
    ciudad_norm = Municipio.normalizar_ciudad(ciudad_solicitud)
    departamento_norm = Municipio.normalizar_ciudad(departamento_solicitud)
    
    print(f"Ciudad normalizada: {ciudad_norm}")
    print(f"Departamento normalizado: {departamento_norm}\n")
    
    # Obtener municipio
    municipio = await Municipio.get_or_none(
        municipio_norm=ciudad_norm,
        departamento=departamento_norm
    )
    
    if not municipio:
        print(f"❌ ERROR: Municipio no encontrado")
        return
    
    print(f"✅ Municipio encontrado:")
    print(f"   - Área metropolitana: {municipio.area_metropolitana}")
    print(f"   - Hub logístico: {municipio.hub_logistico}\n")
    
    # Obtener todos los asesores activos
    todos_asesores = await Asesor.filter(
        estado=EstadoAsesor.ACTIVO,
        usuario__estado=EstadoUsuario.ACTIVO
    ).prefetch_related('usuario').all()
    
    print(f"Total asesores activos en BD: {len(todos_asesores)}\n")
    
    # REGLA 1: Misma ciudad
    print(f"{'='*80}")
    print(f"REGLA 1: ASESORES DE LA MISMA CIUDAD ({ciudad_norm})")
    print(f"{'='*80}")
    
    asesores_misma_ciudad = []
    for asesor in todos_asesores:
        if Municipio.normalizar_ciudad(asesor.ciudad) == ciudad_norm:
            asesores_misma_ciudad.append(asesor)
            print(f"  ✓ {asesor.usuario.email} - {asesor.ciudad}")
    
    print(f"\nTotal: {len(asesores_misma_ciudad)} asesores\n")
    
    # REGLA 2: Áreas metropolitanas nacionales
    print(f"{'='*80}")
    print(f"REGLA 2: ASESORES DE ÁREAS METROPOLITANAS NACIONALES")
    print(f"{'='*80}")
    
    if municipio.area_metropolitana and municipio.area_metropolitana != 'NO':
        # Obtener todos los municipios en áreas metropolitanas (excluyendo 'NO')
        municipios_am = await Municipio.filter(
            area_metropolitana__isnull=False,
            area_metropolitana__not='NO'
        ).values_list('municipio_norm', flat=True)
        
        municipios_am_set = set(municipios_am)
        print(f"Total municipios en áreas metropolitanas: {len(municipios_am_set)}")
        print(f"Primeros 10: {list(municipios_am_set)[:10]}\n")
        
        asesores_am = []
        ciudades_am = set()
        for asesor in todos_asesores:
            ciudad_asesor_norm = Municipio.normalizar_ciudad(asesor.ciudad)
            if ciudad_asesor_norm in municipios_am_set:
                asesores_am.append(asesor)
                ciudades_am.add(asesor.ciudad)
        
        print(f"Ciudades con asesores en áreas metropolitanas:")
        for ciudad in sorted(ciudades_am):
            count = sum(1 for a in asesores_am if a.ciudad == ciudad)
            print(f"  - {ciudad}: {count} asesores")
        
        print(f"\nTotal: {len(asesores_am)} asesores\n")
    else:
        print(f"❌ El municipio NO está en área metropolitana\n")
        asesores_am = []
    
    # REGLA 3: Hub logístico
    print(f"{'='*80}")
    print(f"REGLA 3: ASESORES DEL HUB LOGÍSTICO ({municipio.hub_logistico})")
    print(f"{'='*80}")
    
    municipios_hub = await Municipio.filter(
        hub_logistico=municipio.hub_logistico
    ).values_list('municipio_norm', flat=True)
    
    municipios_hub_set = set(municipios_hub)
    print(f"Total municipios en hub {municipio.hub_logistico}: {len(municipios_hub_set)}")
    print(f"Primeros 10: {list(municipios_hub_set)[:10]}\n")
    
    asesores_hub = []
    ciudades_hub = set()
    for asesor in todos_asesores:
        ciudad_asesor_norm = Municipio.normalizar_ciudad(asesor.ciudad)
        if ciudad_asesor_norm in municipios_hub_set:
            asesores_hub.append(asesor)
            ciudades_hub.add(asesor.ciudad)
    
    print(f"Ciudades con asesores en hub {municipio.hub_logistico}:")
    for ciudad in sorted(ciudades_hub):
        count = sum(1 for a in asesores_hub if a.ciudad == ciudad)
        print(f"  - {ciudad}: {count} asesores")
    
    print(f"\nTotal: {len(asesores_hub)} asesores\n")
    
    # RESUMEN FINAL
    print(f"{'='*80}")
    print(f"RESUMEN FINAL (SIN DUPLICADOS)")
    print(f"{'='*80}")
    
    asesores_elegibles = set()
    for asesor in asesores_misma_ciudad:
        asesores_elegibles.add(asesor.id)
    for asesor in asesores_am:
        asesores_elegibles.add(asesor.id)
    for asesor in asesores_hub:
        asesores_elegibles.add(asesor.id)
    
    print(f"Total asesores elegibles (sin duplicados): {len(asesores_elegibles)}")
    print(f"Reducción: {len(todos_asesores)} → {len(asesores_elegibles)} ({100 * len(asesores_elegibles) / len(todos_asesores):.1f}%)\n")
    
    # Verificar si Villavicencio está incluido
    print(f"{'='*80}")
    print(f"VERIFICACIÓN: ¿Hay asesores de Villavicencio?")
    print(f"{'='*80}")
    
    asesores_finales = await Asesor.filter(
        id__in=list(asesores_elegibles)
    ).prefetch_related('usuario').all()
    
    asesores_villavicencio = [a for a in asesores_finales if 'VILLAVICENCIO' in a.ciudad.upper()]
    
    if asesores_villavicencio:
        print(f"❌ ERROR: Se encontraron {len(asesores_villavicencio)} asesores de Villavicencio")
        for asesor in asesores_villavicencio[:5]:
            print(f"   - {asesor.usuario.email} - {asesor.ciudad}")
    else:
        print(f"✅ CORRECTO: No hay asesores de Villavicencio")
    
    print()
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(test_reglas_geograficas())
