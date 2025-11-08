"""
Solicitudes Router
Endpoints para gestión de solicitudes de crédito
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from models.solicitud import Solicitud
from models.enums import EstadoSolicitud
from models.user import Usuario
from middleware.auth_middleware import get_current_user
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/v1/solicitudes", tags=["solicitudes"])


class SolicitudResponse(BaseModel):
    """Response model for solicitud"""
    id: str
    cliente_nombre: str
    cliente_telefono: str
    monto_solicitado: float
    plazo_meses: int
    estado: str
    fecha_creacion: str
    fecha_limite: Optional[str] = None
    ofertas_count: int = 0
    
    class Config:
        from_attributes = True


@router.get("/metrics")
async def get_advisor_metrics(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener métricas del asesor para el dashboard
    """
    try:
        # Contar solicitudes abiertas disponibles (ABIERTA solamente)
        solicitudes_abiertas = await Solicitud.filter(
            estado=EstadoSolicitud.ABIERTA
        ).count()
        
        return {
            "ofertas_asignadas": 0,
            "monto_total_ganado": 0.0,
            "solicitudes_abiertas": solicitudes_abiertas,
            "tasa_conversion": 0.0
        }
        
    except Exception as e:
        import traceback
        print(f"Error in metrics endpoint: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )


@router.get("", response_model=List[SolicitudResponse])
async def get_solicitudes(
    estado: Optional[EstadoSolicitud] = Query(None, description="Filtrar por estado"),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener solicitudes filtradas por estado
    """
    try:
        # Build query
        query = Solicitud.all()
        
        if estado:
            query = query.filter(estado=estado)
        
        # For advisors, only show solicitudes they can bid on
        if current_user.rol.value == "ASESOR":
            query = query.filter(estado=EstadoSolicitud.ABIERTA)
        
        solicitudes = await query.prefetch_related("ofertas")
        
        # Format response
        result = []
        for sol in solicitudes:
            result.append(SolicitudResponse(
                id=str(sol.id),
                cliente_nombre=sol.cliente_nombre,
                cliente_telefono=sol.cliente_telefono,
                monto_solicitado=float(sol.monto_solicitado),
                plazo_meses=sol.plazo_meses,
                estado=sol.estado.value,
                fecha_creacion=sol.fecha_creacion.isoformat(),
                fecha_limite=sol.fecha_limite.isoformat() if sol.fecha_limite else None,
                ofertas_count=len(sol.ofertas) if hasattr(sol, 'ofertas') else 0
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching solicitudes: {str(e)}"
        )


@router.get("/{solicitud_id}", response_model=SolicitudResponse)
async def get_solicitud(
    solicitud_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener detalle de una solicitud específica
    """
    try:
        solicitud = await Solicitud.get_or_none(id=solicitud_id).prefetch_related("ofertas")
        
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud not found"
            )
        
        return SolicitudResponse(
            id=str(solicitud.id),
            cliente_nombre=solicitud.cliente_nombre,
            cliente_telefono=solicitud.cliente_telefono,
            monto_solicitado=float(solicitud.monto_solicitado),
            plazo_meses=solicitud.plazo_meses,
            estado=solicitud.estado.value,
            fecha_creacion=solicitud.fecha_creacion.isoformat(),
            fecha_limite=solicitud.fecha_limite.isoformat() if solicitud.fecha_limite else None,
            ofertas_count=len(solicitud.ofertas) if hasattr(solicitud, 'ofertas') else 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching solicitud: {str(e)}"
        )




