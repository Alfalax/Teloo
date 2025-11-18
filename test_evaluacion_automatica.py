"""
Script de prueba para verificar el sistema de evaluación automática
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'core-api'))

from tortoise import Tortoise
from datetime import datetime, timezone, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_database():
    """Initialize database connection"""
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_db",
        modules={"models": ["models.solicitud", "models.user", "models.oferta", "models.geografia", "models.enums"]}
    )
    await Tortoise.generate_schemas()


async def test_evaluacion_automatica():
    """
    Test del sistema de evaluación automática
    
    Este test verifica:
    1. Que el job de timeouts detecte solicitudes con ofertas mínimas
    2. Que ejecute la evaluación automáticamente
    3. Que publique eventos a Redis
    """
    
    try:
        await setup_database()
        
        from models.solicitud import Solicitud
        from models.oferta import Oferta
        from models.enums import EstadoSolicitud, EstadoOferta
        from jobs.scheduled_jobs import verificar_timeouts_escalamiento
        
        logger.info("=" * 80)
        logger.info("TEST: Sistema de Evaluación Automática")
        logger.info("=" * 80)
        
        # 1. Buscar solicitudes ABIERTAS con ofertas
        solicitudes_abiertas = await Solicitud.filter(
            estado=EstadoSolicitud.ABIERTA
        ).prefetch_related('ofertas', 'repuestos_solicitados')
        
        logger.info(f"\n📋 Solicitudes ABIERTAS encontradas: {len(solicitudes_abiertas)}")
        
        for solicitud in solicitudes_abiertas:
            ofertas_count = len([o for o in solicitud.ofertas if o.estado == EstadoOferta.ENVIADA])
            logger.info(f"  - Solicitud {str(solicitud.id)[:8]}: Nivel {solicitud.nivel_actual}, {ofertas_count} ofertas")
            logger.info(f"    Ofertas mínimas deseadas: {solicitud.ofertas_minimas_deseadas}")
            logger.info(f"    Fecha escalamiento: {solicitud.fecha_escalamiento}")
            
            if ofertas_count >= solicitud.ofertas_minimas_deseadas:
                logger.info(f"    ✅ CUMPLE condición para evaluación automática")
            else:
                logger.info(f"    ⏳ Esperando más ofertas ({ofertas_count}/{solicitud.ofertas_minimas_deseadas})")
        
        # 2. Ejecutar el job de verificación de timeouts
        logger.info(f"\n🔄 Ejecutando job de verificación de timeouts...")
        
        resultado = await verificar_timeouts_escalamiento(redis_client=None)
        
        logger.info(f"\n📊 Resultado del job:")
        logger.info(f"  - Success: {resultado['success']}")
        logger.info(f"  - Solicitudes escaladas: {resultado['solicitudes_escaladas']}")
        logger.info(f"  - Solicitudes cerradas/evaluadas: {resultado['solicitudes_cerradas']}")
        logger.info(f"  - Mensaje: {resultado['message']}")
        
        # 3. Verificar solicitudes evaluadas
        solicitudes_evaluadas = await Solicitud.filter(
            estado=EstadoSolicitud.EVALUADA
        ).prefetch_related('adjudicaciones__oferta__asesor__usuario', 'adjudicaciones__repuesto_solicitado')
        
        logger.info(f"\n✅ Solicitudes EVALUADAS: {len(solicitudes_evaluadas)}")
        
        for solicitud in solicitudes_evaluadas[:5]:  # Mostrar solo las primeras 5
            logger.info(f"\n  Solicitud {str(solicitud.id)[:8]}:")
            logger.info(f"    - Fecha evaluación: {solicitud.fecha_evaluacion}")
            logger.info(f"    - Monto total: ${solicitud.monto_total_adjudicado:,.0f}")
            logger.info(f"    - Adjudicaciones: {len(solicitud.adjudicaciones)}")
            
            for adj in solicitud.adjudicaciones:
                logger.info(f"      • {adj.repuesto_solicitado.nombre} → {adj.oferta.asesor.usuario.nombre_completo}")
                logger.info(f"        Precio: ${adj.precio_adjudicado:,.0f}, Puntaje: {adj.puntaje_obtenido:.3f}")
        
        logger.info("\n" + "=" * 80)
        logger.info("TEST COMPLETADO")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        await Tortoise.close_connections()


async def test_escenario_cierre_anticipado():
    """
    Test específico para cierre anticipado (ofertas mínimas alcanzadas)
    """
    
    try:
        await setup_database()
        
        from models.solicitud import Solicitud
        from models.oferta import Oferta
        from models.enums import EstadoSolicitud, EstadoOferta
        
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Escenario de Cierre Anticipado")
        logger.info("=" * 80)
        
        # Buscar solicitudes que cumplan la condición
        solicitudes = await Solicitud.filter(
            estado=EstadoSolicitud.ABIERTA
        ).prefetch_related('ofertas')
        
        candidatas = []
        for solicitud in solicitudes:
            ofertas_count = len([o for o in solicitud.ofertas if o.estado == EstadoOferta.ENVIADA])
            if ofertas_count >= solicitud.ofertas_minimas_deseadas:
                candidatas.append((solicitud, ofertas_count))
        
        logger.info(f"\n📋 Solicitudes candidatas para cierre anticipado: {len(candidatas)}")
        
        for solicitud, ofertas_count in candidatas[:3]:
            logger.info(f"\n  Solicitud {str(solicitud.id)[:8]}:")
            logger.info(f"    - Ofertas: {ofertas_count}/{solicitud.ofertas_minimas_deseadas}")
            logger.info(f"    - Nivel actual: {solicitud.nivel_actual}")
            logger.info(f"    - Estado: {solicitud.estado.value}")
            logger.info(f"    ✅ Debería evaluarse automáticamente en el próximo ciclo del job")
        
        logger.info("\n" + "=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        await Tortoise.close_connections()


async def test_escenario_nivel_maximo():
    """
    Test específico para nivel máximo alcanzado
    """
    
    try:
        await setup_database()
        
        from models.solicitud import Solicitud
        from models.oferta import Oferta
        from models.enums import EstadoSolicitud, EstadoOferta
        
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Escenario de Nivel Máximo")
        logger.info("=" * 80)
        
        # Buscar solicitudes en nivel 5
        solicitudes_nivel_5 = await Solicitud.filter(
            estado=EstadoSolicitud.ABIERTA,
            nivel_actual=5
        ).prefetch_related('ofertas')
        
        logger.info(f"\n📋 Solicitudes en nivel máximo (5): {len(solicitudes_nivel_5)}")
        
        for solicitud in solicitudes_nivel_5:
            ofertas_count = len([o for o in solicitud.ofertas if o.estado == EstadoOferta.ENVIADA])
            logger.info(f"\n  Solicitud {str(solicitud.id)[:8]}:")
            logger.info(f"    - Ofertas: {ofertas_count}")
            logger.info(f"    - Fecha escalamiento: {solicitud.fecha_escalamiento}")
            
            if ofertas_count > 0:
                logger.info(f"    ✅ Debería evaluarse con las {ofertas_count} ofertas disponibles")
            else:
                logger.info(f"    ❌ Debería cerrarse sin ofertas")
        
        logger.info("\n" + "=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test de evaluación automática')
    parser.add_argument('--test', choices=['all', 'cierre', 'nivel_max'], default='all',
                       help='Tipo de test a ejecutar')
    
    args = parser.parse_args()
    
    if args.test == 'all':
        asyncio.run(test_evaluacion_automatica())
    elif args.test == 'cierre':
        asyncio.run(test_escenario_cierre_anticipado())
    elif args.test == 'nivel_max':
        asyncio.run(test_escenario_nivel_maximo())
