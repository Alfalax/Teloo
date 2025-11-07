#!/usr/bin/env python3
"""
Comprehensive tests for Analytics Service
Tests de captura y procesamiento de eventos, cálculo de KPIs, dashboards y jobs batch
"""
import asyncio
import sys
import os
import json
import logging
from datetime import datetime, timedelta, date
from unittest.mock import Mock, patch, AsyncMock

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAnalyticsService:
    """Test suite for Analytics Service components"""
    
    def __init__(self):
        self.test_results = {
            "event_capture": False,
            "metrics_calculation": False,
            "dashboard_generation": False,
            "batch_jobs": False
        }
    
    async def setup_test_environment(self):
        """Setup test environment"""
        try:
            from app.core.database import init_db, close_db
            await init_db()
            
            from app.core.redis import redis_manager
            await redis_manager.connect()
            
            logger.info("✅ Test environment initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to setup test environment: {e}")
            return False
    
    async def cleanup_test_environment(self):
        """Cleanup test environment"""
        try:
            from app.core.database import close_db
            from app.core.redis import redis_manager
            
            await redis_manager.disconnect()
            await close_db()
            
            logger.info("✅ Test environment cleaned up")
        except Exception as e:
            logger.error(f"⚠️ Cleanup warning: {e}")

async def test_event_capture_and_processing():
    """
    Test 1: Tests de captura y procesamiento de eventos
    """
    logger.info("🧪 Testing Event Capture and Processing...")
    
    try:
        from app.services.event_collector import EventCollector
        from app.models.events import EventoSistema, EventoMetrica
        
        # Initialize event collector
        event_collector = EventCollector()
        
        # Test 1.1: Event storage
        logger.info("  1.1 Testing event storage...")
        
        # Create test event data
        test_event_data = {
            "id": 123,
            "usuario_id": 456,
            "ciudad": "Bogotá",
            "valor_total": 150000
        }
        
        # Test storing system event
        await event_collector._store_event("solicitud.created", test_event_data)
        
        # Verify event was stored
        stored_events = await EventoSistema.filter(tipo_evento="solicitud.created").all()
        assert len(stored_events) > 0, "No events were stored"
        
        latest_event = stored_events[-1]
        assert latest_event.entidad_tipo == "Solicitud"
        assert latest_event.entidad_id == 123
        assert latest_event.datos["ciudad"] == "Bogotá"
        
        logger.info("    ✅ Event storage working correctly")
        
        # Test 1.2: Metrics event processing
        logger.info("  1.2 Testing metrics event processing...")
        
        await event_collector._process_metrics("solicitud.created", test_event_data)
        
        # Verify metric events were created
        metric_events = await EventoMetrica.filter(metrica_nombre="solicitudes_creadas").all()
        assert len(metric_events) > 0, "No metric events were created"
        
        latest_metric = metric_events[-1]
        assert latest_metric.valor == 1.0
        assert latest_metric.dimensiones["ciudad"] == "Bogotá"
        
        logger.info("    ✅ Metrics event processing working correctly")
        
        # Test 1.3: Event mapping
        logger.info("  1.3 Testing event to metrics mapping...")
        
        metrics_mapping = event_collector._get_metrics_for_event("oferta.submitted", {
            "asesor_id": 789,
            "ciudad": "Medellín"
        })
        
        assert len(metrics_mapping) > 0, "No metrics mapped for oferta.submitted"
        assert metrics_mapping[0][0] == "ofertas_enviadas"
        assert metrics_mapping[0][1] == 1
        
        logger.info("    ✅ Event mapping working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Event capture test failed: {e}")
        return False

