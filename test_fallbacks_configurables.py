#!/usr/bin/env python3
"""
Script de prueba para verificar fallbacks configurables
"""

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'core-api'))

from tortoise import Tortoise
from models.analytics import ParametroConfig
from services.escalamiento_service import EscalamientoService
from decimal import Decimal


async def init_db():
    """Initialize database connection"""
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_v3",
        modules={"models": ["models.user", "models.geografia", "models.solicitud", "models.oferta", "models.analytics"]}
    )


async def test_fallbacks():
    """Test fallbacks configurables"""
    print("🧪 Probando fallbacks configurables...\n")
    
    try:
        await init_db()
        
        # 1. Verificar que los parámetros existen en BD
        print("📊 Verificando parámetros en BD:")
        
        fallback_actividad = await ParametroConfig.get_valor('fallback_actividad_asesores_nuevos')
        fallback_desempeno = await ParametroConfig.get_valor('fallback_desempeno_asesores_nuevos')
        
        print(f"   • fallback_actividad_asesores_nuevos: {fallback_actividad}")
        print(f"   • fallback_desempeno_asesores_nuevos: {fallback_desempeno}")
        
        if fallback_actividad is None or fallback_desempeno is None:
            print("\n❌ ERROR: Parámetros no encontrados en BD")
            print("   Ejecuta: Get-Content scripts/add_puntaje_defecto_param.sql | docker exec -i teloo-postgres psql -U teloo_user -d teloo_v3")
            return
        
        # 2. Probar función aplicar_fallbacks_metricas
        print(f"\n🔧 Probando función aplicar_fallbacks_metricas:")
        
        fallbacks = await EscalamientoService.aplicar_fallbacks_metricas("test-asesor-id")
        
        print(f"   • actividad_reciente: {fallbacks['actividad_reciente']}")
        print(f"   • desempeno_historico: {fallbacks['desempeno_historico']}")
        print(f"   • nivel_confianza: {fallbacks['nivel_confianza']}")
        
        # 3. Verificar que los valores son correctos
        print(f"\n✅ Verificación:")
        
        expected_actividad = Decimal(str(fallback_actividad))
        expected_desempeno = Decimal(str(fallback_desempeno))
        
        if fallbacks['actividad_reciente'] == expected_actividad:
            print(f"   ✓ Actividad correcta: {expected_actividad}")
        else:
            print(f"   ✗ Actividad incorrecta. Esperado: {expected_actividad}, Obtenido: {fallbacks['actividad_reciente']}")
        
        if fallbacks['desempeno_historico'] == expected_desempeno:
            print(f"   ✓ Desempeño correcto: {expected_desempeno}")
        else:
            print(f"   ✗ Desempeño incorrecto. Esperado: {expected_desempeno}, Obtenido: {fallbacks['desempeno_historico']}")
        
        if fallbacks['nivel_confianza'] == Decimal('3.0'):
            print(f"   ✓ Confianza correcta: 3.0")
        else:
            print(f"   ✗ Confianza incorrecta. Esperado: 3.0, Obtenido: {fallbacks['nivel_confianza']}")
        
        # 4. Probar cambio de valores
        print(f"\n🔄 Probando cambio de valores:")
        
        print(f"   Cambiando fallback_actividad a 4.0...")
        await ParametroConfig.filter(clave='fallback_actividad_asesores_nuevos').update(valor_json=4.0)
        
        fallbacks_nuevos = await EscalamientoService.aplicar_fallbacks_metricas("test-asesor-id-2")
        print(f"   • Nuevo valor actividad: {fallbacks_nuevos['actividad_reciente']}")
        
        if fallbacks_nuevos['actividad_reciente'] == Decimal('4.0'):
            print(f"   ✓ Cambio aplicado correctamente")
        else:
            print(f"   ✗ Cambio no aplicado")
        
        # Restaurar valor original
        print(f"   Restaurando valor original (3.0)...")
        await ParametroConfig.filter(clave='fallback_actividad_asesores_nuevos').update(valor_json=3.0)
        
        print(f"\n✅ Prueba completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error en prueba: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(test_fallbacks())
