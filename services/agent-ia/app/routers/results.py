"""
Results endpoints for sending evaluation results to clients
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.results_service import results_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/results", tags=["results"])


class SendResultsRequest(BaseModel):
    """Request model for sending evaluation results"""
    solicitud_id: str


class SendResultsResponse(BaseModel):
    """Response model for sending evaluation results"""
    success: bool
    message: str
    solicitud_id: str
    client_phone: Optional[str] = None
    error: Optional[str] = None
    details: Optional[str] = None


@router.post("/send", response_model=SendResultsResponse)
async def send_evaluation_results(request: SendResultsRequest):
    """
    Send evaluation results to client via WhatsApp
    
    This endpoint is called by the Core API when evaluation is completed
    to notify the client about available offers.
    """
    try:
        logger.info(f"Sending evaluation results for solicitud {request.solicitud_id}")
        
        result = await results_service.enviar_resultado_evaluacion(request.solicitud_id)
        
        if result["success"]:
            return SendResultsResponse(
                success=True,
                message=result["message"],
                solicitud_id=request.solicitud_id,
                client_phone=result.get("client_phone")
            )
        else:
            return SendResultsResponse(
                success=False,
                message="Error enviando resultados",
                solicitud_id=request.solicitud_id,
                error=result["error"],
                details=result.get("details")
            )
            
    except Exception as e:
        logger.error(f"Error in send_evaluation_results endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno enviando resultados: {str(e)}"
        )


@router.get("/status/{solicitud_id}")
async def get_results_status(solicitud_id: str):
    """
    Get status of results sending for a solicitud
    
    This endpoint can be used to check if results were sent successfully.
    """
    try:
        # This would typically check a database or cache for sending status
        # For now, return basic status
        
        return {
            "solicitud_id": solicitud_id,
            "status": "unknown",
            "message": "Status checking not implemented yet"
        }
        
    except Exception as e:
        logger.error(f"Error getting results status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estado: {str(e)}"
        )


@router.get("/health")
async def results_health_check():
    """Health check for results service"""
    return {
        "service": "Results Service",
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }