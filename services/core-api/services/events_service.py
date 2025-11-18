"""
Servicio de Eventos para publicar eventos del sistema
Estos eventos poblarán las tablas auxiliares para métricas de escalamiento
"""
import logging
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID
from models.analytics import OfertaHistorica, HistorialRespuestaOferta

logger = logging.getLogger(__name__)


class EventsService:
    """
    Servicio para manejar eventos del sistema y poblar tablas auxiliares
    """
    
    @staticmethod
    async def on_oferta_created(
        oferta_id: UUID,
        asesor_id: UUID,
        solicitud_id: UUID,
        monto_total: float,
        cantidad_repuestos: int,
        ciudad_solicitud: str,
        ciudad_asesor: str,
        estado: str,
        tiempo_respuesta_seg: int = None
    ):
        """
        Evento: Se creó una nueva oferta
        Pobla la tabla ofertas_historicas para cálculo de desempeño
        """
        try:
            await OfertaHistorica.create(
                asesor_id=asesor_id,
                solicitud_id=solicitud_id,
                fecha=datetime.utcnow().date(),
                adjudicada=False,  # Se actualizará cuando se evalúe
                aceptada_cliente=False,
                entrega_exitosa=False,
                tiempo_respuesta_seg=tiempo_respuesta_seg or 0,  # Default 0 si es None
                monto_total=monto_total,
                cantidad_repuestos=cantidad_repuestos,
                ciudad_solicitud=ciudad_solicitud,
                ciudad_asesor=ciudad_asesor,
                metadata_oferta={'oferta_id': str(oferta_id), 'estado': estado}
            )
            logger.info(f"✅ Evento oferta_created registrado: {oferta_id}")
        except Exception as e:
            logger.error(f"❌ Error registrando evento oferta_created: {e}", exc_info=True)
    
    @staticmethod
    async def on_oferta_adjudicada(oferta_id: UUID):
        """
        Evento: Una oferta fue adjudicada (ganadora)
        Actualiza ofertas_historicas
        """
        try:
            # Buscar por metadata_oferta que contiene el oferta_id
            ofertas_hist = await OfertaHistorica.all()
            for oferta_hist in ofertas_hist:
                if oferta_hist.metadata_oferta.get('oferta_id') == str(oferta_id):
                    oferta_hist.adjudicada = True
                    await oferta_hist.save()
                    logger.info(f"✅ Oferta marcada como adjudicada: {oferta_id}")
                    break
        except Exception as e:
            logger.error(f"❌ Error actualizando oferta adjudicada: {e}", exc_info=True)
    
    @staticmethod
    async def on_solicitud_escalada(
        solicitud_id: UUID,
        asesores_notificados: List[Dict[str, Any]],
        nivel: int,
        canal: str
    ):
        """
        Evento: Se escaló una solicitud a asesores
        Pobla la tabla historial_respuestas_ofertas para cálculo de actividad
        """
        try:
            fecha_envio = datetime.utcnow()
            
            for asesor_data in asesores_notificados:
                asesor_id = asesor_data.get('asesor_id')
                
                await HistorialRespuestaOferta.create(
                    asesor_id=asesor_id,
                    solicitud_id=solicitud_id,
                    fecha_envio=fecha_envio,
                    fecha_vista=None,  # Se actualizará cuando el asesor vea la solicitud
                    respondio=False,  # Se actualizará cuando envíe oferta
                    tiempo_respuesta_seg=None,
                    nivel_escalamiento=nivel,
                    canal_notificacion=canal
                )
            
            logger.info(f"✅ Evento solicitud_escalada registrado: {len(asesores_notificados)} asesores notificados")
        except Exception as e:
            logger.error(f"❌ Error registrando evento solicitud_escalada: {e}", exc_info=True)
    
    @staticmethod
    async def on_asesor_respondio(
        asesor_id: UUID,
        solicitud_id: UUID,
        tiempo_respuesta_seg: int
    ):
        """
        Evento: Un asesor respondió con una oferta
        Actualiza historial_respuestas_ofertas
        """
        try:
            historial = await HistorialRespuestaOferta.filter(
                asesor_id=asesor_id,
                solicitud_id=solicitud_id
            ).first()
            
            if historial:
                historial.respondio = True
                historial.tiempo_respuesta_seg = tiempo_respuesta_seg
                historial.fecha_respuesta = datetime.utcnow()
                await historial.save()
                logger.info(f"✅ Asesor {asesor_id} marcado como respondido")
        except Exception as e:
            logger.error(f"❌ Error actualizando respuesta de asesor: {e}", exc_info=True)


# Instancia global del servicio
events_service = EventsService()
