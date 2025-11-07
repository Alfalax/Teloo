"""
Validation script for TeLOO V3 models
Tests model creation and basic functionality
"""

import asyncio
from database import init_db_standalone, close_db
from models import *
from decimal import Decimal


async def test_models():
    """Test basic model functionality"""
    
    print("🔄 Initializing database...")
    await init_db_standalone()
    
    try:
        print("✅ Database initialized successfully")
        
        # Test Usuario model
        print("\n🧪 Testing Usuario model...")
        usuario = Usuario(
            email="test@teloo.com",
            password_hash="hashed_password",
            nombre="Juan",
            apellido="Pérez",
            telefono="+573001234567",
            rol=RolUsuario.ADVISOR
        )
        print(f"✅ Usuario created: {usuario}")
        
        # Test Cliente model
        print("\n🧪 Testing Cliente model...")
        cliente = Cliente(
            ciudad="BOGOTA",
            departamento="CUNDINAMARCA"
        )
        print(f"✅ Cliente created: {cliente}")
        
        # Test Asesor model
        print("\n🧪 Testing Asesor model...")
        asesor = Asesor(
            ciudad="MEDELLIN",
            departamento="ANTIOQUIA",
            punto_venta="Repuestos El Buen Precio",
            confianza=Decimal('4.2')
        )
        print(f"✅ Asesor created: {asesor}")
        
        # Test Solicitud model
        print("\n🧪 Testing Solicitud model...")
        solicitud = Solicitud(
            ciudad_origen="CALI",
            departamento_origen="VALLE DEL CAUCA",
            estado=EstadoSolicitud.ABIERTA
        )
        print(f"✅ Solicitud created: {solicitud}")
        
        # Test RepuestoSolicitado model
        print("\n🧪 Testing RepuestoSolicitado model...")
        repuesto = RepuestoSolicitado(
            nombre="Pastillas de freno delanteras",
            marca_vehiculo="TOYOTA",
            linea_vehiculo="COROLLA",
            anio_vehiculo=2015
        )
        print(f"✅ RepuestoSolicitado created: {repuesto}")
        
        # Test Oferta model
        print("\n🧪 Testing Oferta model...")
        oferta = Oferta(
            tiempo_entrega_dias=5,
            estado=EstadoOferta.ENVIADA
        )
        print(f"✅ Oferta created: {oferta}")
        
        # Test OfertaDetalle model
        print("\n🧪 Testing OfertaDetalle model...")
        detalle = OfertaDetalle(
            precio_unitario=Decimal('150000'),
            cantidad=1,
            garantia_meses=12,
            tiempo_entrega_dias=5
        )
        print(f"✅ OfertaDetalle created: {detalle}")
        
        # Test AreaMetropolitana model
        print("\n🧪 Testing AreaMetropolitana model...")
        area = AreaMetropolitana(
            area_metropolitana="AREA METROPOLITANA DE BOGOTA",
            ciudad_nucleo="BOGOTA",
            municipio_norm="BOGOTA"
        )
        print(f"✅ AreaMetropolitana created: {area}")
        
        # Test HubLogistico model
        print("\n🧪 Testing HubLogistico model...")
        hub = HubLogistico(
            municipio_norm="BOGOTA",
            hub_asignado_norm="BOGOTA"
        )
        print(f"✅ HubLogistico created: {hub}")
        
        # Test analytics models
        print("\n🧪 Testing Analytics models...")
        
        evento = EventoSistema(
            tipo_evento=TipoEvento.SOLICITUD_CREADA,
            entidad="solicitud",
            entidad_id=solicitud.id
        )
        print(f"✅ EventoSistema created: {evento}")
        
        metrica = MetricaCalculada(
            nombre_metrica="solicitudes_creadas_hoy",
            periodo="diario",
            fecha_periodo="2024-01-01",
            valor_numerico=Decimal('25')
        )
        print(f"✅ MetricaCalculada created: {metrica}")
        
        transaccion = Transaccion(
            tipo=TipoTransaccion.VENTA,
            monto=Decimal('500000'),
            fecha_transaccion="2024-01-01 10:00:00"
        )
        print(f"✅ Transaccion created: {transaccion}")
        
        print("\n🎉 All models validated successfully!")
        
        # Test validation functions
        print("\n🧪 Testing validation functions...")
        
        # Test phone validation
        try:
            validate_colombian_phone("+573001234567")
            print("✅ Colombian phone validation passed")
        except ValueError as e:
            print(f"❌ Phone validation failed: {e}")
            
        # Test email validation
        try:
            validate_email("test@teloo.com")
            print("✅ Email validation passed")
        except ValueError as e:
            print(f"❌ Email validation failed: {e}")
            
        # Test vehicle year validation
        try:
            validate_anio_vehiculo(2015)
            print("✅ Vehicle year validation passed")
        except ValueError as e:
            print(f"❌ Vehicle year validation failed: {e}")
            
        # Test price validation
        try:
            validate_precio_unitario(Decimal('150000'))
            print("✅ Price validation passed")
        except ValueError as e:
            print(f"❌ Price validation failed: {e}")
            
        print("\n🎉 All validations passed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🔄 Closing database connections...")
        await close_db()
        print("✅ Database connections closed")


if __name__ == "__main__":
    asyncio.run(test_models())