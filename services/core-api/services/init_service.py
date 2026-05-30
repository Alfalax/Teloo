"""
Initialization service for TeLOO V3
Handles automatic database initialization on startup

NOTE: This service ONLY creates essential system data (admin user + config parameters).
      NO sample/test/hardcoded data is created here.
      All business data (clients, advisors, PQRs, etc.) must be created through the application UI.
"""

import logging
import os
from models.user import Usuario
from models.enums import RolUsuario, EstadoUsuario
from models.analytics import ParametroConfig

logger = logging.getLogger(__name__)

class InitService:
    """Service for initializing database with essential system data"""
    
    @staticmethod
    async def initialize_default_data():
        """Initialize database with admin user and configuration parameters only"""
        try:
            logger.info("🚀 Starting database initialization...")
            
            # Initialize admin user
            await InitService._create_admin_user()
            
            # Initialize configuration parameters
            await InitService._create_config_parameters()

            # Import DIVIPOLA geography data if table is empty
            await InitService._import_divipola_if_empty()

            logger.info("✅ Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error during database initialization: {e}")
            logger.warning("⚠️ Service starting despite initialization errors")
    
    @staticmethod
    async def _create_admin_user():
        """Create or update admin user"""
        admin_email = os.getenv("ADMIN_EMAIL", "admin@teloo.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        try:
            existing_admin = await Usuario.get_or_none(email=admin_email)
            
            from services.auth_service import AuthService
            
            if existing_admin:
                password_hash = AuthService.get_password_hash(admin_password)
                existing_admin.password_hash = password_hash
                await existing_admin.save()
                logger.info(f"🔄 Admin user updated: {admin_email}")
            else:
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
    async def _import_divipola_if_empty():
        """Import DIVIPOLA geography data if the municipios table is empty"""
        from pathlib import Path
        try:
            from models.geografia import Municipio
            count = await Municipio.all().count()
            if count > 0:
                logger.info(f"ℹ️ DIVIPOLA already loaded: {count} municipios")
                return

            excel_path = Path("/app/DIVIPOLA_Municipios.xlsx")
            if not excel_path.exists():
                logger.warning("⚠️ DIVIPOLA_Municipios.xlsx not found — skipping geography import")
                return

            logger.info("📂 Importing DIVIPOLA data from Excel...")
            import sys
            sys.path.append("/app")
            from scripts.import_divipola import import_divipola_from_excel
            success = await import_divipola_from_excel(str(excel_path))
            if success:
                logger.info("✅ DIVIPOLA import completed successfully")
            else:
                logger.error("❌ DIVIPOLA import failed")
        except Exception as e:
            logger.error(f"❌ Error importing DIVIPOLA: {e}")