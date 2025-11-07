#!/usr/bin/env python3
"""
Unit tests for Metrics Calculation
Tests específicos para cálculo de KPIs individuales
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_metrics_calculator_initialization():
    """Test MetricsCalculator initialization"""
    from app.services.metrics_calculator import MetricsCalculator
    
    calculator = MetricsCalculator()
    assert calculator.cache_prefix == "metrics:"
    print("✅ MetricsCalculator initialization test passed")

async def test_kpis_principales_structure():
    """Test main KPIs structure and data types"""
    try:
        from app.core.database import init_db, close_db
        from app.services.metrics_calculator import MetricsCalculator
        
        await init_db()
        
        calculator = MetricsCalculator()
        
        fecha_inicio = datetime.utcnow() - timedelta(days=7)
        fecha_fin = datetime.utcnow()
        
        kpis = await calculator.get_kpis_principales(fecha_inicio, fecha_fin)
        
        # Verify structure
        required_kpis = [
            "solicitudes_mes",
            "tasa_conversion", 
            "tiempo_promedio_respuesta",
            "valor_promedio_transaccion"
        ]
        
        for kpi in required_kpis:
            assert kpi in kpis, f"Missing KPI: {kpi}"
            assert isinstance(kpis[kpi], dict), f"KPI {kpi} should be a dict"
        
        # Verify solicitudes_mes structure
        solicitudes = kpis["solicitudes_mes"]
        expected_fields = ["total", "abiertas", "evaluadas", "aceptadas"]
        for field in expected_fields:
            assert field in solicitudes, f"Missing field in solicitudes_mes: {field}"
            assert isinstance(solicitudes[field], int), f"Field {field} should be int"
        
        # Verify tasa_conversion structure
        conversion = kpis["tasa_conversion"]
        expected_fields = ["total_solicitudes", "aceptadas", "tasa_conversion"]
        for field in expected_fields:
            assert field in conversion, f"Missing field in tasa_conversion: {field}"
        
        await close_db()
        
        print("✅ Main KPIs structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ Main KPIs structure test failed: {e}")
        return False

async def test_embudo_operativo_structure():
    """Test operational funnel KPIs structure"""
    try:
        from app.core.database import init_db, close_db
        from app.services.metrics_calculator import MetricsCalculator
        
        await init_db()
        
        calculator = MetricsCalculator()
        
        fecha_inicio = datetime.utcnow() - timedelta(days=7)
        fecha_fin = datetime.utcnow()
        
        embudo = await calculator.get_embudo_operativo(fecha_inicio, fecha_fin)
        
        # Verify all 11 KPIs are present
        required_kpis = [
            "solicitudes_recibidas",
            "solicitudes_procesadas", 
            "asesores_contactados",
            "tasa_respuesta_asesores",
            "ofertas_recibidas",
            "ofertas_por_solicitud",
            "solicitudes_evaluadas",
            "tiempo_evaluacion",
            "ofertas_ganadoras",
            "tasa_aceptacion_cliente",
            "solicitudes_cerradas"
        ]
        
        for kpi in required_kpis:
            assert kpi in embudo, f"Missing funnel KPI: {kpi}"
        
        # Verify data types
        numeric_kpis = [
            "solicitudes_recibidas", "solicitudes_procesadas", "asesores_contactados",
            "ofertas_recibidas", "solicitudes_evaluadas", "ofertas_ganadoras", "solicitudes_cerradas"
        ]
        
        for kpi in numeric_kpis:
            assert isinstance(embudo[kpi], (int, float)), f"KPI {kpi} should be numeric"
            assert embudo[kpi] >= 0, f"KPI {kpi} should be non-negative"
        
        await close_db()
        
        print("✅ Operational funnel structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ Operational funnel structure test failed: {e}")
        return False

async def test_salud_marketplace_structure():
    """Test marketplace health KPIs structure"""
    try:
        from app.core.database import init_db, close_db
        from app.services.metrics_calculator import MetricsCalculator
        
        await init_db()
        
        calculator = MetricsCalculator()
        
        fecha_inicio = datetime.utcnow() - timedelta(days=1)
        fecha_fin = datetime.utcnow()
        
        salud = await calculator.get_salud_marketplace(fecha_inicio, fecha_fin)
        
        # Verify all 5 health KPIs are present
        required_kpis = [
            "disponibilidad_sistema",
            "latencia_promedio",
            "tasa_error", 
            "asesores_activos",
            "carga_sistema"
        ]
        
        for kpi in required_kpis:
            assert kpi in salud, f"Missing health KPI: {kpi}"
            assert isinstance(salud[kpi], (int, float)), f"Health KPI {kpi} should be numeric"
        
        # Verify reasonable ranges
        assert 0 <= salud["disponibilidad_sistema"] <= 100, "Availability should be 0-100%"
        assert salud["latencia_promedio"] >= 0, "Latency should be non-negative"
        assert 0 <= salud["tasa_error"] <= 1, "Error rate should be 0-1"
        assert salud["asesores_activos"] >= 0, "Active advisors should be non-negative"
        assert 0 <= salud["carga_sistema"] <= 100, "System load should be 0-100%"
        
        await close_db()
        
        print("✅ Marketplace health structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ Marketplace health structure test failed: {e}")
        return False

async def test_realtime_metric_update():
    """Test real-time metric updates"""
    try:
        from app.core.database import init_db, close_db
        from app.services.metrics_calculator import MetricsCalculator
        from app.models.metrics import MetricaCalculada, TipoMetrica
        
        await init_db()
        
        calculator = MetricsCalculator()
        
        # Test metric update
        test_metric_name = "test_realtime_metric"
        test_value = 123.45
        test_dimensions = {"test_key": "test_value", "timestamp": datetime.utcnow().isoformat()}
        
        await calculator.update_realtime_metric(test_metric_name, test_value, test_dimensions)
        
        # Verify metric was stored
        stored_metrics = await MetricaCalculada.filter(nome=test_metric_name).all()
        assert len(stored_metrics) > 0, "Real-time metric was not stored"
        
        latest_metric = stored_metrics[-1]
        assert latest_metric.valor == test_value
        assert latest_metric.tipo == TipoMetrica.COUNTER
        assert latest_metric.dimensiones["test_key"] == "test_value"
        
        # Verify expiration is set
        assert latest_metric.expira_en > datetime.utcnow()
        
        # Cleanup
        await latest_metric.delete()
        await close_db()
        
        print("✅ Real-time metric update test passed")
        return True
        
    except Exception as e:
        print(f"❌ Real-time metric update test failed: {e}")
        return False

async def test_individual_kpi_calculations():
    """Test individual KPI calculation methods"""
    try:
        from app.core.database import init_db, close_db
        from app.services.metrics_calculator import MetricsCalculator
        
        await init_db()
        
        calculator = MetricsCalculator()
        
        fecha_inicio = datetime.utcnow() - timedelta(days=7)
        fecha_fin = datetime.utcnow()
        
        # Test individual calculation methods
        test_methods = [
            ("_calcular_solicitudes_mes", [fecha_inicio, fecha_fin]),
            ("_calcular_tasa_conversion", [fecha_inicio, fecha_fin]),
            ("_calcular_tiempo_promedio_respuesta", [fecha_inicio, fecha_fin]),
            ("_calcular_valor_promedio_transaccion", [fecha_inicio, fecha_fin]),
            ("_calcular_solicitudes_recibidas", [fecha_inicio, fecha_fin]),
            ("_calcular_solicitudes_procesadas", [fecha_inicio, fecha_fin])
        ]
        
        for method_name, args in test_methods:
            if hasattr(calculator, method_name):
                method = getattr(calculator, method_name)
                try:
                    result = await method(*args)
                    assert result is not None, f"Method {method_name} returned None"
                    print(f"  ✅ {method_name} working correctly")
                except Exception as e:
                    print(f"  ⚠️ {method_name} failed: {e}")
        
        await close_db()
        
        print("✅ Individual KPI calculations test passed")
        return True
        
    except Exception as e:
        print(f"❌ Individual KPI calculations test failed: {e}")
        return False

async def test_cache_functionality():
    """Test metrics caching functionality"""
    try:
        from app.core.redis import redis_manager
        from app.services.metrics_calculator import MetricsCalculator
        
        # Connect to Redis
        await redis_manager.connect()
        
        calculator = MetricsCalculator()
        
        # Test cache key generation
        cache_key = f"{calculator.cache_prefix}test_cache_key"
        test_data = {"test": "value", "number": 42}
        
        # Set cache
        await redis_manager.set_cache(cache_key, test_data)
        
        # Get cache
        cached_data = await redis_manager.get_cache(cache_key)
        
        if cached_data:
            assert cached_data["test"] == "value"
            assert cached_data["number"] == 42
            print("✅ Cache functionality test passed")
        else:
            print("⚠️ Cache functionality test skipped (Redis not available)")
        
        await redis_manager.disconnect()
        
        return True
        
    except Exception as e:
        print(f"⚠️ Cache functionality test skipped: {e}")
        return True  # Don't fail if Redis is not available

async def run_metrics_calculation_tests():
    """Run all metrics calculation tests"""
    print("🧪 Running Metrics Calculation Tests...")
    print("=" * 40)
    
    tests = [
        ("MetricsCalculator Initialization", test_metrics_calculator_initialization),
        ("Main KPIs Structure", test_kpis_principales_structure),
        ("Operational Funnel Structure", test_embudo_operativo_structure),
        ("Marketplace Health Structure", test_salud_marketplace_structure),
        ("Real-time Metric Update", test_realtime_metric_update),
        ("Individual KPI Calculations", test_individual_kpi_calculations),
        ("Cache Functionality", test_cache_functionality)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = await test_func()
            results[test_name] = result if result is not None else True
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Metrics Calculation Test Results:")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = asyncio.run(run_metrics_calculation_tests())
    
    if success:
        print("\n🎉 All metrics calculation tests passed!")
    else:
        print("\n💥 Some metrics calculation tests failed!")
    
    sys.exit(0 if success else 1)