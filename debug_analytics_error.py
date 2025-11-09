"""
Script para debuggear el error 500 en el servicio de Analytics
"""
import asyncio
import sys
import traceback
from datetime import datetime, timedelta

async def test_analytics_endpoints():
    """Probar los endpoints que están fallando"""
    
    print("=" * 80)
    print("DEBUG: ANALYTICS SERVICE ERROR 500")
    print("=" * 80)
    print()
    
    # Inicializar Tortoise
    try:
        from tortoise import Tortoise
        await Tortoise.init(
            db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_v3",
            modules={"models": ["services.core_api.models"]}
        )
        print("✅ Conexión a PostgreSQL exitosa")
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        traceback.print_exc()
        return
    
    print()
    
    # Probar Redis
    try:
        from services.analytics.app.core.redis import redis_manager
        # Intentar operación simple
        await redis_manager.set_cache("test_key", {"test": "value"}, ttl=10)
        result = await redis_manager.get_cache("test_key")
        if result:
            print("✅ Conexión a Redis exitosa")
        else:
            print("⚠️  Redis conecta pero no retorna datos")
    except Exception as e:
        print(f"❌ Error con Redis: {e}")
        print("   Esto puede causar errores en cache pero no debería ser fatal")
        traceback.print_exc()
    
    print()
    
    # Probar MetricsCalculator
    try:
        from services.analytics.app.services.metrics_calculator import MetricsCalculator
        calculator = MetricsCalculator()
        print("✅ MetricsCalculator instanciado correctamente")
        print()
        
        # Probar get_salud_marketplace
        print("Probando get_salud_marketplace()...")
        try:
            fecha_inicio = datetime.utcnow() - timedelta(days=7)
            fecha_fin = datetime.utcnow()
            salud = await calculator.get_salud_marketplace(fecha_inicio, fecha_fin)
            print(f"✅ get_salud_marketplace() exitoso: {salud}")
        except Exception as e:
            print(f"❌ Error en get_salud_marketplace(): {e}")
            traceback.print_exc()
        
        print()
        
        # Probar get_embudo_operativo
        print("Probando get_embudo_operativo()...")
        try:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
            fecha_fin = datetime.utcnow()
            embudo = await calculator.get_embudo_operativo(fecha_inicio, fecha_fin)
            print(f"✅ get_embudo_operativo() exitoso: {embudo}")
        except Exception as e:
            print(f"❌ Error en get_embudo_operativo(): {e}")
            traceback.print_exc()
        
        print()
        
        # Probar métodos individuales
        print("Probando métodos individuales...")
        try:
            asesores_activos = await calculator._calcular_asesores_activos(fecha_inicio, fecha_fin)
            print(f"  _calcular_asesores_activos: {asesores_activos}")
        except Exception as e:
            print(f"  ❌ _calcular_asesores_activos falló: {e}")
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error general con MetricsCalculator: {e}")
        traceback.print_exc()
    
    print()
    print("=" * 80)
    
    await Tortoise.close_connections()

if __name__ == "__main__":
    try:
        asyncio.run(test_analytics_endpoints())
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
