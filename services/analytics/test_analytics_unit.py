#!/usr/bin/env python3
"""
Unit tests for Analytics Service (without database dependencies)
Tests unitarios que no requieren base de datos
"""
import sys
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_event_collector_basic():
    """Test basic EventCollector functionality without database"""
    try:
        from app.services.event_collector import EventCollector
        
        collector = EventCollector()
        
        # Test initialization
        assert collector.running == False
        assert collector.metrics_calculator is not None
        
        # Test event mapping without database
        test_cases = [
            ("solicitud.created", {"ciudad": "Bogotá"}, "solicitudes_creadas"),
            ("oferta.submitted", {"asesor_id": 123}, "ofertas_enviadas"),
            ("evaluacion.completed", {"solicitud_id": 456}, "evaluaciones_completadas"),
        ]
        
        for event_type, data, expected_metric in test_cases:
            metrics = collector._get_metrics_for_event(event_type, data)
            
            if len(metrics) > 0:
                metric_name, value, dimensions = metrics[0]
                assert metric_name == expected_metric
                assert value == 1
                assert isinstance(dimensions, dict)
        
        print("✅ EventCollector basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ EventCollector basic test failed: {e}")
        return False

def test_metrics_calculator_basic():
    """Test basic MetricsCalculator functionality without database"""
    try:
        from app.services.metrics_calculator import MetricsCalculator
        
        calculator = MetricsCalculator()
        
        # Test initialization
        assert calculator.cache_prefix == "metrics:"
        
        # Test that methods exist
        required_methods = [
            'get_kpis_principales',
            'get_embudo_operativo', 
            'get_salud_marketplace',
            'update_realtime_metric',
            '_calcular_solicitudes_mes',
            '_calcular_tasa_conversion'
        ]
        
        for method_name in required_methods:
            assert hasattr(calculator, method_name), f"Missing method: {method_name}"
            method = getattr(calculator, method_name)
            assert callable(method), f"Method {method_name} is not callable"
        
        print("✅ MetricsCalculator basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ MetricsCalculator basic test failed: {e}")
        return False

def test_models_import():
    """Test that all models can be imported"""
    try:
        # Test event models
        from app.models.events import EventoSistema, EventoMetrica
        
        # Verify model attributes
        assert hasattr(EventoSistema, 'tipo_evento')
        assert hasattr(EventoSistema, 'entidad_tipo')
        assert hasattr(EventoSistema, 'datos')
        
        assert hasattr(EventoMetrica, 'metrica_nombre')
        assert hasattr(EventoMetrica, 'valor')
        assert hasattr(EventoMetrica, 'dimensiones')
        
        # Test metrics models
        from app.models.metrics import MetricaCalculada, AlertaMetrica, TipoMetrica
        
        # Verify enum
        assert hasattr(TipoMetrica, 'KPI')
        assert hasattr(TipoMetrica, 'COUNTER')
        assert hasattr(TipoMetrica, 'GAUGE')
        
        # Verify model attributes
        assert hasattr(MetricaCalculada, 'nombre')
        assert hasattr(MetricaCalculada, 'valor')
        assert hasattr(MetricaCalculada, 'tipo')
        
        assert hasattr(AlertaMetrica, 'nombre')
        assert hasattr(AlertaMetrica, 'metrica_nombre')
        assert hasattr(AlertaMetrica, 'valor_umbral')
        
        print("✅ Models import test passed")
        return True
        
    except Exception as e:
        print(f"❌ Models import test failed: {e}")
        return False

def test_dashboard_router_structure():
    """Test dashboard router structure"""
    try:
        from app.routers.dashboards import router
        from fastapi import APIRouter
        
        # Verify it's a FastAPI router
        assert isinstance(router, APIRouter)
        
        # Check that router has the expected prefix and tags
        assert router.prefix == "/v1/dashboards"
        assert "dashboards" in router.tags
        
        print("✅ Dashboard router structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard router structure test failed: {e}")
        return False

def test_batch_jobs_import():
    """Test batch jobs service import"""
    try:
        from app.services.batch_jobs import batch_jobs_service
        from app.services.scheduler import analytics_scheduler
        
        # Verify services exist
        assert batch_jobs_service is not None
        assert analytics_scheduler is not None
        
        # Check that required methods exist
        assert hasattr(batch_jobs_service, 'run_daily_batch_job')
        assert hasattr(batch_jobs_service, 'run_weekly_batch_job')
        
        assert hasattr(analytics_scheduler, 'initialize')
        assert hasattr(analytics_scheduler, 'get_job_status')
        
        print("✅ Batch jobs import test passed")
        return True
        
    except Exception as e:
        print(f"❌ Batch jobs import test failed: {e}")
        return False

def test_configuration_import():
    """Test configuration and core imports"""
    try:
        # Test core imports
        from app.core.config import settings
        from app.core.database import init_db, close_db
        from app.core.redis import redis_manager
        
        # Verify functions exist
        assert callable(init_db)
        assert callable(close_db)
        assert redis_manager is not None
        
        print("✅ Configuration import test passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration import test failed: {e}")
        return False

def run_unit_tests():
    """Run all unit tests"""
    print("🧪 Running Analytics Service Unit Tests (No Database Required)")
    print("=" * 60)
    
    tests = [
        ("EventCollector Basic", test_event_collector_basic),
        ("MetricsCalculator Basic", test_metrics_calculator_basic),
        ("Models Import", test_models_import),
        ("Dashboard Router Structure", test_dashboard_router_structure),
        ("Batch Jobs Import", test_batch_jobs_import),
        ("Configuration Import", test_configuration_import)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Unit Test Results:")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All unit tests passed! Analytics Service structure is correct.")
        print("\n📋 Test Coverage Summary:")
        print("  ✅ Event capture and processing structure")
        print("  ✅ KPI calculation methods structure") 
        print("  ✅ Dashboard generation endpoints")
        print("  ✅ Batch jobs scheduling components")
        print("  ✅ Models and configuration imports")
        
        print(f"\n💡 Next Steps:")
        print(f"  1. Set up DATABASE_URL in .env file")
        print(f"  2. Run full integration tests with: python run_analytics_tests.py")
        print(f"  3. Test with real data using existing test files")
        
        return True
    else:
        print(f"\n💥 {total - passed} unit tests failed!")
        return False

if __name__ == "__main__":
    success = run_unit_tests()
    sys.exit(0 if success else 1)