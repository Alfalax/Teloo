"""
Dashboard endpoints for Analytics Service
"""
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.services.metrics_calculator import MetricsCalculator
from app.services.batch_jobs import batch_jobs_service
from app.services.scheduler import analytics_scheduler

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
        
        return {
            "dashboard": "principal",
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "kpis": kpis,
            "generado_en": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo dashboard principal: {str(e)}")

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