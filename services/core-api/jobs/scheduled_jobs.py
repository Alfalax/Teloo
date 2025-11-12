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
        elif job_name == 'verificar_timeouts_escalamiento':
            return await verificar_timeouts_escalamiento(**kwargs)
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


async def verificar_timeouts_escalamiento(
    redis_client: Optional[redis.Redis] = None
) -> Dict[str, Any]:
    """
    Verifica timeouts de escalamiento y ejecuta siguiente oleada si es necesario
    
    Este job se ejecuta cada minuto y verifica:
    1. Si han pasado los minutos configurados desde el último escalamiento
    2. Si no se han alcanzado las ofertas mínimas
    3. Escala al siguiente nivel o cierra la solicitud
    
    Args:
        redis_client: Cliente Redis para eventos (opcional)
        
    Returns:
        Dict con resultado del procesamiento
    """
    try:
        logger.debug("🔍 Verificando timeouts de escalamiento...")
        
        from models.solicitud import Solicitud
        from models.enums import EstadoSolicitud
        from models.oferta import Oferta
        from services.escalamiento_service import EscalamientoService
        
        # Obtener configuración de tiempos por nivel
        config = await ConfiguracionService.get_config('tiempos_espera_nivel')
        
        # Convertir claves de string a int si es necesario
        if config and isinstance(config, dict):
            tiempos_nivel = {int(k): v for k, v in config.items()}
            logger.info(f"⚙️ Tiempos configurados por nivel: {tiempos_nivel}")
        else:
            tiempos_nivel = {
                1: 15,  # minutos (fallback)
                2: 20,
                3: 25,
                4: 30,
                5: 35
            }
            logger.warning(f"⚠️ Usando tiempos por defecto: {tiempos_nivel}")
        
        # Buscar solicitudes ABIERTAS que puedan necesitar escalamiento
        solicitudes_abiertas = await Solicitud.filter(
            estado=EstadoSolicitud.ABIERTA,
            fecha_escalamiento__isnull=False  # Solo las que ya tienen escalamiento inicial
        ).all()
        
        logger.info(f"📋 Encontradas {len(solicitudes_abiertas)} solicitudes abiertas con escalamiento")
        
        solicitudes_escaladas = 0
        solicitudes_cerradas = 0
        
        for solicitud in solicitudes_abiertas:
            try:
                # Calcular tiempo transcurrido desde último escalamiento
                from datetime import timezone
                ahora = datetime.now(timezone.utc)
                tiempo_transcurrido = ahora - solicitud.fecha_escalamiento
                minutos_transcurridos = int(tiempo_transcurrido.total_seconds() / 60)
                
                # Obtener tiempo de espera para el nivel actual
                tiempo_espera_nivel = tiempos_nivel.get(solicitud.nivel_actual, 30)
                
                logger.debug(f"🔍 Solicitud {str(solicitud.id)[:8]}: Nivel {solicitud.nivel_actual}, {minutos_transcurridos} min / {tiempo_espera_nivel} min")
                
                # Verificar si ya pasó el timeout
                if minutos_transcurridos < tiempo_espera_nivel:
                    continue  # Aún no ha expirado el timeout
                
                logger.info(f"⏰ Timeout alcanzado para solicitud {solicitud.id}: {minutos_transcurridos} min >= {tiempo_espera_nivel} min")
                
                # Contar ofertas recibidas
                ofertas_count = await Oferta.filter(solicitud_id=solicitud.id).count()
                
                # Verificar si se alcanzó el mínimo de ofertas (cierre anticipado)
                if ofertas_count >= solicitud.ofertas_minimas_deseadas:
                    logger.info(f"✅ Cierre anticipado: {ofertas_count} ofertas >= {solicitud.ofertas_minimas_deseadas} mínimas")
                    solicitud.estado = EstadoSolicitud.EVALUADA
                    await solicitud.save()
                    solicitudes_cerradas += 1
                    continue
                
                # Verificar si hay siguiente nivel disponible (máximo nivel 5)
                NIVEL_MAXIMO = 5
                
                if solicitud.nivel_actual >= NIVEL_MAXIMO:
                    # Ya está en el nivel máximo, cerrar solicitud sin ofertas
                    logger.warning(f"❌ Solicitud {solicitud.id} en nivel máximo ({NIVEL_MAXIMO}), cerrando sin ofertas")
                    solicitud.estado = EstadoSolicitud.CERRADA_SIN_OFERTAS
                    await solicitud.save()
                    solicitudes_cerradas += 1
                    
                    # Publicar evento
                    if redis_client:
                        try:
                            event_data = {
                                'tipo_evento': 'solicitud.cerrada_sin_ofertas',
                                'solicitud_id': str(solicitud.id),
                                'nivel_final': solicitud.nivel_actual,
                                'ofertas_recibidas': ofertas_count,
                                'timestamp': datetime.now(timezone.utc).isoformat()
                            }
                            await redis_client.publish('solicitud.cerrada_sin_ofertas', str(event_data))
                        except Exception as e:
                            logger.error(f"Error publicando evento: {e}")
                    
                    continue
                
                # Escalar al siguiente nivel
                siguiente_nivel = solicitud.nivel_actual + 1
                logger.info(f"📈 Escalando solicitud {solicitud.id} de Nivel {solicitud.nivel_actual} → Nivel {siguiente_nivel}")
                
                # Verificar si hay asesores disponibles en el siguiente nivel
                from models.user import Asesor
                from models.enums import EstadoUsuario
                
                asesores_disponibles = await Asesor.filter(
                    nivel_actual=siguiente_nivel,
                    estado=EstadoUsuario.ACTIVO
                ).count()
                
                if asesores_disponibles == 0:
                    logger.warning(f"⚠️ No hay asesores en Nivel {siguiente_nivel}")
                    
                    # Si es el nivel máximo, cerrar la solicitud
                    if siguiente_nivel >= NIVEL_MAXIMO:
                        logger.warning(f"❌ Nivel máximo alcanzado sin asesores, cerrando solicitud {solicitud.id}")
                        solicitud.estado = EstadoSolicitud.CERRADA_SIN_OFERTAS
                        solicitud.nivel_actual = siguiente_nivel
                        await solicitud.save()
                        solicitudes_cerradas += 1
                        
                        # Publicar evento
                        if redis_client:
                            try:
                                event_data = {
                                    'tipo_evento': 'solicitud.cerrada_sin_ofertas',
                                    'solicitud_id': str(solicitud.id),
                                    'nivel_final': siguiente_nivel,
                                    'ofertas_recibidas': ofertas_count,
                                    'razon': f'No hay asesores en nivel máximo {siguiente_nivel}',
                                    'timestamp': datetime.now(timezone.utc).isoformat()
                                }
                                await redis_client.publish('solicitud.cerrada_sin_ofertas', str(event_data))
                            except Exception as e:
                                logger.error(f"Error publicando evento: {e}")
                        
                        continue
                    
                    # No es el nivel máximo, escalar inmediatamente sin esperar timeout
                    # (el próximo ciclo del job lo escalará de nuevo si sigue sin asesores)
                    logger.info(f"⏭️ Escalando sin esperar timeout (no hay asesores en nivel {siguiente_nivel})")
                
                # Escalar al siguiente nivel (con o sin asesores)
                logger.info(f"✅ {asesores_disponibles} asesores disponibles en Nivel {siguiente_nivel}" if asesores_disponibles > 0 else f"⏭️ Escalando a Nivel {siguiente_nivel} (sin asesores)")
                solicitud.nivel_actual = siguiente_nivel
                solicitud.fecha_escalamiento = datetime.now(timezone.utc)
                await solicitud.save()
                
                solicitudes_escaladas += 1
                
                # Publicar evento de escalamiento
                if redis_client:
                    try:
                        event_data = {
                            'tipo_evento': 'solicitud.escalada',
                            'solicitud_id': str(solicitud.id),
                            'nivel_anterior': solicitud.nivel_actual - 1,
                            'nivel_nuevo': siguiente_nivel,
                            'ofertas_actuales': ofertas_count,
                            'timestamp': datetime.now().isoformat()
                        }
                        await redis_client.publish('solicitud.escalada', str(event_data))
                    except Exception as e:
                        logger.error(f"Error publicando evento: {e}")
                
                logger.info(f"✅ Solicitud {solicitud.id} escalada exitosamente a Nivel {siguiente_nivel}")
                
            except Exception as e:
                logger.error(f"Error procesando solicitud {solicitud.id}: {e}")
                continue
        
        # Log resumen
        if solicitudes_escaladas > 0 or solicitudes_cerradas > 0:
            logger.info(f"📊 Resumen: {solicitudes_escaladas} escaladas, {solicitudes_cerradas} cerradas")
        
        return {
            'success': True,
            'solicitudes_escaladas': solicitudes_escaladas,
            'solicitudes_cerradas': solicitudes_cerradas,
            'timestamp': datetime.now().isoformat(),
            'message': f'Verificación completada: {solicitudes_escaladas} escaladas, {solicitudes_cerradas} cerradas'
        }
        
    except Exception as e:
        logger.error(f"❌ Error en verificación de timeouts de escalamiento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'message': 'Error verificando timeouts de escalamiento'
        }
