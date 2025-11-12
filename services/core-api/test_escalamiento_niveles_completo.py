#!/usr/bin/env python3
"""
Test completo del escalamiento con clasificación por niveles
Muestra los 193 asesores elegibles clasificados en 5 niveles
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'core-api'))

from tortoise import Tortoise
from models.solicitud import Solicitud
from models.user import Asesor
from models.geografia import Municipio
from services.escalamiento_service import EscalamientoService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_escalamiento_completo():
    """Test completo con clasificación por niveles"""
    
    await Tortoise.init(
        db_url=f"postgres://{os.getenv('DB_USER', 'teloo_user')}:{os.getenv('DB_PASSWORD', 'teloo_password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME', 'teloo_v3')}",
        modules={"models": ["models.user", "models.solicitud", "models.geografia", "models.oferta", "models.analytics"]}
    )
    await Tortoise.generate_schemas()
    
    try:
        print("=" * 100)
        print("TEST COMPLETO: ESCALAMIENTO CON CLASIFICACIÓN POR NIVELES")
        print("=" * 100)
        
        # 1. Buscar solicitud de MARINILLA
        solicitud = await Solicitud.filter(
            ciudad_origen__icontains="MARINILLA"
        ).first()
        
        if not solicitud:
            print("❌ No se encontró solicitud de MARINILLA")
            return
        
        print(f"\n📋 SOLICITUD:")
        print(f"   ID: {solicitud.id}")
        print(f"   Ciudad: {solicitud.ciudad_origen}, {solicitud.departamento_origen}")
        
        # 2. Determinar asesores elegibles
        print(f"\n🔍 DETERMINANDO ASESORES ELEGIBLES...")
        asesores_elegibles = await EscalamientoService.determinar_asesores_elegibles(solicitud)
        print(f"   ✅ Total asesores elegibles: {len(asesores_elegibles)}")
        
        # 3. Calcular puntajes para TODOS los asesores
        print(f"\n⚙️  CALCULANDO PUNTAJES PARA {len(asesores_elegibles)} ASESORES...")
        evaluaciones = []
        
        for i, asesor in enumerate(asesores_elegibles, 1):
            try:
                puntaje, variables = await EscalamientoService.calcular_puntaje_asesor(asesor, solicitud)
                evaluaciones.append((asesor, puntaje, variables))
                
                if i % 50 == 0:
                    print(f"   Procesados {i}/{len(asesores_elegibles)} asesores...")
                    
            except Exception as e:
                logger.error(f"Error calculando puntaje para asesor {asesor.id}: {e}")
        
        print(f"   ✅ Puntajes calculados: {len(evaluaciones)}")
        
        # 4. Clasificar por niveles
        print(f"\n📊 CLASIFICANDO POR NIVELES...")
        niveles = await EscalamientoService.clasificar_por_niveles(evaluaciones)
        
        print("\n" + "=" * 100)
        print("RESUMEN DE CLASIFICACIÓN POR NIVELES")
        print("=" * 100)
        
        total_clasificados = 0
        for nivel in range(1, 6):
            asesores_nivel = niveles[nivel]
            total_clasificados += len(asesores_nivel)
            
            if asesores_nivel:
                canal = asesores_nivel[0]['canal']
                tiempo = asesores_nivel[0]['tiempo_espera_min']
                puntajes = [float(a['puntaje_total']) for a in asesores_nivel]
                puntaje_min = min(puntajes)
                puntaje_max = max(puntajes)
                puntaje_prom = sum(puntajes) / len(puntajes)
                
                print(f"\n🎯 NIVEL {nivel}:")
                print(f"   Total asesores: {len(asesores_nivel)}")
                print(f"   Canal: {canal}")
                print(f"   Tiempo espera: {tiempo} minutos")
                print(f"   Puntaje rango: {puntaje_min:.2f} - {puntaje_max:.2f} (promedio: {puntaje_prom:.2f})")
                
                # Mostrar top 5 de este nivel
                print(f"   Top 5 asesores:")
                for i, eval_data in enumerate(asesores_nivel[:5], 1):
                    asesor = eval_data['asesor']
                    puntaje = eval_data['puntaje_total']
                    variables = eval_data['variables']
                    
                    print(f"      {i}. {asesor.usuario.nombre_completo:30} | "
                          f"{asesor.municipio.municipio:20} | "
                          f"Puntaje: {puntaje:.2f} | "
                          f"Prox: {variables['proximidad']:.1f} ({variables.get('criterio_proximidad', 'N/A')})")
            else:
                print(f"\n🎯 NIVEL {nivel}: Sin asesores")
        
        print(f"\n{'=' * 100}")
        print(f"TOTAL ASESORES CLASIFICADOS: {total_clasificados}")
        print(f"{'=' * 100}")
        
        # 5. Análisis por criterio geográfico
        print(f"\n📍 ANÁLISIS POR CRITERIO GEOGRÁFICO:")
        print("-" * 100)
        
        criterios = {}
        for asesor, puntaje, variables in evaluaciones:
            criterio = variables.get('criterio_proximidad', 'desconocido')
            if criterio not in criterios:
                criterios[criterio] = []
            criterios[criterio].append((asesor, puntaje))
        
        for criterio, asesores_criterio in sorted(criterios.items(), key=lambda x: len(x[1]), reverse=True):
            puntajes = [float(p) for _, p in asesores_criterio]
            print(f"   {criterio:25} | {len(asesores_criterio):3} asesores | "
                  f"Puntaje promedio: {sum(puntajes)/len(puntajes):.2f}")
        
        # 6. Distribución por hub
        print(f"\n🚚 DISTRIBUCIÓN POR HUB LOGÍSTICO:")
        print("-" * 100)
        
        hubs = {}
        for asesor, puntaje, variables in evaluaciones:
            hub = asesor.municipio.hub_logistico
            if hub not in hubs:
                hubs[hub] = []
            hubs[hub].append(puntaje)
        
        for hub, puntajes in sorted(hubs.items(), key=lambda x: len(x[1]), reverse=True):
            puntajes_float = [float(p) for p in puntajes]
            print(f"   {hub:20} | {len(puntajes):3} asesores | "
                  f"Puntaje promedio: {sum(puntajes_float)/len(puntajes_float):.2f}")
        
        print("\n" + "=" * 100)
        
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(test_escalamiento_completo())
