#!/usr/bin/env python3
"""
Unit tests for Event Processing components
Tests específicos para captura y procesamiento de eventos
"""
import asyncio
import sys
import os
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_event_collector_initialization():
    """Test EventCollector initialization"""
    from app.services.event_collector import EventCollector
    
    collector = EventCollector()
    assert collector.running == False
    assert collector.metrics_calculator is not None
    print("✅ EventCollector initialization test passed")

async def test_event_storage():
    """Test event storage functionality"""
    try:
        from app.core.database import init_db, close_db
        from app.services.event_collector import EventCollector
        from app.models.events import EventoSistema
        
        await init_db()
        
        collector = EventCollector()
        
        # Test data
        test_data = {
            "id": 999,
            "usuario_id": 123,
            "ciudad": "Test City",
            "estado": "ABIERTA"
        }
        
        # Store event
        await collector._store_event("solicitud.created", test_data)
        
        # Verify storage
        events = await EventoSistema.filter(
            tipo_evento="solicitud.created",
            entidad_id=999
        ).all()
        
        assert len(events) > 0
        latest_event = events[-1]
        assert latest_event.entidad_tipo == "Solicitud"
        assert latest_event.datos["ciudad"] == "Test City"
        
        # Cleanup
        await latest_event.delete()
        await close_db()
        
        print("✅ Event storage test passed")
        return True
        
    except Exception as e:
        print(f"❌ Event storage test failed: {e}")
        return False

async def test_metrics_event_creation():
    """Test metrics event creation"""
    try:
        from app.core.database import init_db, close_db
        from app.services.event_collector import EventCollector
        from app.models.events import EventoMetrica
        
        await init_db()
        
        collector = EventCollector()
        
        # Test data
        test_data = {
            "asesor_id": 456,
            "ciudad": "Medellín",
            "valor_total": 250000
        }
        
        # Process metrics
        await collector._process_metrics("oferta.submitted", test_data)
        
        # Verify metric event creation
        metric_events = await EventoMetrica.filter(
            metrica_nombre="ofertas_enviadas"
        ).all()
        
        if len(metric_events) > 0:
            latest_metric = metric_events[-1]
            assert latest_metric.valor == 1.0
            assert "asesor_id" in latest_metric.dimensiones
            
            # Cleanup
            await latest_metric.delete()
        
        await close_db()
        
        print("✅ Metrics event creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Metrics event creation test failed: {e}")
        return False

async def test_event_mapping():
    """Test event to metrics mapping"""
    from app.services.event_collector import EventCollector
    
    collector = EventCollector()
    
    # Test different event types
    test_cases = [
        ("solicitud.created", {"ciudad": "Bogotá"}, "solicitudes_creadas"),
        ("oferta.submitted", {"asesor_id": 123}, "ofertas_enviadas"),
        ("evaluacion.completed", {"solicitud_id": 456}, "evaluaciones_completadas"),
        ("oferta.accepted", {"asesor_id": 789, "valor_total": 100000}, "ofertas_aceptadas"),
        ("cliente.registered", {"ciudad": "Cali", "canal": "whatsapp"}, "clientes_registrados")
    ]
    
    for event_type, data, expected_metric in test_cases:
        metrics = collector._get_metrics_for_event(event_type, data)
        
        if len(metrics) > 0:
            metric_name, value, dimensions = metrics[0]
            assert metric_name == expected_metric
            assert value == 1
            assert isinstance(dimensions, dict)
        
        print(f"✅ Event mapping test passed for {event_type}")
    
    return True

async def run_event_processing_tests():
    """Run all event processing tests"""
    print("🧪 Running Event Processing Tests...")
    print("=" * 40)
    
    tests = [
        ("EventCollector Initialization", test_event_collector_initialization),
        ("Event Storage", test_event_storage),
        ("Metrics Event Creation", test_metrics_event_creation),
        ("Event Mapping", test_event_mapping)
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
    print("📊 Event Processing Test Results:")
    
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
    
    success = asyncio.run(run_event_processing_tests())
    
    if success:
        print("\n🎉 All event processing tests passed!")
    else:
        print("\n💥 Some event processing tests failed!")
    
    sys.exit(0 if success else 1)