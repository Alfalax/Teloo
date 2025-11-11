"""
Solicitudes Router
Endpoints para gestión de solicitudes de crédito
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from tortoise.expressions import Q
from models.solicitud import Solicitud, RepuestoSolicitado
from models.enums import EstadoSolicitud
from models.user import Usuario
from middleware.auth_middleware import get_current_user
from services.solicitudes_service import SolicitudesService
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import pandas as pd
import io

router = APIRouter(prefix="/v1/solicitudes", tags=["solicitudes"])


class RepuestoSolicitadoInput(BaseModel):
    """Input model for repuesto solicitado"""
    nombre: str = Field(..., min_length=1, max_length=200)
    codigo: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None
    cantidad: int = Field(..., ge=1)
    marca_vehiculo: str = Field(..., min_length=1, max_length=50)
    linea_vehiculo: str = Field(..., min_length=1, max_length=100)
    anio_vehiculo: int = Field(..., ge=1980, le=2025)
    observaciones: Optional[str] = None
    es_urgente: bool = False


class RepuestoSolicitadoResponse(BaseModel):
    """Response model for repuesto solicitado"""
    id: str
    nombre: str
    codigo: Optional[str]
    descripcion: Optional[str]
    cantidad: int
    marca_vehiculo: str
    linea_vehiculo: str
    anio_vehiculo: int
    observaciones: Optional[str]
    es_urgente: bool


class ClienteInput(BaseModel):
    """Input model for cliente"""
    nombre: str = Field(..., min_length=1, max_length=200)
    telefono: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = None


class CreateSolicitudRequest(BaseModel):
    """Request model for creating solicitud"""
    cliente: ClienteInput
    ciudad_origen: str = Field(..., min_length=1, max_length=100)
    departamento_origen: str = Field(..., min_length=1, max_length=100)
    repuestos: List[RepuestoSolicitadoInput] = Field(..., min_items=1)


class SolicitudResponse(BaseModel):
    """Response model for solicitud"""
    id: str
    cliente_id: str
    cliente_nombre: str
    cliente_telefono: str
    estado: str
    nivel_actual: int
    ciudad_origen: str
    departamento_origen: str
    ofertas_minimas_deseadas: int
    timeout_horas: int
    fecha_creacion: str
    fecha_escalamiento: Optional[str]
    fecha_evaluacion: Optional[str]
    fecha_expiracion: Optional[str]
    total_repuestos: int
    monto_total_adjudicado: float
    repuestos_solicitados: List[RepuestoSolicitadoResponse] = []
    mi_oferta: Optional[Dict[str, Any]] = None


class SolicitudesPaginatedResponse(BaseModel):
    """Paginated response for solicitudes"""
    items: List[SolicitudResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SolicitudesStatsResponse(BaseModel):
    """Statistics response for solicitudes"""
    total: int
    abiertas: int
    evaluadas: int
    aceptadas: int
    rechazadas_expiradas: int


class ClienteSearchResponse(BaseModel):
    """Response model for cliente search by phone"""
    found: bool
    cliente_id: Optional[str] = None
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None


@router.get("/clientes/buscar", response_model=ClienteSearchResponse)
async def buscar_cliente_por_telefono(
    telefono: str = Query(..., description="Teléfono del cliente"),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Buscar cliente por teléfono para autocompletar formulario
    """
    try:
        from models.user import Cliente
        
        # Normalize phone number
        telefono_normalizado = telefono
        if not telefono.startswith("+57"):
            telefono_digits = ''.join(filter(str.isdigit, telefono))
            telefono_normalizado = f"+57{telefono_digits[-10:]}"
        
        # Search usuario by phone
        usuario = await Usuario.get_or_none(telefono=telefono_normalizado).prefetch_related("cliente")
        
        if not usuario:
            return {"found": False}
        
        # Get cliente profile
        cliente = await Cliente.get_or_none(usuario_id=usuario.id)
        
        if not cliente:
            return {
                "found": True,
                "cliente_id": None,
                "nombre": usuario.nombre_completo,
                "email": usuario.email,
                "telefono": usuario.telefono,
                "ciudad": None,
                "departamento": None
            }
        
        return {
            "found": True,
            "cliente_id": str(cliente.id),
            "nombre": usuario.nombre_completo,
            "email": usuario.email,
            "telefono": usuario.telefono,
            "ciudad": cliente.ciudad,
            "departamento": cliente.departamento
        }
        
    except Exception as e:
        import traceback
        print(f"Error in buscar_cliente_por_telefono: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching cliente: {str(e)}"
        )


