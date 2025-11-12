#!/usr/bin/env python3
"""
Test del escalamiento usando FK municipio_id
"""
import asyncio
import sys
import os

# Agregar path del servicio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'core-api'))

from tortoise import Tortoise
from models.solicitud import Solicitud
from models.user import Asesor
from models.geografia import Municipio
from services.escalamiento_service import EscalamientoService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_escalamiento_marinilla():
    """Test específico para solicitud de MARINILLA"""
    
    # Inicializar DB
    await Tortoise.init(
        db_url=f"postgres://{os.getenv('DB_USER', 'teloo_user')}:{os.getenv('DB_PASSWORD', 'teloo_password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME', 'teloo_v3')}",
        modules={"models": ["models.user", "models.solicitud", "models.geografia", "models.oferta", "models.analytics"]}
    )
    await Tortoise.generate_schemas()
    
    try:
        print("=" * 80)
        print("TEST: ESCALAMIENTO CON FK municipio_id")
        print("=" * 80)
        
        # 1. Buscar solicitud de MARINILLA
        solicitud = await Solicitud.filter(
            ciudad_origen__icontains="MARINILLA"
        ).first()
        
        if not solicitud:
            print("❌ No se encontró solicitud de MARINILLA")
            return
        
        print(f"\n📋 Solicitud encontrada:")
        print(f"   ID: {solicitud.id}")
        print(f"   Ciudad: {solicitud.ciudad_origen}")
        print(f"   Departamento: {solicitud.departamento_origen}")
        
        # 2. Verificar municipio de la solicitud
        ciudad_norm = Municipio.normalizar_ciudad(solicitud.ciudad_origen)
        municipio_solicitud = await Municipio.get_or_none(municipio_norm=ciudad_norm)
        
        if not municipio_solicitud:
            print(f"❌ Municipio {solicitud.ciudad_origen} no encontrado en BD")
            return
        
        print(f"\n📍 Municipio solicitud:")
        print(f"   Municipio: {municipio_solicitud.municipio}")
        print(f"   Departamento: {municipio_solicitud.departamento}")
        print(f"   Hub: {municipio_solicitud.hub_logistico}")
        print(f"   Área Metro: {municipio_solicitud.area_metropolitana}")
        
        # 3. Determinar asesores elegibles
        print(f"\n🔍 Determinando asesores elegibles...")
        asesores_elegibles = await EscalamientoService.determinar_asesores_elegibles(solicitud)
        
        print(f"\n✅ Total asesores elegibles: {len(asesores_elegibles)}")
        
        # 4. Verificar distribución por criterio
        print(f"\n📊 DISTRIBUCIÓN POR CRITERIO GEOGRÁFICO:")
        print("-" * 80)
        
        # Misma ciudad
        misma_ciudad = [a for a in asesores_elegibles if a.municipio_id == municipio_solicitud.id]
        print(f"   Misma ciudad (MARINILLA): {len(misma_ciudad)} asesores")
        
        # Hub logístico
        hub_asesores = [a for a in asesores_elegibles if a.municipio.hub_logistico == municipio_solicitud.hub_logistico]
        print(f"   Hub logístico (MEDELLÍN): {len(hub_asesores)} asesores")
        
        # Áreas metropolitanas
        if municipio_solicitud.area_metropolitana and municipio_solicitud.area_metropolitana != 'NO':
            metro_asesores = [a for a in asesores_elegibles if a.municipio.area_metropolitana and a.municipio.area_metropolitana != 'NO']
            print(f"   Áreas metropolitanas: {len(metro_asesores)} asesores")
        
        # 5. Calcular puntajes para top 10
        print(f"\n🎯 TOP 10 ASESORES POR PUNTAJE:")
        print("-" * 80)
        
        asesores_con_puntaje = []
        for asesor in asesores_elegibles[:20]:  # Solo primeros 20 para velocidad
            try:
                puntaje, variables = await EscalamientoService.calcular_puntaje_asesor(asesor, solicitud)
                asesores_con_puntaje.append((asesor, puntaje, variables))
            except Exception as e:
                logger.error(f"Error calculando puntaje para asesor {asesor.id}: {e}")
        
        # Ordenar por puntaje
        asesores_con_puntaje.sort(key=lambda x: x[1], reverse=True)
        
        for i, (asesor, puntaje, variables) in enumerate(asesores_con_puntaje[:10], 1):
            print(f"\n{i}. Asesor: {asesor.usuario.nombre_completo}")
            print(f"   Ciudad: {asesor.municipio.municipio} ({asesor.municipio.departamento})")
            print(f"   Hub: {asesor.municipio.hub_logistico}")
            print(f"   Puntaje Total: {puntaje:.2f}")
            print(f"   - Proximidad: {variables['proximidad']:.2f} ({variables.get('criterio_proximidad', 'N/A')})")
            print(f"   - Actividad: {variables['actividad_reciente_5']:.2f}")
            print(f"   - Desempeño: {variables['desempeno_historico_5']:.2f}")
            print(f"   - Confianza: {variables['nivel_confianza']:.2f}")
        
        # 6. Verificar que todos los asesores tienen municipio_id
        print(f"\n🔍 VERIFICACIÓN DE INTEGRIDAD:")
        print("-" * 80)
        
        asesores_sin_municipio = await Asesor.filter(municipio_id__isnull=True).count()
        total_asesores = await Asesor.all().count()
        
        print(f"   Total asesores: {total_asesores}")
        print(f"   Asesores sin municipio_id: {asesores_sin_municipio}")
        
        if asesores_sin_municipio == 0:
            print(f"   ✅ TODOS los asesores tienen municipio_id asignado")
            print(f"   ✅ LISTO para hacer municipio_id NOT NULL")
        else:
            print(f"   ⚠️  Hay {asesores_sin_municipio} asesores sin municipio_id")
        
        print("\n" + "=" * 80)
        
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(test_escalamiento_marinilla())
