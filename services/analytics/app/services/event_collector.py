"""
Event Collector Service
Captura y procesa eventos del sistema en tiempo real
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.redis import redis_manager
from app.models.events import EventoSistema, EventoMetrica
from app.services.metrics_calculator import MetricsCalculator

logger = logging.getLogger(__name__)

class EventCollector:
    """
    Capturador de eventos que consume Redis pub/sub
    """
    
    def __init__(self):
        self.running = False
        self.metrics_calculator = MetricsCalculator()
        
    async def start(self):
        """Iniciar el capturador de eventos"""
        logger.info("Iniciando EventCollector...")
        self.running = True
        
        try:
            # Conectar a Redis y suscribirse a eventos
            pubsub = await redis_manager.subscribe_to_events()
            
            logger.info("EventCollector suscrito a eventos Redis")
            
            # Procesar eventos en bucle
            async for message in pubsub.listen():
                if not self.running:
                    break
                    
                if message["type"] == "pmessage":
                    await self._process_event(message)
                    
        except Exception as e:
            logger.error(f"Error en EventCollector: {e}")
        finally:
            await redis_manager.disconnect()
            
    async def stop(self):
        """Detener el capturador de eventos"""
        logger.info("Deteniendo EventCollector...")
        self.running = False
        
    async def _process_event(self, message: Dict[str, Any]):
        """
        Procesar un evento individual
        """
        try:
            # Extraer información del mensaje
            channel = message["channel"]
            data = json.loads(message["data"])
            
            # Parsear el tipo de evento del canal
            # Formato: teloo:events:solicitud.created
            event_type = channel.replace("teloo:events:", "")
            
            logger.debug(f"Procesando evento: {event_type}")
            
            # Guardar evento en base de datos
            await self._store_event(event_type, data)
            
            # Procesar métricas en tiempo real
            await self._process_metrics(event_type, data)
            
        except Exception as e:
            logger.error(f"Error procesando evento: {e}")
            
    async def _store_event(self, event_type: str, data: Dict[str, Any]):
        """
        Almacenar evento en EventoSistema
        """
        try:
            # Extraer información básica
            entidad_tipo, accion = event_type.split(".", 1) if "." in event_type else (event_type, "unknown")
            
            evento = await EventoSistema.create(
                tipo_evento=event_type,
                entidad_tipo=entidad_tipo.capitalize(),
                entidad_id=data.get("id", 0),
                datos=data,
                metadatos={
                    "processed_at": datetime.utcnow().isoformat(),
                    "source": "event_collector"
                },
                usuario_id=data.get("usuario_id")
            )
            
            logger.debug(f"Evento almacenado: {evento.id}")
            
        except Exception as e:
            logger.error(f"Error almacenando evento: {e}")
            
    async def _process_metrics(self, event_type: str, data: Dict[str, Any]):
        """
        Procesar métricas en tiempo real basadas en el evento
        """
        try:
            # Mapear eventos a métricas
            metrics_to_update = self._get_metrics_for_event(event_type, data)
            
            for metric_name, value, dimensions in metrics_to_update:
                # Crear evento de métrica
                await EventoMetrica.create(
                    metrica_nombre=metric_name,
                    valor=value,
                    dimensiones=dimensions
                )
                
                # Actualizar métricas calculadas si es necesario
                await self.metrics_calculator.update_realtime_metric(
                    metric_name, value, dimensions
                )
                
        except Exception as e:
            logger.error(f"Error procesando métricas: {e}")
            
    def _get_metrics_for_event(self, event_type: str, data: Dict[str, Any]) -> list:
        """
        Mapear eventos a métricas que deben actualizarse
        """
        metrics = []
        
        # Métricas por tipo de evento
        if event_type == "solicitud.created":
            metrics.append(("solicitudes_creadas", 1, {
                "ciudad": data.get("ciudad", "unknown"),
                "fecha": datetime.utcnow().date().isoformat()
            }))
            
        elif event_type == "oferta.submitted":
            metrics.append(("ofertas_enviadas", 1, {
                "asesor_id": data.get("asesor_id"),
                "ciudad": data.get("ciudad", "unknown"),
                "fecha": datetime.utcnow().date().isoformat()
            }))
            
        elif event_type == "evaluacion.completed":
            metrics.append(("evaluaciones_completadas", 1, {
                "solicitud_id": data.get("solicitud_id"),
                "fecha": datetime.utcnow().date().isoformat()
            }))
            
        elif event_type == "oferta.accepted":
            metrics.append(("ofertas_aceptadas", 1, {
                "asesor_id": data.get("asesor_id"),
                "valor": data.get("valor_total", 0),
                "fecha": datetime.utcnow().date().isoformat()
            }))
            
        elif event_type == "cliente.registered":
            metrics.append(("clientes_registrados", 1, {
                "ciudad": data.get("ciudad", "unknown"),
                "canal": data.get("canal", "whatsapp"),
                "fecha": datetime.utcnow().date().isoformat()
            }))
            
        return metrics

# Instancia global del collector
event_collector = EventCollector()