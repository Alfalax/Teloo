"""
Notificacion Cliente Service for TeLOO V3
Handles client notifications after offer evaluation
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json

from models.solicitud import Solicitud
from models.enums import EstadoSolicitud
from services.pdf_generator_service import PDFGeneratorService
from services.configuracion_service import ConfiguracionService

logger = logging.getLogger(__name__)


class NotificacionClienteService:
    """Service for notifying clients about winning offers"""
    
    @staticmethod
    async def notificar_ofertas_ganadoras(
        solicitud_id: str,
        redis_client = None
    ) -> Dict[str, Any]:
        """
        Notify client about winning offers with PDF and message
        
        Args:
            solicitud_id: ID of the solicitud
            redis_client: Redis client for publishing events
            
        Returns:
            Dict with notification result
        """
        try:
            # Get solicitud
            solicitud = await Solicitud.get(id=solicitud_id).prefetch_related(
                'cliente__usuario',
                'adjudicaciones'
            )
            
            if solicitud.estado != EstadoSolicitud.EVALUADA:
                raise ValueError(f"Solicitud no está en estado EVALUADA: {solicitud.estado}")
            
            # Generate PDF
            pdf_buffer = await PDFGeneratorService.generar_pdf_ofertas_ganadoras(solicitud_id)
            
            # Calculate metrics
            metricas = await PDFGeneratorService.calcular_metricas_ofertas(solicitud_id)
            
            # Get timeout configuration (reuse existing timeout_ofertas_horas)
            config = await ConfiguracionService.get_config('parametros_generales')
            timeout_horas = config.get('timeout_ofertas_horas', 20)
            
            # Prepare message
            mensaje = await NotificacionClienteService._generar_mensaje_cliente(
                solicitud=solicitud,
                metricas=metricas,
                timeout_horas=timeout_horas
            )
            
            # Publish event to Agent IA for sending
            if redis_client:
                event_data = {
                    'tipo_evento': 'cliente.notificar_ofertas_ganadoras',
                    'solicitud_id': str(solicitud.id),
                    'codigo_solicitud': solicitud.codigo_solicitud,
                    'cliente_telefono': solicitud.cliente.usuario.telefono,
                    'cliente_nombre': solicitud.cliente.usuario.nombre_completo,
                    'mensaje': mensaje,
                    'pdf_filename': f"Propuesta_{solicitud.codigo_solicitud}.pdf",
                    'metricas': metricas,
                    'timeout_horas': timeout_horas,
                    'timestamp': datetime.now().isoformat()
                }
                
                await redis_client.publish(
                    'cliente.notificar_ofertas_ganadoras',
                    json.dumps(event_data)
                )
                
                logger.info(f"Evento de notificación publicado para solicitud {solicitud.codigo_solicitud}")
            
            # Update solicitud with notification timestamp
            solicitud.fecha_notificacion_cliente = datetime.now(timezone.utc)
            try:
                await solicitud.save()
                logger.info(f"✅ fecha_notificacion_cliente guardada para solicitud {solicitud.id}")
            except Exception as save_error:
                logger.error(f"❌ Error guardando fecha_notificacion_cliente: {save_error}")
                raise
            
            logger.info(
                f"Cliente notificado para solicitud {solicitud.codigo_solicitud}: "
                f"{metricas['asesores_contactados']} asesores, "
                f"ahorro ${metricas['ahorro_obtenido']:,.0f}"
            )
            
            return {
                'success': True,
                'solicitud_id': str(solicitud.id),
                'codigo_solicitud': solicitud.codigo_solicitud,
                'cliente_telefono': solicitud.cliente.usuario.telefono,
                'mensaje_enviado': mensaje,
                'metricas': metricas,
                'pdf_generado': True,
                'timeout_horas': timeout_horas
            }
            
        except Exception as e:
            logger.error(f"Error notificando cliente para solicitud {solicitud_id}: {e}")
            return {
                'success': False,
                'solicitud_id': solicitud_id,
                'error': str(e)
            }
    
    @staticmethod
    async def _generar_mensaje_cliente(
        solicitud: Solicitud,
        metricas: Dict[str, Any],
        timeout_horas: int
    ) -> str:
        """
        Generate personalized message for client
        
        Args:
            solicitud: Solicitud instance
            metricas: Metrics dict
            timeout_horas: Timeout in hours
            
        Returns:
            Formatted message string
        """
        mensaje = f"""📋 Solicitaste nuestra ayuda para encontrar las mejores ofertas y en TeLOO lo hemos conseguido.