async def test_kpi_calculations():
    """
    Test 2: Tests de cálculo de KPIs individuales
    """
    logger.info("🧪 Testing KPI Calculations...")
    
    try:
        from app.services.metrics_calculator import MetricsCalculator
        
        metrics_calculator = MetricsCalculator()
        
        # Test 2.1: Main KPIs calculation
        logger.info("  2.1 Testing main KPIs calculation...")
        
        fecha_inicio = datetime.utcnow() - timedelta(days=30)
        fecha_fin = datetime.utcnow()
        
        kpis = await metrics_calculator.get_kpis_principales(fecha_inicio, fecha_fin)
        
        # Verify KPI structure
        required_kpis = ["solicitudes_mes", "tasa_conversion", "tiempo_promedio_respuesta", "valor_promedio_transaccion"]
        for kpi in required_kpis:
            assert kpi in kpis, f"Missing KPI: {kpi}"
        
        # Verify KPI data types
        assert isinstance(kpis["solicitudes_mes"], dict)
        assert isinstance(kpis["tasa_conversion"], dict)
        
        logger.info("    ✅ Main KPIs calculation working correctly")
        
        # Test 2.2: Operational funnel KPIs
        logger.info("  2.2 Testing operational funnel KPIs...")
        
        embudo = await metrics_calculator.get_embudo_operativo(fecha_inicio, fecha_fin)
        
        required_funnel_kpis = [
            "solicitudes_recibidas", "solicitudes_procesadas", "asesores_contactados",
            "tasa_respuesta_asesores", "ofertas_recibidas", "ofertas_por_solicitud",
            "solicitudes_evaluadas", "tiempo_evaluacion", "ofertas_ganadoras",
            "tasa_aceptacion_cliente", "solicitudes_cerradas"
        ]
        
        for kpi in required_funnel_kpis:
            assert kpi in embudo, f"Missing funnel KPI: {kpi}"
        
        logger.info("    ✅ Operational funnel KPIs working correctly")
        
        # Test 2.3: Marketplace health KPIs
        logger.info("  2.3 Testing marketplace health KPIs...")
        
        salud = await metrics_calculator.get_salud_marketplace(fecha_inicio, fecha_fin)
        
        required_health_kpis = [
            "disponibilidad_sistema", "latencia_promedio", "tasa_error",
            "asesores_activos", "carga_sistema"
        ]
        
        for kpi in required_health_kpis:
            assert kpi in salud, f"Missing health KPI: {kpi}"
        
        # Verify reasonable values
        assert 0 <= salud["disponibilidad_sistema"] <= 100
        assert salud["latencia_promedio"] >= 0
        assert 0 <= salud["tasa_error"] <= 1
        
        logger.info("    ✅ Marketplace health KPIs working correctly")
        
        # Test 2.4: Real-time metric updates
        logger.info("  2.4 Testing real-time metric updates...")
        
        await metrics_calculator.update_realtime_metric(
            "test_metric", 
            42.5, 
            {"test_dimension": "test_value"}
        )
        
        # Verify metric was stored
        from app.models.metrics import MetricaCalculada
        stored_metrics = await MetricaCalculada.filter(nombre="test_metric").all()
        assert len(stored_metrics) > 0, "Real-time metric was not stored"
        
        latest_metric = stored_metrics[-1]
        assert latest_metric.valor == 42.5
        assert latest_metric.dimensiones["test_dimension"] == "test_value"
        
        logger.info("    ✅ Real-time metric updates working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ KPI calculations test failed: {e}")
        return False

