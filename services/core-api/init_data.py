#!/usr/bin/env python3
"""
Script de inicialización de datos para TeLOO V3
Crea usuario administrador y datos iniciales necesarios
"""

import asyncio
import os
from tortoise import Tortoise
from models.user import Usuario, Cliente, Asesor
from models.enums import RolUsuario, EstadoUsuario, TipoPQR, PrioridadPQR, EstadoPQR
from models.analytics import ParametroConfig, PQR
from models.geografia import AreaMetropolitana, HubLogistico
from services.auth_service import AuthService

async def init_database_data():
    """Inicializa datos básicos en la base de datos"""
    
    # Configurar conexión
    DATABASE_URL = os.getenv("DATABASE_URL", "postgres://teloo_user:teloo_password@localhost:5432/teloo_v3")
    
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={'models': [
            'models.user', 
            'models.solicitud', 
            'models.oferta', 
            'models.geografia', 
            'models.analytics'
        ]}
    )
    
    try:
        print("🚀 Inicializando datos de TeLOO V3...")
        
        # 1. Crear usuario administrador
        admin_email = "admin@teloo.com"
        admin_password = "admin123"
        
        existing_admin = await Usuario.get_or_none(email=admin_email)
        if existing_admin:
            print(f"🔄 Actualizando usuario admin existente: {admin_email}")
            # Actualizar con nuevo hash
            password_hash = AuthService.get_password_hash(admin_password)
            existing_admin.password_hash = password_hash
            await existing_admin.save()
            print(f"✅ Usuario admin actualizado con nueva contraseña")
        else:
            password_hash = AuthService.get_password_hash(admin_password)
            
            admin_user = await Usuario.create(
                email=admin_email,
                password_hash=password_hash,
                nombre="Administrador",
                apellido="TeLOO",
                telefono="+573001234567",
                rol=RolUsuario.ADMIN,
                estado=EstadoUsuario.ACTIVO
            )
            
            print(f"✅ Usuario administrador creado: {admin_email}")
            print(f"   Contraseña: {admin_password}")
        
        # 2. Crear parámetros de configuración por defecto
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
        
        for clave, valor in config_params.items():
            existing_param = await ParametroConfig.get_or_none(clave=clave)
            if not existing_param:
                await ParametroConfig.create(
                    clave=clave,
                    valor_json=valor
                )
                print(f"✅ Parámetro creado: {clave}")
            else:
                print(f"✅ Parámetro ya existe: {clave}")
        
        # 3. Crear datos de prueba para desarrollo
        await create_sample_data()
        
        print("🎉 Inicialización completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await Tortoise.close_connections()

async def create_sample_data():
    """Crear datos de prueba para desarrollo"""
    try:
        print("📊 Creando datos de prueba...")
        
        # Crear algunas áreas metropolitanas de ejemplo
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
        
        # Crear algunos hubs logísticos de ejemplo
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
        
        # Crear algunos clientes de ejemplo
        from models.user import Cliente
        clientes_sample = [
            {"email": "cliente1@example.com", "nombre": "Juan", "apellido": "Pérez", "telefono": "+573001234567", "ciudad": "Bogotá", "departamento": "Cundinamarca"},
            {"email": "cliente2@example.com", "nombre": "María", "apellido": "García", "telefono": "+573007654321", "ciudad": "Medellín", "departamento": "Antioquia"},
            {"email": "cliente3@example.com", "nombre": "Carlos", "apellido": "López", "telefono": "+573009876543", "ciudad": "Cali", "departamento": "Valle del Cauca"},
        ]
        
        for cliente_data in clientes_sample:
            existing_user = await Usuario.get_or_none(email=cliente_data["email"])
            if not existing_user:
                # Crear usuario cliente
                user = await Usuario.create(
                    email=cliente_data["email"],
                    password_hash=AuthService.get_password_hash("cliente123"),
                    nombre=cliente_data["nombre"],
                    apellido=cliente_data["apellido"],
                    telefono=cliente_data["telefono"],
                    rol=RolUsuario.CLIENT,
                    estado=EstadoUsuario.ACTIVO
                )
                
                # Crear cliente
                await Cliente.create(
                    usuario=user,
                    ciudad=cliente_data["ciudad"],
                    departamento=cliente_data["departamento"]
                )
        
        # Crear algunos asesores de ejemplo
        from models.user import Asesor
        asesores_sample = [
            {
                "email": "asesor1@teloo.com", "password_hash": AuthService.get_password_hash("asesor123"),
                "nombre": "Pedro", "apellido": "Martínez", "telefono": "+573101234567",
                "rol": RolUsuario.ADVISOR, "estado": EstadoUsuario.ACTIVO
            },
            {
                "email": "asesor2@teloo.com", "password_hash": AuthService.get_password_hash("asesor123"),
                "nombre": "Ana", "apellido": "Rodríguez", "telefono": "+573107654321",
                "rol": RolUsuario.ADVISOR, "estado": EstadoUsuario.ACTIVO
            },
        ]
        
        for asesor_data in asesores_sample:
            existing_user = await Usuario.get_or_none(email=asesor_data["email"])
            if not existing_user:
                # Crear usuario
                user_data = {k: v for k, v in asesor_data.items() if k not in ["ciudad", "departamento", "punto_venta"]}
                user = await Usuario.create(**user_data)
                
                # Crear asesor
                await Asesor.create(
                    usuario=user,
                    ciudad="Bogotá",
                    departamento="Cundinamarca",
                    punto_venta=f"Repuestos {asesor_data['nombre']}"
                )
        
        # Crear algunas PQRs de ejemplo
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
                    "cliente": clientes[0] if len(clientes) > 0 else clientes[0],
                    "tipo": TipoPQR.PETICION,
                    "prioridad": PrioridadPQR.BAJA,
                    "estado": EstadoPQR.EN_PROCESO,
                    "resumen": "Solicitud de información sobre garantía",
                    "detalle": "Necesito información sobre la garantía de los repuestos"
                },
            ]
            
            for pqr_data in pqrs_sample:
                existing = await PQR.get_or_none(resumen=pqr_data["resumen"])
                if not existing:
                    await PQR.create(**pqr_data)
        
        print("✅ Datos de prueba creados exitosamente")
        
    except Exception as e:
        print(f"⚠️ Error creando datos de prueba: {e}")

if __name__ == "__main__":
    asyncio.run(init_database_data())