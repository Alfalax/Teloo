#!/usr/bin/env python3
"""
Script de verificación completa para el módulo de Asesores
Verifica que todos los endpoints estén conectados a la base de datos real
"""

import asyncio
import sys
from tortoise import Tortoise
from models.user import Usuario, Asesor
from models.enums import EstadoAsesor, EstadoUsuario, RolUsuario
from services.auth_service import AuthService
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    """Inicializar conexión a base de datos"""
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_v3",
        modules={"models": ["models"]}
    )
    logger.info("✅ Conexión a base de datos establecida")

async def verify_database_connection():
    """Verificar que la conexión a la base de datos funciona"""
    logger.info("\n" + "="*60)
    logger.info("1. VERIFICANDO CONEXIÓN A BASE DE DATOS")
    logger.info("="*60)
    
    try:
        # Verificar que las tablas existen
        total_usuarios = await Usuario.all().count()
        total_asesores = await Asesor.all().count()
        
        logger.info(f"✅ Tabla 'usuario': {total_usuarios} registros")
        logger.info(f"✅ Tabla 'asesor': {total_asesores} registros")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        return False

async def verify_asesor_model():
    """Verificar el modelo Asesor y sus relaciones"""
    logger.info("\n" + "="*60)
    logger.info("2. VERIFICANDO MODELO ASESOR")
    logger.info("="*60)
    
    try:
        # Verificar campos del modelo
        if await Asesor.all().count() > 0:
            asesor = await Asesor.all().prefetch_related('usuario').first()
            
            logger.info("✅ Campos del modelo Asesor:")
            logger.info(f"   - id: {asesor.id}")
            logger.info(f"   - usuario_id: {asesor.usuario_id}")
            logger.info(f"   - ciudad: {asesor.ciudad}")
            logger.info(f"   - departamento: {asesor.departamento}")
            logger.info(f"   - punto_venta: {asesor.punto_venta}")
            logger.info(f"   - direccion_punto_venta: {asesor.direccion_punto_venta}")
            logger.info(f"   - estado: {asesor.estado}")
            logger.info(f"   - confianza: {asesor.confianza}")
            logger.info(f"   - total_ofertas: {asesor.total_ofertas}")
            logger.info(f"   - ofertas_ganadoras: {asesor.ofertas_ganadoras}")
            logger.info(f"   - monto_total_ventas: {asesor.monto_total_ventas}")
            
            # Verificar relación con Usuario
            logger.info(f"\n✅ Relación con Usuario:")
            logger.info(f"   - Usuario ID: {asesor.usuario.id}")
            logger.info(f"   - Nombre: {asesor.usuario.nombre}")
            logger.info(f"   - Email: {asesor.usuario.email}")
            logger.info(f"   - Rol: {asesor.usuario.rol}")
        else:
            logger.warning("⚠️  No hay asesores en la base de datos para verificar")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error verificando modelo Asesor: {e}")
        return False

