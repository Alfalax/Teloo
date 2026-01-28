"""
Scheduled Jobs for TeLOO V3
Standalone functions for background processing
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
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


async def _publicar_evento_evaluacion_completada(
    solicitud,
    resultado_evaluacion: Dict[str, Any],
    redis_client: redis.Redis
):
    """
    Publica evento de evaluación completada para que Agent IA notifique al cliente
    
    Args:
        solicitud: Instancia de Solicitud
        resultado_evaluacion: Resultado de la evaluación
        redis_client: Cliente Redis para publicar eventos
    """
    try:
        # Preparar datos del evento
        evento_data = {
            'tipo_evento': 'evaluacion.completada_automatica',
            'solicitud_id': str(solicitud.id),
            'cliente_telefono': solicitud.cliente.usuario.telefono,
            'cliente_nombre': solicitud.cliente.usuario.nombre_completo,
            'repuestos_adjudicados': resultado_evaluacion['repuestos_adjudicados'],
            'repuestos_totales': resultado_evaluacion['repuestos_totales'],
            'monto_total': resultado_evaluacion['monto_total_adjudicado'],
            'es_adjudicacion_mixta': resultado_evaluacion['es_adjudicacion_mixta'],
            'asesores_ganadores': resultado_evaluacion['asesores_ganadores'],
            'adjudicaciones': resultado_evaluacion['adjudicaciones'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Publicar a Redis para que Agent IA lo procese
        await redis_client.publish(
            'evaluacion.completada_automatica',
            json.dumps(evento_data)
        )
        
        logger.info(f"📢 Evento de evaluación publicado para solicitud {solicitud.id}")
        
    except Exception as e:
        logger.error(f"Error publicando evento de evaluación: {e}")
        import traceback
        logger.error(traceback.format_exc())


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
        config = await ConfiguracionService.get_config('tiempos_espera_minutos')
        
        # Convertir claves de string a int (soporta "1" o "nivel1")
        tiempos_nivel = {}
        if config and isinstance(config, dict):
            for k, v in config.items():
                try:
                    # Extraer solo los números de la llave (ej: "nivel1" -> 1)
                    num_key = ''.join(filter(str.isdigit, str(k)))
                    if num_key:
                        tiempos_nivel[int(num_key)] = int(v)
                except (ValueError, TypeError):
                    continue
            
            if tiempos_nivel:
                logger.info(f"⚙️ Tiempos configurados procesados: {tiempos_nivel}")
            else:
                tiempos_nivel = {1: 15, 2: 20, 3: 25, 4: 30, 5: 35}
                logger.warning(f"⚠️ No se pudieron procesar tiempos, usando fallback: {tiempos_nivel}")
        else:
            tiempos_nivel = {1: 15, 2: 20, 3: 25, 4: 30, 5: 35}
            logger.warning(f"⚠️ Configuración no encontrada, usando fallback: {tiempos_nivel}")
        
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
                
                # Contar ofertas con cobertura 100% (ofertas completas)
                from models.solicitud import RepuestoSolicitado
                from models.oferta import OfertaDetalle
                
                # Obtener total de repuestos solicitados
                total_repuestos = await RepuestoSolicitado.filter(solicitud_id=solicitud.id).count()
                
                # Contar ofertas que cubren el 100% de los repuestos
                ofertas = await Oferta.filter(solicitud_id=solicitud.id).prefetch_related('detalles')
                ofertas_completas = 0
                
                for oferta in ofertas:
                    # Contar cuántos repuestos diferentes cubre esta oferta
                    repuestos_cubiertos = len(set([detalle.repuesto_solicitado_id for detalle in oferta.detalles]))
                    if repuestos_cubiertos == total_repuestos:
                        ofertas_completas += 1
                
                logger.info(f"📊 Ofertas completas (100% cobertura): {ofertas_completas}/{len(ofertas)} ofertas totales")
                
                # Verificar si se alcanzó el mínimo de ofertas COMPLETAS (cierre anticipado con evaluación)
                if ofertas_completas >= solicitud.ofertas_minimas_deseadas:
                    logger.info(f"✅ Ofertas mínimas completas alcanzadas: {ofertas_completas} >= {solicitud.ofertas_minimas_deseadas}")
                    
                    # Verificar si ya fue evaluada (evitar duplicaciones)
                    from models.oferta import AdjudicacionRepuesto
                    adjudicaciones_existentes = await AdjudicacionRepuesto.filter(solicitud_id=solicitud.id).count()
                    if adjudicaciones_existentes > 0:
                        logger.info(f"⚠️ Solicitud {solicitud.id} ya tiene adjudicaciones, omitiendo evaluación")
                        continue
                    
                    # EJECUTAR EVALUACIÓN AUTOMÁTICA
                    try:
                        from services.evaluacion_service import EvaluacionService
                        await solicitud.fetch_related('cliente__usuario')
                        
                        resultado_eval = await EvaluacionService.evaluar_solicitud(str(solicitud.id))
                        
                        if resultado_eval['success']:
                            logger.info(f"✅ Evaluación automática exitosa: {resultado_eval['repuestos_adjudicados']}/{resultado_eval['repuestos_totales']} adjudicados")
                            
                            # Publicar evento de evaluación completada
                            if redis_client:
                                await _publicar_evento_evaluacion_completada(solicitud, resultado_eval, redis_client)
                            
                            solicitudes_cerradas += 1
                        else:
                            logger.error(f"❌ Evaluación automática falló: {resultado_eval.get('message')}")
                            # Marcar como evaluada de todas formas
                            solicitud.estado = EstadoSolicitud.EVALUADA
                            await solicitud.save()
                            solicitudes_cerradas += 1
                            
                    except Exception as e:
                        logger.error(f"❌ Error en evaluación automática: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        # No fallar el job, solo registrar el error y marcar como evaluada
                        solicitud.estado = EstadoSolicitud.EVALUADA
                        await solicitud.save()
                        solicitudes_cerradas += 1
                    
                    continue
                
                # Verificar si hay siguiente nivel disponible (máximo nivel 5)
                NIVEL_MAXIMO = 5
                
                if solicitud.nivel_actual >= NIVEL_MAXIMO:
                    # Ya está en el nivel máximo
                    logger.info(f"⚠️ Solicitud {solicitud.id} en nivel máximo ({solicitud.nivel_actual})")
                    logger.info(f"📊 Ofertas: {len(ofertas)} totales, {ofertas_completas} completas")
                    
                    # Si hay AL MENOS 1 oferta, evaluar (aunque no sea completa)
                    if len(ofertas) > 0:
                        logger.info(f"✅ Hay {len(ofertas)} oferta(s) para evaluar")
                        
                        # Verificar si ya fue evaluada (evitar duplicaciones)
                        from models.oferta import AdjudicacionRepuesto
                        adjudicaciones_existentes = await AdjudicacionRepuesto.filter(solicitud_id=solicitud.id).count()
                        if adjudicaciones_existentes > 0:
                            logger.info(f"⚠️ Solicitud {solicitud.id} ya tiene adjudicaciones, omitiendo evaluación")
                            continue
                        
                        # EJECUTAR EVALUACIÓN AUTOMÁTICA
                        try:
                            from services.evaluacion_service import EvaluacionService
                            await solicitud.fetch_related('cliente__usuario')
                            
                            resultado_eval = await EvaluacionService.evaluar_solicitud(str(solicitud.id))
                            
                            if resultado_eval['success'] and resultado_eval['repuestos_adjudicados'] > 0:
                                logger.info(f"✅ Evaluación exitosa: {resultado_eval['repuestos_adjudicados']} repuestos adjudicados")
                                
                                # Publicar evento de evaluación completada
                                if redis_client:
                                    await _publicar_evento_evaluacion_completada(solicitud, resultado_eval, redis_client)
                                
                                solicitudes_cerradas += 1
                            else:
                                logger.warning(f"⚠️ Evaluación sin adjudicaciones, cerrando sin ofertas")
                                solicitud.estado = EstadoSolicitud.CERRADA_SIN_OFERTAS
                                await solicitud.save()
                                solicitudes_cerradas += 1
                                
                                if redis_client:
                                    try:
                                        event_data = {
                                            'tipo_evento': 'solicitud.cerrada_sin_ofertas',
                                            'solicitud_id': str(solicitud.id),
                                            'nivel_final': solicitud.nivel_actual,
                                            'ofertas_recibidas': len(ofertas),
                                            'razon': 'Evaluación sin adjudicaciones exitosas',
                                            'timestamp': datetime.now(timezone.utc).isoformat()
                                        }
                                        await redis_client.publish('solicitud.cerrada_sin_ofertas', json.dumps(event_data))
                                    except Exception as e:
                                        logger.error(f"Error publicando evento: {e}")
                                
                        except Exception as e:
                            logger.error(f"❌ Error evaluando en nivel máximo: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            solicitud.estado = EstadoSolicitud.CERRADA_SIN_OFERTAS
                            await solicitud.save()
                            solicitudes_cerradas += 1
                    else:
                        # Sin ofertas, cerrar directamente
                        logger.warning(f"❌ Sin ofertas en nivel máximo, cerrando solicitud {solicitud.id}")
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
                                    'ofertas_recibidas': 0,
                                    'razon': 'Sin ofertas en nivel máximo',
                                    'timestamp': datetime.now(timezone.utc).isoformat()
                                }
                                await redis_client.publish('solicitud.cerrada_sin_ofertas', json.dumps(event_data))
                            except Exception as e:
                                logger.error(f"Error publicando evento: {e}")
                    
                    continue
                
                # Escalar al siguiente nivel
                siguiente_nivel = solicitud.nivel_actual + 1
                logger.info(f"📈 Intentando escalar solicitud {solicitud.id} de Nivel {solicitud.nivel_actual} → Nivel {siguiente_nivel}")
                
                # Verificar si el siguiente nivel es el máximo
                if siguiente_nivel >= NIVEL_MAXIMO:
                    logger.info(f"⚠️ Siguiente nivel ({siguiente_nivel}) es el nivel máximo")
                    
                    # Verificar si hay suficientes ofertas COMPLETAS para evaluar
                    if ofertas_completas >= solicitud.ofertas_minimas_deseadas:
                        logger.info(f"✅ Ofertas completas suficientes: {ofertas_completas} >= {solicitud.ofertas_minimas_deseadas}")
                        
                        # Verificar si ya fue evaluada (evitar duplicaciones)
                        from models.oferta import AdjudicacionRepuesto
                        adjudicaciones_existentes = await AdjudicacionRepuesto.filter(solicitud_id=solicitud.id).count()
                        if adjudicaciones_existentes > 0:
                            logger.info(f"⚠️ Solicitud {solicitud.id} ya tiene adjudicaciones, omitiendo evaluación")
                            continue
                        
                        # EVALUAR con ofertas completas
                        try:
                            from services.evaluacion_service import EvaluacionService
                            await solicitud.fetch_related('cliente__usuario')
                            
                            resultado_eval = await EvaluacionService.evaluar_solicitud(str(solicitud.id))
                            
                            if resultado_eval['success'] and resultado_eval['repuestos_adjudicados'] > 0:
                                logger.info(f"✅ Evaluación exitosa: {resultado_eval['repuestos_adjudicados']} repuestos adjudicados")
                                
                                # Publicar evento de evaluación completada
                                if redis_client:
                                    await _publicar_evento_evaluacion_completada(solicitud, resultado_eval, redis_client)
                                
                                solicitudes_cerradas += 1
                            else:
                                logger.warning(f"⚠️ Evaluación sin adjudicaciones exitosas")
                                solicitud.estado = EstadoSolicitud.CERRADA_SIN_OFERTAS
                                await solicitud.save()
                                solicitudes_cerradas += 1
                                
                        except Exception as e:
                            logger.error(f"❌ Error en evaluación: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            solicitud.estado = EstadoSolicitud.CERRADA_SIN_OFERTAS
                            await solicitud.save()
                            solicitudes_cerradas += 1
                        
                        continue
                    
                    else:
                        # No hay ofertas completas suficientes, escalar al nivel máximo y esperar timeout
                        logger.info(f"⚠️ Ofertas completas insuficientes: {ofertas_completas} < {solicitud.ofertas_minimas_deseadas}")
                        logger.info(f"📈 Escalando a nivel máximo {siguiente_nivel} para esperar más ofertas")
                        
                        solicitud.nivel_actual = siguiente_nivel
                        solicitud.fecha_escalamiento = datetime.now(timezone.utc)
                        await solicitud.save()
                        
                        # DISPARAR NOTIFICACIÓN REAL PARA EL NUEVO NIVEL
                        await EscalamientoService.ejecutar_oleada(solicitud, siguiente_nivel, redis_client)
                        
                        solicitudes_escaladas += 1
                        
                        # Publicar evento de escalamiento
                        if redis_client:
                            try:
                                event_data = {
                                    'tipo_evento': 'solicitud.escalada',
                                    'solicitud_id': str(solicitud.id),
                                    'nivel_anterior': solicitud.nivel_actual - 1,
                                    'nivel_nuevo': siguiente_nivel,
                                    'ofertas_actuales': len(ofertas),
                                    'ofertas_completas': ofertas_completas,
                                    'timestamp': datetime.now(timezone.utc).isoformat()
                                }
                                await redis_client.publish('solicitud.escalada', str(event_data))
                            except Exception as e:
                                logger.error(f"Error publicando evento: {e}")
                        
                        logger.info(f"✅ Solicitud {solicitud.id} escalada a nivel máximo {siguiente_nivel}")
                        continue
                
                # No es el nivel máximo, escalar normalmente
                logger.info(f"📈 Escalando a nivel intermedio {siguiente_nivel}")
                solicitud.nivel_actual = siguiente_nivel
                solicitud.fecha_escalamiento = datetime.now(timezone.utc)
                await solicitud.save()
                
                # DISPARAR NOTIFICACIÓN REAL PARA EL NUEVO NIVEL
                await EscalamientoService.ejecutar_oleada(solicitud, siguiente_nivel, redis_client)
                
                solicitudes_escaladas += 1
                
                # Publicar evento de escalamiento
                if redis_client:
                    try:
                        event_data = {
                            'tipo_evento': 'solicitud.escalada',
                            'solicitud_id': str(solicitud.id),
                            'nivel_anterior': solicitud.nivel_actual - 1,
                            'nivel_nuevo': siguiente_nivel,
                            'ofertas_actuales': len(ofertas),
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



async def enviar_recordatorios_cliente(
    redis_client: Optional[redis.Redis] = None
) -> Dict[str, Any]:
    """
    Send reminders to clients about pending offer responses
    
    Sends:
    - Intermediate reminder at 12 hours
    - Final reminder at 23 hours
    - Auto-closes at 24 hours (timeout)
    
    Args:
        redis_client: Redis client for publishing events
        
    Returns:
        Dict with result
    """
    try:
        logger.debug("🔍 Verificando solicitudes con respuestas pendientes...")
        
        from models.solicitud import Solicitud
        from models.enums import EstadoSolicitud
        from services.notificacion_cliente_service import NotificacionClienteService
        from services.configuracion_service import ConfiguracionService
        from datetime import timezone, timedelta
        
        # Get timeout configuration (reuse existing timeout_ofertas_horas)
        config = await ConfiguracionService.get_config('parametros_generales')
        timeout_horas = config.get('timeout_ofertas_horas', 20)
        
        # Find solicitudes EVALUADAS waiting for client response
        solicitudes_pendientes = await Solicitud.filter(
            estado=EstadoSolicitud.EVALUADA,
            fecha_notificacion_cliente__isnull=False,
            fecha_respuesta_cliente__isnull=True  # No response yet
        ).prefetch_related('cliente__usuario')
        
        logger.info(f"📋 Encontradas {len(solicitudes_pendientes)} solicitudes esperando respuesta")
        
        recordatorios_intermedios = 0
        recordatorios_finales = 0
        solicitudes_cerradas = 0
        
        ahora = datetime.now(timezone.utc)
        
        for solicitud in solicitudes_pendientes:
            try:
                # Calculate time elapsed since notification
                tiempo_transcurrido = ahora - solicitud.fecha_notificacion_cliente
                horas_transcurridas = tiempo_transcurrido.total_seconds() / 3600
                
                logger.debug(
                    f"📊 Solicitud {str(solicitud.id)[:8]}: "
                    f"{horas_transcurridas:.1f}h / {timeout_horas}h"
                )
                
                # Check if timeout reached (24 hours)
                if horas_transcurridas >= timeout_horas:
                    logger.warning(
                        f"⏰ Timeout alcanzado para solicitud {solicitud.codigo_solicitud}: "
                        f"{horas_transcurridas:.1f}h >= {timeout_horas}h"
                    )
                    
                    # Auto-reject all offers due to timeout
                    from services.respuesta_cliente_service import RespuestaClienteService
                    
                    resultado = await RespuestaClienteService.procesar_respuesta(
                        solicitud_id=str(solicitud.id),
                        respuesta_texto="rechazo todo",  # Auto-reject
                        usar_nlp=False
                    )
                    
                    if resultado['success']:
                        logger.info(f"✅ Solicitud {solicitud.codigo_solicitud} cerrada por timeout")
                        solicitudes_cerradas += 1
                        
                        # Notify client about timeout
                        if redis_client:
                            event_data = {
                                'tipo_evento': 'cliente.timeout_respuesta',
                                'solicitud_id': str(solicitud.id),
                                'codigo_solicitud': solicitud.codigo_solicitud,
                                'cliente_telefono': solicitud.cliente.usuario.telefono,
                                'cliente_nombre': solicitud.cliente.usuario.nombre_completo,
                                'mensaje': 'El tiempo para responder ha expirado. Las ofertas han sido rechazadas automáticamente.',
                                'timestamp': ahora.isoformat()
                            }
                            await redis_client.publish(
                                'cliente.timeout_respuesta',
                                json.dumps(event_data)
                            )
                    
                    continue
                
                # Check if final reminder needed (23 hours)
                if horas_transcurridas >= (timeout_horas - 1):
                    # Check if final reminder already sent
                    if redis_client:
                        reminder_key = f"reminder_final:{solicitud.id}"
                        if await redis_client.exists(reminder_key):
                            continue
                        
                        # Send final reminder
                        await NotificacionClienteService.enviar_recordatorio(
                            solicitud_id=str(solicitud.id),
                            tipo_recordatorio='final',
                            redis_client=redis_client
                        )
                        
                        # Mark as sent (expires in 2 hours)
                        await redis_client.setex(reminder_key, 7200, "sent")
                        recordatorios_finales += 1
                        
                        logger.info(f"⚠️ Recordatorio final enviado para {solicitud.codigo_solicitud}")
                    
                    continue
                
                # Check if intermediate reminder needed (12 hours)
                if horas_transcurridas >= (timeout_horas / 2):
                    # Check if intermediate reminder already sent
                    if redis_client:
                        reminder_key = f"reminder_intermedio:{solicitud.id}"
                        if await redis_client.exists(reminder_key):
                            continue
                        
                        # Send intermediate reminder
                        await NotificacionClienteService.enviar_recordatorio(
                            solicitud_id=str(solicitud.id),
                            tipo_recordatorio='intermedio',
                            redis_client=redis_client
                        )
                        
                        # Mark as sent (expires in 24 hours)
                        await redis_client.setex(reminder_key, 86400, "sent")
                        recordatorios_intermedios += 1
                        
                        logger.info(f"⏰ Recordatorio intermedio enviado para {solicitud.codigo_solicitud}")
                
            except Exception as e:
                logger.error(f"Error procesando solicitud {solicitud.id}: {e}")
                continue
        
        logger.info(
            f"✅ Recordatorios procesados: {recordatorios_intermedios} intermedios, "
            f"{recordatorios_finales} finales, {solicitudes_cerradas} cerradas por timeout"
        )
        
        return {
            'success': True,
            'recordatorios_intermedios': recordatorios_intermedios,
            'recordatorios_finales': recordatorios_finales,
            'solicitudes_cerradas_timeout': solicitudes_cerradas,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en job de recordatorios: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


async def notificar_clientes_ofertas_ganadoras(
    redis_client: Optional[redis.Redis] = None
) -> Dict[str, Any]:
    """
    Notify clients about winning offers after evaluation
    
    This job runs after evaluation is completed and sends:
    - PDF with winning offers
    - Personalized message with metrics
    
    Args:
        redis_client: Redis client for publishing events
        
    Returns:
        Dict with result
    """
    try:
        logger.debug("🔍 Buscando solicitudes evaluadas sin notificar...")
        
        from models.solicitud import Solicitud
        from models.enums import EstadoSolicitud
        from services.notificacion_cliente_service import NotificacionClienteService
        
        # Find solicitudes EVALUADAS that haven't been notified yet
        solicitudes_sin_notificar = await Solicitud.filter(
            estado=EstadoSolicitud.EVALUADA,
            fecha_evaluacion__isnull=False,
            fecha_notificacion_cliente__isnull=True
        ).prefetch_related('cliente__usuario', 'adjudicaciones')
        
        logger.info(f"📋 Encontradas {len(solicitudes_sin_notificar)} solicitudes para notificar")
        
        notificaciones_enviadas = 0
        
        for solicitud in solicitudes_sin_notificar:
            try:
                # Check if there are adjudications
                adjudicaciones_count = len(solicitud.adjudicaciones)
                
                if adjudicaciones_count == 0:
                    logger.warning(f"⚠️ Solicitud {solicitud.codigo_solicitud} sin adjudicaciones, omitiendo")
                    continue
                
                # Send notification
                resultado = await NotificacionClienteService.notificar_ofertas_ganadoras(
                    solicitud_id=str(solicitud.id),
                    redis_client=redis_client
                )
                
                if resultado['success']:
                    notificaciones_enviadas += 1
                    logger.info(
                        f"✅ Cliente notificado: {solicitud.codigo_solicitud} "
                        f"({adjudicaciones_count} repuestos)"
                    )
                else:
                    logger.error(
                        f"❌ Error notificando {solicitud.codigo_solicitud}: "
                        f"{resultado.get('error')}"
                    )
                
            except Exception as e:
                logger.error(f"Error notificando solicitud {solicitud.id}: {e}")
                continue
        
        logger.info(f"✅ Notificaciones enviadas: {notificaciones_enviadas}")
        
        return {
            'success': True,
            'notificaciones_enviadas': notificaciones_enviadas,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en job de notificaciones: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


async def procesar_notificaciones_pendientes(
    redis_client: Optional[redis.Redis] = None
) -> Dict[str, Any]:
    """
    Procesa notificaciones pendientes en la cola de Redis
    
    Este job se ejecuta cada 5 minutos y procesa notificaciones que fallaron
    en el primer intento (WebSocket no disponible, WhatsApp falló, etc.)
    
    Args:
        redis_client: Cliente Redis para acceder a la cola
        
    Returns:
        Dict con resultado del procesamiento
    """
    try:
        logger.debug("🔍 Procesando notificaciones pendientes...")
        
        if not redis_client:
            logger.warning("Redis client no disponible para procesar notificaciones")
            return {
                'success': False,
                'error': 'Redis client not available',
                'timestamp': datetime.now().isoformat()
            }
        
        # Import notification service
        from services.notification_service import notification_service
        
        # Initialize if not already done
        if not notification_service.redis_client:
            await notification_service.initialize(redis_client)
        
        # Process pending notifications
        processed = await notification_service.process_pending_notifications()
        
        if processed > 0:
            logger.info(f"✅ Procesadas {processed} notificaciones pendientes")
        else:
            logger.debug("No hay notificaciones pendientes para procesar")
        
        return {
            'success': True,
            'notificaciones_procesadas': processed,
            'timestamp': datetime.now().isoformat(),
            'message': f'Procesadas {processed} notificaciones pendientes'
        }
        
    except Exception as e:
        logger.error(f"Error procesando notificaciones pendientes: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'message': 'Error procesando notificaciones pendientes'
        }
