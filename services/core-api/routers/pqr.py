"""
PQR (Peticiones, Quejas, Reclamos) router
Handles CRUD operations for customer service requests
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from models.analytics import PQR
from models.user import Usuario
from models.enums import TipoPQR, PrioridadPQR, EstadoPQR
from middleware.auth_middleware import get_current_active_user
from services.pqr_service import PQRService
from schemas.pqr import (
    PQRCreate, PQRUpdate, PQRResponse, PQRList, 
    PQRMetrics, PQRNotificationCreate
)

router = APIRouter(prefix="/pqr", tags=["PQR"])




@router.get("/", response_model=PQRList)
async def get_pqrs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    estado: Optional[EstadoPQR] = None,
    tipo: Optional[TipoPQR] = None,
    prioridad: Optional[PrioridadPQR] = None,
    search: Optional[str] = None,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener lista de PQRs con filtros y paginación
    """
    return await PQRService.get_pqrs(
        page=page,
        limit=limit,
        estado=estado,
        tipo=tipo,
        prioridad=prioridad,
        search=search
    )


@router.get("/metrics", response_model=PQRMetrics)
async def get_pqr_metrics(
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener métricas de PQRs para el dashboard
    """
    return await PQRService.get_pqr_metrics()


@router.get("/{pqr_id}", response_model=PQRResponse)
async def get_pqr(
    pqr_id: UUID,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener una PQR específica por ID
    """
    pqr = await PQRService.get_pqr_by_id(pqr_id)
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR no encontrada")
    return pqr


@router.post("/", response_model=PQRResponse)
async def create_pqr(
    pqr_data: PQRCreate,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Crear una nueva PQR
    """
    return await PQRService.create_pqr(pqr_data)


@router.put("/{pqr_id}", response_model=PQRResponse)
async def update_pqr(
    pqr_id: UUID,
    pqr_data: PQRUpdate,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Actualizar una PQR existente
    """
    pqr = await PQRService.update_pqr(pqr_id, pqr_data, current_user.id)
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR no encontrada")
    return pqr


@router.post("/{pqr_id}/responder", response_model=PQRResponse)
async def responder_pqr(
    pqr_id: UUID,
    respuesta: str,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Responder a una PQR
    """
    pqr = await PQRService.responder_pqr(pqr_id, respuesta, current_user.id)
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR no encontrada")
    return pqr


@router.post("/{pqr_id}/cambiar-estado", response_model=PQRResponse)
async def cambiar_estado_pqr(
    pqr_id: UUID,
    nuevo_estado: EstadoPQR,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Cambiar el estado de una PQR
    """
    pqr = await PQRService.cambiar_estado(pqr_id, nuevo_estado, current_user.id)
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR no encontrada")
    return pqr


@router.post("/{pqr_id}/cambiar-prioridad", response_model=PQRResponse)
async def cambiar_prioridad_pqr(
    pqr_id: UUID,
    nueva_prioridad: PrioridadPQR,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Cambiar la prioridad de una PQR
    """
    pqr = await PQRService.cambiar_prioridad(pqr_id, nueva_prioridad, current_user.id)
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR no encontrada")
    return pqr


@router.delete("/{pqr_id}")
async def delete_pqr(
    pqr_id: UUID,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Eliminar una PQR (soft delete)
    """
    success = await PQRService.delete_pqr(pqr_id)
    if not success:
        raise HTTPException(status_code=404, detail="PQR no encontrada")
    return {"message": "PQR eliminada exitosamente"}


@router.get("/cliente/{cliente_id}", response_model=List[PQRResponse])
async def get_pqrs_by_cliente(
    cliente_id: UUID,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todas las PQRs de un cliente específico
    """
    return await PQRService.get_pqrs_by_cliente(cliente_id)