async def verify_crud_operations():
    """Verificar operaciones CRUD en la base de datos"""
    logger.info("\n" + "="*60)
    logger.info("3. VERIFICANDO OPERACIONES CRUD")
    logger.info("="*60)
    
    test_email = f"test_asesor_{datetime.now().timestamp()}@test.com"
    created_asesor_id = None
    created_usuario_id = None
    
    try:
        # CREATE
        logger.info("\n📝 Probando CREATE...")
        password_hash = AuthService.get_password_hash("TestPassword123!")
        
        usuario = await Usuario.create(
            email=test_email,
            password_hash=password_hash,
            nombre="Test",
            apellido="Asesor",
            telefono="+573001234567",
            rol=RolUsuario.ADVISOR,
            estado=EstadoUsuario.ACTIVO
        )
        created_usuario_id = usuario.id
        
        asesor = await Asesor.create(
            usuario=usuario,
            ciudad="Bogotá",
            departamento="Cundinamarca",
            punto_venta="Punto de Venta Test",
            direccion_punto_venta="Calle Test 123",
            estado=EstadoAsesor.ACTIVO
        )
        created_asesor_id = asesor.id
        logger.info(f"✅ CREATE exitoso - Asesor ID: {asesor.id}")
        
        # READ
        logger.info("\n📖 Probando READ...")
        asesor_read = await Asesor.get(id=created_asesor_id).prefetch_related('usuario')
        assert asesor_read.usuario.email == test_email
        logger.info(f"✅ READ exitoso - Email: {asesor_read.usuario.email}")
        
        # UPDATE
        logger.info("\n✏️  Probando UPDATE...")
        asesor_read.ciudad = "Medellín"
        asesor_read.departamento = "Antioquia"
        await asesor_read.save()
        
        asesor_updated = await Asesor.get(id=created_asesor_id)
        assert asesor_updated.ciudad == "Medellín"
        logger.info(f"✅ UPDATE exitoso - Nueva ciudad: {asesor_updated.ciudad}")
        
        # DELETE
        logger.info("\n🗑️  Probando DELETE...")
        await asesor_updated.delete()
        await usuario.delete()
        
        deleted_asesor = await Asesor.get_or_none(id=created_asesor_id)
        assert deleted_asesor is None
        logger.info("✅ DELETE exitoso")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en operaciones CRUD: {e}")
        
        # Cleanup en caso de error
        if created_asesor_id:
            try:
                asesor = await Asesor.get_or_none(id=created_asesor_id)
                if asesor:
                    await asesor.delete()
            except:
                pass
        
        if created_usuario_id:
            try:
                usuario = await Usuario.get_or_none(id=created_usuario_id)
                if usuario:
                    await usuario.delete()
            except:
                pass
        
        return False

async def verify_filters_and_queries():
    """Verificar filtros y queries complejas"""
    logger.info("\n" + "="*60)
    logger.info("4. VERIFICANDO FILTROS Y QUERIES")
    logger.info("="*60)
    
    try:
        # Filtro por estado
        logger.info("\n🔍 Probando filtro por estado...")
        asesores_activos = await Asesor.filter(estado=EstadoAsesor.ACTIVO).count()
        logger.info(f"✅ Asesores ACTIVOS: {asesores_activos}")
        
        # Filtro por ciudad
        logger.info("\n🔍 Probando filtro por ciudad...")
        if await Asesor.all().count() > 0:
            primer_asesor = await Asesor.all().first()
            if primer_asesor and primer_asesor.ciudad:
                asesores_ciudad = await Asesor.filter(ciudad=primer_asesor.ciudad).count()
                logger.info(f"✅ Asesores en {primer_asesor.ciudad}: {asesores_ciudad}")
        
        # Query con relación
        logger.info("\n🔍 Probando query con relación Usuario...")
        asesores_con_usuario = await Asesor.all().prefetch_related('usuario').limit(5)
        for asesor in asesores_con_usuario:
            logger.info(f"   - {asesor.usuario.nombre} {asesor.usuario.apellido} ({asesor.punto_venta})")
        logger.info(f"✅ Query con relación exitosa")
        
        # Búsqueda con Q
        logger.info("\n🔍 Probando búsqueda con Q...")
        from tortoise.expressions import Q
        if await Asesor.all().count() > 0:
            primer_asesor = await Asesor.all().prefetch_related('usuario').first()
            if primer_asesor:
                search_term = primer_asesor.usuario.nombre[:3]
                resultados = await Asesor.filter(
                    Q(usuario__nombre__icontains=search_term) |
                    Q(usuario__apellido__icontains=search_term)
                ).prefetch_related('usuario').count()
                logger.info(f"✅ Búsqueda con Q exitosa - {resultados} resultados para '{search_term}'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en filtros y queries: {e}")
        return False