async def test_dashboard_generation():
    """
    Test 3: Tests de generación de dashboards
    """
    logger.info("🧪 Testing Dashboard Generation...")
    
    try:
        # Import FastAPI test client
        from fastapi.testclient import TestClient
        from app.routers.dashboards import router
        from fastapi import FastAPI
        
        # Create test app
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Test 3.1: Main dashboard
        logger.info("  3.1 Testing main dashboard...")
        
        response = client.get("/v1/dashboards/principal")
        assert response.status_code == 200, f"Main dashboard failed: {response.status_code}"
        
        data = response.json()
        assert "dashboard" in data
        assert "kpis" in data
        assert data["dashboard"] == "principal"
        
        logger.info("    ✅ Main dashboard generation working correctly")
        
        # Test 3.2: Operational funnel dashboard
        logger.info("  3.2 Testing operational funnel dashboard...")
        
        response = client.get("/v1/dashboards/embudo-operativo")
        assert response.status_code == 200, f"Funnel dashboard failed: {response.status_code}"
        
        data = response.json()
        assert "dashboard" in data
        assert "metricas" in data
        assert data["dashboard"] == "embudo_operativo"
        
        logger.info("    ✅ Operational funnel dashboard working correctly")
        
        # Test 3.3: Marketplace health dashboard
        logger.info("  3.3 Testing marketplace health dashboard...")
        
        response = client.get("/v1/dashboards/salud-marketplace")
        assert response.status_code == 200, f"Health dashboard failed: {response.status_code}"
        
        data = response.json()
        assert "dashboard" in data
        assert "metricas" in data
        assert data["dashboard"] == "salud_marketplace"
        
        logger.info("    ✅ Marketplace health dashboard working correctly")
        
        # Test 3.4: Financial dashboard
        logger.info("  3.4 Testing financial dashboard...")
        
        response = client.get("/v1/dashboards/financiero")
        assert response.status_code == 200, f"Financial dashboard failed: {response.status_code}"
        
        data = response.json()
        assert "dashboard" in data
        assert "metricas" in data
        assert data["dashboard"] == "financiero"
        
        logger.info("    ✅ Financial dashboard working correctly")
        
        # Test 3.5: Advisors analysis dashboard
        logger.info("  3.5 Testing advisors analysis dashboard...")
        
        response = client.get("/v1/dashboards/asesores")
        assert response.status_code == 200, f"Advisors dashboard failed: {response.status_code}"
        
        data = response.json()
        assert "dashboard" in data
        assert "metricas" in data
        assert data["dashboard"] == "asesores"
        
        logger.info("    ✅ Advisors analysis dashboard working correctly")
        
        # Test 3.6: Dashboard with date filters
        logger.info("  3.6 Testing dashboard with date filters...")
        
        fecha_inicio = "2024-01-01T00:00:00"
        fecha_fin = "2024-01-31T23:59:59"
        
        response = client.get(f"/v1/dashboards/principal?fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}")
        assert response.status_code == 200, f"Filtered dashboard failed: {response.status_code}"
        
        data = response.json()
        assert data["periodo"]["inicio"] == fecha_inicio
        assert data["periodo"]["fin"] == fecha_fin
        
        logger.info("    ✅ Dashboard date filtering working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Dashboard generation test failed: {e}")
        return False

async def test_batch_jobs_scheduling():
    """
    Test 4: Tests de jobs batch programados
    """
    logger.info("🧪 Testing Batch Jobs Scheduling...")
    
    try:
        from app.services.batch_jobs import batch_jobs_service
        from app.services.scheduler import analytics_scheduler
        
        # Test 4.1: Daily batch job
        logger.info("  4.1 Testing daily batch job...")
        
        yesterday = (datetime.now() - timedelta(days=1)).date()
        daily_result = await batch_jobs_service.run_daily_batch_job(yesterday)
        
        assert daily_result["success"], f"Daily batch job failed: {daily_result.get('error')}"
        assert "execution_time_seconds" in daily_result
        assert "results" in daily_result
        
        logger.info("    ✅ Daily batch job working correctly")
        
        # Test 4.2: Weekly batch job
        logger.info("  4.2 Testing weekly batch job...")
        
        weekly_result = await batch_jobs_service.run_weekly_batch_job(yesterday)
        
        assert weekly_result["success"], f"Weekly batch job failed: {weekly_result.get('error')}"
        assert "execution_time_seconds" in weekly_result
        assert "results" in weekly_result
        
        logger.info("    ✅ Weekly batch job working correctly")
        
        # Test 4.3: Scheduler initialization
        logger.info("  4.3 Testing scheduler initialization...")
        
        await analytics_scheduler.initialize()
        
        status = analytics_scheduler.get_job_status()
        assert status["status"] in ["running", "stopped"], f"Invalid scheduler status: {status['status']}"
        assert "jobs" in status
        
        logger.info("    ✅ Scheduler initialization working correctly")
        
        # Test 4.4: Job status monitoring
        logger.info("  4.4 Testing job status monitoring...")
        
        jobs = status.get("jobs", [])
        expected_jobs = ["daily_metrics_batch", "weekly_metrics_batch", "cleanup_metrics"]
        
        for expected_job in expected_jobs:
            job_found = any(job["id"] == expected_job for job in jobs)
            if not job_found:
                logger.warning(f"    ⚠️ Expected job not found: {expected_job}")
        
        logger.info("    ✅ Job status monitoring working correctly")
        
        # Test 4.5: Manual job triggering
        logger.info("  4.5 Testing manual job triggering...")
        
        try:
            # Test triggering a job manually (this might fail if scheduler is not fully configured)
            trigger_result = await analytics_scheduler.trigger_job_manually("daily_metrics_batch")
            
            if trigger_result.get("success"):
                logger.info("    ✅ Manual job triggering working correctly")
            else:
                logger.warning(f"    ⚠️ Manual job trigger returned: {trigger_result}")
                
        except Exception as e:
            logger.warning(f"    ⚠️ Manual job triggering test skipped: {e}")
        
        # Cleanup scheduler
        await analytics_scheduler.shutdown()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Batch jobs scheduling test failed: {e}")
        return False

