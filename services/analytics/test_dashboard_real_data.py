"""
Script para probar que el dashboard obtiene datos reales de la base de datos
"""
import asyncio
import sys
from datetime import datetime, timedelta
from tortoise import Tortoise
from app.services.metrics_calculator import MetricsCalculator

async def test_dashboard_data():
    """Probar que los datos del dashboard se obtienen correctamente"""
    
    # Inicializar conexión a la base de datos
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_v3",
        modules={"models": ["app.models.metrics"]}
    )
    
    print("=" * 80)
    print("PRUEBA DE DATOS REALES DEL DASHBOARD")
    print("=" * 80)
    
    calculator = MetricsCalculator()
    
    # Definir período de prueba (últimos 30 días)
    fecha_fin = datetime.utcnow()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    print(f"\nPeríodo de análisis:")
    print(f"  Desde: {fecha_inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Hasta: {fecha_fin.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. Probar KPIs principales
        print("1. KPIs PRINCIPALES")
        print("-" * 80)
        kpis = await calculator.get_kpis_principales(fecha_inicio, fecha_fin)
        
        print(f"  Ofertas Totales Asignadas: {kpis['ofertas_totales']}")
        print(f"    Cambio: {kpis['ofertas_cambio']:+.2f}%")
        print()
        print(f"  Monto Total Aceptado: ${kpis['monto_total']:,.0f}")
        print(f"    Cambio: {kpis['monto_cambio']:+.2f}%")
        print()
        print(f"  Solicitudes Abiertas: {kpis['solicitudes_abiertas']}")
        print(f"    Cambio: {kpis['solicitudes_cambio']:+.2f}%")
        print()
        print(f"  Tasa de Conversión: {kpis['tasa_conversion']:.2f}%")
        print(f"    Cambio: {kpis['conversion_cambio']:+.2f}%")
        print()
        
        # 2. Probar gráficos del mes
        print("2. GRÁFICOS DEL MES")
        print("-" * 80)
        graficos = await calculator.get_graficos_mes(fecha_inicio, fecha_fin)
        
        if graficos:
            print(f"  Total de días con datos: {len(graficos)}")
            print(f"  Primer día: {graficos[0]['date']}")
            print(f"    Solicitudes: {graficos[0]['solicitudes']}")
            print(f"    Aceptadas: {graficos[0]['aceptadas']}")
            print(f"    Cerradas: {graficos[0]['cerradas']}")
            print()
            print(f"  Último día: {graficos[-1]['date']}")
            print(f"    Solicitudes: {graficos[-1]['solicitudes']}")
            print(f"    Aceptadas: {graficos[-1]['aceptadas']}")
            print(f"    Cerradas: {graficos[-1]['cerradas']}")
        else:
            print("  ⚠️  No hay datos de gráficos disponibles")
        print()
        
        # 3. Probar top solicitudes abiertas
        print("3. TOP SOLICITUDES ABIERTAS")
        print("-" * 80)
        top_solicitudes = await calculator.get_top_solicitudes_abiertas(10)
        
        if top_solicitudes:
            print(f"  Total de solicitudes abiertas: {len(top_solicitudes)}")
            print()
            for i, sol in enumerate(top_solicitudes[:5], 1):
                print(f"  {i}. {sol['codigo']} - {sol['vehiculo']}")
                print(f"     Cliente: {sol['cliente']}")
                print(f"     Ciudad: {sol['ciudad']}")
                print(f"     Tiempo en proceso: {sol['tiempo_proceso_horas']:.1f} horas")
                print(f"     Repuestos: {sol['repuestos_count']}")
                print()
        else:
            print("  ℹ️  No hay solicitudes abiertas en este momento")
        print()
        
        # 4. Verificar si hay datos reales
        print("4. VERIFICACIÓN DE DATOS")
        print("-" * 80)
        
        tiene_datos_reales = (
            kpis['ofertas_totales'] > 0 or
            kpis['solicitudes_abiertas'] > 0 or
            len(graficos) > 0 or
            len(top_solicitudes) > 0
        )
        
        if tiene_datos_reales:
            print("  ✅ El dashboard tiene datos reales de la base de datos")
        else:
            print("  ⚠️  La base de datos parece estar vacía")
            print("  💡 Ejecuta el script de inicialización de datos:")
            print("     python services/core-api/init_data.py")
        print()
        
        print("=" * 80)
        print("PRUEBA COMPLETADA EXITOSAMENTE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(test_dashboard_data())