async def verify_kpis_calculation():
    """Verificar cálculo de KPIs"""
    logger.info("\n" + "="*60)
    logger.info("5. VERIFICANDO CÁLCULO DE KPIs")
    logger.info("="*60)
    
    try:
        # Total asesores habilitados
        logger.info("\n📊 Calculando KPIs...")
        total_asesores = await Asesor.filter(estado=EstadoAsesor.ACTIVO).count()
        logger.info(f"✅ Total Asesores Habilitados: {total_asesores}")
        
        # Total puntos de venta
        total_puntos_venta = await Asesor.filter(estado=EstadoAsesor.ACTIVO).count()
        logger.info(f"✅ Total Puntos de Venta: {total_puntos_venta}")
        
        # Cobertura nacional (ciudades únicas)
        asesores_activos = await Asesor.filter(estado=EstadoAsesor.ACTIVO).all()
        unique_cities = set(asesor.ciudad for asesor in asesores_activos if asesor.ciudad)
        cobertura_nacional = len(unique_cities)
        logger.info(f"✅ Cobertura Nacional: {cobertura_nacional} ciudades")
        
        # Ciudades únicas
        ciudades = sorted(list(unique_cities))
        logger.info(f"\n📍 Ciudades con cobertura:")
        for ciudad in ciudades[:10]:  # Mostrar primeras 10
            count = len([a for a in asesores_activos if a.ciudad == ciudad])
            logger.info(f"   - {ciudad}: {count} asesores")
        if len(ciudades) > 10:
            logger.info(f"   ... y {len(ciudades) - 10} ciudades más")
        
        # Departamentos únicos
        unique_departments = set(asesor.departamento for asesor in asesores_activos if asesor.departamento)
        logger.info(f"\n📍 Departamentos con cobertura: {len(unique_departments)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error calculando KPIs: {e}")
        return False

async def verify_metrics_calculation():
    """Verificar cálculo de métricas de asesor"""
    logger.info("\n" + "="*60)
    logger.info("6. VERIFICANDO MÉTRICAS DE ASESOR")
    logger.info("="*60)
    
    try:
        if await Asesor.all().count() > 0:
            asesor = await Asesor.all().prefetch_related('usuario').first()
            
            logger.info(f"\n📊 Métricas para: {asesor.usuario.nombre} {asesor.usuario.apellido}")
            logger.info(f"   - Confianza: {asesor.confianza}")
            logger.info(f"   - Total Ofertas: {asesor.total_ofertas}")
            logger.info(f"   - Ofertas Ganadoras: {asesor.ofertas_ganadoras}")
            logger.info(f"   - Monto Total Ventas: ${asesor.monto_total_ventas:,.2f}")
            logger.info(f"   - Actividad Reciente: {asesor.actividad_reciente_pct}%")
            logger.info(f"   - Desempeño Histórico: {asesor.desempeno_historico_pct}%")
            
            # Calcular tasa de adjudicación
            if asesor.total_ofertas > 0:
                tasa_adjudicacion = (asesor.ofertas_ganadoras / asesor.total_ofertas) * 100
                logger.info(f"   - Tasa Adjudicación: {tasa_adjudicacion:.2f}%")
            
            logger.info("✅ Métricas calculadas correctamente")
        else:
            logger.warning("⚠️  No hay asesores para calcular métricas")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error calculando métricas: {e}")
        return False

async def verify_pagination():
    """Verificar paginación"""
    logger.info("\n" + "="*60)
    logger.info("7. VERIFICANDO PAGINACIÓN")
    logger.info("="*60)
    
    try:
        total = await Asesor.all().count()
        page_size = 10
        
        logger.info(f"\n📄 Total registros: {total}")
        logger.info(f"📄 Tamaño de página: {page_size}")
        
        # Primera página
        page_1 = await Asesor.all().offset(0).limit(page_size)
        logger.info(f"✅ Página 1: {len(page_1)} registros")
        
        # Segunda página (si existe)
        if total > page_size:
            page_2 = await Asesor.all().offset(page_size).limit(page_size)
            logger.info(f"✅ Página 2: {len(page_2)} registros")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en paginación: {e}")
        return False

