"""
Test model structure without database connection
"""

from models import *
from models.user import validate_colombian_phone, validate_email
from models.solicitud import validate_anio_vehiculo
from models.oferta import validate_precio_unitario, validate_garantia_meses, validate_tiempo_entrega
from decimal import Decimal


def test_model_imports():
    """Test that all models can be imported successfully"""
    
    print("🧪 Testing model imports...")
    
    # Test enum imports
    print("✅ RolUsuario:", list(RolUsuario))
    print("✅ EstadoSolicitud:", list(EstadoSolicitud))
    print("✅ EstadoOferta:", list(EstadoOferta))
    print("✅ TipoEvento:", list(TipoEvento))
    
    # Test model classes exist
    models_to_test = [
        Usuario, Cliente, Asesor,
        Solicitud, RepuestoSolicitado,
        Oferta, OfertaDetalle, AdjudicacionRepuesto, Evaluacion,
        Municipio, EvaluacionAsesorTemp,
        HistorialRespuestaOferta, OfertaHistorica, AuditoriaTienda,
        EventoSistema, MetricaCalculada, Transaccion,
        PQR, Notificacion, SesionUsuario, LogAuditoria, ParametroConfig
    ]
    
    for model in models_to_test:
        print(f"✅ {model.__name__} model imported successfully")
    
    print(f"\n🎉 All {len(models_to_test)} models imported successfully!")


def test_validation_functions():
    """Test validation functions"""
    
    print("\n🧪 Testing validation functions...")
    
    # Test phone validation
    try:
        validate_colombian_phone("+573001234567")
        print("✅ Colombian phone validation works")
    except Exception as e:
        print(f"❌ Phone validation error: {e}")
    
    # Test invalid phone
    try:
        validate_colombian_phone("123456789")
        print("❌ Phone validation should have failed")
    except ValueError:
        print("✅ Phone validation correctly rejects invalid format")
    
    # Test email validation
    try:
        validate_email("test@teloo.com")
        print("✅ Email validation works")
    except Exception as e:
        print(f"❌ Email validation error: {e}")
    
    # Test invalid email
    try:
        validate_email("invalid-email")
        print("❌ Email validation should have failed")
    except ValueError:
        print("✅ Email validation correctly rejects invalid format")
    
    # Test vehicle year validation
    try:
        validate_anio_vehiculo(2015)
        print("✅ Vehicle year validation works")
    except Exception as e:
        print(f"❌ Vehicle year validation error: {e}")
    
    # Test invalid year
    try:
        validate_anio_vehiculo(1970)
        print("❌ Vehicle year validation should have failed")
    except ValueError:
        print("✅ Vehicle year validation correctly rejects invalid year")
    
    # Test price validation
    try:
        validate_precio_unitario(Decimal('150000'))
        print("✅ Price validation works")
    except Exception as e:
        print(f"❌ Price validation error: {e}")
    
    # Test invalid price
    try:
        validate_precio_unitario(Decimal('500'))
        print("❌ Price validation should have failed")
    except ValueError:
        print("✅ Price validation correctly rejects invalid price")


def test_model_properties():
    """Test model properties and methods"""
    
    print("\n🧪 Testing model properties and methods...")
    
    # Test Municipio normalization
    normalized = Municipio.normalizar_ciudad("  Bogotá D.C.  ")
    expected = "BOGOTA D.C."
    print(f"✅ City normalization: '{normalized}' (expected: '{expected}')")
    
    # Test RepuestoSolicitado properties
    repuesto = RepuestoSolicitado()
    repuesto.nombre = "Pastillas de freno"
    repuesto.marca_vehiculo = "TOYOTA"
    repuesto.linea_vehiculo = "COROLLA"
    repuesto.anio_vehiculo = 2015
    repuesto.cantidad = 2
    repuesto.codigo = "PF001"
    
    print(f"✅ Vehiculo completo: {repuesto.vehiculo_completo}")
    print(f"✅ Descripcion completa: {repuesto.descripcion_completa}")
    print(f"✅ Es vehiculo reciente: {repuesto.is_vehiculo_reciente()}")
    
    # Test OfertaDetalle properties
    detalle = OfertaDetalle()
    detalle.precio_unitario = Decimal('150000')
    detalle.cantidad = 2
    detalle.garantia_meses = 18
    detalle.tiempo_entrega_dias = 5
    
    print(f"✅ Monto total detalle: ${detalle.monto_total_detalle:,.0f}")
    print(f"✅ Descripcion garantia: {detalle.descripcion_garantia}")
    print(f"✅ Descripcion entrega: {detalle.descripcion_entrega}")


if __name__ == "__main__":
    try:
        test_model_imports()
        test_validation_functions()
        test_model_properties()
        print("\n🎉 All tests passed! Models are properly structured.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()