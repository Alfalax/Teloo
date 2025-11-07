"""
Test script for Alert System
Verifica que el sistema de alertas funcione correctamente
"""
import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_alert_system():
    """Test the alert system functionality"""
    try:
        # Initialize database connection
        from app.core.database import init_db, close_db
        await init_db()
        
        # Initialize Redis
        from app.core.redis import redis_manager
        await redis_manager.connect()
        
        # Test AlertManager
        from app.services.alert_manager import alert_manager
        
        logger.info("🧪 Testing Alert Manager...")
        
        # 1. Initialize default alerts
        logger.info("1. Inicializando alertas por defecto...")
        await alert_manager.initialize_default_alerts()
        
        # 2. Get active alerts
        logger.info("2. Obteniendo alertas activas...")
        active_alerts = await alert_manager.get_active_alerts()
        logger.info(f"   Alertas activas: {len(active_alerts)}")
        for alert in active_alerts:
            logger.info(f"   - {alert['nombre']}: {alert['metrica_nombre']} {alert['operador']} {alert['valor_umbral']}")
        
        # 3. Test creating a custom alert
        logger.info("3. Creando alerta personalizada...")
        custom_alert = await alert_manager.create_custom_alert(
            nombre="Test Alert - High CPU",
            metrica_nombre="cpu_usage",
            operador=">",
            valor_umbral=80.0,
            canales=["email"]
        )
        logger.info(f"   Alerta creada: {custom_alert.nombre} (ID: {custom_alert.id})")
        
        # 4. Test notification service
        logger.info("4. Probando servicio de notificaciones...")
        from app.services.notification_service import NotificationService
        notification_service = NotificationService()
        
        # Test email configuration (won't actually send if not configured)
        email_test = await notification_service.test_email_configuration()
        logger.info(f"   Email test: {email_test['success']} - {email_test['message']}")
        
        # Test Slack configuration (won't actually send if not configured)
        slack_test = await notification_service.test_slack_configuration()
        logger.info(f"   Slack test: {slack_test['success']} - {slack_test['message']}")
        
        # 5. Test alert checking (simulate)
        logger.info("5. Simulando verificación de alertas...")
        
        # This will check all alerts but won't trigger any since we don't have real metrics
        await alert_manager.check_all_alerts()
        logger.info("   Verificación completada (sin alertas disparadas - métricas simuladas)")
        
        # 6. Get alert history
        logger.info("6. Obteniendo historial de alertas...")
        history = await alert_manager.get_alert_history(days=7)
        logger.info(f"   Alertas en historial (últimos 7 días): {len(history)}")
        
        # 7. Test updating alert threshold
        logger.info("7. Actualizando umbral de alerta personalizada...")
        await alert_manager.update_alert_threshold(custom_alert.id, 90.0)
        logger.info("   Umbral actualizado de 80.0 a 90.0")
        
        # 8. Clean up - delete test alert
        logger.info("8. Limpiando alerta de prueba...")
        from app.models.metrics import AlertaMetrica
        await AlertaMetrica.filter(id=custom_alert.id).delete()
        logger.info("   Alerta de prueba eliminada")
        
        logger.info("✅ Test del sistema de alertas completado exitosamente!")
        
        return {
            "success": True,
            "active_alerts_count": len(active_alerts),
            "email_configured": email_test['success'],
            "slack_configured": slack_test['success'],
            "history_count": len(history)
        }
        
    except Exception as e:
        logger.error(f"❌ Error en test del sistema de alertas: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    
    finally:
        # Clean up connections
        try:
            await redis_manager.disconnect()
            await close_db()
        except:
            pass

async def test_alert_models():
    """Test alert models and database operations"""
    try:
        from app.core.database import init_db, close_db
        await init_db()
        
        logger.info("🧪 Testing Alert Models...")
        
        from app.models.metrics import AlertaMetrica, HistorialAlerta
        
        # Test creating an alert
        alert = await AlertaMetrica.create(
            nombre="Test Model Alert",
            metrica_nombre="test_metric",
            operador=">",
            valor_umbral=100.0,
            canales_notificacion=["email", "slack"],
            activa=True
        )
        
        logger.info(f"✅ Alert created: {alert.nombre} (ID: {alert.id})")
        
        # Test creating alert history
        history = await HistorialAlerta.create(
            alerta=alert,
            valor_actual=150.0,
            mensaje="Test alert triggered",
            enviada=True,
            canales_enviados=["email"]
        )
        
        logger.info(f"✅ Alert history created: ID {history.id}")
        
        # Test querying
        alerts = await AlertaMetrica.filter(activa=True).all()
        logger.info(f"✅ Found {len(alerts)} active alerts")
        
        # Clean up
        await history.delete()
        await alert.delete()
        logger.info("✅ Test data cleaned up")
        
        await close_db()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing alert models: {e}")
        return False

if __name__ == "__main__":
    async def main():
        logger.info("🚀 Iniciando tests del sistema de alertas...")
        
        # Test models first
        models_ok = await test_alert_models()
        if not models_ok:
            logger.error("❌ Test de modelos falló")
            return
        
        # Test full alert system
        result = await test_alert_system()
        
        if result["success"]:
            logger.info("🎉 Todos los tests pasaron exitosamente!")
            logger.info(f"📊 Resumen:")
            logger.info(f"   - Alertas activas: {result['active_alerts_count']}")
            logger.info(f"   - Email configurado: {result['email_configured']}")
            logger.info(f"   - Slack configurado: {result['slack_configured']}")
            logger.info(f"   - Historial de alertas: {result['history_count']}")
        else:
            logger.error(f"❌ Test falló: {result['error']}")
    
    asyncio.run(main())