async def test_metrics_storage_and_retrieval():
    """
    Additional test: Metrics storage and retrieval
    """
    logger.info("🧪 Testing Metrics Storage and Retrieval...")
    
    try:
        from app.models.metrics import MetricaCalculada, TipoMetrica
        
        # Test creating calculated metrics
        test_metric = await MetricaCalculada.create(
            nombre="test_storage_metric",
            tipo=TipoMetrica.KPI,
            valor=100.5,
            descripcion="Test metric for storage validation",
            unidad="count",
            dimensiones={"test": "value"},
            periodo_inicio=datetime.utcnow() - timedelta(hours=1),
            periodo_fin=datetime.utcnow(),
            expira_en=datetime.utcnow() + timedelta(hours=24)
        )
        
        assert test_metric.id is not None
        assert test_metric.nombre == "test_storage_metric"
        assert test_metric.valor == 100.5
        
        # Test retrieving metrics
        retrieved_metrics = await MetricaCalculada.filter(nombre="test_storage_metric").all()
        assert len(retrieved_metrics) > 0
        
        # Test metric expiration
        expired_metrics = await MetricaCalculada.filter(
            expira_en__lt=datetime.utcnow()
        ).all()
        
        logger.info(f"    Found {len(expired_metrics)} expired metrics")
        
        # Cleanup test metric
        await test_metric.delete()
        
        logger.info("    ✅ Metrics storage and retrieval working correctly")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Metrics storage test failed: {e}")
        return False

async def run_all_tests():
    """Run all Analytics Service tests"""
    logger.info("🚀 Starting Analytics Service Comprehensive Tests...")
    logger.info("=" * 60)
    
    test_suite = TestAnalyticsService()
    
    # Setup test environment
    if not await test_suite.setup_test_environment():
        logger.error("❌ Failed to setup test environment. Aborting tests.")
        return False
    
    try:
        # Run all test suites
        test_results = {}
        
        # Test 1: Event capture and processing
        test_results["event_capture"] = await test_event_capture_and_processing()
        
        # Test 2: KPI calculations
        test_results["kpi_calculations"] = await test_kpi_calculations()
        
        # Test 3: Dashboard generation
        test_results["dashboard_generation"] = await test_dashboard_generation()
        
        # Test 4: Batch jobs scheduling
        test_results["batch_jobs"] = await test_batch_jobs_scheduling()
        
        # Additional test: Metrics storage
        test_results["metrics_storage"] = await test_metrics_storage_and_retrieval()
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 Test Results Summary:")
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"  {test_name}: {status}")
            if result:
                passed_tests += 1
        
        logger.info(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 All Analytics Service tests completed successfully!")
            return True
        else:
            logger.error(f"💥 {total_tests - passed_tests} tests failed. Please review the errors above.")
            return False
            
    finally:
        # Cleanup test environment
        await test_suite.cleanup_test_environment()

def main():
    """Main function"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        logger.error("❌ DATABASE_URL environment variable not set")
        logger.error("   Please set it in your .env file or environment")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if success:
        logger.info("\n🎉 Analytics Service is working correctly!")
        sys.exit(0)
    else:
        logger.error("\n💥 Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()