@router.get("/metrics")
async def get_advisor_metrics(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener métricas del asesor para el dashboard
    
    - ofertas_asignadas: Número de ofertas que el asesor ha enviado
    - monto_total_ganado: Suma de montos de ofertas ganadoras aceptadas
    - solicitudes_abiertas: Solicitudes ABIERTAS asignadas al asesor
    - tasa_conversion: Porcentaje de ofertas ganadoras vs enviadas
    """
    try:
        from models.user import Asesor
        from models.oferta import Oferta
        from models.enums import EstadoOferta
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 DEBUG METRICS - Usuario logueado: {current_user.email} (ID: {current_user.id})")
        
        # Get asesor
        asesor = await Asesor.get_or_none(usuario_id=current_user.id)
        if not asesor:
            logger.warning(f"⚠️ No se encontró asesor para usuario {current_user.email}")
            return {
                "ofertas_asignadas": 0,
                "monto_total_ganado": 0.0,
                "solicitudes_abiertas": 0,
                "tasa_conversion": 0.0
            }
        
        logger.info(f"✅ Asesor encontrado: {asesor.id}")
        
        # Contar ofertas enviadas por el asesor
        ofertas_asignadas = await Oferta.filter(asesor_id=asesor.id).count()
        
        # Calcular monto total ganado (ofertas ACEPTADAS)
        ofertas_ganadoras = await Oferta.filter(
            asesor_id=asesor.id,
            estado=EstadoOferta.ACEPTADA
        ).prefetch_related("detalles")
        
        monto_total_ganado = 0.0
        for oferta in ofertas_ganadoras:
            monto_total_ganado += float(oferta.monto_total)
        
        # Contar solicitudes ABIERTAS asignadas al asesor (evaluadas o con oferta)
        from models.geografia import EvaluacionAsesorTemp
        solicitudes_abiertas = await Solicitud.filter(
            Q(evaluaciones_asesores__asesor_id=asesor.id) |
            Q(ofertas__asesor_id=asesor.id),
            estado=EstadoSolicitud.ABIERTA
        ).distinct().count()
        
        # Calcular tasa de conversión
        ofertas_ganadoras_count = await Oferta.filter(
            asesor_id=asesor.id,
            estado__in=[EstadoOferta.GANADORA, EstadoOferta.ACEPTADA]
        ).count()
        
        tasa_conversion = 0.0
        if ofertas_asignadas > 0:
            tasa_conversion = (ofertas_ganadoras_count / ofertas_asignadas) * 100
        
        return {
            "ofertas_asignadas": ofertas_asignadas,
            "monto_total_ganado": round(monto_total_ganado, 2),
            "solicitudes_abiertas": solicitudes_abiertas,
            "tasa_conversion": round(tasa_conversion, 2)
        }
        
    except Exception as e:
        import traceback
        print(f"Error in metrics endpoint: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )


@router.get("", response_model=SolicitudesPaginatedResponse)
async def get_solicitudes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    estado: Optional[EstadoSolicitud] = Query(None, description="Filtrar por estado"),
    search: Optional[str] = Query(None, description="Buscar por nombre, teléfono o ciudad"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad"),
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener solicitudes paginadas con filtros
    
    Para ASESORES: Solo muestra solicitudes donde fueron evaluados/notificados O hicieron oferta
    Para ADMIN: Muestra todas las solicitudes
    """
    try:
        # Get asesor_id if user is an asesor
        asesor_id = None
        if current_user.rol.value == "ADVISOR":
            from models.user import Asesor
            asesor = await Asesor.get_or_none(usuario_id=current_user.id)
            if asesor:
                asesor_id = asesor.id
        
        result = await SolicitudesService.get_solicitudes_paginated(
            page=page,
            page_size=page_size,
            estado=estado,
            search=search,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            ciudad=ciudad,
            departamento=departamento,
            user_rol=current_user.rol.value,
            asesor_id=asesor_id
        )
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Error in get_solicitudes: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching solicitudes: {str(e)}"
        )


@router.get("/stats", response_model=SolicitudesStatsResponse)
async def get_solicitudes_stats(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener estadísticas de solicitudes por estado
    """
    try:
        stats = await SolicitudesService.get_stats()
        return stats
        
    except Exception as e:
        import traceback
        print(f"Error in get_solicitudes_stats: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching stats: {str(e)}"
        )


@router.post("", response_model=SolicitudResponse, status_code=status.HTTP_201_CREATED)
async def create_solicitud(
    request: CreateSolicitudRequest,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear nueva solicitud con cliente y repuestos
    """
    try:
        # Convert request to dict
        cliente_data = request.cliente.model_dump()
        repuestos_data = [rep.model_dump() for rep in request.repuestos]
        
        solicitud = await SolicitudesService.create_solicitud(
            cliente_data=cliente_data,
            ciudad_origen=request.ciudad_origen,
            departamento_origen=request.departamento_origen,
            repuestos=repuestos_data
        )
        
        return solicitud
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        print(f"Error in create_solicitud: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating solicitud: {str(e)}"
        )


@router.get("/{solicitud_id}/plantilla-oferta")
async def descargar_plantilla_oferta(
    solicitud_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Generar plantilla Excel con los repuestos de la solicitud para facilitar la carga de ofertas
    """
    try:
        # Obtener solicitud con repuestos
        solicitud = await Solicitud.get_or_none(id=solicitud_id).prefetch_related('repuestos_solicitados')
        
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada"
            )
        
        repuestos = await RepuestoSolicitado.filter(solicitud_id=solicitud_id).order_by('created_at')
        
        if not repuestos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La solicitud no tiene repuestos"
            )
        
        # Crear DataFrame con los repuestos
        data = []
        for repuesto in repuestos:
            data.append({
                'repuesto_id': str(repuesto.id),
                'repuesto_nombre': repuesto.nombre,
                'cantidad': repuesto.cantidad,
                'precio_unitario': '',  # Vacío para que el asesor lo complete
                'garantia_meses': '',   # Vacío para que el asesor lo complete
                'marca_repuesto': '',
                'modelo_repuesto': '',
                'origen_repuesto': '',
                'observaciones': ''
            })
        
        df = pd.DataFrame(data)
        
        # Crear Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Oferta')
            
            # Ajustar ancho de columnas
            worksheet = writer.sheets['Oferta']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
        
        output.seek(0)
        
        # Retornar como descarga
        filename = f"plantilla_oferta_{solicitud.codigo_solicitud}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error generando plantilla: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando plantilla: {str(e)}"
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
        solicitud = await SolicitudesService.get_solicitud_by_id(solicitud_id)
        
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud not found"
            )
        
        return solicitud
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_solicitud: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching solicitud: {str(e)}"
        )




