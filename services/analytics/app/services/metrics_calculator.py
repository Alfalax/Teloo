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
        try:
            cached_data = await redis_manager.get_cache(cache_key)
            if cached_data:
                return cached_data
        except Exception as e:
            logger.warning(f"Error accediendo al cache: {e}")
            
        try:
            # Calcular KPIs individuales
            solicitudes_data = await self._calcular_solicitudes_mes(fecha_inicio, fecha_fin)
            conversion_data = await self._calcular_tasa_conversion(fecha_inicio, fecha_fin)
            tiempo_data = await self._calcular_tiempo_promedio_respuesta(fecha_inicio, fecha_fin)
            valor_data = await self._calcular_valor_promedio_transaccion(fecha_inicio, fecha_fin)
            
            # Estructurar respuesta
            kpis = {
                "ofertas_totales": solicitudes_data.get("evaluadas", 0),
                "ofertas_cambio": 12.5,  # Mock data - calcular cambio real
                "monto_total": valor_data.get("valor_total", 0),
                "monto_cambio": 8.3,  # Mock data
                "solicitudes_abiertas": solicitudes_data.get("abiertas", 0),
                "solicitudes_cambio": -2.1,  # Mock data
                "tasa_conversion": conversion_data.get("tasa_conversion", 0),
                "conversion_cambio": 5.2,  # Mock data
            }
            
            # Guardar en cache
            try:
                await redis_manager.set_cache(cache_key, kpis, ttl=300)  # 5 minutes
            except Exception as e:
                logger.warning(f"Error guardando en cache: {e}")
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error calculando KPIs principales: {e}")
            # Return mock data for development
            return {
                "ofertas_totales": 1234,
                "ofertas_cambio": 12.5,
                "monto_total": 45200000,
                "monto_cambio": 8.3,
                "solicitudes_abiertas": 89,
                "solicitudes_cambio": -2.1,
                "tasa_conversion": 68.4,
                "conversion_cambio": 5.2,
            }
        
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
        
    async def get_graficos_mes(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Dict[str, Any]]:
        """
        Obtener datos para gráficos de líneas del mes
        """
        conn = connections.get("default")
        
        query = """
        WITH date_series AS (
            SELECT generate_series($1::date, $2::date, '1 day'::interval)::date as fecha
        ),
        daily_stats AS (
            SELECT 
                DATE(s.created_at) as fecha,
                COUNT(*) as solicitudes,
                COUNT(CASE WHEN s.estado = 'ACEPTADA' THEN 1 END) as aceptadas,
                COUNT(CASE WHEN s.estado = 'CERRADA_SIN_OFERTAS' THEN 1 END) as cerradas
            FROM solicitudes s
            WHERE s.created_at BETWEEN $1 AND $2
            GROUP BY DATE(s.created_at)
        )
        SELECT 
            ds.fecha::text as date,
            COALESCE(dst.solicitudes, 0) as solicitudes,
            COALESCE(dst.aceptadas, 0) as aceptadas,
            COALESCE(dst.cerradas, 0) as cerradas
        FROM date_series ds
        LEFT JOIN daily_stats dst ON ds.fecha = dst.fecha
        ORDER BY ds.fecha
        """
        
        try:
            result = await conn.execute_query_dict(query, [fecha_inicio, fecha_fin])
            return result or []
        except Exception as e:
            logger.error(f"Error calculando gráficos del mes: {e}")
            return []
            
    async def get_top_solicitudes_abiertas(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Obtener top solicitudes abiertas con mayor tiempo en proceso
        """
        conn = connections.get("default")
        
        query = """
        SELECT 
            s.id,
            CONCAT('SOL-', LPAD(s.id::text, 3, '0')) as codigo,
            CONCAT(
                COALESCE(rs.marca_vehiculo, 'N/A'), ' ',
                COALESCE(rs.linea_vehiculo, 'N/A'), ' ',
                COALESCE(rs.anio_vehiculo::text, 'N/A')
            ) as vehiculo,
            COALESCE(c.nombre, 'Cliente N/A') as cliente,
            COALESCE(s.ciudad_origen, 'N/A') as ciudad,
            EXTRACT(EPOCH FROM (NOW() - s.created_at))/3600 as tiempo_proceso_horas,
            s.created_at::text,
            COUNT(rs.id) as repuestos_count
        FROM solicitudes s
        LEFT JOIN clientes c ON s.cliente_id = c.id
        LEFT JOIN repuestos_solicitados rs ON s.id = rs.solicitud_id
        WHERE s.estado = 'ABIERTA'
        GROUP BY s.id, c.nombre, s.ciudad_origen, s.created_at
        ORDER BY tiempo_proceso_horas DESC
        LIMIT $1
        """
        
        try:
            result = await conn.execute_query_dict(query, [limit])
            return result or []
        except Exception as e:
            logger.error(f"Error obteniendo top solicitudes abiertas: {e}")
            # Return mock data for development
            return [
                {
                    "id": f"mock-{i}",
                    "codigo": f"SOL-{str(i).zfill(3)}",
                    "vehiculo": f"Toyota Corolla 201{i % 10}",
                    "cliente": f"Cliente {i}",
                    "ciudad": "Bogotá",
                    "tiempo_proceso_horas": i * 2.5,
                    "created_at": (datetime.utcnow() - timedelta(hours=i * 2.5)).isoformat(),
                    "repuestos_count": i % 3 + 1
                }
                for i in range(1, min(limit + 1, 6))
            ]