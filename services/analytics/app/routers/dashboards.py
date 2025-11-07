"""
Dashboard endpoints for Analytics Service
"""
import logging
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.services.metrics_calculator import MetricsCalculator
from app.services.batch_jobs import batch_jobs_service
from app.services.scheduler import analytics_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/dashboards", tags=["dashboards"])

metrics_calculator = MetricsCalculator()

@router.get("/principal")
async def get_dashboard_principal(
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (ISO format)")
) -> Dict[str, Any]:
    """
    Obtener dashboard principal con 4 KPIs superiores
    """
    try:
        # Usar últimos 30 días por defecto
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        kpis = await metrics_calculator.get_kpis_principales(fecha_inicio, fecha_fin)
        
        # Estructura de respuesta compatible con el frontend
        dashboard_data = {
            "kpis": {
                "ofertas_totales_asignadas": {
                    "valor": kpis.get("ofertas_totales", 0),
                    "cambio_porcentual": kpis.get("ofertas_cambio", 0),
                    "periodo": "mes_actual"
                },
                "monto_total_aceptado": {
                    "valor": kpis.get("monto_total", 0),
                    "cambio_porcentual": kpis.get("monto_cambio", 0),
                    "periodo": "mes_actual"
                },
                "solicitudes_abiertas": {
                    "valor": kpis.get("solicitudes_abiertas", 0),
                    "cambio_porcentual": kpis.get("solicitudes_cambio", 0),
                    "periodo": "actual"
                },
                "tasa_conversion": {
                    "valor": kpis.get("tasa_conversion", 0),
                    "cambio_porcentual": kpis.get("conversion_cambio", 0),
                    "periodo": "promedio_mensual"
                }
            }
        }
        
        return {
            "success": True,
            "data": dashboard_data,
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo dashboard principal: {str(e)}")

@router.get("/graficos-mes")
async def get_graficos_mes(
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (ISO format)")
) -> Dict[str, Any]:
    """
    Obtener datos para gráficos de líneas del mes
    """
    try:
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        graficos_data = await metrics_calculator.get_graficos_mes(fecha_inicio, fecha_fin)
        
        return {
            "success": True,
            "data": graficos_data,
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo gráficos del mes: {str(e)}")

@router.get("/top-solicitudes-abiertas")
async def get_top_solicitudes_abiertas(
    limit: int = Query(15, description="Número de solicitudes a retornar")
) -> Dict[str, Any]:
    """
    Obtener top solicitudes abiertas con mayor tiempo en proceso
    """
    try:
        solicitudes = await metrics_calculator.get_top_solicitudes_abiertas(limit)
        
        return {
            "success": True,
            "data": solicitudes,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo top solicitudes abiertas: {str(e)}")

@router.get("/embudo-operativo")
async def get_embudo_operativo(
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (ISO format)")
) -> Dict[str, Any]:
    """
    Obtener embudo operativo con 11 KPIs de proceso
    """
    try:
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        embudo = await metrics_calculator.get_embudo_operativo(fecha_inicio, fecha_fin)
        
        return {
            "dashboard": "embudo_operativo",
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "metricas": embudo,
            "generado_en": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo embudo operativo: {str(e)}")

@router.get("/salud-marketplace")
async def get_salud_marketplace(
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (ISO format)")
) -> Dict[str, Any]:
    """
    Obtener salud del marketplace con 5 KPIs de sistema
    """
    try:
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=7)  # Última semana
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        salud = await metrics_calculator.get_salud_marketplace(fecha_inicio, fecha_fin)
        
        return {
            "dashboard": "salud_marketplace",
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "metricas": salud,
            "generado_en": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo salud del marketplace: {str(e)}")

@router.get("/financiero")
async def get_dashboard_financiero(
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (ISO format)")
) -> Dict[str, Any]:
    """
    Obtener dashboard financiero con 5 KPIs de transacciones
    """
    try:
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        # Por ahora retornamos estructura básica
        financiero = {
            "ingresos_totales": 0,
            "comisiones_generadas": 0,
            "valor_promedio_transaccion": 0,
            "transacciones_completadas": 0,
            "crecimiento_mensual": 0
        }
        
        return {
            "dashboard": "financiero",
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "metricas": financiero,
            "generado_en": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo dashboard financiero: {str(e)}")

@router.get("/asesores")
async def get_analisis_asesores(
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (ISO format)"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad")
) -> Dict[str, Any]:
    """
    Obtener análisis de asesores con 13 KPIs de performance
    """
    try:
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        # Por ahora retornamos estructura básica
        asesores = {
            "total_asesores": 0,
            "asesores_activos": 0,
            "tasa_respuesta_promedio": 0,
            "tiempo_respuesta_promedio": 0,
            "ofertas_por_asesor": 0,
            "tasa_adjudicacion": 0,
            "ranking_top_10": [],
            "especializacion_por_repuesto": {},
            "distribucion_geografica": {},
            "nivel_confianza_promedio": 0,
            "asesores_nuevos": 0,
            "retension_asesores": 0,
            "satisfaccion_cliente": 0
        }
        
        return {
            "dashboard": "asesores",
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "filtros": {
                "ciudad": ciudad
            },
            "metricas": asesores,
            "generado_en": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo análisis de asesores: {str(e)}")
# Batch Jobs Endpoints

@router.get("/batch-jobs/status")
async def get_batch_jobs_status():
    """
    Obtener estado de los jobs batch programados
    """
    try:
        status = analytics_scheduler.get_job_status()
        return {
            "success": True,
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado de batch jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-jobs/trigger/{job_id}")
async def trigger_batch_job(job_id: str):
    """
    Ejecutar manualmente un job batch específico
    
    Args:
        job_id: ID del job a ejecutar (daily_metrics_batch, weekly_metrics_batch, cleanup_metrics)
    """
    try:
        valid_jobs = ['daily_metrics_batch', 'weekly_metrics_batch', 'cleanup_metrics']
        if job_id not in valid_jobs:
            raise HTTPException(
                status_code=400, 
                detail=f"Job ID inválido. Válidos: {', '.join(valid_jobs)}"
            )
        
        result = await analytics_scheduler.trigger_job_manually(job_id)
        
        return {
            "success": result['success'],
            "data": result,
            "message": f"Job {job_id} {'ejecutado exitosamente' if result['success'] else 'falló'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-jobs/daily")
async def run_daily_batch_job(fecha: str = None):
    """
    Ejecutar job diario de métricas para una fecha específica
    
    Args:
        fecha: Fecha en formato YYYY-MM-DD (opcional, default: ayer)
    """
    try:
        target_date = None
        if fecha:
            try:
                target_date = datetime.strptime(fecha, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Formato de fecha inválido. Use YYYY-MM-DD"
                )
        
        result = await batch_jobs_service.run_daily_batch_job(target_date)
        
        return {
            "success": result['success'],
            "data": result,
            "message": "Job diario ejecutado" + (" exitosamente" if result['success'] else " con errores")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando job diario: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-jobs/weekly")
async def run_weekly_batch_job(fecha_fin: str = None):
    """
    Ejecutar job semanal de análisis de tendencias para un período específico
    
    Args:
        fecha_fin: Fecha final del período en formato YYYY-MM-DD (opcional, default: ayer)
    """
    try:
        target_date = None
        if fecha_fin:
            try:
                target_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Formato de fecha inválido. Use YYYY-MM-DD"
                )
        
        result = await batch_jobs_service.run_weekly_batch_job(target_date)
        
        return {
            "success": result['success'],
            "data": result,
            "message": "Job semanal ejecutado" + (" exitosamente" if result['success'] else " con errores")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando job semanal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/calculated")
async def get_calculated_metrics(
    nombre_metrica: str = None,
    fecha_inicio: str = None,
    fecha_fin: str = None,
    limit: int = 100
):
    """
    Obtener métricas calculadas almacenadas
    
    Args:
        nombre_metrica: Filtrar por nombre de métrica específica
        fecha_inicio: Fecha inicio del período (YYYY-MM-DD)
        fecha_fin: Fecha fin del período (YYYY-MM-DD)
        limit: Límite de resultados (default: 100)
    """
    try:
        from app.models.metrics import MetricaCalculada
        
        # Construir query
        query = MetricaCalculada.all()
        
        if nombre_metrica:
            query = query.filter(nombre=nombre_metrica)
        
        if fecha_inicio:
            try:
                fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
                query = query.filter(periodo_inicio__gte=fecha_inicio_dt)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Formato de fecha_inicio inválido. Use YYYY-MM-DD"
                )
        
        if fecha_fin:
            try:
                fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
                query = query.filter(periodo_fin__lte=fecha_fin_dt)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Formato de fecha_fin inválido. Use YYYY-MM-DD"
                )
        
        # Ejecutar query con límite
        metricas = await query.order_by('-calculado_en').limit(limit)
        
        # Formatear resultados
        results = []
        for metrica in metricas:
            results.append({
                "id": metrica.id,
                "nombre": metrica.nombre,
                "tipo": metrica.tipo,
                "valor": metrica.valor,
                "descripcion": metrica.descripcion,
                "unidad": metrica.unidad,
                "dimensiones": metrica.dimensiones,
                "periodo_inicio": metrica.periodo_inicio.isoformat(),
                "periodo_fin": metrica.periodo_fin.isoformat(),
                "calculado_en": metrica.calculado_en.isoformat(),
                "expira_en": metrica.expira_en.isoformat()
            })
        
        return {
            "success": True,
            "data": {
                "metricas": results,
                "total": len(results),
                "filtros": {
                    "nombre_metrica": nombre_metrica,
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "limit": limit
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo métricas calculadas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export endpoints
@router.get("/embudo-operativo/export")
async def export_embudo_operativo(
    format: str = Query("json", description="Formato de exportación: json o csv"),
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (ISO format)")
):
    """
    Exportar datos del embudo operativo
    """
    try:
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        data = await metrics_calculator.get_embudo_operativo(fecha_inicio, fecha_fin)
        
        if format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Headers
            writer.writerow(["Métrica", "Valor", "Período Inicio", "Período Fin"])
            
            # Data rows
            for key, value in data.items():
                writer.writerow([
                    key.replace('_', ' ').title(),
                    str(value),
                    fecha_inicio.isoformat(),
                    fecha_fin.isoformat()
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            from fastapi.responses import Response
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=embudo-operativo-{fecha_inicio.date()}-{fecha_fin.date()}.csv"}
            )
        else:
            # JSON format
            return {
                "dashboard": "embudo_operativo",
                "periodo": {
                    "inicio": fecha_inicio.isoformat(),
                    "fin": fecha_fin.isoformat()
                },
                "metricas": data,
                "generado_en": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando embudo operativo: {str(e)}")

@router.get("/salud-marketplace/export")
async def export_salud_marketplace(
    format: str = Query("json", description="Formato de exportación: json o csv"),
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (ISO format)")
):
    """
    Exportar datos de salud del marketplace
    """
    try:
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=7)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        data = await metrics_calculator.get_salud_marketplace(fecha_inicio, fecha_fin)
        
        if format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Headers
            writer.writerow(["Métrica", "Valor", "Unidad", "Período Inicio", "Período Fin"])
            
            # Data rows
            for key, value in data.items():
                unit = ""
                if "porcentaje" in key or "tasa" in key:
                    unit = "%"
                elif "tiempo" in key or "latencia" in key:
                    unit = "ms"
                elif "disponibilidad" in key:
                    unit = "%"
                    
                writer.writerow([
                    key.replace('_', ' ').title(),
                    str(value),
                    unit,
                    fecha_inicio.isoformat(),
                    fecha_fin.isoformat()
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            from fastapi.responses import Response
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=salud-marketplace-{fecha_inicio.date()}-{fecha_fin.date()}.csv"}
            )
        else:
            # JSON format
            return {
                "dashboard": "salud_marketplace",
                "periodo": {
                    "inicio": fecha_inicio.isoformat(),
                    "fin": fecha_fin.isoformat()
                },
                "metricas": data,
                "generado_en": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando salud del marketplace: {str(e)}")

@router.get("/financiero/export")
async def export_dashboard_financiero(
    format: str = Query("json", description="Formato de exportación: json o csv"),
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (ISO format)")
):
    """
    Exportar datos del dashboard financiero
    """
    try:
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        # Mock data for now - implement real calculation later
        data = {
            "ingresos_totales": 45200000,
            "comisiones_generadas": 2260000,
            "valor_promedio_transaccion": 850000,
            "transacciones_completadas": 156,
            "crecimiento_mensual": 12.5
        }
        
        if format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Headers
            writer.writerow(["Métrica", "Valor", "Unidad", "Período Inicio", "Período Fin"])
            
            # Data rows
            for key, value in data.items():
                unit = ""
                if "ingresos" in key or "comisiones" in key or "valor" in key:
                    unit = "COP"
                elif "crecimiento" in key:
                    unit = "%"
                elif "transacciones" in key:
                    unit = "unidades"
                    
                writer.writerow([
                    key.replace('_', ' ').title(),
                    str(value),
                    unit,
                    fecha_inicio.isoformat(),
                    fecha_fin.isoformat()
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            from fastapi.responses import Response
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=dashboard-financiero-{fecha_inicio.date()}-{fecha_fin.date()}.csv"}
            )
        else:
            # JSON format
            return {
                "dashboard": "financiero",
                "periodo": {
                    "inicio": fecha_inicio.isoformat(),
                    "fin": fecha_fin.isoformat()
                },
                "metricas": data,
                "generado_en": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando dashboard financiero: {str(e)}")

@router.get("/asesores/export")
async def export_analisis_asesores(
    format: str = Query("json", description="Formato de exportación: json o csv"),
    fecha_inicio: Optional[datetime] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_fin: Optional[datetime] = Query(None, description="Fecha fin (ISO format)"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad")
):
    """
    Exportar datos del análisis de asesores
    """
    try:
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
            
        # Mock data for now - implement real calculation later
        data = {
            "total_asesores": 245,
            "asesores_activos": 189,
            "tasa_respuesta_promedio": 78.5,
            "tiempo_respuesta_promedio": 25.3,
            "ofertas_por_asesor": 12.8,
            "tasa_adjudicacion": 34.2,
            "ranking_top_10": [
                {"nombre": "Asesor Premium 1", "puntaje": 4.8, "ciudad": "BOGOTA"},
                {"nombre": "Asesor Premium 2", "puntaje": 4.7, "ciudad": "MEDELLIN"},
                {"nombre": "Asesor Premium 3", "puntaje": 4.6, "ciudad": "CALI"}
            ],
            "nivel_confianza_promedio": 4.2,
            "retension_asesores": 92.1,
            "satisfaccion_cliente": 4.3
        }
        
        if format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Headers for main metrics
            writer.writerow(["Métrica", "Valor", "Unidad", "Período Inicio", "Período Fin"])
            
            # Main metrics
            for key, value in data.items():
                if key != "ranking_top_10":  # Skip complex nested data for CSV
                    unit = ""
                    if "tasa" in key or "retension" in key:
                        unit = "%"
                    elif "tiempo" in key:
                        unit = "minutos"
                    elif "total" in key or "ofertas" in key:
                        unit = "unidades"
                    elif "nivel" in key or "satisfaccion" in key:
                        unit = "escala 1-5"
                        
                    writer.writerow([
                        key.replace('_', ' ').title(),
                        str(value),
                        unit,
                        fecha_inicio.isoformat(),
                        fecha_fin.isoformat()
                    ])
            
            # Add ranking section
            writer.writerow([])  # Empty row
            writer.writerow(["Ranking Top Asesores", "", "", "", ""])
            writer.writerow(["Nombre", "Puntaje", "Ciudad", "", ""])
            
            for asesor in data.get("ranking_top_10", []):
                writer.writerow([
                    asesor.get("nombre", ""),
                    str(asesor.get("puntaje", "")),
                    asesor.get("ciudad", ""),
                    "",
                    ""
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            from fastapi.responses import Response
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=analisis-asesores-{fecha_inicio.date()}-{fecha_fin.date()}.csv"}
            )
        else:
            # JSON format
            return {
                "dashboard": "asesores",
                "periodo": {
                    "inicio": fecha_inicio.isoformat(),
                    "fin": fecha_fin.isoformat()
                },
                "filtros": {
                    "ciudad": ciudad
                },
                "metricas": data,
                "generado_en": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando análisis de asesores: {str(e)}")