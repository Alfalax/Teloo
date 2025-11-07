"""
Evaluaciones Router for TeLOO V3
Handles evaluation endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional
import logging

from services.evaluacion_service import EvaluacionService
from services.concurrencia_service import ConcurrenciaService
from middleware.auth_middleware import get_current_user
from models.user import Usuario

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/evaluaciones", tags=["evaluaciones"])


@router.post("/{solicitud_id}/run")
async def ejecutar_evaluacion(
    solicitud_id: str,
    timeout_segundos: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Execute forced evaluation for a solicitud
    
    Args:
        solicitud_id: ID of the solicitud to evaluate
        timeout_segundos: Optional timeout in seconds (uses config default if not provided)
        current_user: Current authenticated user
        
    Returns:
        Dict with evaluation results and adjudications
        
    Raises:
        HTTPException: If validation fails or evaluation errors occur
    """
    try:
        # Check if evaluation is already in progress (concurrency control)
        if await ConcurrenciaService.is_evaluacion_en_progreso(solicitud_id):
            raise HTTPException(
                status_code=409,
                detail=f"Evaluación ya en progreso para solicitud {solicitud_id}"
            )
        
        # Acquire evaluation lock
        async with ConcurrenciaService.lock_evaluacion(solicitud_id):
            # TODO: Get Redis client from dependency injection
            redis_client = None  # Will be injected when Redis is set up
            
            # Execute evaluation with timeout
            resultado = await EvaluacionService.ejecutar_evaluacion_con_timeout(
                solicitud_id=solicitud_id,
                timeout_segundos=timeout_segundos,
                redis_client=redis_client
            )
            
            if not resultado['success']:
                if resultado.get('error') == 'timeout':
                    raise HTTPException(
                        status_code=408,
                        detail=resultado['message']
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=resultado['message']
                    )
            
            logger.info(
                f"Evaluación ejecutada exitosamente por {current_user.nombre_completo} "
                f"para solicitud {resultado['codigo_solicitud']}: "
                f"{resultado['repuestos_adjudicados']}/{resultado['repuestos_totales']} adjudicados"
            )
            
            return {
                "success": True,
                "data": resultado,
                "message": f"Evaluación completada: {resultado['repuestos_adjudicados']} repuestos adjudicados"
            }
            
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error de validación en evaluación forzada: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado en evaluación forzada: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/{solicitud_id}")
async def obtener_evaluacion(
    solicitud_id: str,
    current_user: Usuario = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get evaluation record for a solicitud
    
    Args:
        solicitud_id: ID of the solicitud
        current_user: Current authenticated user
        
    Returns:
        Dict with evaluation data
        
    Raises:
        HTTPException: If evaluation not found
    """
    try:
        evaluacion = await EvaluacionService.get_evaluacion_by_solicitud(solicitud_id)
        
        if not evaluacion:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró evaluación para solicitud {solicitud_id}"
            )
        
        return {
            "success": True,
            "data": evaluacion,
            "message": "Evaluación obtenida exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo evaluación: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/admin/procesar-expiracion")
async def procesar_expiracion_ofertas(
    horas_expiracion: int = 20,
    current_user: Usuario = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process offer expiration (Admin only)
    
    Args:
        horas_expiracion: Hours after which offers expire (default 20)
        current_user: Current authenticated user
        
    Returns:
        Dict with expiration processing results
        
    Raises:
        HTTPException: If user is not admin or processing fails
    """
    try:
        # Check admin permissions
        if current_user.rol != "ADMIN":
            raise HTTPException(
                status_code=403,
                detail="Solo administradores pueden procesar expiración de ofertas"
            )
        
        # Validate hours
        if not (1 <= horas_expiracion <= 168):  # 1 hour to 1 week
            raise HTTPException(
                status_code=400,
                detail="Horas de expiración debe estar entre 1 y 168 (1 semana)"
            )
        
        # TODO: Get Redis client from dependency injection
        redis_client = None
        
        # Process expiration
        resultado = await EvaluacionService.procesar_expiracion_ofertas(
            horas_expiracion=horas_expiracion,
            redis_client=redis_client
        )
        
        if not resultado['success']:
            raise HTTPException(
                status_code=500,
                detail=resultado['message']
            )
        
        logger.info(
            f"Expiración de ofertas procesada por {current_user.nombre_completo}: "
            f"{resultado['ofertas_expiradas']} ofertas expiradas"
        )
        
        return {
            "success": True,
            "data": resultado,
            "message": f"Procesamiento completado: {resultado['ofertas_expiradas']} ofertas expiradas"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando expiración de ofertas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/admin/notificar-expiracion")
async def notificar_expiracion_proxima(
    horas_antes: int = 2,
    horas_expiracion_total: int = 20,
    current_user: Usuario = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Send expiration notifications to clients (Admin only)
    
    Args:
        horas_antes: Hours before expiration to send notification (default 2)
        horas_expiracion_total: Total hours for offer expiration (default 20)
        current_user: Current authenticated user
        
    Returns:
        Dict with notification results
        
    Raises:
        HTTPException: If user is not admin or processing fails
    """
    try:
        # Check admin permissions
        if current_user.rol != "ADMIN":
            raise HTTPException(
                status_code=403,
                detail="Solo administradores pueden enviar notificaciones de expiración"
            )
        
        # Validate parameters
        if not (1 <= horas_antes <= 12):
            raise HTTPException(
                status_code=400,
                detail="Horas antes de expiración debe estar entre 1 y 12"
            )
        
        if not (1 <= horas_expiracion_total <= 168):
            raise HTTPException(
                status_code=400,
                detail="Horas de expiración total debe estar entre 1 y 168"
            )
        
        if horas_antes >= horas_expiracion_total:
            raise HTTPException(
                status_code=400,
                detail="Horas antes debe ser menor que horas de expiración total"
            )
        
        # TODO: Get Redis client from dependency injection
        redis_client = None
        
        # Send notifications
        resultado = await EvaluacionService.notificar_expiracion_proxima(
            horas_antes_expiracion=horas_antes,
            horas_expiracion_total=horas_expiracion_total,
            redis_client=redis_client
        )
        
        if not resultado['success']:
            raise HTTPException(
                status_code=500,
                detail=resultado['message']
            )
        
        logger.info(
            f"Notificaciones de expiración enviadas por {current_user.nombre_completo}: "
            f"{resultado['notificaciones_enviadas']} notificaciones"
        )
        
        return {
            "success": True,
            "data": resultado,
            "message": f"Notificaciones enviadas: {resultado['notificaciones_enviadas']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enviando notificaciones de expiración: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/admin/ofertas-proximas-expirar")
async def get_ofertas_proximas_expirar(
    horas_limite: int = 4,
    current_user: Usuario = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get offers that will expire within specified hours (Admin only)
    
    Args:
        horas_limite: Hours limit to consider "próximas a expirar" (default 4)
        current_user: Current authenticated user
        
    Returns:
        Dict with offers that will expire soon
        
    Raises:
        HTTPException: If user is not admin
    """
    try:
        # Check admin permissions
        if current_user.rol != "ADMIN":
            raise HTTPException(
                status_code=403,
                detail="Solo administradores pueden ver ofertas próximas a expirar"
            )
        
        # Validate hours
        if not (1 <= horas_limite <= 24):
            raise HTTPException(
                status_code=400,
                detail="Horas límite debe estar entre 1 y 24"
            )
        
        # Get offers
        ofertas = await EvaluacionService.get_ofertas_proximas_a_expirar(horas_limite)
        
        # Categorize by urgency
        criticas = [o for o in ofertas if o['es_critica']]
        normales = [o for o in ofertas if not o['es_critica']]
        
        return {
            "success": True,
            "data": {
                "horas_limite": horas_limite,
                "total_ofertas": len(ofertas),
                "ofertas_criticas": len(criticas),
                "ofertas_normales": len(normales),
                "ofertas": ofertas,
                "resumen": {
                    "criticas": criticas,
                    "normales": normales
                }
            },
            "message": f"Encontradas {len(ofertas)} ofertas próximas a expirar"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo ofertas próximas a expirar: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")