📊 Resultados:
• Contactamos {metricas['asesores_contactados']} asesores de repuestos
• Ahorro obtenido: ${metricas['ahorro_obtenido']:,.0f} ({metricas['porcentaje_ahorro']:.0f}%)

📎 [Adjunto: Propuesta_{solicitud.codigo_solicitud}.pdf]

Revisa el detalle de cada oferta y dinos qué piensas.

💰 Total: ${metricas['monto_total']:,.0f}
⏰ Tienes {timeout_horas} horas para responder

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 ¿Qué deseas hacer?

Responde:
• "acepto" - Aceptar todas las ofertas
• "rechazo" - Rechazar todas
• "acepto 1,3" - Aceptar solo repuestos 1 y 3

💡 Después de aceptar, los asesores te contactarán para coordinar entrega y pago. Los precios pueden ser negociables."""
        
        return mensaje
    
    @staticmethod
    async def enviar_recordatorio(
        solicitud_id: str,
        tipo_recordatorio: str,  # 'intermedio' o 'final'
        redis_client = None
    ) -> Dict[str, Any]:
        """
        Send reminder to client about pending response
        
        Args:
            solicitud_id: ID of the solicitud
            tipo_recordatorio: Type of reminder
            redis_client: Redis client for publishing events
            
        Returns:
            Dict with result
        """
        try:
            solicitud = await Solicitud.get(id=solicitud_id).prefetch_related(
                'cliente__usuario'
            )
            
            # Get timeout configuration (reuse existing timeout_ofertas_horas)
            config = await ConfiguracionService.get_config('parametros_generales')
            timeout_horas = config.get('timeout_ofertas_horas', 20)
            
            # Generate reminder message
            if tipo_recordatorio == 'intermedio':
                mensaje = f"""⏰ Recordatorio: Tienes ofertas pendientes de respuesta

Solicitud #{solicitud.codigo_solicitud}

Recuerda que tienes hasta {timeout_horas} horas para aceptar o rechazar las ofertas.

Responde:
• "acepto" - Aceptar todas
• "rechazo" - Rechazar todas
• "acepto 1,3" - Aceptar parcialmente"""
            
            else:  # final
                mensaje = f"""⚠️ ÚLTIMA HORA para responder

Solicitud #{solicitud.codigo_solicitud}

Las ofertas expirarán pronto. Por favor responde lo antes posible.

Responde:
• "acepto" - Aceptar todas
• "rechazo" - Rechazar todas"""
            
            # Publish event
            if redis_client:
                event_data = {
                    'tipo_evento': 'cliente.recordatorio_ofertas',
                    'solicitud_id': str(solicitud.id),
                    'codigo_solicitud': solicitud.codigo_solicitud,
                    'cliente_telefono': solicitud.cliente.usuario.telefono,
                    'cliente_nombre': solicitud.cliente.usuario.nombre_completo,
                    'mensaje': mensaje,
                    'tipo_recordatorio': tipo_recordatorio,
                    'timestamp': datetime.now().isoformat()
                }
                
                await redis_client.publish(
                    'cliente.recordatorio_ofertas',
                    json.dumps(event_data)
                )
            
            logger.info(f"Recordatorio {tipo_recordatorio} enviado para solicitud {solicitud.codigo_solicitud}")
            
            return {
                'success': True,
                'solicitud_id': str(solicitud.id),
                'tipo_recordatorio': tipo_recordatorio,
                'mensaje_enviado': mensaje
            }
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio para solicitud {solicitud_id}: {e}")
            return {
                'success': False,
                'solicitud_id': solicitud_id,
                'error': str(e)
            }
