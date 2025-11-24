"""
Batch Jobs Service for Analytics
Handles scheduled complex metrics calculations
"""
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from tortoise import connections
from app.core.redis import redis_manager
from app.models.metrics import MetricaCalculada, TipoMetrica
from app.core.config import settings

logger = logging.getLogger(__name__)

class BatchJobsService:
    """
    Service for running batch jobs to calculate complex metrics
    """
    
    def __init__(self):
        self.cache_prefix = "batch_metrics:"
        
    async def run_daily_batch_job(self, fecha: date = None) -> Dict[str, Any]:
        """
        Job diario (2 AM): ranking de asesores, especialización por repuesto
        
        Args:
            fecha: Fecha para calcular métricas (default: ayer)
            
        Returns:
            Dict con resultado del procesamiento
        """
        try:
            if not fecha:
                fecha = (datetime.now() - timedelta(days=1)).date()
                
            logger.info(f"Iniciando job diario de métricas para {fecha}")
            
            start_time = datetime.now()
            results = {}
            
            # 1. Calcular ranking de asesores
            ranking_result = await self._calcular_ranking_asesores(fecha)
            results['ranking_asesores'] = ranking_result
            
            # 2. Calcular especialización por repuesto
            especializacion_result = await self._calcular_especializacion_repuestos(fecha)
            results['especializacion_repuestos'] = especializacion_result
            
            # 3. Calcular métricas de conversión por ciudad
            conversion_result = await self._calcular_conversion_por_ciudad(fecha)
            results['conversion_ciudades'] = conversion_result
            
            # 4. Calcular tiempo promedio de respuesta por asesor
            tiempo_respuesta_result = await self._calcular_tiempo_respuesta_asesores(fecha)
            results['tiempo_respuesta_asesores'] = tiempo_respuesta_result
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Job diario completado en {execution_time:.2f}s")
            
            return {
                'success': True,
                'fecha': fecha.isoformat(),
                'execution_time_seconds': execution_time,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en job diario: {e}")
            return {
                'success': False,
                'error': str(e),
                'fecha': fecha.isoformat() if fecha else None,
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_weekly_batch_job(self, fecha_fin: date = None) -> Dict[str, Any]:
        """
        Job semanal: evolución temporal, análisis de tendencias
        
        Args:
            fecha_fin: Fecha final del período (default: ayer)
            
        Returns:
            Dict con resultado del procesamiento
        """
        try:
            if not fecha_fin:
                fecha_fin = (datetime.now() - timedelta(days=1)).date()
            fecha_inicio = fecha_fin - timedelta(days=6)  # Última semana
            
            logger.info(f"Iniciando job semanal de métricas para {fecha_inicio} - {fecha_fin}")
            
            start_time = datetime.now()
            results = {}
            
            # 1. Análisis de tendencias de solicitudes
            tendencias_result = await self._analizar_tendencias_solicitudes(fecha_inicio, fecha_fin)
            results['tendencias_solicitudes'] = tendencias_result
            
            # 2. Evolución de métricas de asesores
            evolucion_asesores_result = await self._analizar_evolucion_asesores(fecha_inicio, fecha_fin)
            results['evolucion_asesores'] = evolucion_asesores_result
            
            # 3. Análisis de patrones de demanda por repuesto
            patrones_demanda_result = await self._analizar_patrones_demanda(fecha_inicio, fecha_fin)
            results['patrones_demanda'] = patrones_demanda_result
            
            # 4. Métricas de satisfacción y calidad
            satisfaccion_result = await self._calcular_metricas_satisfaccion(fecha_inicio, fecha_fin)
            results['metricas_satisfaccion'] = satisfaccion_result
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Job semanal completado en {execution_time:.2f}s")
            
            return {
                'success': True,
                'fecha_inicio': fecha_inicio.isoformat(),
                'fecha_fin': fecha_fin.isoformat(),
                'execution_time_seconds': execution_time,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en job semanal: {e}")
            return {
                'success': False,
                'error': str(e),
                'fecha_inicio': fecha_inicio.isoformat() if 'fecha_inicio' in locals() else None,
                'fecha_fin': fecha_fin.isoformat() if fecha_fin else None,
                'timestamp': datetime.now().isoformat()
            }
    
    # Métodos privados para cálculos específicos
    
    async def _calcular_ranking_asesores(self, fecha: date) -> Dict[str, Any]:
        """Calcular ranking de asesores por desempeño"""
        try:
            conn = connections.get("default")
            
            query = """
            WITH asesor_stats AS (
                SELECT 
                    a.id as asesor_id,
                    u.nombre_completo,
                    COUNT(o.id) as ofertas_enviadas,
                    COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras,
                    AVG(EXTRACT(EPOCH FROM (o.created_at - s.created_at))/3600) as tiempo_promedio_respuesta_horas,
                    AVG(od.precio * od.cantidad) as valor_promedio_oferta,
                    COUNT(CASE WHEN ev.resultado = 'ACEPTADA' THEN 1 END) as ofertas_aceptadas
                FROM asesores a
                JOIN usuarios u ON a.usuario_id = u.id
                LEFT JOIN ofertas o ON a.id = o.asesor_id AND DATE(o.created_at) = $1
                LEFT JOIN solicitudes s ON o.solicitud_id = s.id
                LEFT JOIN ofertas_detalle od ON o.id = od.oferta_id
                LEFT JOIN evaluaciones ev ON o.id = ev.oferta_ganadora_id
                WHERE a.activo = true
                GROUP BY a.id, u.nombre_completo
                HAVING COUNT(o.id) > 0
            )
            SELECT 
                asesor_id,
                nombre_completo,
                ofertas_enviadas,
                ofertas_ganadoras,
                ofertas_aceptadas,
                COALESCE(tiempo_promedio_respuesta_horas, 0) as tiempo_promedio_respuesta_horas,
                COALESCE(valor_promedio_oferta, 0) as valor_promedio_oferta,
                CASE 
                    WHEN ofertas_enviadas > 0 THEN 
                        ROUND((ofertas_ganadoras::float / ofertas_enviadas) * 100, 2)
                    ELSE 0 
                END as tasa_exito,
                -- Puntaje compuesto (normalizado)
                ROUND(
                    (ofertas_ganadoras * 0.4) + 
                    ((ofertas_aceptadas * 0.3)) + 
                    (CASE WHEN tiempo_promedio_respuesta_horas > 0 THEN (24 / tiempo_promedio_respuesta_horas) * 0.3 ELSE 0 END),
                    2
                ) as puntaje_desempeno
            FROM asesor_stats
            ORDER BY puntaje_desempeno DESC, ofertas_ganadoras DESC
            LIMIT 50
            """
            
            result = await conn.execute_query_dict(query, [fecha])
            
            # Almacenar en MetricaCalculada
            await MetricaCalculada.create(
                nombre="ranking_asesores_diario",
                tipo=TipoMetrica.KPI,
                valor=len(result),
                descripcion="Ranking diario de asesores por desempeño",
                dimensiones={"fecha": fecha.isoformat(), "tipo": "ranking"},
                periodo_inicio=datetime.combine(fecha, datetime.min.time()),
                periodo_fin=datetime.combine(fecha, datetime.max.time()),
                expira_en=datetime.now() + timedelta(days=7)
            )
            
            return {
                'total_asesores': len(result),
                'ranking': result[:10],  # Top 10
                'fecha': fecha.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculando ranking de asesores: {e}")
            return {'error': str(e)}
    
    async def _calcular_especializacion_repuestos(self, fecha: date) -> Dict[str, Any]:
        """Calcular especialización de asesores por tipo de repuesto"""
        try:
            conn = connections.get("default")
            
            query = """
            WITH especializacion_data AS (
                SELECT 
                    a.id as asesor_id,
                    u.nombre_completo,
                    sd.nombre_repuesto,
                    sd.categoria_repuesto,
                    COUNT(o.id) as ofertas_categoria,
                    COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras_categoria,
                    AVG(od.precio) as precio_promedio_categoria
                FROM asesores a
                JOIN usuarios u ON a.usuario_id = u.id
                JOIN ofertas o ON a.id = o.asesor_id
                JOIN solicitudes s ON o.solicitud_id = s.id
                JOIN solicitudes_detalle sd ON s.id = sd.solicitud_id
                JOIN ofertas_detalle od ON o.id = od.oferta_id AND sd.nombre_repuesto = od.nombre_repuesto
                WHERE DATE(o.created_at) = $1
                GROUP BY a.id, u.nombre_completo, sd.nombre_repuesto, sd.categoria_repuesto
            ),
            asesor_totals AS (
                SELECT 
                    asesor_id,
                    COUNT(*) as total_ofertas,
                    COUNT(CASE WHEN ofertas_ganadoras_categoria > 0 THEN 1 END) as categorias_exitosas
                FROM especializacion_data
                GROUP BY asesor_id
            )
            SELECT 
                ed.asesor_id,
                ed.nombre_completo,
                ed.categoria_repuesto,
                ed.ofertas_categoria,
                ed.ofertas_ganadoras_categoria,
                ed.precio_promedio_categoria,
                ROUND((ed.ofertas_categoria::float / at.total_ofertas) * 100, 2) as porcentaje_especializacion,
                CASE 
                    WHEN ed.ofertas_categoria > 0 THEN 
                        ROUND((ed.ofertas_ganadoras_categoria::float / ed.ofertas_categoria) * 100, 2)
                    ELSE 0 
                END as tasa_exito_categoria
            FROM especializacion_data ed
            JOIN asesor_totals at ON ed.asesor_id = at.asesor_id
            WHERE ed.ofertas_categoria >= 3  -- Mínimo 3 ofertas para considerar especialización
            ORDER BY ed.asesor_id, porcentaje_especializacion DESC
            """
            
            result = await conn.execute_query_dict(query, [fecha])
            
            # Procesar datos para encontrar especializaciones principales
            especializaciones = {}
            for row in result:
                asesor_id = row['asesor_id']
                if asesor_id not in especializaciones:
                    especializaciones[asesor_id] = {
                        'nombre_completo': row['nombre_completo'],
                        'especializaciones': []
                    }
                
                if row['porcentaje_especializacion'] >= 30:  # 30% o más se considera especialización
                    especializaciones[asesor_id]['especializaciones'].append({
                        'categoria': row['categoria_repuesto'],
                        'porcentaje': row['porcentaje_especializacion'],
                        'tasa_exito': row['tasa_exito_categoria'],
                        'ofertas_total': row['ofertas_categoria']
                    })
            
            # Almacenar en MetricaCalculada
            await MetricaCalculada.create(
                nombre="especializacion_repuestos_diario",
                tipo=TipoMetrica.KPI,
                valor=len(especializaciones),
                descripcion="Especialización de asesores por categoría de repuesto",
                dimensiones={"fecha": fecha.isoformat(), "tipo": "especializacion"},
                periodo_inicio=datetime.combine(fecha, datetime.min.time()),
                periodo_fin=datetime.combine(fecha, datetime.max.time()),
                expira_en=datetime.now() + timedelta(days=7)
            )
            
            return {
                'total_asesores_especializados': len(especializaciones),
                'especializaciones': dict(list(especializaciones.items())[:20]),  # Top 20
                'fecha': fecha.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculando especialización por repuestos: {e}")
            return {'error': str(e)}
    
    async def _calcular_conversion_por_ciudad(self, fecha: date) -> Dict[str, Any]:
        """Calcular métricas de conversión por ciudad"""
        try:
            conn = connections.get("default")
            
            query = """
            SELECT 
                c.nombre as ciudad,
                COUNT(s.id) as solicitudes_total,
                COUNT(CASE WHEN s.estado != 'ABIERTA' THEN 1 END) as solicitudes_procesadas,
                COUNT(CASE WHEN s.estado = 'OFERTAS_ACEPTADAS' THEN 1 END) as solicitudes_aceptadas,
                COUNT(DISTINCT o.id) as ofertas_total,
                AVG(od.precio * od.cantidad) as valor_promedio_transaccion,
                CASE 
                    WHEN COUNT(s.id) > 0 THEN 
                        ROUND((COUNT(CASE WHEN s.estado = 'OFERTAS_ACEPTADAS' THEN 1 END)::float / COUNT(s.id)) * 100, 2)
                    ELSE 0 
                END as tasa_conversion
            FROM ciudades c
            LEFT JOIN solicitudes s ON c.id = s.ciudad_id AND DATE(s.created_at) = $1
            LEFT JOIN ofertas o ON s.id = o.solicitud_id
            LEFT JOIN ofertas_detalle od ON o.id = od.oferta_id
            GROUP BY c.id, c.nombre
            HAVING COUNT(s.id) > 0
            ORDER BY tasa_conversion DESC, solicitudes_total DESC
            """
            
            result = await conn.execute_query_dict(query, [fecha])
            
            # Almacenar en MetricaCalculada
            await MetricaCalculada.create(
                nombre="conversion_por_ciudad_diario",
                tipo=TipoMetrica.KPI,
                valor=len(result),
                descripcion="Métricas de conversión por ciudad",
                dimensiones={"fecha": fecha.isoformat(), "tipo": "conversion_ciudad"},
                periodo_inicio=datetime.combine(fecha, datetime.min.time()),
                periodo_fin=datetime.combine(fecha, datetime.max.time()),
                expira_en=datetime.now() + timedelta(days=7)
            )
            
            return {
                'total_ciudades': len(result),
                'metricas_por_ciudad': result,
                'fecha': fecha.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculando conversión por ciudad: {e}")
            return {'error': str(e)}
    
    async def _calcular_tiempo_respuesta_asesores(self, fecha: date) -> Dict[str, Any]:
        """Calcular tiempo promedio de respuesta por asesor"""
        try:
            conn = connections.get("default")
            
            query = """
            SELECT 
                a.id as asesor_id,
                u.nombre_completo,
                COUNT(o.id) as ofertas_enviadas,
                AVG(EXTRACT(EPOCH FROM (o.created_at - s.created_at))/3600) as tiempo_promedio_horas,
                MIN(EXTRACT(EPOCH FROM (o.created_at - s.created_at))/3600) as tiempo_minimo_horas,
                MAX(EXTRACT(EPOCH FROM (o.created_at - s.created_at))/3600) as tiempo_maximo_horas,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (o.created_at - s.created_at))/3600) as mediana_horas
            FROM asesores a
            JOIN usuarios u ON a.usuario_id = u.id
            JOIN ofertas o ON a.id = o.asesor_id
            JOIN solicitudes s ON o.solicitud_id = s.id
            WHERE DATE(o.created_at) = $1
            GROUP BY a.id, u.nombre_completo
            HAVING COUNT(o.id) >= 3  -- Mínimo 3 ofertas para estadística confiable
            ORDER BY tiempo_promedio_horas ASC
            """
            
            result = await conn.execute_query_dict(query, [fecha])
            
            # Almacenar en MetricaCalculada
            if result:
                tiempo_promedio_global = sum(r['tiempo_promedio_horas'] for r in result) / len(result)
                
                await MetricaCalculada.create(
                    nombre="tiempo_respuesta_asesores_diario",
                    tipo=TipoMetrica.KPI,
                    valor=tiempo_promedio_global,
                    descripcion="Tiempo promedio de respuesta de asesores",
                    dimensiones={"fecha": fecha.isoformat(), "tipo": "tiempo_respuesta"},
                    periodo_inicio=datetime.combine(fecha, datetime.min.time()),
                    periodo_fin=datetime.combine(fecha, datetime.max.time()),
                    expira_en=datetime.now() + timedelta(days=7)
                )
            
            return {
                'total_asesores': len(result),
                'tiempo_promedio_global_horas': round(sum(r['tiempo_promedio_horas'] for r in result) / len(result), 2) if result else 0,
                'asesores_mas_rapidos': result[:10],  # Top 10 más rápidos
                'fecha': fecha.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculando tiempo de respuesta de asesores: {e}")
            return {'error': str(e)}
    
    async def _analizar_tendencias_solicitudes(self, fecha_inicio: date, fecha_fin: date) -> Dict[str, Any]:
        """Analizar tendencias de solicitudes en la semana"""
        try:
            conn = connections.get("default")
            
            query = """
            SELECT 
                DATE(created_at) as fecha,
                COUNT(*) as solicitudes_dia,
                COUNT(CASE WHEN estado = 'OFERTAS_ACEPTADAS' THEN 1 END) as aceptadas_dia,
                AVG(EXTRACT(HOUR FROM created_at)) as hora_promedio_solicitud,
                COUNT(DISTINCT ciudad_id) as ciudades_activas
            FROM solicitudes
            WHERE DATE(created_at) BETWEEN $1 AND $2
            GROUP BY DATE(created_at)
            ORDER BY fecha
            """
            
            result = await conn.execute_query_dict(query, [fecha_inicio, fecha_fin])
            
            # Calcular tendencia (regresión lineal simple)
            if len(result) >= 2:
                dias = list(range(len(result)))
                solicitudes = [r['solicitudes_dia'] for r in result]
                
                # Calcular pendiente de la tendencia
                n = len(dias)
                sum_x = sum(dias)
                sum_y = sum(solicitudes)
                sum_xy = sum(x * y for x, y in zip(dias, solicitudes))
                sum_x2 = sum(x * x for x in dias)
                
                pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                tendencia = "creciente" if pendiente > 0 else "decreciente" if pendiente < 0 else "estable"
            else:
                tendencia = "insuficientes_datos"
                pendiente = 0
            
            # Almacenar en MetricaCalculada
            await MetricaCalculada.create(
                nombre="tendencias_solicitudes_semanal",
                tipo=TipoMetrica.KPI,
                valor=pendiente,
                descripcion="Análisis de tendencias de solicitudes semanales",
                dimensiones={
                    "fecha_inicio": fecha_inicio.isoformat(),
                    "fecha_fin": fecha_fin.isoformat(),
                    "tipo": "tendencias",
                    "tendencia": tendencia
                },
                periodo_inicio=datetime.combine(fecha_inicio, datetime.min.time()),
                periodo_fin=datetime.combine(fecha_fin, datetime.max.time()),
                expira_en=datetime.now() + timedelta(days=30)
            )
            
            return {
                'datos_diarios': result,
                'tendencia': tendencia,
                'pendiente': round(pendiente, 4),
                'total_solicitudes_semana': sum(r['solicitudes_dia'] for r in result),
                'promedio_diario': round(sum(r['solicitudes_dia'] for r in result) / len(result), 2) if result else 0
            }
            
        except Exception as e:
            logger.error(f"Error analizando tendencias de solicitudes: {e}")
            return {'error': str(e)}
    
    async def _analizar_evolucion_asesores(self, fecha_inicio: date, fecha_fin: date) -> Dict[str, Any]:
        """Analizar evolución del desempeño de asesores"""
        try:
            conn = connections.get("default")
            
            query = """
            SELECT 
                a.id as asesor_id,
                u.nombre_completo,
                DATE(o.created_at) as fecha,
                COUNT(o.id) as ofertas_dia,
                COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras_dia,
                AVG(od.precio * od.cantidad) as valor_promedio_dia
            FROM asesores a
            JOIN usuarios u ON a.usuario_id = u.id
            JOIN ofertas o ON a.id = o.asesor_id
            JOIN ofertas_detalle od ON o.id = od.oferta_id
            WHERE DATE(o.created_at) BETWEEN $1 AND $2
            GROUP BY a.id, u.nombre_completo, DATE(o.created_at)
            ORDER BY a.id, fecha
            """
            
            result = await conn.execute_query_dict(query, [fecha_inicio, fecha_fin])
            
            # Procesar evolución por asesor
            evolucion_asesores = {}
            for row in result:
                asesor_id = row['asesor_id']
                if asesor_id not in evolucion_asesores:
                    evolucion_asesores[asesor_id] = {
                        'nombre_completo': row['nombre_completo'],
                        'datos_diarios': [],
                        'mejora_ofertas': 0,
                        'mejora_exito': 0
                    }
                
                evolucion_asesores[asesor_id]['datos_diarios'].append({
                    'fecha': row['fecha'].isoformat(),
                    'ofertas': row['ofertas_dia'],
                    'ganadoras': row['ofertas_ganadoras_dia'],
                    'valor_promedio': float(row['valor_promedio_dia'] or 0)
                })
            
            # Calcular mejoras (comparar primer día vs último día)
            for asesor_id, data in evolucion_asesores.items():
                if len(data['datos_diarios']) >= 2:
                    primer_dia = data['datos_diarios'][0]
                    ultimo_dia = data['datos_diarios'][-1]
                    
                    data['mejora_ofertas'] = ultimo_dia['ofertas'] - primer_dia['ofertas']
                    data['mejora_exito'] = ultimo_dia['ganadoras'] - primer_dia['ganadoras']
            
            # Almacenar en MetricaCalculada
            await MetricaCalculada.create(
                nombre="evolucion_asesores_semanal",
                tipo=TipoMetrica.KPI,
                valor=len(evolucion_asesores),
                descripcion="Evolución del desempeño de asesores",
                dimensiones={
                    "fecha_inicio": fecha_inicio.isoformat(),
                    "fecha_fin": fecha_fin.isoformat(),
                    "tipo": "evolucion_asesores"
                },
                periodo_inicio=datetime.combine(fecha_inicio, datetime.min.time()),
                periodo_fin=datetime.combine(fecha_fin, datetime.max.time()),
                expira_en=datetime.now() + timedelta(days=30)
            )
            
            return {
                'total_asesores_analizados': len(evolucion_asesores),
                'evolucion_top_10': dict(list(evolucion_asesores.items())[:10]),
                'asesores_con_mejora': len([a for a in evolucion_asesores.values() if a['mejora_ofertas'] > 0])
            }
            
        except Exception as e:
            logger.error(f"Error analizando evolución de asesores: {e}")
            return {'error': str(e)}
    
    async def _analizar_patrones_demanda(self, fecha_inicio: date, fecha_fin: date) -> Dict[str, Any]:
        """Analizar patrones de demanda por repuesto"""
        try:
            conn = connections.get("default")
            
            query = """
            SELECT 
                sd.categoria_repuesto,
                sd.nombre_repuesto,
                COUNT(s.id) as solicitudes_total,
                COUNT(CASE WHEN s.estado = 'OFERTAS_ACEPTADAS' THEN 1 END) as solicitudes_exitosas,
                AVG(sd.cantidad) as cantidad_promedio,
                EXTRACT(DOW FROM s.created_at) as dia_semana,
                EXTRACT(HOUR FROM s.created_at) as hora_dia,
                COUNT(*) as frecuencia_temporal
            FROM solicitudes s
            JOIN solicitud_detalles sd ON s.id = sd.solicitud_id
            WHERE DATE(s.created_at) BETWEEN $1 AND $2
            GROUP BY sd.categoria_repuesto, sd.nombre_repuesto, 
                     EXTRACT(DOW FROM s.created_at), EXTRACT(HOUR FROM s.created_at)
            ORDER BY solicitudes_total DESC, frecuencia_temporal DESC
            """
            
            result = await conn.execute_query_dict(query, [fecha_inicio, fecha_fin])
            
            # Procesar patrones
            patrones_categoria = {}
            patrones_temporales = {}
            
            for row in result:
                categoria = row['categoria_repuesto']
                if categoria not in patrones_categoria:
                    patrones_categoria[categoria] = {
                        'solicitudes_total': 0,
                        'solicitudes_exitosas': 0,
                        'repuestos_mas_demandados': []
                    }
                
                patrones_categoria[categoria]['solicitudes_total'] += row['solicitudes_total']
                patrones_categoria[categoria]['solicitudes_exitosas'] += row['solicitudes_exitosas']
                
                # Patrones temporales
                dia_hora = f"{row['dia_semana']}-{row['hora_dia']}"
                if dia_hora not in patrones_temporales:
                    patrones_temporales[dia_hora] = 0
                patrones_temporales[dia_hora] += row['frecuencia_temporal']
            
            # Almacenar en MetricaCalculada
            await MetricaCalculada.create(
                nombre="patrones_demanda_semanal",
                tipo=TipoMetrica.KPI,
                valor=len(patrones_categoria),
                descripcion="Patrones de demanda por categoría de repuesto",
                dimensiones={
                    "fecha_inicio": fecha_inicio.isoformat(),
                    "fecha_fin": fecha_fin.isoformat(),
                    "tipo": "patrones_demanda"
                },
                periodo_inicio=datetime.combine(fecha_inicio, datetime.min.time()),
                periodo_fin=datetime.combine(fecha_fin, datetime.max.time()),
                expira_en=datetime.now() + timedelta(days=30)
            )
            
            return {
                'patrones_por_categoria': patrones_categoria,
                'picos_temporales': sorted(patrones_temporales.items(), key=lambda x: x[1], reverse=True)[:10],
                'total_categorias_analizadas': len(patrones_categoria)
            }
            
        except Exception as e:
            logger.error(f"Error analizando patrones de demanda: {e}")
            return {'error': str(e)}
    
    async def _calcular_metricas_satisfaccion(self, fecha_inicio: date, fecha_fin: date) -> Dict[str, Any]:
        """Calcular métricas de satisfacción y calidad"""
        try:
            conn = connections.get("default")
            
            query = """
            SELECT 
                COUNT(CASE WHEN ev.resultado = 'ACEPTADA' THEN 1 END) as ofertas_aceptadas,
                COUNT(CASE WHEN ev.resultado = 'RECHAZADA' THEN 1 END) as ofertas_rechazadas,
                COUNT(pqr.id) as pqrs_total,
                COUNT(CASE WHEN pqr.tipo = 'QUEJA' THEN 1 END) as quejas,
                COUNT(CASE WHEN pqr.tipo = 'FELICITACION' THEN 1 END) as felicitaciones,
                AVG(pqr.tiempo_resolucion_horas) as tiempo_promedio_resolucion_pqr,
                COUNT(CASE WHEN pqr.estado = 'RESUELTA' THEN 1 END) as pqrs_resueltas
            FROM evaluaciones ev
            LEFT JOIN pqrs pqr ON DATE(pqr.created_at) BETWEEN $1 AND $2
            WHERE DATE(ev.created_at) BETWEEN $1 AND $2
            """
            
            result = await conn.execute_query_dict(query, [fecha_inicio, fecha_fin])
            data = result[0] if result else {}
            
            # Calcular métricas derivadas
            total_evaluaciones = (data.get('ofertas_aceptadas', 0) + data.get('ofertas_rechazadas', 0))
            tasa_satisfaccion = 0
            if total_evaluaciones > 0:
                tasa_satisfaccion = (data.get('ofertas_aceptadas', 0) / total_evaluaciones) * 100
            
            # Almacenar en MetricaCalculada
            await MetricaCalculada.create(
                nombre="metricas_satisfaccion_semanal",
                tipo=TipoMetrica.KPI,
                valor=tasa_satisfaccion,
                descripcion="Métricas de satisfacción y calidad del servicio",
                dimensiones={
                    "fecha_inicio": fecha_inicio.isoformat(),
                    "fecha_fin": fecha_fin.isoformat(),
                    "tipo": "satisfaccion"
                },
                periodo_inicio=datetime.combine(fecha_inicio, datetime.min.time()),
                periodo_fin=datetime.combine(fecha_fin, datetime.max.time()),
                expira_en=datetime.now() + timedelta(days=30)
            )
            
            return {
                'tasa_satisfaccion': round(tasa_satisfaccion, 2),
                'total_evaluaciones': total_evaluaciones,
                'ofertas_aceptadas': data.get('ofertas_aceptadas', 0),
                'ofertas_rechazadas': data.get('ofertas_rechazadas', 0),
                'pqrs_total': data.get('pqrs_total', 0),
                'quejas': data.get('quejas', 0),
                'felicitaciones': data.get('felicitaciones', 0),
                'tiempo_promedio_resolucion_pqr_horas': round(float(data.get('tiempo_promedio_resolucion_pqr', 0) or 0), 2),
                'pqrs_resueltas': data.get('pqrs_resueltas', 0)
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas de satisfacción: {e}")
            return {'error': str(e)}

# Instancia global del servicio
batch_jobs_service = BatchJobsService()