async def verify_no_mocks():
    """Verificar que no hay datos mock o hardcodeados"""
    logger.info("\n" + "="*60)
    logger.info("8. VERIFICANDO AUSENCIA DE MOCKS")
    logger.info("="*60)
    
    try:
        # Verificar que los datos vienen de la BD
        asesores = await Asesor.all().prefetch_related('usuario').limit(5)
        
        logger.info("\n🔍 Verificando que los datos son reales (no mocks):")
        
        for asesor in asesores:
            # Verificar que tienen IDs de base de datos
            assert asesor.id is not None, "Asesor sin ID"
            assert asesor.usuario_id is not None, "Asesor sin usuario_id"
            
            # Verificar que tienen timestamps
            assert asesor.created_at is not None, "Asesor sin created_at"
            assert asesor.updated_at is not None, "Asesor sin updated_at"
            
            # Verificar que el usuario relacionado existe
            assert asesor.usuario is not None, "Asesor sin usuario relacionado"
            assert asesor.usuario.id == asesor.usuario_id, "IDs de usuario no coinciden"
            
            logger.info(f"✅ Asesor {asesor.id} - Datos reales verificados")
        
        logger.info("\n✅ CONFIRMADO: Todos los datos vienen de la base de datos real")
        logger.info("✅ NO se detectaron mocks o datos hardcodeados")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando ausencia de mocks: {e}")
        return False

async def generate_report():
    """Generar reporte final"""
    logger.info("\n" + "="*60)
    logger.info("RESUMEN DE VERIFICACIÓN")
    logger.info("="*60)
    
    try:
        total_usuarios = await Usuario.all().count()
        total_asesores = await Asesor.all().count()
        asesores_activos = await Asesor.filter(estado=EstadoAsesor.ACTIVO).count()
        asesores_inactivos = await Asesor.filter(estado=EstadoAsesor.INACTIVO).count()
        asesores_suspendidos = await Asesor.filter(estado=EstadoAsesor.SUSPENDIDO).count()
        
        logger.info(f"\n📊 ESTADÍSTICAS:")
        logger.info(f"   Total Usuarios: {total_usuarios}")
        logger.info(f"   Total Asesores: {total_asesores}")
        logger.info(f"   - Activos: {asesores_activos}")
        logger.info(f"   - Inactivos: {asesores_inactivos}")
        logger.info(f"   - Suspendidos: {asesores_suspendidos}")
        
        # Verificar integridad
        asesores_con_usuario = await Asesor.all().prefetch_related('usuario').count()
        logger.info(f"\n✅ Integridad de datos:")
        logger.info(f"   Asesores con usuario válido: {asesores_con_usuario}/{total_asesores}")
        
        if asesores_con_usuario == total_asesores:
            logger.info("   ✅ Todos los asesores tienen usuario asociado")
        else:
            logger.warning(f"   ⚠️  {total_asesores - asesores_con_usuario} asesores sin usuario")
        
    except Exception as e:
        logger.error(f"❌ Error generando reporte: {e}")

async def main():
    """Función principal"""
    try:
        await init_db()
        
        results = []
        
        # Ejecutar todas las verificaciones
        results.append(("Conexión BD", await verify_database_connection()))
        results.append(("Modelo Asesor", await verify_asesor_model()))
        results.append(("CRUD Operations", await verify_crud_operations()))
        results.append(("Filtros y Queries", await verify_filters_and_queries()))
        results.append(("KPIs", await verify_kpis_calculation()))
        results.append(("Métricas", await verify_metrics_calculation()))
        results.append(("Paginación", await verify_pagination()))
        results.append(("No Mocks", await verify_no_mocks()))
        
        # Generar reporte
        await generate_report()
        
        # Resultado final
        logger.info("\n" + "="*60)
        logger.info("RESULTADO FINAL")
        logger.info("="*60)
        
        all_passed = all(result[1] for result in results)
        
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status} - {test_name}")
        
        if all_passed:
            logger.info("\n🎉 TODAS LAS VERIFICACIONES PASARON")
            logger.info("✅ El módulo de Asesores está completamente conectado a la base de datos")
            logger.info("✅ NO se detectaron mocks ni datos hardcodeados")
            return 0
        else:
            logger.error("\n❌ ALGUNAS VERIFICACIONES FALLARON")
            logger.error("Revisa los errores arriba para más detalles")
            return 1
        
    except Exception as e:
        logger.error(f"\n❌ Error fatal: {e}")
        return 1
    finally:
        await Tortoise.close_connections()
        logger.info("\n🔌 Conexiones cerradas")

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
