"""
Initialization service for TeLOO V3
Handles automatic database initialization on startup
"""

import logging
import hashlib
from models.user import Usuario, Cliente, Asesor
from models.enums import RolUsuario, EstadoUsuario, TipoPQR, PrioridadPQR, EstadoPQR
from models.analytics import ParametroConfig, PQR
from models.geografia import AreaMetropolitana, HubLogistico

logger = logging.getLogger(__name__)

class InitService:
    """Service for initializing database with default data"""
    
    @staticmethod
    async def initialize_default_data():
        """Initialize database with default admin user and configuration"""
        try:
            logger.info("🚀 Starting database initialization...")
            
            # Initialize admin user
            await InitService._create_admin_user()
            
            # Initialize configuration parameters
            await InitService._create_config_parameters()
            
            # Create sample data for development
            await InitService._create_sample_data()
            
            logger.info("✅ Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error during database initialization: {e}")
            raise
    
    @staticmethod
    async def _create_admin_user():
        """Create or update admin user"""
        admin_email = "admin@teloo.com"
        admin_password = "admin123"
        
        try:
            existing_admin = await Usuario.get_or_none(email=admin_email)
            
            # Import AuthService for proper password hashing
            from services.auth_service import AuthService
            
            if existing_admin:
                # Update existing admin password with proper bcrypt hash
                password_hash = AuthService.get_password_hash(admin_password)
                existing_admin.password_hash = password_hash
                await existing_admin.save()
                logger.info(f"🔄 Admin user updated: {admin_email}")
            else:
                # Create new admin user with proper bcrypt hash
                password_hash = AuthService.get_password_hash(admin_password)
                await Usuario.create(
                    email=admin_email,
                    password_hash=password_hash,
                    nombre="Administrador",
                    apellido="TeLOO",
                    telefono="+573001234567",
                    rol=RolUsuario.ADMIN,
                    estado=EstadoUsuario.ACTIVO
                )
                
                logger.info(f"✅ Admin user created: {admin_email}")
                logger.info(f"   Default password: {admin_password}")
                
        except Exception as e:
            logger.error(f"❌ Error creating admin user: {e}")
            raise
    
    @staticmethod
    async def _create_config_parameters():
        """Create default configuration parameters"""
        config_params = {
            'pesos_escalamiento': {
                "proximidad": 0.40, 
                "actividad": 0.25, 
                "desempeno": 0.20, 
                "confianza": 0.15
            },
            'umbrales_niveles': {
                "nivel1_min": 4.5, 
                "nivel2_min": 4.0, 
                "nivel3_min": 3.5, 
                "nivel4_min": 3.0
            },
            'tiempos_espera_minutos': {
                "nivel1": 15, 
                "nivel2": 20, 
                "nivel3": 25, 
                "nivel4": 30
            },
            'canales_notificacion': {
                "nivel1": "whatsapp", 
                "nivel2": "whatsapp", 
                "nivel3": "push", 
                "nivel4": "push"
            },
            'pesos_evaluacion': {
                "precio": 0.50, 
                "tiempo": 0.35, 
                "garantia": 0.15
            },
            'ofertas_minimas_deseadas': 2,
            'timeout_evaluacion_segundos': 5,
            'periodo_actividad_reciente_dias': 30,
            'periodo_desempeno_historico_meses': 6,
            'vigencia_auditoria_dias': 30,
            'cobertura_minima_porcentaje': 50
        }
        
        try:
            params_created = 0
            for clave, valor in config_params.items():
                existing_param = await ParametroConfig.get_or_none(clave=clave)
                if not existing_param:
                    await ParametroConfig.create(
                        clave=clave,
                        valor_json=valor
                    )
                    params_created += 1
                    logger.info(f"✅ Config parameter created: {clave}")
                else:
                    logger.debug(f"⏭️ Config parameter already exists: {clave}")
            
            if params_created > 0:
                logger.info(f"✅ Created {params_created} configuration parameters")
            else:
                logger.info("ℹ️ All configuration parameters already exist")
                
        except Exception as e:
            logger.error(f"❌ Error creating config parameters: {e}")
            raise

    @staticmethod
    async def _create_sample_data():
        """Create sample data for development"""
        try:
            logger.info("📊 Creating sample data...")
            
            # Create sample metropolitan areas
            areas_sample = [
                {"area_metropolitana": "Área Metropolitana de Bogotá", "ciudad_nucleo": "Bogotá", "municipio_norm": "BOGOTA"},
                {"area_metropolitana": "Área Metropolitana del Valle de Aburrá", "ciudad_nucleo": "Medellín", "municipio_norm": "MEDELLIN"},
                {"area_metropolitana": "Área Metropolitana de Cali", "ciudad_nucleo": "Cali", "municipio_norm": "CALI"},
                {"area_metropolitana": "Área Metropolitana de Barranquilla", "ciudad_nucleo": "Barranquilla", "municipio_norm": "BARRANQUILLA"},
            ]
            
            for area_data in areas_sample:
                existing = await AreaMetropolitana.get_or_none(municipio_norm=area_data["municipio_norm"])
                if not existing:
                    await AreaMetropolitana.create(**area_data)
            
            # Create sample logistic hubs
            hubs_sample = [
                {"municipio_norm": "BOGOTA", "hub_asignado_norm": "HUB_CENTRO"},
                {"municipio_norm": "MEDELLIN", "hub_asignado_norm": "HUB_ANTIOQUIA"},
                {"municipio_norm": "CALI", "hub_asignado_norm": "HUB_VALLE"},
                {"municipio_norm": "BARRANQUILLA", "hub_asignado_norm": "HUB_ATLANTICO"},
            ]
            
            for hub_data in hubs_sample:
                existing = await HubLogistico.get_or_none(municipio_norm=hub_data["municipio_norm"])
                if not existing:
                    await HubLogistico.create(**hub_data)
            
            # Create sample clients
            clientes_sample = [
                {"email": "cliente1@example.com", "nombre": "Juan", "apellido": "Pérez", "telefono": "+573001234567", "ciudad": "Bogotá", "departamento": "Cundinamarca"},
                {"email": "cliente2@example.com", "nombre": "María", "apellido": "García", "telefono": "+573007654321", "ciudad": "Medellín", "departamento": "Antioquia"},
                {"email": "cliente3@example.com", "nombre": "Carlos", "apellido": "López", "telefono": "+573009876543", "ciudad": "Cali", "departamento": "Valle del Cauca"},
                {"email": "cliente4@example.com", "nombre": "Ana", "apellido": "Martínez", "telefono": "+573005555555", "ciudad": "Barranquilla", "departamento": "Atlántico"},
                {"email": "cliente5@example.com", "nombre": "Luis", "apellido": "Rodríguez", "telefono": "+573006666666", "ciudad": "Bogotá", "departamento": "Cundinamarca"},
            ]
            
            for cliente_data in clientes_sample:
                existing_user = await Usuario.get_or_none(email=cliente_data["email"])
                if not existing_user:
                    # Create user
                    from services.auth_service import AuthService
                    password_hash = AuthService.get_password_hash("cliente123")
                    user = await Usuario.create(
                        email=cliente_data["email"],
                        password_hash=password_hash,
                        nombre=cliente_data["nombre"],
                        apellido=cliente_data["apellido"],
                        telefono=cliente_data["telefono"],
                        rol=RolUsuario.CLIENT,
                        estado=EstadoUsuario.ACTIVO
                    )
                    
                    # Create client
                    await Cliente.create(
                        usuario=user,
                        ciudad=cliente_data["ciudad"],
                        departamento=cliente_data["departamento"]
                    )
            
            # Create sample advisors
            asesores_sample = [
                {
                    "email": "asesor1@teloo.com", 
                    "nombre": "Pedro", "apellido": "Martínez", "telefono": "+573101234567",
                    "ciudad": "Bogotá", "departamento": "Cundinamarca", "punto_venta": "Repuestos Martínez"
                },
                {
                    "email": "asesor2@teloo.com", 
                    "nombre": "Ana", "apellido": "Rodríguez", "telefono": "+573107654321",
                    "ciudad": "Medellín", "departamento": "Antioquia", "punto_venta": "AutoPartes Ana"
                },
                {
                    "email": "asesor3@teloo.com", 
                    "nombre": "Carlos", "apellido": "Gómez", "telefono": "+573108888888",
                    "ciudad": "Cali", "departamento": "Valle del Cauca", "punto_venta": "Repuestos Valle"
                },
                {
                    "email": "asesor4@teloo.com", 
                    "nombre": "Laura", "apellido": "Díaz", "telefono": "+573109999999",
                    "ciudad": "Barranquilla", "departamento": "Atlántico", "punto_venta": "Costa Repuestos"
                },
                {
                    "email": "asesor5@teloo.com", 
                    "nombre": "Miguel", "apellido": "Torres", "telefono": "+573100000000",
                    "ciudad": "Bogotá", "departamento": "Cundinamarca", "punto_venta": "Torres AutoPartes"
                },
            ]
            
            for asesor_data in asesores_sample:
                existing_user = await Usuario.get_or_none(email=asesor_data["email"])
                if not existing_user:
                    # Create user
                    from services.auth_service import AuthService
                    password_hash = AuthService.get_password_hash("asesor123")
                    user = await Usuario.create(
                        email=asesor_data["email"],
                        password_hash=password_hash,
                        nombre=asesor_data["nombre"],
                        apellido=asesor_data["apellido"],
                        telefono=asesor_data["telefono"],
                        rol=RolUsuario.ADVISOR,
                        estado=EstadoUsuario.ACTIVO
                    )
                    
                    # Create advisor
                    await Asesor.create(
                        usuario=user,
                        ciudad=asesor_data["ciudad"],
                        departamento=asesor_data["departamento"],
                        punto_venta=asesor_data["punto_venta"]
                    )
            
            # Create sample PQRs
            clientes = await Cliente.all()
            if clientes:
                pqrs_sample = [
                    {
                        "cliente": clientes[0],
                        "tipo": TipoPQR.QUEJA,
                        "prioridad": PrioridadPQR.MEDIA,
                        "estado": EstadoPQR.ABIERTA,
                        "resumen": "Demora en la entrega del repuesto",
                        "detalle": "El repuesto solicitado no llegó en el tiempo prometido"
                    },
                    {
                        "cliente": clientes[1] if len(clientes) > 1 else clientes[0],
                        "tipo": TipoPQR.PETICION,
                        "prioridad": PrioridadPQR.BAJA,
                        "estado": EstadoPQR.EN_PROCESO,
                        "resumen": "Solicitud de información sobre garantía",
                        "detalle": "Necesito información sobre la garantía de los repuestos"
                    },
                    {
                        "cliente": clientes[2] if len(clientes) > 2 else clientes[0],
                        "tipo": TipoPQR.RECLAMO,
                        "prioridad": PrioridadPQR.ALTA,
                        "estado": EstadoPQR.ABIERTA,
                        "resumen": "Repuesto defectuoso recibido",
                        "detalle": "El repuesto recibido presenta fallas de fabricación"
                    },
                    {
                        "cliente": clientes[3] if len(clientes) > 3 else clientes[0],
                        "tipo": TipoPQR.PETICION,
                        "prioridad": PrioridadPQR.BAJA,
                        "estado": EstadoPQR.CERRADA,
                        "resumen": "Consulta sobre disponibilidad",
                        "detalle": "Consulta sobre disponibilidad de repuestos específicos"
                    },
                    {
                        "cliente": clientes[4] if len(clientes) > 4 else clientes[0],
                        "tipo": TipoPQR.QUEJA,
                        "prioridad": PrioridadPQR.CRITICA,
                        "estado": EstadoPQR.ABIERTA,
                        "resumen": "Problema con facturación",
                        "detalle": "Error en el cobro de la factura, se cobró de más"
                    },
                    {
                        "cliente": clientes[0],
                        "tipo": TipoPQR.RECLAMO,
                        "prioridad": PrioridadPQR.MEDIA,
                        "estado": EstadoPQR.EN_PROCESO,
                        "resumen": "Servicio de instalación deficiente",
                        "detalle": "El técnico no instaló correctamente el repuesto"
                    },
                ]
                
                for pqr_data in pqrs_sample:
                    existing = await PQR.get_or_none(resumen=pqr_data["resumen"])
                    if not existing:
                        await PQR.create(**pqr_data)
            
            logger.info("✅ Sample data created successfully")
            
        except Exception as e:
            logger.error(f"⚠️ Error creating sample data: {e}")