"""
Materialized Views API Router
Provides endpoints for managing and querying materialized views
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from ..services.materialized_views import materialized_views_service
from ..services.mv_scheduler import mv_scheduler

router = APIRouter(prefix="/materialized-views", tags=["Materialized Views"])

# Pydantic models for request/response
class RefreshRequest(BaseModel):
    """Request model for manual refresh"""
    force: bool = Field(False, description="Force refresh even if recently updated")

class RefreshResponse(BaseModel):
    """Response model for refresh operations"""
    success: bool
    total_views: int
    successful_refreshes: int
    total_duration_ms: int
    refreshed_at: str
    details: List[Dict[str, Any]]
    error: Optional[str] = None

class MonthlyMetricsResponse(BaseModel):
    """Response model for monthly metrics"""
    mes: str
    solicitudes_creadas: int
    solicitudes_aceptadas: int
    solicitudes_rechazadas: int
    solicitudes_expiradas: int
    tiempo_promedio_cierre_seg: float
    ofertas_totales: int
    ofertas_ganadoras: int
    precio_promedio_ofertas: float
    tiempo_entrega_promedio: float
    clientes_activos: int
    asesores_activos: int
    tasa_aceptacion_pct: float
    tasa_conversion_ofertas_pct: float

class AdvisorRankingResponse(BaseModel):
    """Response model for advisor rankings"""
    asesor_id: str
    asesor_nombre: str
    ciudad: str
    departamento: str
    confianza: float
    nivel_actual: int
    actividad_reciente_pct: float
    desempeno_historico_pct: float
    ofertas_historicas_total: int
    ofertas_ganadoras: int
    entregas_exitosas: int
    tiempo_promedio_respuesta_seg: float
    monto_promedio_ofertas: float
    confianza_auditada: float
    notificaciones_recibidas: int
    notificaciones_respondidas: int
    tasa_respuesta_pct: float
    ranking_ciudad: int
    ranking_nacional: int
    calculado_at: str

class SchedulerStatusResponse(BaseModel):
    """Response model for scheduler status"""
    is_running: bool
    scheduler_state: str
    jobs: List[Dict[str, Any]]
    last_refresh_result: Optional[Dict[str, Any]]
    checked_at: str
    error: Optional[str] = None

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_materialized_views(request: RefreshRequest = RefreshRequest()):
    """
    Manually refresh all materialized views
    """
    try:
        result = await materialized_views_service.refresh_materialized_views()
        
        return RefreshResponse(
            success=result.get('success', False),
            total_views=result.get('total_views', 0),
            successful_refreshes=result.get('successful_refreshes', 0),
            total_duration_ms=result.get('total_duration_ms', 0),
            refreshed_at=result.get('refreshed_at', datetime.now().isoformat()),
            details=result.get('details', []),
            error=result.get('error')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing materialized views: {str(e)}")

@router.get("/status")
async def get_materialized_views_status():
    """
    Get status information about materialized views
    """
    try:
        status = await materialized_views_service.get_view_status()
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting view status: {str(e)}")

@router.get("/monthly-metrics", response_model=List[MonthlyMetricsResponse])
async def get_monthly_metrics(
    start_month: Optional[str] = Query(None, description="Start month in YYYY-MM format"),
    end_month: Optional[str] = Query(None, description="End month in YYYY-MM format"),
    limit: int = Query(12, ge=1, le=60, description="Maximum number of months to return")
):
    """
    Get monthly metrics from materialized view
    """
    try:
        start_date = None
        end_date = None
        
        if start_month:
            try:
                start_date = datetime.strptime(start_month, "%Y-%m")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_month format. Use YYYY-MM")
        
        if end_month:
            try:
                end_date = datetime.strptime(end_month, "%Y-%m")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_month format. Use YYYY-MM")
        
        metrics = await materialized_views_service.get_monthly_metrics(
            start_month=start_date,
            end_month=end_date
        )
        
        # Apply limit
        if limit and len(metrics) > limit:
            metrics = metrics[:limit]
        
        return [MonthlyMetricsResponse(**metric) for metric in metrics]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting monthly metrics: {str(e)}")

@router.get("/advisor-rankings", response_model=List[AdvisorRankingResponse])
async def get_advisor_rankings(
    ciudad: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of advisors to return")
):
    """
    Get advisor rankings from materialized view
    """
    try:
        rankings = await materialized_views_service.get_advisor_rankings(
            ciudad=ciudad,
            limit=limit
        )
        
        return [AdvisorRankingResponse(**ranking) for ranking in rankings]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting advisor rankings: {str(e)}")

@router.get("/top-advisors")
async def get_top_advisors(
    ciudad: Optional[str] = Query(None, description="Filter by city"),
    metric: str = Query("ofertas_ganadoras", description="Metric to rank by"),
    limit: int = Query(10, ge=1, le=50, description="Number of top advisors to return")
):
    """
    Get top advisors based on a specific metric
    """
    try:
        valid_metrics = [
            "ofertas_ganadoras", "entregas_exitosas", "tasa_respuesta_pct",
            "tasa_conversion_ofertas_pct", "monto_promedio_ofertas", "confianza_auditada"
        ]
        
        if metric not in valid_metrics:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}"
            )
        
        rankings = await materialized_views_service.get_advisor_rankings(
            ciudad=ciudad,
            limit=limit * 2  # Get more to ensure we have enough after sorting
        )
        
        # Sort by the requested metric (descending)
        sorted_rankings = sorted(
            rankings, 
            key=lambda x: x.get(metric, 0), 
            reverse=True
        )
        
        # Apply limit
        top_advisors = sorted_rankings[:limit]
        
        return {
            "metric": metric,
            "ciudad": ciudad,
            "total_found": len(rankings),
            "top_advisors": top_advisors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting top advisors: {str(e)}")

@router.get("/city-summary")
async def get_city_summary():
    """
    Get summary statistics by city from advisor rankings
    """
    try:
        rankings = await materialized_views_service.get_advisor_rankings(limit=1000)
        
        # Group by city
        city_stats = {}
        for advisor in rankings:
            ciudad = advisor['ciudad']
            if ciudad not in city_stats:
                city_stats[ciudad] = {
                    'ciudad': ciudad,
                    'total_asesores': 0,
                    'ofertas_ganadoras_total': 0,
                    'entregas_exitosas_total': 0,
                    'volumen_total': 0,
                    'tasa_respuesta_promedio': 0,
                    'confianza_promedio': 0
                }
            
            stats = city_stats[ciudad]
            stats['total_asesores'] += 1
            stats['ofertas_ganadoras_total'] += advisor['ofertas_ganadoras']
            stats['entregas_exitosas_total'] += advisor['entregas_exitosas']
            stats['volumen_total'] += advisor.get('monto_promedio_ofertas', 0) * advisor['ofertas_ganadoras']
            stats['tasa_respuesta_promedio'] += advisor['tasa_respuesta_pct']
            stats['confianza_promedio'] += advisor['confianza_auditada']
        
        # Calculate averages
        for ciudad, stats in city_stats.items():
            if stats['total_asesores'] > 0:
                stats['tasa_respuesta_promedio'] /= stats['total_asesores']
                stats['confianza_promedio'] /= stats['total_asesores']
        
        # Sort by total advisors
        sorted_cities = sorted(
            city_stats.values(), 
            key=lambda x: x['total_asesores'], 
            reverse=True
        )
        
        return {
            'total_cities': len(sorted_cities),
            'cities': sorted_cities,
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting city summary: {str(e)}")

# Scheduler management endpoints
@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """
    Get current status of the materialized views scheduler
    """
    try:
        status = mv_scheduler.get_scheduler_status()
        
        return SchedulerStatusResponse(
            is_running=status.get('is_running', False),
            scheduler_state=status.get('scheduler_state', 'unknown'),
            jobs=status.get('jobs', []),
            last_refresh_result=status.get('last_refresh_result'),
            checked_at=status.get('checked_at', datetime.now().isoformat()),
            error=status.get('error')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting scheduler status: {str(e)}")

@router.post("/scheduler/trigger-refresh")
async def trigger_manual_refresh():
    """
    Manually trigger a refresh job through the scheduler
    """
    try:
        result = await mv_scheduler.trigger_manual_refresh()
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering manual refresh: {str(e)}")

@router.put("/scheduler/reschedule")
async def reschedule_daily_refresh(
    hour: int = Query(..., ge=0, le=23, description="Hour for daily refresh (0-23)"),
    minute: int = Query(0, ge=0, le=59, description="Minute for daily refresh (0-59)")
):
    """
    Reschedule the daily refresh job to a different time
    """
    try:
        result = await mv_scheduler.reschedule_daily_refresh(hour=hour, minute=minute)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rescheduling daily refresh: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for materialized views service
    """
    try:
        # Check if views exist and are populated
        status = await materialized_views_service.get_view_status()
        scheduler_status = mv_scheduler.get_scheduler_status()
        
        views_healthy = len(status.get('views', [])) >= 2  # Should have 2 views
        scheduler_healthy = scheduler_status.get('is_running', False)
        
        return {
            'status': 'healthy' if views_healthy and scheduler_healthy else 'degraded',
            'views_count': len(status.get('views', [])),
            'scheduler_running': scheduler_healthy,
            'last_refresh': scheduler_status.get('last_refresh_result', {}).get('refreshed_at'),
            'checked_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'checked_at': datetime.now().isoformat()
        }