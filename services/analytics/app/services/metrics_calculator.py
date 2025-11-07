"""
Metrics Calculator Service
Calcula KPIs y métricas del sistema
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tortoise import connections
from app.core.redis import redis_manager
from app.models.metrics import MetricaCalculada, TipoMetrica
from app.core.config import settings

logger = logging.getLogger(__name__)

class MetricsCalculator:
    """
    Calculadora de métricas y KPIs del sistema
    """
    
    def __init__(self):
        self.cache_prefix = "metrics:"
        
    async def get_kpis_principales(self, fecha_inicio: datetime = None, fecha_fin: datetime = None) -> Dict[str, Any]:
        """
        Obtener los 4 KPIs principales del dashboard
        """
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        cache_key = f"{self.cache_prefix}kpis_principales:{fecha_inicio.date()}:{fecha_fin.date()}"
        
        # Intentar obtener del cache
        cached_data = await redis_manager.get_cache(cache_key)
        if cached_data:
            return cached_data
            
        # Calcular KPIs
        kpis = {
            "solicitudes_mes": await self._calcular_solicitudes_mes(fecha_inicio, fecha_fin),
            "tasa_conversion": await self._calcular_tasa_conversion(fecha_inicio, fecha_fin),
            "tiempo_promedio_respuesta": await self._calcular_tiempo_promedio_respuesta(fecha_inicio, fecha_fin),
            "valor_promedio_transaccion": await self._calcular_valor_promedio_transaccion(fecha_inicio, fecha_fin)
        }
        
        # Guardar en cache
        await redis_manager.set_cache(cache_key, kpis)
        
        return kpis
        
    async def get_embudo_operativo(self, fecha_inicio: datetime = None, fecha_fin: datetime = None) -> Dict[str, Any]:
        """
        Obtener métricas del embudo operativo (11 KPIs)
        """
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        cache_key = f"{self.cache_prefix}embudo_operativo:{fecha_inicio.date()}:{fecha_fin.date()}"
        
        cached_data = await redis_manager.get_cache(cache_key)
        if cached_data:
            return cached_data
            
        embudo = {
            # Entrada del embudo
            "solicitudes_recibidas": await self._calcular_solicitudes_recibidas(fecha_inicio, fecha_fin),
            "solicitudes_procesadas": await self._calcular_solicitudes_procesadas(fecha_inicio, fecha_fin),
            
            # Escalamiento
            "asesores_contactados": await self._calcular_asesores_contactados(fecha_inicio, fecha_fin),
            "tasa_respuesta_asesores": await self._calcular_tasa_respuesta_asesores(fecha_inicio, fecha_fin),
            
            # Ofertas
            "ofertas_recibidas": await self._calcular_ofertas_recibidas(fecha_inicio, fecha_fin),
            "ofertas_por_solicitud": await self._calcular_ofertas_por_solicitud(fecha_inicio, fecha_fin),
            
            # Evaluación
            "solicitudes_evaluadas": await self._calcular_solicitudes_evaluadas(fecha_inicio, fecha_fin),
            "tiempo_evaluacion": await self._calcular_tiempo_evaluacion(fecha_inicio, fecha_fin),
            
            # Cierre
            "ofertas_ganadoras": await self._calcular_ofertas_ganadoras(fecha_inicio, fecha_fin),
            "tasa_aceptacion_cliente": await self._calcular_tasa_aceptacion_cliente(fecha_inicio, fecha_fin),
            "solicitudes_cerradas": await self._calcular_solicitudes_cerradas(fecha_inicio, fecha_fin)
        }
        
        await redis_manager.set_cache(cache_key, embudo)
        return embudo
        
    async def get_salud_marketplace(self, fecha_inicio: datetime = None, fecha_fin: datetime = None) -> Dict[str, Any]:
        """
        Obtener métricas de salud del marketplace (5 KPIs)
        """
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=7)  # Última semana
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        cache_key = f"{self.cache_prefix}salud_marketplace:{fecha_inicio.date()}:{fecha_fin.date()}"
        
        cached_data = await redis_manager.get_cache(cache_key)
        if cached_data:
            return cached_data
            
        salud = {
            "disponibilidad_sistema": await self._calcular_disponibilidad_sistema(fecha_inicio, fecha_fin),
            "latencia_promedio": await self._calcular_latencia_promedio(fecha_inicio, fecha_fin),
            "tasa_error": await self._calcular_tasa_error(fecha_inicio, fecha_fin),
            "asesores_activos": await self._calcular_asesores_activos(fecha_inicio, fecha_fin),
            "carga_sistema": await self._calcular_carga_sistema(fecha_inicio, fecha_fin)
        }
        
        await redis_manager.set_cache(cache_key, salud)
        return salud
        
    async def update_realtime_metric(self, metric_name: str, value: float, dimensions: Dict[str, Any]):
        """
        Actualizar métrica en tiempo real
        """
        try:
            # Crear o actualizar métrica calculada
            now = datetime.utcnow()
            
            await MetricaCalculada.create(
                nombre=metric_name,
                tipo=TipoMetrica.COUNTER,
                valor=value,
                dimensiones=dimensions,
                periodo_inicio=now,
                periodo_fin=now,
                expira_en=now + timedelta(hours=1)  # Expira en 1 hora
            )
            
            # Invalidar cache relacionado
            await self._invalidate_related_cache(metric_name)
            
        except Exception as e:
            logger.error(f"Error actualizando métrica en tiempo real: {e}")
            
    # Métodos privados para cálculos específicos
    
    async def _calcular_solicitudes_mes(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """Calcular solicitudes del mes"""
        conn = connections.get("default")
        
        query = """
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN estado = 'ABIERTA' THEN 1 END) as abiertas,
               COUNT(CASE WHEN estado = 'EVALUADA' THEN 1 END) as evaluadas,
               COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END) as aceptadas
        FROM solicitudes 
        WHERE created_at BETWEEN $1 AND $2
        """
        
        result = await conn.execute_query_dict(query, [fecha_inicio, fecha_fin])
        return result[0] if result else {"total": 0, "abiertas": 0, "evaluadas": 0, "aceptadas": 0}
        
    async def _calcular_tasa_conversion(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """Calcular tasa de conversión"""
        conn = connections.get("default")
        
        query = """
        SELECT 
            COUNT(*) as total_solicitudes,
            COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END) as aceptadas,
            CASE 
                WHEN COUNT(*) > 0 THEN 
                    ROUND((COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END)::float / COUNT(*)) * 100, 2)
                ELSE 0 
            END as tasa_conversion
        FROM solicitudes 
        WHERE created_at BETWEEN $1 AND $2
        """
        
        result = await conn.execute_query_dict(query, [fecha_inicio, fecha_fin])
        return result[0] if result else {"total_solicitudes": 0, "aceptadas": 0, "tasa_conversion": 0}
        
    async def _calcular_tiempo_promedio_respuesta(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """Calcular tiempo promedio de respuesta"""
        conn = connections.get("default")
        
        query = """
        SELECT 
            AVG(EXTRACT(EPOCH FROM (primera_oferta.created_at - s.created_at))/3600) as horas_promedio,
            COUNT(*) as solicitudes_con_ofertas
        FROM solicitudes s
        JOIN (
            SELECT solicitud_id, MIN(created_at) as created_at
            FROM ofertas 
            GROUP BY solicitud_id
        ) primera_oferta ON s.id = primera_oferta.solicitud_id
        WHERE s.created_at BETWEEN $1 AND $2
        """
        
        result = await conn.execute_query_dict(query, [fecha_inicio, fecha_fin])
        data = result[0] if result else {"horas_promedio": 0, "solicitudes_con_ofertas": 0}
        
        return {
            "horas_promedio": round(float(data["horas_promedio"] or 0), 2),
            "solicitudes_con_ofertas": data["solicitudes_con_ofertas"]
        }
        
    async def _calcular_valor_promedio_transaccion(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """Calcular valor promedio de transacción"""
        conn = connections.get("default")
        
        query = """
        SELECT 
            AVG(od.precio * od.cantidad) as valor_promedio,
            COUNT(DISTINCT o.solicitud_id) as transacciones,
            SUM(od.precio * od.cantidad) as valor_total
        FROM ofertas o
        JOIN oferta_detalles od ON o.id = od.oferta_id
        WHERE o.estado = 'GANADORA' 
        AND o.created_at BETWEEN $1 AND $2
        """
        
        result = await conn.execute_query_dict(query, [fecha_inicio, fecha_fin])
        data = result[0] if result else {"valor_promedio": 0, "transacciones": 0, "valor_total": 0}
        
        return {
            "valor_promedio": round(float(data["valor_promedio"] or 0), 0),
            "transacciones": data["transacciones"],
            "valor_total": round(float(data["valor_total"] or 0), 0)
        }
        
    # Métodos adicionales para otros KPIs...
    
    async def _calcular_solicitudes_recibidas(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        """Calcular solicitudes recibidas"""
        conn = connections.get("default")
        query = "SELECT COUNT(*) as total FROM solicitudes WHERE created_at BETWEEN $1 AND $2"
        result = await conn.execute_query_dict(query, [fecha_inicio, fecha_fin])
        return result[0]["total"] if result else 0
        
    async def _calcular_solicitudes_procesadas(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        """Calcular solicitudes procesadas (que tienen al menos una oferta)"""
        conn = connections.get("default")
        query = """
        SELECT COUNT(DISTINCT s.id) as total 
        FROM solicitudes s 
        JOIN ofertas o ON s.id = o.solicitud_id
        WHERE s.created_at BETWEEN $1 AND $2
        """
        result = await conn.execute_query_dict(query, [fecha_inicio, fecha_fin])
        return result[0]["total"] if result else 0
        
    async def _invalidate_related_cache(self, metric_name: str):
        """Invalidar cache relacionado con una métrica"""
        # Implementar lógica para invalidar cache relacionado
        pass
        
    # Placeholder methods para otros KPIs
    async def _calcular_asesores_contactados(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return 0
        
    async def _calcular_tasa_respuesta_asesores(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        return 0.0
        
    async def _calcular_ofertas_recibidas(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return 0
        
    async def _calcular_ofertas_por_solicitud(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        return 0.0
        
    async def _calcular_solicitudes_evaluadas(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return 0
        
    async def _calcular_tiempo_evaluacion(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        return 0.0
        
    async def _calcular_ofertas_ganadoras(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return 0
        
    async def _calcular_tasa_aceptacion_cliente(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        return 0.0
        
    async def _calcular_solicitudes_cerradas(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return 0
        
    async def _calcular_disponibilidad_sistema(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        return 99.5
        
    async def _calcular_latencia_promedio(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        return 150.0
        
    async def _calcular_tasa_error(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        return 0.02
        
    async def _calcular_asesores_activos(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return 0
        
    async def _calcular_carga_sistema(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        return 65.0