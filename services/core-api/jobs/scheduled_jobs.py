"""
Scheduled Jobs for TeLOO V3
Standalone functions for background processing
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import redis.asyncio as redis

from services.ofertas_service import OfertasService
from services.configuracion_service import ConfiguracionService

logger = logging.getLogger(__name__)


async def procesar_expiracion_ofertas(
    timeout_horas: Optional[int] = None,
    redis_client: Optional[redis.Redis] = None
) -> Dict[str, Any]:
    """
    Función principal para procesar expiración de ofertas
    Marca ofertas como EXPIRADA después del timeout configurado
    
    Args:
        timeout_horas: Horas después de las cuales las ofertas expiran (opcional)
        redis_client: Cliente Redis para eventos (opcional)
        
    Returns:
        Dict con resultado del procesamiento
    """
    try:
        logger.info("Iniciando proceso de expiración de ofertas")
        
        # Get timeout from configuration if not provided
        if timeout_horas is None:
            config = await ConfiguracionService.get_config('parametros_generales')
            timeout_horas = config.get('timeout_ofertas_horas', 20)
        
        # Process expiration using the service
        result = await OfertasService.marcar_ofertas_expiradas(
            horas_expiracion=timeout_horas,
            redis_client=redis_client
        )
        
        # Log results
        if result['ofertas_expiradas'] > 0:
            logger.info(f"Proceso completado: {result['ofertas_expiradas']} ofertas marcadas como expiradas")
        else:
            logger.debug("Proceso completado: no hay ofertas para expirar")
        
        # Publish system event if Redis client available
        if redis_client:
            try:
                event_data = {
                    'tipo_evento': 'sistema.expiracion_procesada',
                    'ofertas_expiradas': result['ofertas_expiradas'],
                    'timeout_horas': timeout_horas,
                    'timestamp': datetime.now().isoformat()
                }
                
                await redis_client.publish(
                    'sistema.expiracion_procesada',
                    str(event_data).replace("'", '"')
                )
                
            except Exception as e:
                logger.error(f"Error publicando evento de expiración: {e}")
        
        return {
            'success': True,
            'ofertas_procesadas': result['ofertas_expiradas'],
            'timeout_horas': timeout_horas,
            'timestamp': datetime.now().isoformat(),
            'message': f'Proceso completado: {result["ofertas_expiradas"]} ofertas expiradas'
        }
        
    except Exception as e:
        logger.error(f"Error en proceso de expiración de ofertas: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'message': 'Error procesando expiración de ofertas'
        }


async def enviar_notificaciones_expiracion(
    redis_client: Optional[redis.Redis] = None
) -> Dict[str, Any]:
    """
    Envía notificaciones de advertencia antes de que las ofertas expiren
    
    Args:
        redis_client: Cliente Redis para enviar notificaciones
        
    Returns:
        Dict con resultado del procesamiento
    """
    try:
        logger.debug("Verificando ofertas próximas a expirar para notificaciones")
        
        # Get configuration
        config = await ConfiguracionService.get_config('parametros_generales')
        timeout_horas = config.get('timeout_ofertas_horas', 20)
        advertencia_horas = config.get('notificacion_expiracion_horas_antes', 2)
        
        # Calculate warning cutoff time
        warning_cutoff = datetime.now() - timedelta(hours=timeout_horas - advertencia_horas)
        expiration_cutoff = datetime.now() - timedelta(hours=timeout_horas)
        
        # Import models
        from models.oferta import Oferta
        from models.enums import EstadoOferta
        
        # Find offers that need warning
        ofertas_advertencia = await Oferta.filter(
            estado=EstadoOferta.ENVIADA,
            created_at__lt=warning_cutoff,
            created_at__gte=expiration_cutoff
        ).prefetch_related('solicitud__cliente__usuario', 'asesor__usuario')
        
        notifications_sent = 0
        
        for oferta in ofertas_advertencia:
            try:
                # Check if warning already sent (using Redis to track)
                if redis_client:
                    warning_key = f"warning_sent:{oferta.id}"
                    if await redis_client.exists(warning_key):
                        continue
                
                # Calculate time remaining
                time_remaining = timedelta(hours=timeout_horas) - (datetime.now() - oferta.created_at)
                hours_remaining = max(0, int(time_remaining.total_seconds() / 3600))
                
                # Send warning notification
                await _enviar_notificacion_individual(oferta, hours_remaining, redis_client)
                
                # Mark warning as sent (expires in 24 hours)
                if redis_client:
                    await redis_client.setex(warning_key, 86400, "sent")
                
                notifications_sent += 1
                
            except Exception as e:
                logger.error(f"Error enviando advertencia para oferta {oferta.id}: {e}")
        
        if notifications_sent > 0:
            logger.info(f"Notificaciones de expiración enviadas: {notifications_sent}")
        
        return {
            'success': True,
            'notificaciones_enviadas': notifications_sent,
            'advertencia_horas': advertencia_horas,
            'timestamp': datetime.now().isoformat(),
            'message': f'Notificaciones enviadas: {notifications_sent}'
        }
        
    except Exception as e:
        logger.error(f"Error en proceso de notificaciones de expiración: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'message': 'Error enviando notificaciones de expiración'
        }


async def _enviar_notificacion_individual(
    oferta,
    hours_remaining: int,
    redis_client: Optional[redis.Redis]
):
    """
    Envía notificación individual de expiración
    
    Args:
        oferta: Instancia de Oferta
        hours_remaining: Horas restantes antes de expiración
        redis_client: Cliente Redis para publicar eventos
    """
    try:
        # Prepare notification data for Agent IA
        notification_data = {
            'tipo_evento': 'oferta.expiracion_warning',
            'oferta_id': str(oferta.id),
            'solicitud_id': str(oferta.solicitud.id),
            'cliente_telefono': oferta.solicitud.cliente.usuario.telefono,
            'cliente_nombre': oferta.solicitud.cliente.usuario.nombre_completo,
            'hours_remaining': hours_remaining,
            'codigo_oferta': oferta.codigo_oferta,
            'monto_total': float(oferta.monto_total),
            'asesor_nombre': oferta.asesor.usuario.nombre_completo,
            'timestamp': datetime.now().isoformat()
        }
        
        # Publish to Redis for Agent IA to process
        if redis_client:
            await redis_client.publish(
                'oferta.expiracion_warning',
                str(notification_data).replace("'", '"')
            )
        
        logger.debug(f"Notificación de expiración enviada para oferta {oferta.codigo_oferta}")
        
    except Exception as e:
        logger.error(f"Error enviando notificación individual: {e}")
        raise


async def limpiar_datos_temporales() -> Dict[str, Any]:
    """
    Limpia datos temporales y claves expiradas
    
    Returns:
        Dict con resultado de la limpieza
    """
    try:
        logger.info("Iniciando limpieza de datos temporales")
        
        # This could include:
        # - Cleaning expired Redis keys
        # - Removing old audit logs
        # - Cleaning temporary files
        # - Removing old notifications
        
        cleaned_items = 0
        
        # Example: Clean old audit logs (older than configured days)
        try:
            from models.analytics import LogAuditoria
            config = await ConfiguracionService.get_config('parametros_generales')
            vigencia_dias = config.get('vigencia_auditoria_dias', 30)
            
            cutoff_date = datetime.now() - timedelta(days=vigencia_dias)
            
            # Count old logs
            old_logs = await LogAuditoria.filter(created_at__lt=cutoff_date)
            old_count = len(old_logs)
            
            # Delete old logs
            if old_count > 0:
                await LogAuditoria.filter(created_at__lt=cutoff_date).delete()
                cleaned_items += old_count
                logger.info(f"Eliminados {old_count} logs de auditoría antiguos")
            
        except Exception as e:
            logger.error(f"Error limpiando logs de auditoría: {e}")
        
        return {
            'success': True,
            'items_eliminados': cleaned_items,
            'timestamp': datetime.now().isoformat(),
            'message': f'Limpieza completada: {cleaned_items} elementos eliminados'
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza de datos temporales: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'message': 'Error en limpieza de datos temporales'
        }


# Convenience function for manual execution
async def ejecutar_job_manual(job_name: str, **kwargs) -> Dict[str, Any]:
    """
    Ejecuta un job específico manualmente
    
    Args:
        job_name: Nombre del job a ejecutar
        **kwargs: Argumentos adicionales para el job
        
    Returns:
        Dict con resultado de la ejecución
    """
    try:
        if job_name == 'procesar_expiracion_ofertas':
            return await procesar_expiracion_ofertas(**kwargs)
        elif job_name == 'enviar_notificaciones_expiracion':
            return await enviar_notificaciones_expiracion(**kwargs)
        elif job_name == 'limpiar_datos_temporales':
            return await limpiar_datos_temporales()
        else:
            raise ValueError(f"Job desconocido: {job_name}")
            
    except Exception as e:
        logger.error(f"Error ejecutando job {job_name}: {e}")
        return {
            'success': False,
            'job_name': job_name,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }