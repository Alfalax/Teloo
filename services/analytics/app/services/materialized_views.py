"""
Materialized Views Service for Analytics
Manages creation, refresh, and querying of materialized views for KPIs históricos
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from tortoise import connections
from tortoise.exceptions import OperationalError

logger = logging.getLogger(__name__)

class MaterializedViewsService:
    """
    Service to manage materialized views for historical KPIs
    """
    
    def __init__(self):
        self.connection_name = "default"
    
    async def get_connection(self):
        """Get database connection"""
        return connections.get(self.connection_name)
    
    async def create_materialized_views(self) -> bool:
        """
        Create all materialized views for historical KPIs
        Returns True if successful, False otherwise
        """
        try:
            conn = await self.get_connection()
            
            # Create mv_metricas_mensuales
            await self._create_mv_metricas_mensuales(conn)
            
            # Create mv_ranking_asesores
            await self._create_mv_ranking_asesores(conn)
            
            # Create refresh function
            await self._create_refresh_function(conn)
            
            logger.info("Materialized views created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating materialized views: {e}")
            return False
    
    async def _create_mv_metricas_mensuales(self, conn):
        """Create materialized view for monthly metrics"""
        sql = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_metricas_mensuales AS
        SELECT 
            DATE_TRUNC('month', s.created_at) as mes,
            COUNT(*) as solicitudes_creadas,
            COUNT(CASE WHEN s.estado = 'OFERTAS_ACEPTADAS' THEN 1 END) as solicitudes_aceptadas,
            COUNT(CASE WHEN s.estado = 'OFERTAS_RECHAZADAS' THEN 1 END) as solicitudes_rechazadas,
            COUNT(CASE WHEN s.estado = 'CERRADA_SIN_OFERTAS' THEN 1 END) as solicitudes_cerradas_sin_ofertas,
            AVG(EXTRACT(EPOCH FROM (s.updated_at - s.created_at))) as tiempo_promedio_cierre_seg,
            COUNT(DISTINCT o.id) as ofertas_totales,
            COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras,
            COUNT(CASE WHEN o.estado = 'EXPIRADA' THEN 1 END) as ofertas_expiradas,
            COUNT(CASE WHEN o.estado = 'ACEPTADA' THEN 1 END) as ofertas_aceptadas_cliente,
            COUNT(CASE WHEN o.estado = 'RECHAZADA' THEN 1 END) as ofertas_rechazadas_cliente,
            AVG(od.precio_unitario) as precio_promedio_ofertas,
            AVG(o.tiempo_entrega_dias) as tiempo_entrega_promedio,
            COUNT(DISTINCT s.cliente_id) as clientes_activos,
            COUNT(DISTINCT o.asesor_id) as asesores_activos
        FROM solicitudes s
        LEFT JOIN ofertas o ON s.id = o.solicitud_id
        LEFT JOIN ofertas_detalle od ON o.id = od.oferta_id
        GROUP BY DATE_TRUNC('month', s.created_at)
        ORDER BY mes DESC;
        """
        
        await conn.execute_query(sql)
        
        # Create index for better performance
        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_mv_metricas_mensuales_mes 
        ON mv_metricas_mensuales(mes);
        """
        await conn.execute_query(index_sql)
    
    async def _create_mv_ranking_asesores(self, conn):
        """Create materialized view for advisor rankings by city"""
        sql = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ranking_asesores AS
        SELECT 
            a.id as asesor_id,
            u.nombre as asesor_nombre,
            a.ciudad,
            a.departamento,
            a.confianza,
            a.nivel_actual,
            a.actividad_reciente_pct,
            a.desempeno_historico_pct,
            COUNT(oh.id) as ofertas_historicas_total,
            COUNT(CASE WHEN oh.adjudicada = true THEN 1 END) as ofertas_ganadoras,
            COUNT(CASE WHEN oh.entrega_exitosa = true THEN 1 END) as entregas_exitosas,
            AVG(oh.tiempo_respuesta_seg) as tiempo_promedio_respuesta_seg,
            AVG(oh.monto_total) as monto_promedio_ofertas,
            COALESCE(AVG(at.puntaje_confianza), a.confianza) as confianza_auditada,
            COUNT(hr.id) as notificaciones_recibidas,
            COUNT(CASE WHEN hr.respondio = true THEN 1 END) as notificaciones_respondidas,
            CASE 
                WHEN COUNT(hr.id) > 0 THEN 
                    (COUNT(CASE WHEN hr.respondio = true THEN 1 END)::float / COUNT(hr.id)::float) * 100
                ELSE 0 
            END as tasa_respuesta_pct,
            RANK() OVER (
                PARTITION BY a.ciudad 
                ORDER BY COUNT(CASE WHEN oh.adjudicada = true THEN 1 END) DESC,
                         AVG(oh.tiempo_respuesta_seg) ASC NULLS LAST
            ) as ranking_ciudad,
            RANK() OVER (
                ORDER BY COUNT(CASE WHEN oh.adjudicada = true THEN 1 END) DESC,
                         AVG(oh.tiempo_respuesta_seg) ASC NULLS LAST
            ) as ranking_nacional,
            NOW() as calculado_at
        FROM asesores a
        INNER JOIN usuarios u ON a.usuario_id = u.id
        LEFT JOIN ofertas_historicas oh ON a.id = oh.asesor_id 
            AND oh.fecha >= NOW() - INTERVAL '30 days'
        LEFT JOIN auditoria_tiendas at ON a.id = at.asesor_id
            AND at.fecha_revision >= NOW() - INTERVAL '90 days'
        LEFT JOIN historial_respuestas_ofertas hr ON a.id = hr.asesor_id
            AND hr.fecha_envio >= NOW() - INTERVAL '30 days'
        WHERE a.estado = 'ACTIVO'
        GROUP BY a.id, u.nombre, a.ciudad, a.departamento, a.confianza, 
                 a.nivel_actual, a.actividad_reciente_pct, a.desempeno_historico_pct
        ORDER BY ranking_nacional;
        """
        
        await conn.execute_query(sql)
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_mv_ranking_asesores_ciudad ON mv_ranking_asesores(ciudad);",
            "CREATE INDEX IF NOT EXISTS idx_mv_ranking_asesores_ranking_ciudad ON mv_ranking_asesores(ranking_ciudad);",
            "CREATE INDEX IF NOT EXISTS idx_mv_ranking_asesores_ranking_nacional ON mv_ranking_asesores(ranking_nacional);",
            "CREATE INDEX IF NOT EXISTS idx_mv_ranking_asesores_asesor_id ON mv_ranking_asesores(asesor_id);"
        ]
        
        for index_sql in indexes:
            await conn.execute_query(index_sql)
    
    async def _create_refresh_function(self, conn):
        """Create PostgreSQL function to refresh all materialized views"""
        sql = """
        CREATE OR REPLACE FUNCTION refresh_all_mv()
        RETURNS TABLE(
            view_name TEXT,
            refresh_status TEXT,
            refresh_time_ms BIGINT,
            error_message TEXT
        ) AS $$
        DECLARE
            start_time TIMESTAMP;
            end_time TIMESTAMP;
            duration_ms BIGINT;
        BEGIN
            -- Refresh mv_metricas_mensuales
            BEGIN
                start_time := clock_timestamp();
                REFRESH MATERIALIZED VIEW CONCURRENTLY mv_metricas_mensuales;
                end_time := clock_timestamp();
                duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
                
                RETURN QUERY SELECT 
                    'mv_metricas_mensuales'::TEXT,
                    'SUCCESS'::TEXT,
                    duration_ms,
                    NULL::TEXT;
            EXCEPTION WHEN OTHERS THEN
                RETURN QUERY SELECT 
                    'mv_metricas_mensuales'::TEXT,
                    'ERROR'::TEXT,
                    0::BIGINT,
                    SQLERRM::TEXT;
            END;
            
            -- Refresh mv_ranking_asesores
            BEGIN
                start_time := clock_timestamp();
                REFRESH MATERIALIZED VIEW CONCURRENTLY mv_ranking_asesores;
                end_time := clock_timestamp();
                duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
                
                RETURN QUERY SELECT 
                    'mv_ranking_asesores'::TEXT,
                    'SUCCESS'::TEXT,
                    duration_ms,
                    NULL::TEXT;
            EXCEPTION WHEN OTHERS THEN
                RETURN QUERY SELECT 
                    'mv_ranking_asesores'::TEXT,
                    'ERROR'::TEXT,
                    0::BIGINT,
                    SQLERRM::TEXT;
            END;
            
            RETURN;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        await conn.execute_query(sql)
    
    async def refresh_materialized_views(self) -> Dict[str, Any]:
        """
        Refresh all materialized views and return status
        """
        try:
            conn = await self.get_connection()
            
            # Execute refresh function
            result = await conn.execute_query("SELECT * FROM refresh_all_mv();")
            
            refresh_results = []
            for row in result[1]:  # result[1] contains the data rows
                refresh_results.append({
                    'view_name': row[0],
                    'status': row[1],
                    'duration_ms': row[2],
                    'error_message': row[3]
                })
            
            success_count = sum(1 for r in refresh_results if r['status'] == 'SUCCESS')
            total_duration = sum(r['duration_ms'] for r in refresh_results if r['duration_ms'])
            
            return {
                'success': success_count == len(refresh_results),
                'total_views': len(refresh_results),
                'successful_refreshes': success_count,
                'total_duration_ms': total_duration,
                'refreshed_at': datetime.now().isoformat(),
                'details': refresh_results
            }
            
        except Exception as e:
            logger.error(f"Error refreshing materialized views: {e}")
            return {
                'success': False,
                'error': str(e),
                'refreshed_at': datetime.now().isoformat()
            }
    
    async def get_monthly_metrics(self, 
                                 start_month: Optional[datetime] = None,
                                 end_month: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get monthly metrics from materialized view
        """
        try:
            conn = await self.get_connection()
            
            where_clause = ""
            params = []
            
            if start_month:
                where_clause += " WHERE mes >= $1"
                params.append(start_month)
                
            if end_month:
                if where_clause:
                    where_clause += " AND mes <= $2"
                else:
                    where_clause += " WHERE mes <= $1"
                params.append(end_month)
            
            sql = f"""
            SELECT 
                mes,
                solicitudes_creadas,
                solicitudes_aceptadas,
                solicitudes_rechazadas,
                solicitudes_expiradas,
                tiempo_promedio_cierre_seg,
                ofertas_totales,
                ofertas_ganadoras,
                precio_promedio_ofertas,
                tiempo_entrega_promedio,
                clientes_activos,
                asesores_activos,
                CASE 
                    WHEN solicitudes_creadas > 0 THEN 
                        (solicitudes_aceptadas::float / solicitudes_creadas::float) * 100
                    ELSE 0 
                END as tasa_aceptacion_pct,
                CASE 
                    WHEN ofertas_totales > 0 THEN 
                        (ofertas_ganadoras::float / ofertas_totales::float) * 100
                    ELSE 0 
                END as tasa_conversion_ofertas_pct
            FROM mv_metricas_mensuales
            {where_clause}
            ORDER BY mes DESC
            """
            
            result = await conn.execute_query(sql, params)
            
            metrics = []
            for row in result[1]:
                metrics.append({
                    'mes': row[0].isoformat() if row[0] else None,
                    'solicitudes_creadas': row[1],
                    'solicitudes_aceptadas': row[2],
                    'solicitudes_rechazadas': row[3],
                    'solicitudes_expiradas': row[4],
                    'tiempo_promedio_cierre_seg': float(row[5]) if row[5] else 0,
                    'ofertas_totales': row[6],
                    'ofertas_ganadoras': row[7],
                    'precio_promedio_ofertas': float(row[8]) if row[8] else 0,
                    'tiempo_entrega_promedio': float(row[9]) if row[9] else 0,
                    'clientes_activos': row[10],
                    'asesores_activos': row[11],
                    'tasa_aceptacion_pct': float(row[12]) if row[12] else 0,
                    'tasa_conversion_ofertas_pct': float(row[13]) if row[13] else 0
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting monthly metrics: {e}")
            return []
    
    async def get_advisor_rankings(self, 
                                  ciudad: Optional[str] = None,
                                  limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get advisor rankings from materialized view
        """
        try:
            conn = await self.get_connection()
            
            where_clause = ""
            params = []
            
            if ciudad:
                where_clause = " WHERE ciudad = $1"
                params.append(ciudad)
            
            sql = f"""
            SELECT 
                asesor_id,
                asesor_nombre,
                ciudad,
                departamento,
                confianza,
                nivel_actual,
                actividad_reciente_pct,
                desempeno_historico_pct,
                ofertas_historicas_total,
                ofertas_ganadoras,
                entregas_exitosas,
                tiempo_promedio_respuesta_seg,
                monto_promedio_ofertas,
                confianza_auditada,
                notificaciones_recibidas,
                notificaciones_respondidas,
                tasa_respuesta_pct,
                ranking_ciudad,
                ranking_nacional,
                calculado_at
            FROM mv_ranking_asesores
            {where_clause}
            ORDER BY {"ranking_ciudad" if ciudad else "ranking_nacional"}
            LIMIT ${"2" if ciudad else "1"}
            """
            
            params.append(limit)
            result = await conn.execute_query(sql, params)
            
            rankings = []
            for row in result[1]:
                rankings.append({
                    'asesor_id': str(row[0]),
                    'asesor_nombre': row[1],
                    'ciudad': row[2],
                    'departamento': row[3],
                    'confianza': float(row[4]) if row[4] else 0,
                    'nivel_actual': row[5],
                    'actividad_reciente_pct': float(row[6]) if row[6] else 0,
                    'desempeno_historico_pct': float(row[7]) if row[7] else 0,
                    'ofertas_historicas_total': row[8],
                    'ofertas_ganadoras': row[9],
                    'entregas_exitosas': row[10],
                    'tiempo_promedio_respuesta_seg': float(row[11]) if row[11] else 0,
                    'monto_promedio_ofertas': float(row[12]) if row[12] else 0,
                    'confianza_auditada': float(row[13]) if row[13] else 0,
                    'notificaciones_recibidas': row[14],
                    'notificaciones_respondidas': row[15],
                    'tasa_respuesta_pct': float(row[16]) if row[16] else 0,
                    'ranking_ciudad': row[17],
                    'ranking_nacional': row[18],
                    'calculado_at': row[19].isoformat() if row[19] else None
                })
            
            return rankings
            
        except Exception as e:
            logger.error(f"Error getting advisor rankings: {e}")
            return []
    
    async def get_view_status(self) -> Dict[str, Any]:
        """
        Get status information about materialized views
        """
        try:
            conn = await self.get_connection()
            
            # Check if views exist and get basic info
            sql = """
            SELECT 
                schemaname,
                matviewname,
                hasindexes,
                ispopulated,
                definition
            FROM pg_matviews 
            WHERE matviewname IN ('mv_metricas_mensuales', 'mv_ranking_asesores')
            ORDER BY matviewname;
            """
            
            result = await conn.execute_query(sql)
            
            views_info = []
            for row in result[1]:
                views_info.append({
                    'schema': row[0],
                    'name': row[1],
                    'has_indexes': row[2],
                    'is_populated': row[3],
                    'definition': row[4][:200] + '...' if len(row[4]) > 200 else row[4]
                })
            
            # Get row counts
            counts = {}
            for view_name in ['mv_metricas_mensuales', 'mv_ranking_asesores']:
                try:
                    count_result = await conn.execute_query(f"SELECT COUNT(*) FROM {view_name};")
                    counts[view_name] = count_result[1][0][0] if count_result[1] else 0
                except:
                    counts[view_name] = 0
            
            return {
                'views': views_info,
                'row_counts': counts,
                'checked_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting view status: {e}")
            return {
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }

# Global instance
materialized_views_service = MaterializedViewsService()
