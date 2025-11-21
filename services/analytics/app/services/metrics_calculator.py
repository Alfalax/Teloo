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
    
    def _convert_decimals(self, data: Any) -> Any:
        """
        Convertir Decimals a float recursivamente para serialización JSON
        """
        from decimal import Decimal
        
        if isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, dict):
            return {k: self._convert_decimals(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimals(item) for item in data]
        else:
            return data
    
    async def _execute_query(self, query: str, params: list = None) -> List[Dict[str, Any]]:
        """
        Helper para ejecutar queries SQL y retornar resultados como diccionarios
        Usa la API correcta de Tortoise/asyncpg
        """
        try:
            conn = connections.get("default")
            # Usar el método correcto de Tortoise que retorna diccionarios
            results = await conn.execute_query_dict(query, params or [])
            # Convertir Decimals a float
            return self._convert_decimals(results) if results else []
        except AttributeError:
            # Si execute_query_dict no existe, usar execute_query y convertir manualmente
            try:
                results = await conn.execute_query(query, params or [])
                if not results or len(results) < 2:
                    return []
                # results[0] = columnas, results[1] = filas
                columns = [desc[0] for desc in results[0]]
                rows = results[1]
                data = [dict(zip(columns, row)) for row in rows]
                # Convertir Decimals a float
                return self._convert_decimals(data)
            except Exception as e2:
                logger.error(f"Error en fallback de query: {e2}")
                return []
        except Exception as e:
            logger.error(f"Error ejecutando query: {e}\nQuery: {query[:100]}...")
            return []
        
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
            # Calcular período anterior para comparación
            duracion = fecha_fin - fecha_inicio
            fecha_inicio_anterior = fecha_inicio - duracion
            fecha_fin_anterior = fecha_inicio
            
            # Calcular KPIs del período actual
            solicitudes_data = await self._calcular_solicitudes_mes(fecha_inicio, fecha_fin)
            conversion_data = await self._calcular_tasa_conversion(fecha_inicio, fecha_fin)
            valor_data = await self._calcular_valor_promedio_transaccion(fecha_inicio, fecha_fin)
            ofertas_data = await self._calcular_ofertas_totales(fecha_inicio, fecha_fin)
            
            # Calcular KPIs del período anterior para cambios porcentuales
            solicitudes_anterior = await self._calcular_solicitudes_mes(fecha_inicio_anterior, fecha_fin_anterior)
            conversion_anterior = await self._calcular_tasa_conversion(fecha_inicio_anterior, fecha_fin_anterior)
            valor_anterior = await self._calcular_valor_promedio_transaccion(fecha_inicio_anterior, fecha_fin_anterior)
            ofertas_anterior = await self._calcular_ofertas_totales(fecha_inicio_anterior, fecha_fin_anterior)
            
            # Calcular cambios porcentuales
            ofertas_cambio = self._calcular_cambio_porcentual(
                ofertas_data.get("total", 0),
                ofertas_anterior.get("total", 0)
            )
            monto_cambio = self._calcular_cambio_porcentual(
                valor_data.get("valor_total", 0),
                valor_anterior.get("valor_total", 0)
            )
            solicitudes_cambio = self._calcular_cambio_porcentual(
                solicitudes_data.get("abiertas", 0),
                solicitudes_anterior.get("abiertas", 0)
            )
            conversion_cambio = self._calcular_cambio_porcentual(
                conversion_data.get("tasa_conversion", 0),
                conversion_anterior.get("tasa_conversion", 0)
            )
            
            # Estructurar respuesta
            kpis = {
                "ofertas_totales": ofertas_data.get("total", 0),
                "ofertas_cambio": ofertas_cambio,
                "monto_total": valor_data.get("valor_total", 0),
                "monto_cambio": monto_cambio,
                "solicitudes_abiertas": solicitudes_data.get("abiertas", 0),
                "solicitudes_cambio": solicitudes_cambio,
                "tasa_conversion": conversion_data.get("tasa_conversion", 0),
                "conversion_cambio": conversion_cambio,
            }
            
            # Guardar en cache
            try:
                await redis_manager.set_cache(cache_key, kpis, ttl=300)  # 5 minutes
            except Exception as e:
                logger.warning(f"Error guardando en cache: {e}")
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error calculando KPIs principales: {e}", exc_info=True)
            # Return zeros instead of mock data
            return {
                "ofertas_totales": 0,
                "ofertas_cambio": 0,
                "monto_total": 0,
                "monto_cambio": 0,
                "solicitudes_abiertas": 0,
                "solicitudes_cambio": 0,
                "tasa_conversion": 0,
                "conversion_cambio": 0,
            }
        
    async def get_embudo_operativo(self, fecha_inicio: datetime = None, fecha_fin: datetime = None, nivel: str = "solicitud") -> Dict[str, Any]:
        """
        Obtener métricas del embudo operativo (11 KPIs alineados con Indicadores.txt)
        
        Args:
            nivel: 'solicitud' para métricas por solicitud completa (default)
                   'repuesto' para métricas por repuesto individual
        """
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        cache_key = f"{self.cache_prefix}embudo_operativo:{nivel}:{fecha_inicio.date()}:{fecha_fin.date()}"
        
        try:
            cached_data = await redis_manager.get_cache(cache_key)
            if cached_data:
                return cached_data
        except Exception as e:
            logger.warning(f"Error accediendo al cache: {e}")
            
        try:
            # Seleccionar métodos según nivel
            if nivel == "repuesto":
                # Calcular todos los KPIs del embudo a nivel de repuesto
                embudo = {
                    # 1. Tasa de Entrada
                    "tasa_entrada": await self._calcular_tasa_entrada(fecha_inicio, fecha_fin),
                    
                    # 2-5. Tasas de Conversión (nivel repuesto)
                    "conversiones": {
                        "abierta_a_evaluacion": await self._calcular_conversion_abierta_evaluacion(fecha_inicio, fecha_fin),
                        "evaluacion_a_adjudicada": await self._calcular_conversion_evaluacion_adjudicada(fecha_inicio, fecha_fin),
                        "adjudicada_a_aceptada": await self._calcular_conversion_adjudicada_aceptada(fecha_inicio, fecha_fin),
                        "conversion_general": await self._calcular_conversion_general(fecha_inicio, fecha_fin)
                    },
                    
                    # 6-8. Métricas de Tiempo
                    "tiempos": {
                        "ttfo": await self._calcular_ttfo(fecha_inicio, fecha_fin),
                        "tta": await self._calcular_tta(fecha_inicio, fecha_fin),
                        "ttcd": await self._calcular_ttcd(fecha_inicio, fecha_fin)
                    },
                    
                    # 9-10. Métricas de Fallo
                    "fallos": {
                        "tasa_escalamiento": await self._calcular_tasa_escalamiento(fecha_inicio, fecha_fin),
                        "fallo_por_nivel": await self._calcular_fallo_por_nivel(fecha_inicio, fecha_fin)
                    }
                }
            else:  # nivel == "solicitud"
                # Calcular todos los KPIs del embudo a nivel de solicitud
                embudo = {
                    # 1. Tasa de Entrada
                    "tasa_entrada": await self._calcular_tasa_entrada(fecha_inicio, fecha_fin),
                    
                    # 2-5. Tasas de Conversión (nivel solicitud)
                    "conversiones": {
                        "abierta_a_evaluacion": await self._calcular_conversion_abierta_evaluacion_solicitud(fecha_inicio, fecha_fin),
                        "evaluacion_a_adjudicada": await self._calcular_conversion_evaluacion_adjudicada_solicitud(fecha_inicio, fecha_fin),
                        "adjudicada_a_aceptada": await self._calcular_conversion_adjudicada_aceptada_solicitud(fecha_inicio, fecha_fin),
                        "conversion_general": await self._calcular_conversion_general_solicitud(fecha_inicio, fecha_fin)
                    },
                    
                    # 6-8. Métricas de Tiempo
                    "tiempos": {
                        "ttfo": await self._calcular_ttfo(fecha_inicio, fecha_fin),
                        "tta": await self._calcular_tta(fecha_inicio, fecha_fin),
                        "ttcd": await self._calcular_ttcd(fecha_inicio, fecha_fin)
                    },
                    
                    # 9-10. Métricas de Fallo
                    "fallos": {
                        "tasa_escalamiento": await self._calcular_tasa_escalamiento(fecha_inicio, fecha_fin),
                        "fallo_por_nivel": await self._calcular_fallo_por_nivel(fecha_inicio, fecha_fin)
                    }
                }
            
            try:
                await redis_manager.set_cache(cache_key, embudo, ttl=900)  # 15 minutos
            except Exception as e:
                logger.warning(f"Error guardando en cache: {e}")
                
            return embudo
        except Exception as e:
            logger.error(f"Error calculando embudo operativo: {e}", exc_info=True)
            return {
                "tasa_entrada": {"por_dia": []},
                "conversiones": {
                    "abierta_a_evaluacion": 0.0,
                    "evaluacion_a_adjudicada": 0.0,
                    "adjudicada_a_aceptada": 0.0,
                    "conversion_general": 0.0
                },
                "tiempos": {
                    "ttfo": {"mediana_horas": 0.0},
                    "tta": {"mediana_horas": 0.0},
                    "ttcd": {"mediana_horas": 0.0}
                },
                "fallos": {
                    "tasa_escalamiento": {
                        "tasa_general": 0.0,
                        "por_nivel": {"1_a_2": 0.0, "2_a_3": 0.0, "3_a_4": 0.0, "4_a_5": 0.0},
                        "total_solicitudes": 0
                    },
                    "fallo_por_nivel": {}
                }
            }
        
    async def get_salud_marketplace(self, fecha_inicio: datetime = None, fecha_fin: datetime = None) -> Dict[str, Any]:
        """
        Obtener métricas de salud del marketplace (5 KPIs alineados con Indicadores.txt)
        """
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=7)  # Última semana
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        cache_key = f"{self.cache_prefix}salud_marketplace:{fecha_inicio.date()}:{fecha_fin.date()}"
        
        try:
            cached_data = await redis_manager.get_cache(cache_key)
            if cached_data:
                return cached_data
        except Exception as e:
            logger.warning(f"Error accediendo al cache: {e}")
            
        try:
            salud = {
                "ratio_oferta_demanda": await self._calcular_ratio_oferta_demanda(fecha_inicio, fecha_fin),
                "densidad_ofertas": await self._calcular_densidad_ofertas(fecha_inicio, fecha_fin),
                "tasa_participacion_asesores": await self._calcular_tasa_participacion_asesores(fecha_inicio, fecha_fin),
                "tasa_adjudicacion_promedio": await self._calcular_tasa_adjudicacion_promedio(fecha_inicio, fecha_fin),
                "tasa_aceptacion_cliente": await self._calcular_tasa_aceptacion_cliente_marketplace(fecha_inicio, fecha_fin)
            }
            
            try:
                await redis_manager.set_cache(cache_key, salud, ttl=600)  # 10 minutos
            except Exception as e:
                logger.warning(f"Error guardando en cache: {e}")
                
            return salud
        except Exception as e:
            logger.error(f"Error calculando salud del marketplace: {e}", exc_info=True)
            return {
                "ratio_oferta_demanda": {"ratio": 0.0},
                "densidad_ofertas": {"densidad_promedio": 0.0},
                "tasa_participacion_asesores": {"tasa_participacion": 0.0},
                "tasa_adjudicacion_promedio": {"tasa_promedio": 0.0},
                "tasa_aceptacion_cliente": {"tasa_aceptacion": 0.0}
            }
        
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
        query = """
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN estado = 'ABIERTA' THEN 1 END) as abiertas,
               COUNT(CASE WHEN estado = 'EVALUADA' THEN 1 END) as evaluadas,
               COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END) as aceptadas
        FROM solicitudes 
        WHERE created_at BETWEEN $1 AND $2
        """
        
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return result[0] if result else {"total": 0, "abiertas": 0, "evaluadas": 0, "aceptadas": 0}
        
    async def _calcular_tasa_conversion(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """Calcular tasa de conversión"""
        query = """
        SELECT 
            COUNT(*) as total_solicitudes,
            COUNT(CASE WHEN cliente_acepto = true THEN 1 END) as aceptadas,
            CASE 
                WHEN COUNT(*) > 0 THEN 
                    ROUND(CAST((COUNT(CASE WHEN cliente_acepto = true THEN 1 END)::float / COUNT(*)) * 100 AS numeric), 2)
                ELSE 0 
            END as tasa_conversion
        FROM solicitudes 
        WHERE created_at BETWEEN $1 AND $2
        """
        
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        data = result[0] if result else {"total_solicitudes": 0, "aceptadas": 0, "tasa_conversion": 0}
        
        # Convertir Decimal a float para serialización JSON
        return {
            "total_solicitudes": data.get("total_solicitudes", 0),
            "aceptadas": data.get("aceptadas", 0),
            "tasa_conversion": float(data.get("tasa_conversion", 0))
        }
        
    async def _calcular_tiempo_promedio_respuesta(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """Calcular tiempo promedio de respuesta"""
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
        
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        data = result[0] if result else {"horas_promedio": 0, "solicitudes_con_ofertas": 0}
        
        return {
            "horas_promedio": round(float(data["horas_promedio"] or 0), 2),
            "solicitudes_con_ofertas": data["solicitudes_con_ofertas"]
        }
        
    async def _calcular_valor_promedio_transaccion(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """Calcular valor promedio de transacción"""
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
        
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        data = result[0] if result else {"valor_promedio": 0, "transacciones": 0, "valor_total": 0}
        
        return {
            "valor_promedio": round(float(data["valor_promedio"] or 0), 0),
            "transacciones": data["transacciones"],
            "valor_total": round(float(data["valor_total"] or 0), 0)
        }
        
    # Métodos adicionales para otros KPIs...
    
    async def _calcular_solicitudes_recibidas(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        """Calcular solicitudes recibidas"""
        query = "SELECT COUNT(*) as total FROM solicitudes WHERE created_at BETWEEN $1 AND $2"
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return result[0]["total"] if result else 0
        
    async def _calcular_solicitudes_procesadas(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        """Calcular solicitudes procesadas (que tienen al menos una oferta)"""
        query = """
        SELECT COUNT(DISTINCT s.id) as total 
        FROM solicitudes s 
        JOIN ofertas o ON s.id = o.solicitud_id
        WHERE s.created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return result[0]["total"] if result else 0
        
    async def _invalidate_related_cache(self, metric_name: str):
        """Invalidar cache relacionado con una métrica"""
        # Implementar lógica para invalidar cache relacionado
        pass
        
    async def _calcular_ofertas_totales(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """Calcular ofertas totales asignadas en el período"""
        query = """
        SELECT COUNT(*) as total
        FROM ofertas 
        WHERE created_at BETWEEN $1 AND $2
        """
        
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return {"total": result[0]["total"] if result else 0}
    
    def _calcular_cambio_porcentual(self, valor_actual: float, valor_anterior: float) -> float:
        """Calcular cambio porcentual entre dos valores"""
        if valor_anterior == 0:
            return 0.0 if valor_actual == 0 else 100.0
        return round(((valor_actual - valor_anterior) / valor_anterior) * 100, 2)
    
    # Placeholder methods para otros KPIs
    async def _calcular_asesores_contactados(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        query = """
        SELECT COUNT(DISTINCT asesor_id) as total
        FROM escalamientos
        WHERE created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return result[0]["total"] if result else 0
        
    async def _calcular_tasa_respuesta_asesores(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        query = """
        SELECT 
            COUNT(*) as total_escalamientos,
            COUNT(CASE WHEN estado != 'PENDIENTE' THEN 1 END) as respondidos,
            CASE 
                WHEN COUNT(*) > 0 THEN 
                    ROUND(CAST((COUNT(CASE WHEN estado != 'PENDIENTE' THEN 1 END)::float / COUNT(*)) * 100 AS numeric), 2)
                ELSE 0 
            END as tasa_respuesta
        FROM escalamientos
        WHERE created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return float(result[0]["tasa_respuesta"]) if result else 0.0
        
    async def _calcular_ofertas_recibidas(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        query = "SELECT COUNT(*) as total FROM ofertas WHERE created_at BETWEEN $1 AND $2"
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return result[0]["total"] if result else 0
        
    async def _calcular_ofertas_por_solicitud(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        query = """
        SELECT 
            COALESCE(AVG(ofertas_count), 0) as promedio
        FROM (
            SELECT solicitud_id, COUNT(*) as ofertas_count
            FROM ofertas
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY solicitud_id
        ) subquery
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return round(float(result[0]["promedio"] or 0), 2) if result else 0.0
        
    async def _calcular_solicitudes_evaluadas(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        query = """
        SELECT COUNT(*) as total 
        FROM solicitudes 
        WHERE estado = 'EVALUADA' 
        AND created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return result[0]["total"] if result else 0
        
    async def _calcular_tiempo_evaluacion(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        query = """
        SELECT 
            AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/3600) as horas_promedio
        FROM solicitudes
        WHERE estado = 'EVALUADA'
        AND created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return round(float(result[0]["horas_promedio"] or 0), 2) if result else 0.0
        
    async def _calcular_ofertas_ganadoras(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        query = """
        SELECT COUNT(*) as total 
        FROM ofertas 
        WHERE estado = 'GANADORA' 
        AND created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return result[0]["total"] if result else 0
        
    async def _calcular_tasa_aceptacion_cliente(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        query = """
        SELECT 
            COUNT(*) as total_solicitudes,
            COUNT(CASE WHEN cliente_acepto = true THEN 1 END) as aceptadas,
            CASE 
                WHEN COUNT(*) > 0 THEN 
                    ROUND(CAST((COUNT(CASE WHEN cliente_acepto = true THEN 1 END)::float / COUNT(*)) * 100 AS numeric), 2)
                ELSE 0 
            END as tasa_aceptacion
        FROM solicitudes 
        WHERE created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return float(result[0]["tasa_aceptacion"]) if result else 0.0
        
    async def _calcular_solicitudes_cerradas(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        query = """
        SELECT COUNT(*) as total 
        FROM solicitudes 
        WHERE estado IN ('CERRADA_SIN_OFERTAS', 'CERRADA') 
        AND created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return result[0]["total"] if result else 0
        
    async def _calcular_disponibilidad_sistema(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        # TODO: Implementar con métricas reales de uptime
        return 99.5
        
    async def _calcular_latencia_promedio(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        # TODO: Implementar con métricas reales de latencia
        return 150.0
        
    async def _calcular_tasa_error(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        # TODO: Implementar con logs de errores
        return 0.02
        
    async def _calcular_asesores_activos(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        query = """
        SELECT COUNT(DISTINCT u.id) as total
        FROM users u
        JOIN ofertas o ON u.id = o.asesor_id
        WHERE o.created_at BETWEEN $1 AND $2
        AND u.rol = 'ASESOR'
        AND u.activo = true
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return result[0]["total"] if result else 0
        
    async def _calcular_carga_sistema(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        # TODO: Implementar con métricas reales de carga del sistema
        return 65.0
        
    async def get_graficos_mes(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Dict[str, Any]]:
        """
        Obtener datos para gráficos de líneas del mes
        """
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
        
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return result or []
            
    async def get_top_solicitudes_abiertas(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Obtener top solicitudes abiertas con mayor tiempo en proceso
        """
        query = """
        SELECT 
            s.id,
            CONCAT('SOL-', LPAD(s.id::text, 3, '0')) as codigo,
            CONCAT(
                COALESCE(MAX(rs.marca_vehiculo), 'N/A'), ' ',
                COALESCE(MAX(rs.linea_vehiculo), 'N/A'), ' ',
                COALESCE(MAX(rs.anio_vehiculo)::text, 'N/A')
            ) as vehiculo,
            COALESCE(u.nombre, 'Cliente N/A') as cliente,
            COALESCE(s.ciudad_origen, 'N/A') as ciudad,
            EXTRACT(EPOCH FROM (NOW() - s.created_at))/3600 as tiempo_proceso_horas,
            s.created_at::text,
            COUNT(rs.id) as repuestos_count
        FROM solicitudes s
        LEFT JOIN clientes c ON s.cliente_id = c.id
        LEFT JOIN usuarios u ON c.usuario_id = u.id
        LEFT JOIN repuestos_solicitados rs ON s.id = rs.solicitud_id
        WHERE s.estado = 'ABIERTA'
        GROUP BY s.id, u.nombre, s.ciudad_origen, s.created_at
        ORDER BY tiempo_proceso_horas DESC
        LIMIT $1
        """
        
        result = await self._execute_query(query, [limit])
        return result or []
    

    # ============================================================================
    # MÉTODOS PARA EMBUDO OPERATIVO (11 KPIs)
    # ============================================================================
    
    async def _calcular_tasa_entrada(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 1: Tasa de Entrada de Solicitudes por día"""
        query = """
        SELECT 
            DATE(created_at) as periodo,
            COUNT(*) as solicitudes
        FROM solicitudes
        WHERE created_at BETWEEN $1 AND $2
        GROUP BY DATE(created_at)
        ORDER BY periodo
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        return {"por_dia": result or []}
    
    async def _calcular_conversion_abierta_evaluacion(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        """KPI 2: Conversión ABIERTA → EN_EVALUACION (% repuestos que reciben ofertas)
        Mide la capacidad inicial de la plataforma para generar interés de los asesores
        Calculado a nivel de repuesto individual, no solicitud completa
        """
        query = """
        SELECT 
            COUNT(DISTINCT rs.id) as total_repuestos,
            COUNT(DISTINCT CASE WHEN od.id IS NOT NULL THEN rs.id END) as con_ofertas
        FROM repuestos_solicitados rs
        JOIN solicitudes s ON rs.solicitud_id = s.id
        LEFT JOIN ofertas_detalle od ON rs.id = od.repuesto_solicitado_id
        WHERE s.created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['total_repuestos'] > 0:
            return round((result[0]['con_ofertas'] / result[0]['total_repuestos']) * 100, 2)
        return 0.0
    
    async def _calcular_conversion_evaluacion_adjudicada(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        """KPI 3: Conversión EN_EVALUACION → ADJUDICADA
        Porcentaje de repuestos con ofertas que resultan en la selección de un ganador
        Mide la eficacia del algoritmo de evaluación
        Calculado a nivel de repuesto individual
        """
        query = """
        SELECT 
            COUNT(DISTINCT rs.id) as total_con_ofertas,
            COUNT(DISTINCT CASE WHEN ar.id IS NOT NULL THEN rs.id END) as con_ganador
        FROM repuestos_solicitados rs
        JOIN solicitudes s ON rs.solicitud_id = s.id
        JOIN ofertas_detalle od ON rs.id = od.repuesto_solicitado_id
        LEFT JOIN adjudicaciones_repuesto ar ON rs.id = ar.repuesto_solicitado_id
        WHERE s.created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['total_con_ofertas'] > 0:
            return round((result[0]['con_ganador'] / result[0]['total_con_ofertas']) * 100, 2)
        return 0.0
    
    async def _calcular_conversion_adjudicada_aceptada(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        """KPI 4: Conversión ADJUDICADA → ACEPTADA
        Porcentaje de repuestos adjudicados que son aceptados por el cliente
        Mide la competitividad final de la oferta presentada
        Calculado a nivel de repuesto individual
        Nota: Requiere que Agent IA haya enviado ofertas a clientes y campo aceptado_cliente
        """
        query = """
        SELECT 
            COUNT(DISTINCT ar.id) as total_adjudicados,
            COUNT(DISTINCT CASE WHEN ar.aceptado_cliente = true THEN ar.id END) as aceptados
        FROM adjudicaciones_repuesto ar
        JOIN repuestos_solicitados rs ON ar.repuesto_solicitado_id = rs.id
        JOIN solicitudes s ON rs.solicitud_id = s.id
        WHERE s.created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['total_adjudicados'] > 0:
            return round((result[0]['aceptados'] / result[0]['total_adjudicados']) * 100, 2)
        return 0.0
    
    async def _calcular_conversion_general(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        """KPI 5: Tasa de Conversión General
        Calculada como (Total de Repuestos Aceptados / Total de Repuestos Solicitados)
        Calculado a nivel de repuesto individual
        Nota: Requiere que Agent IA haya completado el flujo con clientes
        """
        query = """
        SELECT 
            COUNT(DISTINCT rs.id) as total_repuestos,
            COUNT(DISTINCT CASE WHEN ar.aceptado_cliente = true THEN rs.id END) as aceptados
        FROM repuestos_solicitados rs
        JOIN solicitudes s ON rs.solicitud_id = s.id
        LEFT JOIN adjudicaciones_repuesto ar ON rs.id = ar.repuesto_solicitado_id
        WHERE s.created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['total_repuestos'] > 0:
            return round((result[0]['aceptados'] / result[0]['total_repuestos']) * 100, 2)
        return 0.0
    
    # ============================================================================
    # MÉTODOS DE CONVERSIÓN A NIVEL DE SOLICITUD (Vista Ejecutiva)
    # ============================================================================
    
    async def _calcular_conversion_abierta_evaluacion_solicitud(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        """KPI 2 (Solicitud): Conversión ABIERTA → EN_EVALUACION
        % de solicitudes que reciben al menos una oferta
        Vista ejecutiva: mide si la solicitud completa genera interés
        """
        query = """
        SELECT 
            COUNT(DISTINCT s.id) as total_solicitudes,
            COUNT(DISTINCT CASE WHEN o.id IS NOT NULL THEN s.id END) as con_ofertas
        FROM solicitudes s
        LEFT JOIN ofertas o ON s.id = o.solicitud_id
        WHERE s.created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['total_solicitudes'] > 0:
            return round((result[0]['con_ofertas'] / result[0]['total_solicitudes']) * 100, 2)
        return 0.0
    
    async def _calcular_conversion_evaluacion_adjudicada_solicitud(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        """KPI 3 (Solicitud): Conversión EN_EVALUACION → ADJUDICADA
        % de solicitudes con ofertas que tienen al menos un ganador
        Vista ejecutiva: mide si la solicitud completa llega a adjudicación
        """
        query = """
        SELECT 
            COUNT(DISTINCT s.id) as total_con_ofertas,
            COUNT(DISTINCT CASE WHEN o_ganadora.id IS NOT NULL THEN s.id END) as con_ganador
        FROM solicitudes s
        JOIN ofertas o ON s.id = o.solicitud_id
        LEFT JOIN ofertas o_ganadora ON s.id = o_ganadora.solicitud_id AND o_ganadora.estado = 'GANADORA'
        WHERE s.created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['total_con_ofertas'] > 0:
            return round((result[0]['con_ganador'] / result[0]['total_con_ofertas']) * 100, 2)
        return 0.0
    
    async def _calcular_conversion_adjudicada_aceptada_solicitud(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        """KPI 4 (Solicitud): Conversión ADJUDICADA → ACEPTADA
        % de solicitudes con ganador que son aceptadas por el cliente
        Vista ejecutiva: mide aceptación de la solicitud completa
        Nota: Usa estado de solicitud (requiere Agent IA)
        """
        query = """
        SELECT 
            COUNT(DISTINCT s.id) as total_adjudicadas,
            COUNT(DISTINCT CASE WHEN s.estado = 'ACEPTADA' THEN s.id END) as aceptadas
        FROM solicitudes s
        WHERE EXISTS (
            SELECT 1 FROM ofertas o 
            WHERE o.solicitud_id = s.id 
            AND o.estado = 'GANADORA'
        )
        AND s.created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['total_adjudicadas'] > 0:
            return round((result[0]['aceptadas'] / result[0]['total_adjudicadas']) * 100, 2)
        return 0.0
    
    async def _calcular_conversion_general_solicitud(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        """KPI 5 (Solicitud): Tasa de Conversión General
        % de solicitudes que llegan a estado ACEPTADA
        Vista ejecutiva: conversión end-to-end de la solicitud completa
        """
        query = """
        SELECT 
            COUNT(*) as total_solicitudes,
            COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END) as aceptadas
        FROM solicitudes
        WHERE created_at BETWEEN $1 AND $2
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['total_solicitudes'] > 0:
            return round((result[0]['aceptadas'] / result[0]['total_solicitudes']) * 100, 2)
        return 0.0
    
    async def _calcular_ttfo(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, float]:
        """KPI 6: Tiempo hasta Primera Oferta (TTFO) en minutos"""
        query = """
        WITH tiempos AS (
            SELECT 
                EXTRACT(EPOCH FROM (MIN(o.created_at) - s.created_at))/60 as minutos
            FROM solicitudes s
            JOIN ofertas o ON s.id = o.solicitud_id
            WHERE s.created_at BETWEEN $1 AND $2
            GROUP BY s.id, s.created_at
        )
        SELECT 
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY minutos) as mediana_minutos,
            AVG(minutos) as promedio_minutos,
            MIN(minutos) as min_minutos,
            MAX(minutos) as max_minutos
        FROM tiempos
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['mediana_minutos'] is not None:
            return {
                "mediana_minutos": round(float(result[0]['mediana_minutos']), 2),
                "promedio_minutos": round(float(result[0]['promedio_minutos'] or 0), 2),
                "min_minutos": round(float(result[0]['min_minutos'] or 0), 2),
                "max_minutos": round(float(result[0]['max_minutos'] or 0), 2)
            }
        return {"mediana_minutos": 0.0, "promedio_minutos": 0.0, "min_minutos": 0.0, "max_minutos": 0.0}
    
    async def _calcular_tta(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, float]:
        """KPI 7: Tiempo hasta Adjudicación (TTA) en minutos - Tiempo hasta primera oferta GANADORA"""
        query = """
        WITH primera_ganadora AS (
            SELECT 
                s.id as solicitud_id,
                s.created_at as solicitud_created,
                MIN(o.created_at) as primera_oferta_ganadora
            FROM solicitudes s
            INNER JOIN ofertas o ON o.solicitud_id = s.id
            WHERE o.estado = 'GANADORA'
            AND s.created_at BETWEEN $1 AND $2
            GROUP BY s.id, s.created_at
        ),
        tiempos AS (
            SELECT 
                EXTRACT(EPOCH FROM (primera_oferta_ganadora - solicitud_created))/60 as minutos
            FROM primera_ganadora
        )
        SELECT 
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY minutos) as mediana_minutos,
            AVG(minutos) as promedio_minutos,
            MIN(minutos) as min_minutos,
            MAX(minutos) as max_minutos
        FROM tiempos
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['mediana_minutos'] is not None:
            return {
                "mediana_minutos": round(float(result[0]['mediana_minutos']), 2),
                "promedio_minutos": round(float(result[0]['promedio_minutos'] or 0), 2),
                "min_minutos": round(float(result[0]['min_minutos'] or 0), 2),
                "max_minutos": round(float(result[0]['max_minutos'] or 0), 2)
            }
        return {"mediana_minutos": 0.0, "promedio_minutos": 0.0, "min_minutos": 0.0, "max_minutos": 0.0}
    
    async def _calcular_ttcd(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, float]:
        """KPI 8: Tiempo hasta Decisión del Cliente (TTCD) en minutos"""
        query = """
        WITH tiempos AS (
            SELECT 
                EXTRACT(EPOCH FROM (updated_at - created_at))/60 as minutos
            FROM solicitudes
            WHERE estado IN ('ACEPTADA', 'RECHAZADA')
            AND created_at BETWEEN $1 AND $2
        )
        SELECT 
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY minutos) as mediana_minutos,
            AVG(minutos) as promedio_minutos
        FROM tiempos
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['mediana_minutos'] is not None:
            return {
                "mediana_minutos": round(float(result[0]['mediana_minutos']), 2),
                "promedio_minutos": round(float(result[0]['promedio_minutos'] or 0), 2)
            }
        return {"mediana_minutos": 0.0, "promedio_minutos": 0.0}
    

    async def _calcular_tasa_escalamiento(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 13: Tasa de Escalamiento - Desglose por transición de niveles"""
        query = """
        WITH solicitudes_nivel AS (
            SELECT 
                s.id as solicitud_id,
                COALESCE(MAX(eat.nivel_entrega), 1) as max_nivel
            FROM solicitudes s
            LEFT JOIN evaluaciones_asesores_temp eat ON eat.solicitud_id = s.id
            WHERE s.created_at BETWEEN $1 AND $2
            GROUP BY s.id
        )
        SELECT 
            COUNT(*) as total_solicitudes,
            COUNT(CASE WHEN max_nivel >= 2 THEN 1 END) as nivel_2_o_mas,
            COUNT(CASE WHEN max_nivel >= 3 THEN 1 END) as nivel_3_o_mas,
            COUNT(CASE WHEN max_nivel >= 4 THEN 1 END) as nivel_4_o_mas,
            COUNT(CASE WHEN max_nivel >= 5 THEN 1 END) as nivel_5
        FROM solicitudes_nivel
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        
        if result and result[0]['total_solicitudes'] > 0:
            total = result[0]['total_solicitudes']
            return {
                "tasa_general": round((result[0]['nivel_2_o_mas'] / total) * 100, 2),
                "por_nivel": {
                    "1_a_2": round((result[0]['nivel_2_o_mas'] / total) * 100, 2),
                    "2_a_3": round((result[0]['nivel_3_o_mas'] / total) * 100, 2),
                    "3_a_4": round((result[0]['nivel_4_o_mas'] / total) * 100, 2),
                    "4_a_5": round((result[0]['nivel_5'] / total) * 100, 2)
                },
                "total_solicitudes": total
            }
        return {
            "tasa_general": 0.0,
            "por_nivel": {"1_a_2": 0.0, "2_a_3": 0.0, "3_a_4": 0.0, "4_a_5": 0.0},
            "total_solicitudes": 0
        }
    
    async def _calcular_fallo_por_nivel(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 14: Tasa de Fallo por Nivel - % de solicitudes que pasaron por un nivel y NO recibieron ninguna oferta"""
        query = """
        WITH solicitudes_periodo AS (
            SELECT id FROM solicitudes WHERE created_at BETWEEN $1 AND $2
        ),
        solicitudes_por_nivel AS (
            SELECT 
                eat.nivel_entrega,
                COUNT(DISTINCT eat.solicitud_id) as total_solicitudes,
                -- Solicitudes que NO recibieron ninguna oferta en este nivel
                COUNT(DISTINCT CASE 
                    WHEN NOT EXISTS (
                        SELECT 1 FROM ofertas o 
                        JOIN evaluaciones_asesores_temp eat2 
                            ON o.solicitud_id = eat2.solicitud_id 
                            AND o.asesor_id = eat2.asesor_id
                        WHERE eat2.solicitud_id = eat.solicitud_id 
                        AND eat2.nivel_entrega = eat.nivel_entrega
                    ) THEN eat.solicitud_id
                END) as sin_ofertas
            FROM evaluaciones_asesores_temp eat
            WHERE eat.solicitud_id IN (SELECT id FROM solicitudes_periodo)
            GROUP BY eat.nivel_entrega
        )
        SELECT 
            nivel_entrega,
            total_solicitudes,
            sin_ofertas,
            CASE 
                WHEN total_solicitudes > 0 THEN 
                    ROUND((CAST(sin_ofertas AS NUMERIC) / total_solicitudes * 100)::numeric, 2)
                ELSE 0 
            END as tasa_fallo
        FROM solicitudes_por_nivel
        ORDER BY nivel_entrega
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        
        if result:
            # Retornar tanto las tasas como los detalles
            return {
                'por_nivel': {str(row['nivel_entrega']): float(row['tasa_fallo']) for row in result},
                'detalles': [
                    {
                        'nivel': int(row['nivel_entrega']),
                        'total_solicitudes': int(row['total_solicitudes']),
                        'sin_ofertas': int(row['sin_ofertas']),
                        'tasa': float(row['tasa_fallo'])
                    }
                    for row in result
                ]
            }
        return {'por_nivel': {}, 'detalles': []}

    
    # ============================================================================
    # MÉTODOS PARA SALUD DEL MARKETPLACE (5 KPIs)
    # ============================================================================
    
    async def _calcular_ratio_oferta_demanda(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 1: Ratio Oferta/Demanda (Asesores Activos / Solicitudes Diarias)"""
        query = """
        WITH asesores_activos AS (
            SELECT COUNT(DISTINCT a.id)::numeric as total_asesores
            FROM asesores a
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE u.estado = 'ACTIVO' 
            AND a.estado = 'ACTIVO'
        ),
        solicitudes_diarias AS (
            SELECT 
                COUNT(*)::numeric as total_solicitudes,
                GREATEST(EXTRACT(EPOCH FROM ($2::timestamptz - $1::timestamptz)) / 86400, 1)::numeric as dias,
                COUNT(*)::numeric / GREATEST(EXTRACT(EPOCH FROM ($2::timestamptz - $1::timestamptz)) / 86400, 1)::numeric as promedio_diario
            FROM solicitudes
            WHERE created_at BETWEEN $1 AND $2
        )
        SELECT 
            aa.total_asesores,
            sd.promedio_diario,
            CASE 
                WHEN sd.promedio_diario > 0 THEN 
                    aa.total_asesores / sd.promedio_diario
                ELSE 0 
            END as ratio
        FROM asesores_activos aa, solicitudes_diarias sd
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result:
            return {
                "asesores_activos": int(result[0]['total_asesores']),
                "solicitudes_diarias_promedio": round(float(result[0]['promedio_diario'] or 0), 2),
                "ratio": round(float(result[0]['ratio'] or 0), 2)
            }
        return {"asesores_activos": 0, "solicitudes_diarias_promedio": 0.0, "ratio": 0.0}
    
    async def _calcular_densidad_ofertas(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 2: Densidad de Ofertas (promedio ofertas por solicitud llenada)"""
        query = """
        WITH solicitudes_con_ofertas AS (
            SELECT 
                s.id,
                COUNT(o.id) as num_ofertas
            FROM solicitudes s
            JOIN ofertas o ON s.id = o.solicitud_id
            WHERE s.created_at BETWEEN $1 AND $2
            GROUP BY s.id
        )
        SELECT 
            COUNT(*) as solicitudes_llenadas,
            SUM(num_ofertas) as total_ofertas,
            ROUND(AVG(num_ofertas), 2) as densidad_promedio,
            MIN(num_ofertas) as min_ofertas,
            MAX(num_ofertas) as max_ofertas
        FROM solicitudes_con_ofertas
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['solicitudes_llenadas']:
            return {
                "solicitudes_llenadas": result[0]['solicitudes_llenadas'],
                "total_ofertas": result[0]['total_ofertas'],
                "densidad_promedio": float(result[0]['densidad_promedio'] or 0),
                "min_ofertas": result[0]['min_ofertas'],
                "max_ofertas": result[0]['max_ofertas']
            }
        return {
            "solicitudes_llenadas": 0,
            "total_ofertas": 0,
            "densidad_promedio": 0.0,
            "min_ofertas": 0,
            "max_ofertas": 0
        }
    
    async def _calcular_tasa_participacion_asesores(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 3: Tasa de Participación de Asesores (% que enviaron oferta)"""
        query = """
        WITH asesores_habilitados AS (
            SELECT COUNT(DISTINCT a.id) as total
            FROM asesores a
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE u.estado = 'ACTIVO' 
            AND a.estado = 'ACTIVO'
        ),
        asesores_con_ofertas AS (
            SELECT COUNT(DISTINCT o.asesor_id) as total
            FROM ofertas o
            WHERE o.created_at BETWEEN $1 AND $2
        )
        SELECT 
            ah.total as total_habilitados,
            aco.total as total_participantes,
            CASE 
                WHEN ah.total > 0 THEN 
                    ROUND(aco.total::numeric / ah.total * 100, 2)
                ELSE 0 
            END as tasa_participacion
        FROM asesores_habilitados ah, asesores_con_ofertas aco
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result:
            return {
                "total_habilitados": result[0]['total_habilitados'],
                "total_participantes": result[0]['total_participantes'],
                "tasa_participacion": float(result[0]['tasa_participacion'] or 0)
            }
        return {"total_habilitados": 0, "total_participantes": 0, "tasa_participacion": 0.0}
    
    async def _calcular_tasa_adjudicacion_promedio(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 4: Tasa de Adjudicación del Asesor Promedio"""
        query = """
        WITH ofertas_por_asesor AS (
            SELECT 
                o.asesor_id,
                COUNT(*) as total_ofertas,
                COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras
            FROM ofertas o
            WHERE o.created_at BETWEEN $1::timestamptz AND $2::timestamptz
            GROUP BY o.asesor_id
        ),
        tasas_individuales AS (
            SELECT 
                CASE 
                    WHEN total_ofertas > 0 THEN 
                        ofertas_ganadoras::numeric / total_ofertas * 100
                    ELSE 0 
                END as tasa_individual
            FROM ofertas_por_asesor
        )
        SELECT 
            COUNT(*) as asesores_con_ofertas,
            AVG(tasa_individual)::numeric as tasa_adjudicacion_promedio,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tasa_individual)::numeric as mediana,
            MIN(tasa_individual)::numeric as min_tasa,
            MAX(tasa_individual)::numeric as max_tasa
        FROM tasas_individuales
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result and result[0]['asesores_con_ofertas']:
            return {
                "asesores_con_ofertas": result[0]['asesores_con_ofertas'],
                "tasa_promedio": round(float(result[0]['tasa_adjudicacion_promedio'] or 0), 2),
                "mediana": round(float(result[0]['mediana'] or 0), 2),
                "min_tasa": round(float(result[0]['min_tasa'] or 0), 2),
                "max_tasa": round(float(result[0]['max_tasa'] or 0), 2)
            }
        return {
            "asesores_con_ofertas": 0,
            "tasa_promedio": 0.0,
            "mediana": 0.0,
            "min_tasa": 0.0,
            "max_tasa": 0.0
        }
    
    async def _calcular_tasa_aceptacion_cliente_marketplace(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 5: Tasa de Aceptación del Cliente (% ADJUDICADA que son ACEPTADA)"""
        query = """
        WITH ofertas_adjudicadas AS (
            SELECT 
                COUNT(*) as total_adjudicadas,
                COUNT(CASE WHEN s.cliente_acepto = true THEN 1 END) as aceptadas
            FROM ofertas o
            JOIN solicitudes s ON o.solicitud_id = s.id
            WHERE o.estado = 'GANADORA'
            AND o.created_at BETWEEN $1 AND $2
        )
        SELECT 
            total_adjudicadas,
            aceptadas,
            CASE 
                WHEN total_adjudicadas > 0 THEN 
                    ROUND(aceptadas::numeric / total_adjudicadas * 100, 2)
                ELSE 0 
            END as tasa_aceptacion
        FROM ofertas_adjudicadas
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result:
            return {
                "total_adjudicadas": result[0]['total_adjudicadas'],
                "aceptadas": result[0]['aceptadas'],
                "tasa_aceptacion": float(result[0]['tasa_aceptacion'] or 0)
            }
        return {"total_adjudicadas": 0, "aceptadas": 0, "tasa_aceptacion": 0.0}


    async def get_dashboard_financiero(self, fecha_inicio: datetime = None, fecha_fin: datetime = None) -> Dict[str, Any]:
        """
        Obtener métricas del dashboard financiero (5 KPIs alineados con Indicadores.txt)
        """
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        cache_key = f"{self.cache_prefix}dashboard_financiero:{fecha_inicio.date()}:{fecha_fin.date()}"
        
        try:
            cached_data = await redis_manager.get_cache(cache_key)
            if cached_data:
                return cached_data
        except Exception as e:
            logger.warning(f"Error accediendo al cache: {e}")
            
        try:
            financiero = {
                "valor_bruto_ofertado": await self._calcular_valor_bruto_ofertado(fecha_inicio, fecha_fin),
                "valor_bruto_adjudicado": await self._calcular_valor_bruto_adjudicado(fecha_inicio, fecha_fin),
                "valor_bruto_aceptado": await self._calcular_valor_bruto_aceptado(fecha_inicio, fecha_fin),
                "valor_promedio_solicitud": await self._calcular_valor_promedio_solicitud(fecha_inicio, fecha_fin),
                "tasa_fuga_valor": await self._calcular_tasa_fuga_valor(fecha_inicio, fecha_fin)
            }
            
            # Calcular métricas derivadas
            gov = financiero["valor_bruto_ofertado"].get("valor_total", 0)
            gav_adj = financiero["valor_bruto_adjudicado"].get("valor_total", 0)
            gav_acc = financiero["valor_bruto_aceptado"].get("valor_total", 0)
            
            financiero["resumen_financiero"] = {
                "conversion_oferta_adjudicacion": round((gav_adj / gov * 100) if gov > 0 else 0, 2),
                "conversion_adjudicacion_aceptacion": round((gav_acc / gav_adj * 100) if gav_adj > 0 else 0, 2),
                "conversion_general_financiera": round((gav_acc / gov * 100) if gov > 0 else 0, 2),
                "ticket_promedio_marketplace": financiero["valor_promedio_solicitud"].get("valor_promedio_por_solicitud", 0)
            }
            
            try:
                await redis_manager.set_cache(cache_key, financiero, ttl=1800)  # 30 minutos
            except Exception as e:
                logger.warning(f"Error guardando en cache: {e}")
                
            return financiero
        except Exception as e:
            logger.error(f"Error calculando dashboard financiero: {e}", exc_info=True)
            return {
                "valor_bruto_ofertado": {"valor_total": 0},
                "valor_bruto_adjudicado": {"valor_total": 0},
                "valor_bruto_aceptado": {"valor_total": 0},
                "valor_promedio_solicitud": {"valor_promedio_por_solicitud": 0},
                "tasa_fuga_valor": {"tasa_fuga_porcentaje": 0.0},
                "resumen_financiero": {
                    "conversion_oferta_adjudicacion": 0.0,
                    "conversion_adjudicacion_aceptacion": 0.0,
                    "conversion_general_financiera": 0.0,
                    "ticket_promedio_marketplace": 0
                }
            }
    
    # ============================================================================
    # MÉTODOS PARA DASHBOARD FINANCIERO (5 KPIs)
    # ============================================================================
    
    async def _calcular_valor_bruto_ofertado(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 1: Valor Bruto Ofertado (GOV) - Suma de todas las ofertas"""
        query = """
        WITH valores_ofertas AS (
            SELECT 
                o.id,
                SUM(od.precio_unitario * od.cantidad) as valor_total
            FROM ofertas o
            JOIN ofertas_detalle od ON o.id = od.oferta_id
            WHERE o.created_at BETWEEN $1::timestamptz AND $2::timestamptz
            GROUP BY o.id
        )
        SELECT 
            COUNT(*) as total_ofertas,
            COALESCE(SUM(valor_total), 0)::numeric as valor_bruto_ofertado,
            COALESCE(AVG(valor_total), 0)::numeric as valor_promedio_oferta,
            COALESCE(MIN(valor_total), 0)::numeric as valor_minimo,
            COALESCE(MAX(valor_total), 0)::numeric as valor_maximo
        FROM valores_ofertas
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result:
            return {
                "total_ofertas": result[0]['total_ofertas'],
                "valor_total": int(result[0]['valor_bruto_ofertado']),
                "valor_promedio": round(float(result[0]['valor_promedio_oferta'] or 0), 0),
                "valor_minimo": int(result[0]['valor_minimo']),
                "valor_maximo": int(result[0]['valor_maximo'])
            }
        return {"total_ofertas": 0, "valor_total": 0, "valor_promedio": 0, "valor_minimo": 0, "valor_maximo": 0}
    
    async def _calcular_valor_bruto_adjudicado(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 2: Valor Bruto Adjudicado (GAV_adj) - Suma de ofertas GANADORA"""
        query = """
        WITH valores_adjudicadas AS (
            SELECT 
                o.id,
                SUM(od.precio_unitario * od.cantidad) as valor_total
            FROM ofertas o
            JOIN ofertas_detalle od ON o.id = od.oferta_id
            WHERE o.estado = 'GANADORA'
            AND o.created_at BETWEEN $1::timestamptz AND $2::timestamptz
            GROUP BY o.id
        )
        SELECT 
            COUNT(*) as total_adjudicadas,
            COALESCE(SUM(valor_total), 0)::numeric as valor_bruto_adjudicado,
            COALESCE(AVG(valor_total), 0)::numeric as valor_promedio_adjudicada,
            COALESCE(MIN(valor_total), 0)::numeric as valor_minimo,
            COALESCE(MAX(valor_total), 0)::numeric as valor_maximo
        FROM valores_adjudicadas
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result:
            return {
                "total_adjudicadas": result[0]['total_adjudicadas'],
                "valor_total": int(result[0]['valor_bruto_adjudicado']),
                "valor_promedio": round(float(result[0]['valor_promedio_adjudicada'] or 0), 0),
                "valor_minimo": int(result[0]['valor_minimo']),
                "valor_maximo": int(result[0]['valor_maximo'])
            }
        return {"total_adjudicadas": 0, "valor_total": 0, "valor_promedio": 0, "valor_minimo": 0, "valor_maximo": 0}
    
    async def _calcular_valor_bruto_aceptado(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 3: Valor Bruto Aceptado (GAV_acc) - Suma de ofertas ACEPTADA"""
        query = """
        WITH valores_aceptadas AS (
            SELECT 
                o.id,
                SUM(od.precio_unitario * od.cantidad) as valor_total
            FROM ofertas o
            JOIN ofertas_detalle od ON o.id = od.oferta_id
            JOIN solicitudes s ON o.solicitud_id = s.id
            WHERE o.estado = 'GANADORA'
            AND s.estado = 'ACEPTADA'
            AND o.created_at BETWEEN $1::timestamptz AND $2::timestamptz
            GROUP BY o.id
        )
        SELECT 
            COUNT(*) as total_aceptadas,
            COALESCE(SUM(valor_total), 0)::numeric as valor_bruto_aceptado,
            COALESCE(AVG(valor_total), 0)::numeric as valor_promedio_aceptada,
            COALESCE(MIN(valor_total), 0)::numeric as valor_minimo,
            COALESCE(MAX(valor_total), 0)::numeric as valor_maximo
        FROM valores_aceptadas
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result:
            return {
                "total_aceptadas": result[0]['total_aceptadas'],
                "valor_total": int(result[0]['valor_bruto_aceptado']),
                "valor_promedio": round(float(result[0]['valor_promedio_aceptada'] or 0), 0),
                "valor_minimo": int(result[0]['valor_minimo']),
                "valor_maximo": int(result[0]['valor_maximo'])
            }
        return {"total_aceptadas": 0, "valor_total": 0, "valor_promedio": 0, "valor_minimo": 0, "valor_maximo": 0}
    
    async def _calcular_valor_promedio_solicitud(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 4: Valor Promedio por Solicitud Aceptada"""
        query = """
        WITH solicitudes_aceptadas AS (
            SELECT COUNT(*) as total_solicitudes_aceptadas
            FROM solicitudes
            WHERE estado = 'ACEPTADA'
            AND created_at BETWEEN $1::timestamptz AND $2::timestamptz
        ),
        valor_total_aceptado AS (
            SELECT COALESCE(SUM(od.precio_unitario * od.cantidad), 0)::numeric as valor_total
            FROM ofertas o
            JOIN ofertas_detalle od ON o.id = od.oferta_id
            JOIN solicitudes s ON o.solicitud_id = s.id
            WHERE o.estado = 'GANADORA'
            AND s.estado = 'ACEPTADA'
            AND o.created_at BETWEEN $1::timestamptz AND $2::timestamptz
        )
        SELECT 
            sa.total_solicitudes_aceptadas,
            vta.valor_total,
            CASE 
                WHEN sa.total_solicitudes_aceptadas > 0 THEN 
                    ROUND(vta.valor_total / sa.total_solicitudes_aceptadas, 0)
                ELSE 0 
            END as valor_promedio_por_solicitud
        FROM solicitudes_aceptadas sa, valor_total_aceptado vta
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result:
            return {
                "solicitudes_aceptadas": result[0]['total_solicitudes_aceptadas'],
                "valor_total_aceptado": int(result[0]['valor_total']),
                "valor_promedio_por_solicitud": int(result[0]['valor_promedio_por_solicitud'])
            }
        return {"solicitudes_aceptadas": 0, "valor_total_aceptado": 0, "valor_promedio_por_solicitud": 0}
    
    async def _calcular_tasa_fuga_valor(self, fecha_inicio: datetime, fecha_fin: datetime) -> Dict[str, Any]:
        """KPI 5: Tasa de Fuga de Valor ((GAV_adj - GAV_acc) / GAV_adj)"""
        query = """
        WITH valor_adjudicado AS (
            SELECT COALESCE(SUM(od.precio_unitario * od.cantidad), 0)::numeric as total
            FROM ofertas o
            JOIN ofertas_detalle od ON o.id = od.oferta_id
            WHERE o.estado = 'GANADORA'
            AND o.created_at BETWEEN $1::timestamptz AND $2::timestamptz
        ),
        valor_aceptado AS (
            SELECT COALESCE(SUM(od.precio_unitario * od.cantidad), 0)::numeric as total
            FROM ofertas o
            JOIN ofertas_detalle od ON o.id = od.oferta_id
            JOIN solicitudes s ON o.solicitud_id = s.id
            WHERE o.estado = 'GANADORA'
            AND s.estado = 'ACEPTADA'
            AND o.created_at BETWEEN $1::timestamptz AND $2::timestamptz
        )
        SELECT 
            vadj.total as valor_adjudicado,
            vacc.total as valor_aceptado,
            (vadj.total - vacc.total) as valor_fugado,
            CASE 
                WHEN vadj.total > 0 THEN 
                    ROUND(((vadj.total - vacc.total) / vadj.total) * 100, 2)
                ELSE 0 
            END as tasa_fuga_porcentaje
        FROM valor_adjudicado vadj, valor_aceptado vacc
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result:
            return {
                "valor_adjudicado": int(result[0]['valor_adjudicado']),
                "valor_aceptado": int(result[0]['valor_aceptado']),
                "valor_fugado": int(result[0]['valor_fugado']),
                "tasa_fuga_porcentaje": float(result[0]['tasa_fuga_porcentaje'])
            }
        return {"valor_adjudicado": 0, "valor_aceptado": 0, "valor_fugado": 0, "tasa_fuga_porcentaje": 0.0}


    async def get_analisis_asesores(self, fecha_inicio: datetime = None, fecha_fin: datetime = None, ciudad: str = None) -> Dict[str, Any]:
        """
        Cuadros de Mando de Rendimiento del Asesor (Advisor Scorecards) + Segmentación RFM
        Implementación según especificación 3.1 y 3.2
        """
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        cache_key = f"{self.cache_prefix}advisor_scorecards_rfm:{fecha_inicio.date()}:{fecha_fin.date()}:{ciudad or 'all'}"
        
        try:
            cached_data = await redis_manager.get_cache(cache_key)
            if cached_data:
                return cached_data
        except Exception as e:
            logger.warning(f"Error accediendo al cache: {e}")
            
        try:
            # 3.1 Cuadros de Mando: Calcular métricas por asesor
            scorecards = await self._calcular_advisor_scorecards(fecha_inicio, fecha_fin, ciudad)
            
            # 3.2 Segmentación RFM: Clasificar asesores en segmentos
            segmentacion_rfm = await self._calcular_segmentacion_rfm(fecha_inicio, fecha_fin, ciudad)
            
            result = {
                "advisor_scorecards": scorecards,
                "segmentacion_rfm": segmentacion_rfm,
                "resumen_ejecutivo": {
                    "total_asesores_analizados": len(scorecards.get("asesores", [])),
                    "periodo_analisis": {
                        "inicio": fecha_inicio.isoformat(),
                        "fin": fecha_fin.isoformat()
                    },
                    "filtro_ciudad": ciudad
                }
            }
            
            try:
                await redis_manager.set_cache(cache_key, result, ttl=900)  # 15 minutos
            except Exception as e:
                logger.warning(f"Error guardando en cache: {e}")
                
            return result
        except Exception as e:
            logger.error(f"Error calculando análisis de asesores: {e}", exc_info=True)
            return {
                "advisor_scorecards": {"asesores": [], "metricas_definicion": {}},
                "segmentacion_rfm": {"segmentos": [], "acciones_recomendadas": {}, "definiciones": {}},
                "resumen_ejecutivo": {
                    "total_asesores_analizados": 0,
                    "periodo_analisis": {
                        "inicio": fecha_inicio.isoformat(),
                        "fin": fecha_fin.isoformat()
                    },
                    "filtro_ciudad": ciudad
                }
            }

    
    # ============================================================================
    # 3.1 CUADROS DE MANDO DE RENDIMIENTO DEL ASESOR (ADVISOR SCORECARDS)
    # ============================================================================
    
    async def _calcular_advisor_scorecards(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> Dict[str, Any]:
        """
        Calcula las 5 métricas de rendimiento por asesor según especificación 3.1
        """
        ciudad_filter = "AND a.ciudad = $3" if ciudad else ""
        params = [fecha_inicio, fecha_fin]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        WITH asesores_base AS (
            SELECT DISTINCT a.id, u.nombre, a.ciudad
            FROM asesores a
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE u.estado = 'ACTIVO' AND a.estado = 'ACTIVO'
            {ciudad_filter}
        ),
        -- 1. Tasa de Presentación de Ofertas (usando historial_respuestas_ofertas como fuente única)
        asignaciones_por_asesor AS (
            SELECT 
                hro.asesor_id,
                COUNT(DISTINCT hro.solicitud_id) as solicitudes_asignadas,
                COUNT(DISTINCT CASE WHEN hro.respondio = true THEN hro.solicitud_id END) as solicitudes_respondidas
            FROM historial_respuestas_ofertas hro
            WHERE hro.fecha_envio BETWEEN $1::timestamptz AND $2::timestamptz
            GROUP BY hro.asesor_id
        ),
        ofertas_por_asesor AS (
            SELECT 
                o.asesor_id,
                COUNT(*) as total_ofertas
            FROM ofertas o
            WHERE o.created_at BETWEEN $1::timestamptz AND $2::timestamptz
            GROUP BY o.asesor_id
        ),
        -- 2. Tasa de Adjudicación Personal
        adjudicaciones_por_asesor AS (
            SELECT 
                o.asesor_id,
                COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_adjudicadas
            FROM ofertas o
            WHERE o.created_at BETWEEN $1::timestamptz AND $2::timestamptz
            GROUP BY o.asesor_id
        ),
        -- 3. Tasa de Aceptación sobre Adjudicaciones
        aceptaciones_por_asesor AS (
            SELECT 
                o.asesor_id,
                COUNT(CASE WHEN o.estado = 'GANADORA' AND s.estado = 'ACEPTADA' THEN 1 END) as ofertas_aceptadas
            FROM ofertas o
            JOIN solicitudes s ON o.solicitud_id = s.id
            WHERE o.created_at BETWEEN $1::timestamptz AND $2::timestamptz
            GROUP BY o.asesor_id
        ),
        -- 4. Índice de Competitividad (simplificado por ahora)
        competitividad_por_asesor AS (
            SELECT 
                o.asesor_id,
                AVG(COALESCE(o.puntaje_total, 0)) as indice_competitividad
            FROM ofertas o
            WHERE o.created_at BETWEEN $1::timestamptz AND $2::timestamptz
            GROUP BY o.asesor_id
        ),
        -- 5. Mediana de Tiempo de Respuesta
        tiempos_respuesta AS (
            SELECT 
                hro.asesor_id,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hro.tiempo_respuesta_seg) as mediana_tiempo_respuesta_seg
            FROM historial_respuestas_ofertas hro
            WHERE hro.respondio = true
            AND hro.fecha_envio BETWEEN $1::timestamptz AND $2::timestamptz
            AND hro.tiempo_respuesta_seg IS NOT NULL
            GROUP BY hro.asesor_id
        )
        SELECT 
            ab.id as asesor_id,
            ab.nombre,
            ab.ciudad,
            -- Métricas calculadas
            COALESCE(apa.solicitudes_asignadas, 0) as solicitudes_asignadas,
            COALESCE(apa.solicitudes_respondidas, 0) as solicitudes_respondidas,
            COALESCE(opa.total_ofertas, 0) as total_ofertas,
            COALESCE(adpa.ofertas_adjudicadas, 0) as ofertas_adjudicadas,
            COALESCE(acpa.ofertas_aceptadas, 0) as ofertas_aceptadas,
            COALESCE(cpa.indice_competitividad, 0)::numeric as indice_competitividad,
            COALESCE(tr.mediana_tiempo_respuesta_seg, 0)::numeric as mediana_tiempo_respuesta_seg,
            -- KPIs calculados
            CASE 
                WHEN COALESCE(apa.solicitudes_asignadas, 0) > 0 THEN 
                    ROUND((COALESCE(apa.solicitudes_respondidas, 0)::numeric / apa.solicitudes_asignadas * 100), 2)
                ELSE 0 
            END as tasa_presentacion_ofertas,
            CASE 
                WHEN COALESCE(opa.total_ofertas, 0) > 0 THEN 
                    ROUND((COALESCE(adpa.ofertas_adjudicadas, 0)::numeric / opa.total_ofertas * 100), 2)
                ELSE 0 
            END as tasa_adjudicacion_personal,
            CASE 
                WHEN COALESCE(adpa.ofertas_adjudicadas, 0) > 0 THEN 
                    ROUND((COALESCE(acpa.ofertas_aceptadas, 0)::numeric / adpa.ofertas_adjudicadas * 100), 2)
                ELSE 0 
            END as tasa_aceptacion_adjudicaciones
        FROM asesores_base ab
        LEFT JOIN asignaciones_por_asesor apa ON ab.id = apa.asesor_id
        LEFT JOIN ofertas_por_asesor opa ON ab.id = opa.asesor_id
        LEFT JOIN adjudicaciones_por_asesor adpa ON ab.id = adpa.asesor_id
        LEFT JOIN aceptaciones_por_asesor acpa ON ab.id = acpa.asesor_id
        LEFT JOIN competitividad_por_asesor cpa ON ab.id = cpa.asesor_id
        LEFT JOIN tiempos_respuesta tr ON ab.id = tr.asesor_id
        ORDER BY tasa_adjudicacion_personal DESC, tasa_presentacion_ofertas DESC
        """
        
        asesores_data = await self._execute_query(query, params)
        
        return {
            "asesores": asesores_data or [],
            "metricas_definicion": {
                "tasa_presentacion_ofertas": "% de solicitudes asignadas que recibieron oferta del asesor",
                "tasa_adjudicacion_personal": "% de ofertas del asesor que resultaron ganadoras",
                "tasa_aceptacion_adjudicaciones": "% de adjudicaciones del asesor aceptadas por el cliente",
                "indice_competitividad": "Puntaje promedio de competitividad de las ofertas",
                "mediana_tiempo_respuesta_seg": "Tiempo mediano de respuesta en segundos"
            }
        }
    
    async def _calcular_segmentacion_rfm(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> Dict[str, Any]:
        """
        Segmentación RFM de asesores según especificación 3.2
        R: Recencia (días desde última oferta)
        F: Frecuencia (ofertas en últimos 30 días)  
        M: Valor Monetario (GAV_acc en últimos 90 días)
        """
        ciudad_filter = "AND a.ciudad = $4" if ciudad else ""
        params = [fecha_inicio, fecha_fin, datetime.utcnow() - timedelta(days=90)]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        WITH asesores_base AS (
            SELECT DISTINCT a.id, u.nombre, a.ciudad, u.created_at as fecha_registro
            FROM asesores a
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE u.estado = 'ACTIVO' AND a.estado = 'ACTIVO'
            {ciudad_filter}
        ),
        -- Calcular dimensiones RFM
        rfm_data AS (
            SELECT 
                ab.id as asesor_id,
                ab.nombre,
                ab.ciudad,
                ab.fecha_registro,
                -- R: Recencia (días desde última oferta)
                COALESCE(
                    EXTRACT(EPOCH FROM (NOW() - MAX(o.created_at))) / 86400, 
                    999
                )::numeric as recencia_dias,
                -- F: Frecuencia (ofertas en período actual)
                COUNT(CASE WHEN o.created_at BETWEEN $1::timestamptz AND $2::timestamptz THEN 1 END) as frecuencia_ofertas,
                -- M: Valor Monetario (GAV_acc en últimos 90 días)
                COALESCE(SUM(
                    CASE WHEN o.estado = 'GANADORA' 
                         AND s.estado = 'ACEPTADA' 
                         AND o.created_at >= $3::timestamptz
                    THEN (
                        SELECT SUM(od.precio_unitario * od.cantidad)
                        FROM ofertas_detalle od 
                        WHERE od.oferta_id = o.id
                    )
                    ELSE 0 END
                ), 0)::numeric as valor_monetario
            FROM asesores_base ab
            LEFT JOIN ofertas o ON ab.id = o.asesor_id
            LEFT JOIN solicitudes s ON o.solicitud_id = s.id
            GROUP BY ab.id, ab.nombre, ab.ciudad, ab.fecha_registro
        ),
        -- Calcular cuartiles para segmentación
        cuartiles AS (
            SELECT 
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY recencia_dias) as q1_recencia,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY recencia_dias) as q3_recencia,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY frecuencia_ofertas) as q1_frecuencia,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY frecuencia_ofertas) as q3_frecuencia,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY valor_monetario) as q1_valor,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY valor_monetario) as q3_valor
            FROM rfm_data
        ),
        -- Asignar segmentos
        segmentacion AS (
            SELECT 
                rd.*,
                -- Determinar segmento según reglas de negocio
                CASE 
                    -- Asesores Estrella: Alto en las 3 dimensiones
                    WHEN rd.recencia_dias <= c.q1_recencia 
                         AND rd.frecuencia_ofertas >= c.q3_frecuencia 
                         AND rd.valor_monetario >= c.q3_valor 
                    THEN 'ASESORES_ESTRELLA'
                    
                    -- Estrellas en Ascenso: Alta Recencia y Frecuencia, bajo Valor
                    WHEN rd.recencia_dias <= c.q1_recencia 
                         AND rd.frecuencia_ofertas >= c.q3_frecuencia 
                         AND rd.valor_monetario < c.q1_valor 
                    THEN 'ESTRELLAS_ASCENSO'
                    
                    -- Gigantes Dormidos: Baja Recencia, alto Valor histórico
                    WHEN rd.recencia_dias >= c.q3_recencia 
                         AND rd.valor_monetario >= c.q3_valor 
                    THEN 'GIGANTES_DORMIDOS'
                    
                    -- Asesores en Riesgo: Recencia media, Frecuencia y Valor en declive
                    WHEN rd.recencia_dias BETWEEN c.q1_recencia AND c.q3_recencia
                         AND rd.frecuencia_ofertas < c.q1_frecuencia 
                         AND rd.valor_monetario < c.q1_valor 
                    THEN 'ASESORES_RIESGO'
                    
                    -- Nuevos Asesores: Menos de 30 días registrados
                    WHEN EXTRACT(EPOCH FROM (NOW() - rd.fecha_registro)) / 86400 <= 30
                    THEN 'NUEVOS_ASESORES'
                    
                    -- Otros casos
                    ELSE 'OTROS'
                END as segmento
            FROM rfm_data rd
            CROSS JOIN cuartiles c
        )
        SELECT 
            segmento,
            COUNT(*) as cantidad_asesores,
            ROUND(AVG(recencia_dias), 1) as recencia_promedio,
            ROUND(AVG(frecuencia_ofertas), 1) as frecuencia_promedio,
            ROUND(AVG(valor_monetario), 0) as valor_promedio,
            -- Detalle de asesores por segmento (top 10)
            JSON_AGG(
                JSON_BUILD_OBJECT(
                    'asesor_id', asesor_id,
                    'nombre', nombre,
                    'ciudad', ciudad,
                    'recencia_dias', ROUND(recencia_dias, 1),
                    'frecuencia_ofertas', frecuencia_ofertas,
                    'valor_monetario', ROUND(valor_monetario, 0)
                ) ORDER BY valor_monetario DESC
            ) FILTER (WHERE segmento != 'OTROS') as asesores_detalle
        FROM segmentacion
        GROUP BY segmento
        ORDER BY 
            CASE segmento
                WHEN 'ASESORES_ESTRELLA' THEN 1
                WHEN 'ESTRELLAS_ASCENSO' THEN 2
                WHEN 'GIGANTES_DORMIDOS' THEN 3
                WHEN 'ASESORES_RIESGO' THEN 4
                WHEN 'NUEVOS_ASESORES' THEN 5
                ELSE 6
            END
        """
        
        segmentos_data = await self._execute_query(query, params)
        
        # Definir acciones recomendadas según especificación
        acciones_recomendadas = {
            "ASESORES_ESTRELLA": [
                "Programa de lealtad (comisiones reducidas, soporte prioritario)",
                "Acceso beta a nuevas funcionalidades",
                "Reconocimiento público (ej. 'Asesor del Mes')"
            ],
            "ESTRELLAS_ASCENSO": [
                "Webinars de estrategia sobre cómo crear ofertas ganadoras",
                "Informes personalizados de competitividad",
                "Mentoría por parte de Asesores Estrella"
            ],
            "GIGANTES_DORMIDOS": [
                "Campaña de email/WhatsApp personalizada",
                "Encuesta de salida para entender razones de inactividad",
                "Incentivo de reactivación (0% comisión en próximas 5 ventas)"
            ],
            "ASESORES_RIESGO": [
                "Alerta automática al gestor de cuentas",
                "Llamada proactiva para entender problemas",
                "Sesión de revisión de estrategia"
            ],
            "NUEVOS_ASESORES": [
                "Secuencia de emails de bienvenida con tutoriales",
                "Asignación de un 'buddy' o mentor",
                "Metas iniciales gamificadas"
            ]
        }
        
        return {
            "segmentos": segmentos_data or [],
            "acciones_recomendadas": acciones_recomendadas,
            "definiciones": {
                "recencia": "Días transcurridos desde la última oferta enviada",
                "frecuencia": "Número de ofertas enviadas en el período",
                "valor": "GAV_acc (Valor Bruto Aceptado) generado en últimos 90 días"
            }
        }
    
    # ============================================================================
    # MÉTODOS AUXILIARES LEGACY (MANTENER POR COMPATIBILIDAD)
    # ============================================================================
    
    async def _calcular_total_asesores_activos(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> int:
        """KPI 1: Total de Asesores Activos (con al menos una oferta)"""
        query = """
        SELECT COUNT(DISTINCT o.asesor_id) as total_asesores_activos
        FROM ofertas o
        """
        params = [fecha_inicio, fecha_fin]
        
        if ciudad:
            query += """
            JOIN asesores a ON o.asesor_id = a.id
            WHERE o.created_at BETWEEN $1 AND $2
            AND a.ciudad = $3
            """
            params.append(ciudad)
        else:
            query += "WHERE o.created_at BETWEEN $1 AND $2"
            
        result = await self._execute_query(query, params)
        return result[0]['total_asesores_activos'] if result else 0

    
    async def _calcular_tasa_respuesta_asesores(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> Dict[str, Any]:
        """KPI 2: Tasa de Respuesta Promedio"""
        ciudad_filter = "AND a.ciudad = $3" if ciudad else ""
        params = [fecha_inicio, fecha_fin]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        WITH asignaciones AS (
            SELECT 
                hro.asesor_id,
                COUNT(DISTINCT hro.solicitud_id) as solicitudes_asignadas
            FROM historial_respuestas_ofertas hro
            JOIN asesores a ON hro.asesor_id = a.id
            WHERE hro.fecha_envio BETWEEN $1::timestamptz AND $2::timestamptz
            {ciudad_filter}
            GROUP BY hro.asesor_id
        ),
        respuestas AS (
            SELECT 
                hro.asesor_id,
                COUNT(DISTINCT hro.solicitud_id) as solicitudes_respondidas
            FROM historial_respuestas_ofertas hro
            JOIN asesores a ON hro.asesor_id = a.id
            WHERE hro.respondio = true
            AND hro.fecha_envio BETWEEN $1::timestamptz AND $2::timestamptz
            {ciudad_filter}
            GROUP BY hro.asesor_id
        )
        SELECT 
            COUNT(DISTINCT asig.asesor_id) as total_asesores,
            ROUND(AVG(CASE 
                WHEN asig.solicitudes_asignadas > 0 THEN 
                    (COALESCE(resp.solicitudes_respondidas, 0)::numeric / asig.solicitudes_asignadas * 100)
                ELSE 0 
            END)::numeric, 2) as tasa_respuesta_promedio
        FROM asignaciones asig
        LEFT JOIN respuestas resp ON asig.asesor_id = resp.asesor_id
        """
        result = await self._execute_query(query, params)
        if result:
            return {
                "total_asesores": result[0]['total_asesores'],
                "tasa_promedio": float(result[0]['tasa_respuesta_promedio'] or 0)
            }
        return {"total_asesores": 0, "tasa_promedio": 0.0}

    
    async def _calcular_tiempo_respuesta_asesores(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> Dict[str, Any]:
        """KPI 3: Tiempo de Respuesta Promedio (TTFO por Asesor)"""
        ciudad_filter = "AND a.ciudad = $3" if ciudad else ""
        params = [fecha_inicio, fecha_fin]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        WITH tiempos_respuesta AS (
            SELECT 
                o.asesor_id,
                EXTRACT(EPOCH FROM (o.created_at - sa.created_at)) / 60 as minutos
            FROM ofertas o
            JOIN solicitudes_asesores sa ON o.solicitud_id = sa.solicitud_id 
                AND o.asesor_id = sa.asesor_id
            JOIN asesores a ON o.asesor_id = a.id
            WHERE o.created_at BETWEEN $1 AND $2
            AND sa.created_at < o.created_at
            {ciudad_filter}
        )
        SELECT 
            COUNT(DISTINCT asesor_id) as asesores_con_respuestas,
            ROUND(AVG(minutos), 2) as tiempo_promedio_minutos,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY minutos), 2) as mediana_minutos,
            ROUND(MIN(minutos), 2) as min_minutos,
            ROUND(MAX(minutos), 2) as max_minutos
        FROM tiempos_respuesta
        """
        result = await self._execute_query(query, params)
        if result and result[0]['asesores_con_respuestas']:
            return {
                "asesores_con_respuestas": result[0]['asesores_con_respuestas'],
                "tiempo_promedio_minutos": float(result[0]['tiempo_promedio_minutos'] or 0),
                "mediana_minutos": float(result[0]['mediana_minutos'] or 0),
                "min_minutos": float(result[0]['min_minutos'] or 0),
                "max_minutos": float(result[0]['max_minutos'] or 0)
            }
        return {"asesores_con_respuestas": 0, "tiempo_promedio_minutos": 0.0, "mediana_minutos": 0.0, "min_minutos": 0.0, "max_minutos": 0.0}

    
    async def _calcular_ofertas_por_asesor(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> Dict[str, Any]:
        """KPI 4: Ofertas por Asesor (Promedio)"""
        ciudad_filter = "AND a.ciudad = $3" if ciudad else ""
        params = [fecha_inicio, fecha_fin]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        WITH ofertas_por_asesor AS (
            SELECT 
                o.asesor_id,
                COUNT(*) as total_ofertas
            FROM ofertas o
            JOIN asesores a ON o.asesor_id = a.id
            WHERE o.created_at BETWEEN $1 AND $2
            {ciudad_filter}
            GROUP BY o.asesor_id
        )
        SELECT 
            COUNT(*) as total_asesores,
            ROUND(AVG(total_ofertas), 2) as ofertas_promedio,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_ofertas), 2) as mediana,
            MIN(total_ofertas) as min_ofertas,
            MAX(total_ofertas) as max_ofertas
        FROM ofertas_por_asesor
        """
        result = await self._execute_query(query, params)
        if result and result[0]['total_asesores']:
            return {
                "total_asesores": result[0]['total_asesores'],
                "ofertas_promedio": float(result[0]['ofertas_promedio'] or 0),
                "mediana": float(result[0]['mediana'] or 0),
                "min_ofertas": result[0]['min_ofertas'],
                "max_ofertas": result[0]['max_ofertas']
            }
        return {"total_asesores": 0, "ofertas_promedio": 0.0, "mediana": 0.0, "min_ofertas": 0, "max_ofertas": 0}

    
    async def _calcular_tasa_adjudicacion_asesor(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> Dict[str, Any]:
        """KPI 5: Tasa de Adjudicación por Asesor"""
        ciudad_filter = "AND a.ciudad = $3" if ciudad else ""
        params = [fecha_inicio, fecha_fin]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        WITH estadisticas_asesor AS (
            SELECT 
                o.asesor_id,
                COUNT(*) as total_ofertas,
                COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras,
                CASE 
                    WHEN COUNT(*) > 0 THEN 
                        ROUND(COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END)::FLOAT / COUNT(*) * 100, 2)
                    ELSE 0 
                END as tasa_adjudicacion
            FROM ofertas o
            JOIN asesores a ON o.asesor_id = a.id
            WHERE o.created_at BETWEEN $1 AND $2
            {ciudad_filter}
            GROUP BY o.asesor_id
        )
        SELECT 
            COUNT(*) as total_asesores,
            ROUND(AVG(tasa_adjudicacion), 2) as tasa_promedio,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tasa_adjudicacion), 2) as mediana,
            ROUND(MIN(tasa_adjudicacion), 2) as min_tasa,
            ROUND(MAX(tasa_adjudicacion), 2) as max_tasa
        FROM estadisticas_asesor
        """
        result = await self._execute_query(query, params)
        if result and result[0]['total_asesores']:
            return {
                "total_asesores": result[0]['total_asesores'],
                "tasa_promedio": float(result[0]['tasa_promedio'] or 0),
                "mediana": float(result[0]['mediana'] or 0),
                "min_tasa": float(result[0]['min_tasa'] or 0),
                "max_tasa": float(result[0]['max_tasa'] or 0)
            }
        return {"total_asesores": 0, "tasa_promedio": 0.0, "mediana": 0.0, "min_tasa": 0.0, "max_tasa": 0.0}

    
    async def _calcular_ranking_top_asesores(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> list:
        """KPI 6: Ranking Top 10 Asesores"""
        ciudad_filter = "AND a.ciudad = $3" if ciudad else ""
        params = [fecha_inicio, fecha_fin]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        WITH ofertas_totales AS (
            SELECT asesor_id, COUNT(*) as total
            FROM ofertas 
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY asesor_id
        )
        SELECT 
            a.id,
            a.nombre_comercial,
            a.ciudad,
            COUNT(o.id) as ofertas_ganadoras,
            ROUND(AVG(COALESCE(ev.puntaje_total, 0)), 2) as puntaje_promedio,
            ROUND(COUNT(o.id)::FLOAT / NULLIF(ot.total, 0) * 100, 2) as tasa_adjudicacion
        FROM asesores a
        JOIN ofertas o ON a.id = o.asesor_id
        LEFT JOIN evaluaciones ev ON o.id = ev.oferta_id
        LEFT JOIN ofertas_totales ot ON a.id = ot.asesor_id
        WHERE o.estado = 'GANADORA'
        AND o.created_at BETWEEN $1 AND $2
        {ciudad_filter}
        GROUP BY a.id, a.nombre_comercial, a.ciudad, ot.total
        ORDER BY ofertas_ganadoras DESC, puntaje_promedio DESC
        LIMIT 10
        """
        result = await self._execute_query(query, params)
        if result:
            return [
                {
                    "id": row['id'],
                    "nombre_comercial": row['nombre_comercial'],
                    "ciudad": row['ciudad'],
                    "ofertas_ganadoras": row['ofertas_ganadoras'],
                    "puntaje_promedio": float(row['puntaje_promedio'] or 0),
                    "tasa_adjudicacion": float(row['tasa_adjudicacion'] or 0)
                }
                for row in result
            ]
        return []

    
    async def _calcular_especializacion_repuestos(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> list:
        """KPI 7: Especialización por Tipo de Repuesto"""
        ciudad_filter = "AND a.ciudad = $3" if ciudad else ""
        params = [fecha_inicio, fecha_fin]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        SELECT 
            rs.categoria,
            COUNT(DISTINCT o.asesor_id) as asesores_participantes,
            COUNT(o.id) as total_ofertas,
            COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras,
            ROUND(COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END)::FLOAT / NULLIF(COUNT(o.id), 0) * 100, 2) as tasa_exito
        FROM ofertas o
        JOIN asesores a ON o.asesor_id = a.id
        JOIN ofertas_detalle od ON o.id = od.oferta_id
        JOIN repuestos_solicitud rs ON od.repuesto_solicitud_id = rs.id
        WHERE o.created_at BETWEEN $1 AND $2
        {ciudad_filter}
        GROUP BY rs.categoria
        ORDER BY total_ofertas DESC
        LIMIT 20
        """
        result = await self._execute_query(query, params)
        if result:
            return [
                {
                    "categoria": row['categoria'],
                    "asesores_participantes": row['asesores_participantes'],
                    "total_ofertas": row['total_ofertas'],
                    "ofertas_ganadoras": row['ofertas_ganadoras'],
                    "tasa_exito": float(row['tasa_exito'] or 0)
                }
                for row in result
            ]
        return []

    
    async def _calcular_distribucion_geografica(self, fecha_inicio: datetime, fecha_fin: datetime) -> list:
        """KPI 8: Distribución Geográfica"""
        query = """
        SELECT 
            a.ciudad,
            COUNT(DISTINCT a.id) as asesores_activos,
            COUNT(o.id) as total_ofertas,
            COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras,
            ROUND(AVG(CASE 
                WHEN o.estado = 'GANADORA' THEN 1.0 
                ELSE 0.0 
            END) * 100, 2) as tasa_adjudicacion
        FROM asesores a
        JOIN ofertas o ON a.id = o.asesor_id
        WHERE o.created_at BETWEEN $1 AND $2
        GROUP BY a.ciudad
        ORDER BY asesores_activos DESC
        LIMIT 20
        """
        result = await self._execute_query(query, [fecha_inicio, fecha_fin])
        if result:
            return [
                {
                    "ciudad": row['ciudad'],
                    "asesores_activos": row['asesores_activos'],
                    "total_ofertas": row['total_ofertas'],
                    "ofertas_ganadoras": row['ofertas_ganadoras'],
                    "tasa_adjudicacion": float(row['tasa_adjudicacion'] or 0)
                }
                for row in result
            ]
        return []

    
    async def _calcular_nivel_confianza_promedio(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> Dict[str, Any]:
        """KPI 9: Nivel de Confianza Promedio"""
        ciudad_filter = "AND a.ciudad = $3" if ciudad else ""
        params = [fecha_inicio, fecha_fin]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        SELECT 
            COUNT(DISTINCT a.id) as total_asesores,
            ROUND(AVG(a.nivel_confianza), 2) as nivel_promedio,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY a.nivel_confianza), 2) as mediana,
            ROUND(MIN(a.nivel_confianza), 2) as min_nivel,
            ROUND(MAX(a.nivel_confianza), 2) as max_nivel
        FROM asesores a
        WHERE a.id IN (
            SELECT DISTINCT asesor_id 
            FROM ofertas 
            WHERE created_at BETWEEN $1 AND $2
        )
        {ciudad_filter}
        """
        result = await self._execute_query(query, params)
        if result and result[0]['total_asesores']:
            return {
                "total_asesores": result[0]['total_asesores'],
                "nivel_promedio": float(result[0]['nivel_promedio'] or 0),
                "mediana": float(result[0]['mediana'] or 0),
                "min_nivel": float(result[0]['min_nivel'] or 0),
                "max_nivel": float(result[0]['max_nivel'] or 0)
            }
        return {"total_asesores": 0, "nivel_promedio": 0.0, "mediana": 0.0, "min_nivel": 0.0, "max_nivel": 0.0}

    
    async def _calcular_asesores_nuevos(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> Dict[str, Any]:
        """KPI 10: Asesores Nuevos"""
        ciudad_filter = "AND ciudad = $3" if ciudad else ""
        params = [fecha_inicio, fecha_fin]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        SELECT 
            COUNT(*) as asesores_nuevos,
            COUNT(CASE WHEN estado = 'ACTIVO' THEN 1 END) as activos,
            COUNT(CASE WHEN id IN (
                SELECT DISTINCT asesor_id FROM ofertas 
                WHERE created_at BETWEEN $1 AND $2
            ) THEN 1 END) as con_ofertas
        FROM asesores
        WHERE created_at BETWEEN $1 AND $2
        {ciudad_filter}
        """
        result = await self._execute_query(query, params)
        if result:
            return {
                "asesores_nuevos": result[0]['asesores_nuevos'],
                "activos": result[0]['activos'],
                "con_ofertas": result[0]['con_ofertas']
            }
        return {"asesores_nuevos": 0, "activos": 0, "con_ofertas": 0}

    
    async def _calcular_tasa_retencion_asesores(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> Dict[str, Any]:
        """KPI 11: Tasa de Retención"""
        ciudad_filter = "AND a.ciudad = $4" if ciudad else ""
        params = [fecha_inicio, fecha_fin, fecha_inicio]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        WITH periodo_anterior AS (
            SELECT DISTINCT o.asesor_id
            FROM ofertas o
            JOIN asesores a ON o.asesor_id = a.id
            WHERE o.created_at BETWEEN $1 - INTERVAL '30 days' AND $1
            {ciudad_filter}
        ),
        periodo_actual AS (
            SELECT DISTINCT o.asesor_id
            FROM ofertas o
            JOIN asesores a ON o.asesor_id = a.id
            WHERE o.created_at BETWEEN $1 AND $2
            {ciudad_filter}
        )
        SELECT 
            (SELECT COUNT(*) FROM periodo_anterior) as asesores_periodo_anterior,
            (SELECT COUNT(*) FROM periodo_actual WHERE asesor_id IN (SELECT asesor_id FROM periodo_anterior)) as asesores_retenidos,
            ROUND(
                (SELECT COUNT(*) FROM periodo_actual WHERE asesor_id IN (SELECT asesor_id FROM periodo_anterior))::FLOAT / 
                NULLIF((SELECT COUNT(*) FROM periodo_anterior), 0) * 100, 
                2
            ) as tasa_retencion
        """
        result = await self._execute_query(query, params)
        if result:
            return {
                "asesores_periodo_anterior": result[0]['asesores_periodo_anterior'],
                "asesores_retenidos": result[0]['asesores_retenidos'],
                "tasa_retencion": float(result[0]['tasa_retencion'] or 0)
            }
        return {"asesores_periodo_anterior": 0, "asesores_retenidos": 0, "tasa_retencion": 0.0}

    
    async def _calcular_satisfaccion_cliente_asesores(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> Dict[str, Any]:
        """KPI 12: Satisfacción del Cliente (por Asesor)"""
        ciudad_filter = "AND a.ciudad = $3" if ciudad else ""
        params = [fecha_inicio, fecha_fin]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        SELECT 
            COUNT(DISTINCT o.asesor_id) as asesores_calificados,
            ROUND(AVG(s.calificacion_asesor), 2) as calificacion_promedio,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.calificacion_asesor), 2) as mediana,
            ROUND(MIN(s.calificacion_asesor), 2) as min_calificacion,
            ROUND(MAX(s.calificacion_asesor), 2) as max_calificacion
        FROM ofertas o
        JOIN solicitudes s ON o.solicitud_id = s.id
        JOIN asesores a ON o.asesor_id = a.id
        WHERE o.estado = 'GANADORA'
        AND s.calificacion_asesor IS NOT NULL
        AND o.created_at BETWEEN $1 AND $2
        {ciudad_filter}
        """
        result = await self._execute_query(query, params)
        if result and result[0]['asesores_calificados']:
            return {
                "asesores_calificados": result[0]['asesores_calificados'],
                "calificacion_promedio": float(result[0]['calificacion_promedio'] or 0),
                "mediana": float(result[0]['mediana'] or 0),
                "min_calificacion": float(result[0]['min_calificacion'] or 0),
                "max_calificacion": float(result[0]['max_calificacion'] or 0)
            }
        return {"asesores_calificados": 0, "calificacion_promedio": 0.0, "mediana": 0.0, "min_calificacion": 0.0, "max_calificacion": 0.0}

    
    async def _calcular_valor_promedio_oferta_asesor(self, fecha_inicio: datetime, fecha_fin: datetime, ciudad: str = None) -> Dict[str, Any]:
        """KPI 13: Valor Promedio de Oferta por Asesor"""
        ciudad_filter = "AND a.ciudad = $3" if ciudad else ""
        params = [fecha_inicio, fecha_fin]
        if ciudad:
            params.append(ciudad)
            
        query = f"""
        WITH valores_por_asesor AS (
            SELECT 
                o.asesor_id,
                SUM(od.precio_unitario * rs.cantidad) as valor_oferta
            FROM ofertas o
            JOIN asesores a ON o.asesor_id = a.id
            JOIN ofertas_detalle od ON o.id = od.oferta_id
            JOIN repuestos_solicitud rs ON od.repuesto_solicitud_id = rs.id
            WHERE o.created_at BETWEEN $1 AND $2
            {ciudad_filter}
            GROUP BY o.asesor_id, o.id
        )
        SELECT 
            COUNT(DISTINCT asesor_id) as total_asesores,
            ROUND(AVG(valor_oferta), 0) as valor_promedio,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_oferta), 0) as mediana,
            ROUND(MIN(valor_oferta), 0) as min_valor,
            ROUND(MAX(valor_oferta), 0) as max_valor
        FROM valores_por_asesor
        """
        result = await self._execute_query(query, params)
        if result and result[0]['total_asesores']:
            return {
                "total_asesores": result[0]['total_asesores'],
                "valor_promedio": int(result[0]['valor_promedio'] or 0),
                "mediana": int(result[0]['mediana'] or 0),
                "min_valor": int(result[0]['min_valor'] or 0),
                "max_valor": int(result[0]['max_valor'] or 0)
            }
        return {"total_asesores": 0, "valor_promedio": 0, "mediana": 0, "min_valor": 0, "max_valor": 0}
