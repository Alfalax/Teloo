"""
Simple test to verify alert system imports work correctly
"""
import sys
import os

# Add the analytics service to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_imports():
    """Test that all alert system components can be imported"""
    try:
        print("🧪 Testing Alert System Imports...")
        
        # Test model imports
        print("1. Testing model imports...")
        from app.models.metrics import AlertaMetrica, HistorialAlerta, TipoMetrica
        from app.models.events import EventoSistema, EventoMetrica
        print("   ✅ Models imported successfully")
        
        # Test service imports
        print("2. Testing service imports...")
        from app.services.alert_manager import AlertManager, AlertSeverity, AlertOperator
        from app.services.notification_service import NotificationService
        print("   ✅ Services imported successfully")
        
        # Test configuration
        print("3. Testing configuration...")
        from app.core.config import settings
        print(f"   ✅ Configuration loaded - Environment: {settings.ENVIRONMENT}")
        print(f"   ✅ Alert thresholds: {settings.ALERT_THRESHOLDS}")
        
        # Test router imports
        print("4. Testing router imports...")
        from app.routers.alerts import router
        print("   ✅ Router imported successfully")
        
        # Test enum values
        print("5. Testing enum values...")
        severities = [s.value for s in AlertSeverity]
        operators = [o.value for o in AlertOperator]
        print(f"   ✅ Alert severities: {severities}")
        print(f"   ✅ Alert operators: {operators}")
        
        # Test alert manager instantiation
        print("6. Testing alert manager instantiation...")
        alert_manager = AlertManager()
        print("   ✅ AlertManager instantiated successfully")
        
        # Test notification service instantiation
        print("7. Testing notification service instantiation...")
        notification_service = NotificationService()
        print("   ✅ NotificationService instantiated successfully")
        
        print("🎉 All imports and instantiations successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n✅ Alert system is ready for deployment!")
    else:
        print("\n❌ Alert system has import issues that need to be fixed.")
        sys.exit(1)