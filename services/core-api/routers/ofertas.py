"""
Ofertas Router for TeLOO V3
Handles offer creation, bulk upload, and state management
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from decimal import Decimal
import logging
import io

from services.ofertas_service import OfertasService
from middleware.auth_middleware import get_current_user
from models.user import Usuario
from models.solicitud import Solicitud, RepuestoSolicitado
from models.enums import EstadoSolicitud, EstadoOferta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ofertas", tags=["ofertas"])


# Pydantic models for request/response
class OfertaDetalleCreate(BaseModel):
    """Schema for creating offer detail"""
    repuesto_solicitado_id: str = Field(..., description="ID del repuesto solicitado")
    precio_unitario: Decimal = Field(..., ge=1000, le=50000000, description="Precio unitario en COP")
    cantidad: int = Field(default=1, ge=1, description="Cantidad del repuesto")
    garantia_meses: int = Field(..., ge=1, le=60, description="Garantía en meses")
    marca_repuesto: Optional[str] = Field(None, max_length=100, description="Marca del repuesto")
    modelo_repuesto: Optional[str] = Field(None, max_length=100, description="Modelo del repuesto")
    origen_repuesto: Optional[str] = Field(None, max_length=50, description="Origen del repuesto")
    observaciones: Optional[str] = Field(None, description="Observaciones específicas")


class OfertaIndividualCreate(BaseModel):
    """Schema for creating individual offer"""
    solicitud_id: str = Field(..., description="ID de la solicitud")
    tiempo_entrega_dias: int = Field(..., ge=0, le=90, description="Tiempo de entrega en días")
    observaciones: Optional[str] = Field(None, description="Observaciones generales")
    detalles: List[OfertaDetalleCreate] = Field(..., min_items=1, description="Detalles de la oferta")
    
    @validator('detalles')
    def validate_detalles_not_empty(cls, v):
        if not v:
            raise ValueError('Debe incluir al menos un repuesto en la oferta')
        return v


class OfertaResponse(BaseModel):
    """Schema for offer response"""
    success: bool
    oferta_id: str
    codigo_oferta: str
    monto_total: float
    cantidad_repuestos: int
    cobertura_porcentaje: float
    detalles_count: int
    message: str


class ValidationResponse(BaseModel):
    """Schema for validation response"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    cobertura_estimada: Optional[float] = None


class EstadoUpdateRequest(BaseModel):
    """Schema for updating offer state"""
    nuevo_estado: EstadoOferta = Field(..., description="Nuevo estado de la oferta")
    motivo: Optional[str] = Field(None, description="Motivo del cambio de estado")


class EstadoUpdateResponse(BaseModel):
    """Schema for state update response"""
    success: bool
    oferta_id: str
    estado_anterior: str
    estado_nuevo: str
    motivo: Optional[str]
    message: str


class BulkUploadResponse(BaseModel):
    """Schema for bulk upload response"""
    success: bool
    oferta_id: Optional[str] = None
    codigo_oferta: Optional[str] = None
    monto_total: Optional[float] = None
    cantidad_repuestos: Optional[int] = None
    cobertura_porcentaje: Optional[float] = None
    rows_processed: int
    errors: List[str] = []
    warnings: List[str] = []
    message: str


@router.post("/", response_model=OfertaResponse)
async def create_oferta_individual(
    oferta_data: OfertaIndividualCreate,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Create individual offer from form data
    
    - **solicitud_id**: ID of the solicitud to make offer for
    - **tiempo_entrega_dias**: General delivery time for entire order (0-90 days)
    - **observaciones**: Optional general observations
    - **detalles**: List of offer details per repuesto
    
    Requirements: 4.3, 4.5
    """
    try:
        # Get asesor from current user
        asesor = await current_user.asesor
        if not asesor:
            raise HTTPException(
                status_code=403,
                detail="Usuario no es un asesor registrado"
            )
        
        # Convert Pydantic model to dict for service
        detalles_dict = [detalle.dict() for detalle in oferta_data.detalles]
        
        # Create offer
        result = await OfertasService.create_oferta_individual(
            solicitud_id=oferta_data.solicitud_id,
            asesor_id=str(asesor.id),
            tiempo_entrega_dias=oferta_data.tiempo_entrega_dias,
            observaciones=oferta_data.observaciones,
            detalles=detalles_dict,
            redis_client=None  # TODO: Inject Redis client
        )
        
        return OfertaResponse(**result)
        
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"Error de validación en create_oferta_individual: {e}")
        
        # Check for concurrency error
        if "evaluación en progreso" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Error inesperado en create_oferta_individual: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/validate", response_model=ValidationResponse)
async def validate_oferta_data(
    oferta_data: OfertaIndividualCreate,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Validate offer data before creation
    
    Useful for frontend validation and preview
    """
    try:
        # Get asesor from current user
        asesor = await current_user.asesor
        if not asesor:
            raise HTTPException(
                status_code=403,
                detail="Usuario no es un asesor registrado"
            )
        
        # Convert Pydantic model to dict for service
        detalles_dict = [detalle.dict() for detalle in oferta_data.detalles]
        
        # Validate data
        result = await OfertasService.validate_oferta_data(
            solicitud_id=oferta_data.solicitud_id,
            asesor_id=str(asesor.id),
            tiempo_entrega_dias=oferta_data.tiempo_entrega_dias,
            detalles=detalles_dict
        )
        
        return ValidationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error validando datos de oferta: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/{oferta_id}")
async def get_oferta(
    oferta_id: str,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Get offer by ID
    
    Returns complete offer information with details
    """
    try:
        oferta = await OfertasService.get_oferta_by_id(oferta_id)
        if not oferta:
            raise HTTPException(status_code=404, detail="Oferta no encontrada")
        
        # Check permissions - user must be the asesor or admin
        asesor = await current_user.asesor
        if current_user.rol != "ADMIN" and (not asesor or str(asesor.id) != str(oferta.asesor.id)):
            raise HTTPException(status_code=403, detail="No tiene permisos para ver esta oferta")
        
        # Convert to dict for response
        return {
            "id": str(oferta.id),
            "codigo_oferta": oferta.codigo_oferta,
            "solicitud_id": str(oferta.solicitud.id),
            "asesor": {
                "id": str(oferta.asesor.id),
                "nombre": oferta.asesor.usuario.nombre_completo,
                "telefono": oferta.asesor.usuario.telefono
            },
            "tiempo_entrega_dias": oferta.tiempo_entrega_dias,
            "observaciones": oferta.observaciones,
            "estado": oferta.estado,
            "origen": oferta.origen,
            "monto_total": float(oferta.monto_total),
            "cantidad_repuestos": oferta.cantidad_repuestos,
            "cobertura_porcentaje": float(oferta.cobertura_porcentaje),
            "puntaje_total": float(oferta.puntaje_total) if oferta.puntaje_total else None,
            "created_at": oferta.created_at.isoformat(),
            "detalles": [
                {
                    "id": str(detalle.id),
                    "repuesto": {
                        "id": str(detalle.repuesto_solicitado.id),
                        "nombre": detalle.repuesto_solicitado.nombre,
                        "vehiculo": detalle.repuesto_solicitado.vehiculo_completo
                    },
                    "precio_unitario": float(detalle.precio_unitario),
                    "cantidad": detalle.cantidad,
                    "garantia_meses": detalle.garantia_meses,
                    "tiempo_entrega_dias": detalle.tiempo_entrega_dias,
                    "marca_repuesto": detalle.marca_repuesto,
                    "modelo_repuesto": detalle.modelo_repuesto,
                    "origen_repuesto": detalle.origen_repuesto,
                    "observaciones": detalle.observaciones,
                    "monto_total": float(detalle.monto_total_detalle),
                    "puntaje_total": float(detalle.puntaje_total) if detalle.puntaje_total else None
                }
                for detalle in oferta.detalles
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo oferta {oferta_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/upload", response_model=OfertaResponse)
async def upload_oferta_excel(
    solicitud_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Upload Excel file to create bulk offer
    
    - **solicitud_id**: ID of the solicitud to make offer for
    - **file**: Excel file (.xlsx format, max 5MB)
    
    Expected Excel columns:
    - repuesto_nombre: Name of the repuesto (for matching)
    - precio_unitario: Unit price (1000-50000000)
    - cantidad: Quantity (default 1)
    - garantia_meses: Warranty in months (1-60)
    - marca_repuesto: Optional brand
    - modelo_repuesto: Optional model
    - origen_repuesto: Optional origin
    - observaciones: Optional observations
    
    First row can contain general info:
    - tiempo_entrega_dias: General delivery time
    - observaciones_generales: General observations
    
    Requirements: 4.4
    """
    try:
        # Get asesor from current user
        asesor = await current_user.asesor
        if not asesor:
            raise HTTPException(
                status_code=403,
                detail="Usuario no es un asesor registrado"
            )
        
        # Validate file format
        if not file.filename.lower().endswith('.xlsx'):
            raise HTTPException(
                status_code=400,
                detail="Archivo debe ser formato .xlsx"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Create bulk offer
        result = await OfertasService.create_oferta_bulk_excel(
            solicitud_id=solicitud_id,
            asesor_id=str(asesor.id),
            excel_file_content=file_content,
            filename=file.filename,
            redis_client=None  # TODO: Inject Redis client
        )
        
        if not result['success']:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "errors": result['errors'],
                    "warnings": result.get('warnings', []),
                    "rows_processed": result.get('rows_processed', 0),
                    "message": result['message']
                }
            )
        
        return OfertaResponse(**result)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error de validación en upload Excel: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado en upload Excel: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/template/{solicitud_id}")
async def download_excel_template(
    solicitud_id: str,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Download Excel template for bulk offer upload
    
    - **solicitud_id**: ID of the solicitud to generate template for
    
    Returns Excel file with repuestos from the solicitud pre-filled
    """
    try:
        # Get asesor from current user
        asesor = await current_user.asesor
        if not asesor:
            raise HTTPException(
                status_code=403,
                detail="Usuario no es un asesor registrado"
            )
        
        # Get solicitud and repuestos
        solicitud = await Solicitud.get_or_none(id=solicitud_id).prefetch_related('repuestos_solicitados')
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
        if solicitud.estado != EstadoSolicitud.ABIERTA:
            raise HTTPException(
                status_code=400,
                detail="Solicitud no está en estado ABIERTA"
            )
        
        # Generate Excel template
        excel_content = OfertasService.generate_excel_template(solicitud.repuestos_solicitados)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(excel_content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=template_oferta_{solicitud.codigo_solicitud}.xlsx"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando template Excel: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.patch("/{oferta_id}/estado", response_model=EstadoUpdateResponse)
async def update_oferta_estado(
    oferta_id: str,
    estado_data: EstadoUpdateRequest,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Update offer state
    
    - **oferta_id**: ID of the offer to update
    - **nuevo_estado**: New state to set
    - **motivo**: Optional reason for state change
    
    Allowed transitions:
    - ENVIADA → GANADORA, NO_SELECCIONADA, EXPIRADA, RECHAZADA
    - GANADORA → ACEPTADA, RECHAZADA, EXPIRADA
    - Other states are final
    
    Requirements: 5.1, 6.4
    """
    try:
        # Check if user has permission to update offer states
        # Only admins and the offer's asesor can update states
        oferta = await OfertasService.get_oferta_by_id(oferta_id)
        if not oferta:
            raise HTTPException(status_code=404, detail="Oferta no encontrada")
        
        asesor = await current_user.asesor
        if current_user.rol != "ADMIN" and (not asesor or str(asesor.id) != str(oferta.asesor.id)):
            raise HTTPException(
                status_code=403, 
                detail="No tiene permisos para actualizar el estado de esta oferta"
            )
        
        # Update state
        result = await OfertasService.actualizar_estado_oferta(
            oferta_id=oferta_id,
            nuevo_estado=estado_data.nuevo_estado,
            motivo=estado_data.motivo,
            redis_client=None  # TODO: Inject Redis client
        )
        
        return EstadoUpdateResponse(**result)
        
    except ValueError as e:
        logger.error(f"Error de validación actualizando estado: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado actualizando estado: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/estado/{estado}")
async def get_ofertas_by_estado(
    estado: EstadoOferta,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Get offers by state
    
    - **estado**: State to filter by
    
    Returns list of offers in the specified state
    """
    try:
        # Check permissions - advisors can only see their own offers
        ofertas = await OfertasService.get_ofertas_by_estado(estado)
        
        # Filter by asesor if user is advisor
        if current_user.rol == "ADVISOR":
            asesor = await current_user.asesor
            if asesor:
                ofertas = [o for o in ofertas if str(o.asesor.id) == str(asesor.id)]
        
        return {
            "estado": estado,
            "total": len(ofertas),
            "ofertas": [
                {
                    "id": str(oferta.id),
                    "codigo_oferta": oferta.codigo_oferta,
                    "solicitud_id": str(oferta.solicitud.id),
                    "asesor": {
                        "id": str(oferta.asesor.id),
                        "nombre": oferta.asesor.usuario.nombre_completo
                    },
                    "estado": oferta.estado,
                    "monto_total": float(oferta.monto_total),
                    "cantidad_repuestos": oferta.cantidad_repuestos,
                    "cobertura_porcentaje": float(oferta.cobertura_porcentaje),
                    "created_at": oferta.created_at.isoformat(),
                    "updated_at": oferta.updated_at.isoformat()
                }
                for oferta in ofertas
            ]
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo ofertas por estado {estado}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/expirar")
async def marcar_ofertas_expiradas(
    horas_expiracion: int = 20,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Mark offers as expired after specified hours
    
    - **horas_expiracion**: Hours after which offers expire (default 20)
    
    Only admins can trigger this operation
    """
    try:
        # Only admins can expire offers
        if current_user.rol != "ADMIN":
            raise HTTPException(
                status_code=403,
                detail="Solo administradores pueden marcar ofertas como expiradas"
            )
        
        # Validate hours
        if not (1 <= horas_expiracion <= 168):  # 1 hour to 1 week
            raise HTTPException(
                status_code=400,
                detail="Horas de expiración debe estar entre 1 y 168 (1 semana)"
            )
        
        # Mark offers as expired
        result = await OfertasService.marcar_ofertas_expiradas(
            horas_expiracion=horas_expiracion,
            redis_client=None  # TODO: Inject Redis client
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marcando ofertas como expiradas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/")
async def get_ofertas(
    solicitud_id: Optional[str] = None,
    asesor_id: Optional[str] = None,
    estado: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Get offers with optional filters
    
    - **solicitud_id**: Filter by solicitud
    - **asesor_id**: Filter by asesor (admins only, or current asesor)
    - **estado**: Filter by estado
    - **page**: Page number (1-based)
    - **limit**: Items per page (max 100)
    """
    try:
        # Validate pagination
        if page < 1:
            page = 1
        if limit > 100:
            limit = 100
        
        # Build query
        query = {}
        
        if solicitud_id:
            query['solicitud_id'] = solicitud_id
        
        if asesor_id:
            # Check permissions
            user_asesor = await current_user.asesor
            if current_user.rol != "ADMIN":
                if not user_asesor or str(user_asesor.id) != asesor_id:
                    raise HTTPException(status_code=403, detail="No tiene permisos para ver ofertas de otros asesores")
            query['asesor_id'] = asesor_id
        elif current_user.rol == "ADVISOR":
            # If user is advisor and no asesor_id specified, show only their offers
            user_asesor = await current_user.asesor
            if user_asesor:
                query['asesor_id'] = str(user_asesor.id)
        
        if estado:
            query['estado'] = estado
        
        # Get offers (simplified response for list)
        if solicitud_id:
            ofertas = await OfertasService.get_ofertas_by_solicitud(solicitud_id)
        else:
            # TODO: Implement general filtering in service
            ofertas = []
        
        # Apply pagination
        offset = (page - 1) * limit
        ofertas_page = ofertas[offset:offset + limit]
        
        return {
            "ofertas": [
                {
                    "id": str(oferta.id),
                    "codigo_oferta": oferta.codigo_oferta,
                    "solicitud_id": str(oferta.solicitud.id),
                    "asesor": {
                        "id": str(oferta.asesor.id),
                        "nombre": oferta.asesor.usuario.nombre_completo
                    },
                    "estado": oferta.estado,
                    "monto_total": float(oferta.monto_total),
                    "cantidad_repuestos": oferta.cantidad_repuestos,
                    "cobertura_porcentaje": float(oferta.cobertura_porcentaje),
                    "created_at": oferta.created_at.isoformat()
                }
                for oferta in ofertas_page
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(ofertas),
                "pages": (len(ofertas) + limit - 1) // limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo ofertas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/upload", response_model=BulkUploadResponse)
async def upload_oferta_excel(
    solicitud_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Upload Excel file with bulk offer data
    
    - **solicitud_id**: ID of the solicitud to make offer for
    - **file**: Excel file (.xlsx format, max 5MB)
    
    Expected Excel format:
    - First row: Configuration (tiempo_entrega_dias, observaciones_generales)
    - Following rows: One per repuesto with columns:
      - repuesto_nombre: Name matching solicitud repuestos
      - precio_unitario: Unit price (1000-50000000 COP)
      - cantidad: Quantity (default 1)
      - garantia_meses: Warranty months (1-60)
      - marca_repuesto, modelo_repuesto, origen_repuesto: Optional
      - observaciones: Optional observations
    
    Requirements: 4.4
    """
    try:
        # Get asesor from current user
        asesor = await current_user.asesor
        if not asesor:
            raise HTTPException(
                status_code=403,
                detail="Usuario no es un asesor registrado"
            )
        
        # Validate file format
        if not file.filename.lower().endswith('.xlsx'):
            raise HTTPException(
                status_code=400,
                detail="Archivo debe ser formato .xlsx"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size (5MB max)
        max_size = 5 * 1024 * 1024  # 5MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo excede el tamaño máximo de 5MB (actual: {len(file_content)/1024/1024:.1f}MB)"
            )
        
        # Process bulk upload
        result = await OfertasService.create_oferta_bulk_excel(
            solicitud_id=solicitud_id,
            asesor_id=str(asesor.id),
            excel_file_content=file_content,
            filename=file.filename,
            redis_client=None  # TODO: Inject Redis client
        )
        
        return BulkUploadResponse(**result)
        
    except HTTPException:
        raise
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"Error de validación en upload_oferta_excel: {e}")
        
        # Check for concurrency error
        if "evaluación en progreso" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        
        return BulkUploadResponse(
            success=False,
            rows_processed=0,
            errors=[error_msg],
            message="Error de validación"
        )
    except Exception as e:
        logger.error(f"Error inesperado en upload_oferta_excel: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/template/{solicitud_id}")
async def download_excel_template(
    solicitud_id: str,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Download Excel template for bulk offer upload
    
    - **solicitud_id**: ID of the solicitud to generate template for
    
    Returns Excel file with pre-filled repuestos from the solicitud
    """
    try:
        # Get asesor from current user
        asesor = await current_user.asesor
        if not asesor:
            raise HTTPException(
                status_code=403,
                detail="Usuario no es un asesor registrado"
            )
        
        # Get solicitud and repuestos
        solicitud = await Solicitud.get_or_none(id=solicitud_id).prefetch_related('repuestos_solicitados')
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
        if not solicitud.is_abierta():
            raise HTTPException(
                status_code=400,
                detail=f"Solicitud no está en estado ABIERTA (estado actual: {solicitud.estado})"
            )
        
        # Generate template
        repuestos = await RepuestoSolicitado.filter(solicitud=solicitud)
        excel_content = OfertasService.generate_excel_template(repuestos)
        
        # Create response
        excel_buffer = io.BytesIO(excel_content)
        
        return StreamingResponse(
            io.BytesIO(excel_content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=template_oferta_{solicitud.codigo_solicitud}.xlsx"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando template para solicitud {solicitud_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/validate-excel")
async def validate_excel_file(
    solicitud_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Validate Excel file without creating the offer
    
    Useful for preview and validation before actual upload
    """
    try:
        # Get asesor from current user
        asesor = await current_user.asesor
        if not asesor:
            raise HTTPException(
                status_code=403,
                detail="Usuario no es un asesor registrado"
            )
        
        # Validate file format
        if not file.filename.lower().endswith('.xlsx'):
            raise HTTPException(
                status_code=400,
                detail="Archivo debe ser formato .xlsx"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        max_size = 5 * 1024 * 1024  # 5MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo excede el tamaño máximo de 5MB"
            )
        
        # Parse and validate Excel
        result = await OfertasService.parse_and_validate_excel(
            excel_content=file_content,
            solicitud_id=solicitud_id,
            asesor_id=str(asesor.id)
        )
        
        return {
            "valid": result['valid'],
            "errors": result['errors'],
            "warnings": result['warnings'],
            "rows_processed": result['rows_processed'],
            "cobertura_estimada": result.get('cobertura_estimada', 0),
            "repuestos_encontrados": len(result.get('detalles', [])),
            "tiempo_entrega_dias": result.get('tiempo_entrega_dias', 1),
            "observaciones": result.get('observaciones'),
            "message": "Validación completada" if result['valid'] else "Errores encontrados en el archivo"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validando Excel: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/{oferta_id}/estado")
async def actualizar_estado_oferta(
    oferta_id: str,
    nuevo_estado: str = Form(...),
    motivo: Optional[str] = Form(None),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Update offer state
    
    - **oferta_id**: ID of the offer to update
    - **nuevo_estado**: New state (ENVIADA, GANADORA, NO_SELECCIONADA, EXPIRADA, RECHAZADA, ACEPTADA)
    - **motivo**: Optional reason for state change
    
    Allowed transitions:
    - ENVIADA → GANADORA, NO_SELECCIONADA, EXPIRADA, RECHAZADA
    - GANADORA → ACEPTADA, RECHAZADA
    - Other states are final
    
    Requirements: 5.1, 6.4
    """
    try:
        # Check permissions - only admin or offer owner can change state
        oferta = await OfertasService.get_oferta_by_id(oferta_id)
        if not oferta:
            raise HTTPException(status_code=404, detail="Oferta no encontrada")
        
        asesor = await current_user.asesor
        if current_user.rol != "ADMIN" and (not asesor or str(asesor.id) != str(oferta.asesor.id)):
            raise HTTPException(status_code=403, detail="No tiene permisos para modificar esta oferta")
        
        # Update state
        result = await OfertasService.actualizar_estado_oferta(
            oferta_id=oferta_id,
            nuevo_estado=nuevo_estado,
            usuario_id=str(current_user.id),
            motivo=motivo,
            redis_client=None  # TODO: Inject Redis client
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Error actualizando estado de oferta: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado actualizando estado: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/{oferta_id}/estados-permitidos")
async def get_estados_permitidos(
    oferta_id: str,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Get allowed next states for an offer
    
    - **oferta_id**: ID of the offer
    
    Returns list of allowed next states based on current state
    """
    try:
        # Check permissions
        oferta = await OfertasService.get_oferta_by_id(oferta_id)
        if not oferta:
            raise HTTPException(status_code=404, detail="Oferta no encontrada")
        
        asesor = await current_user.asesor
        if current_user.rol != "ADMIN" and (not asesor or str(asesor.id) != str(oferta.asesor.id)):
            raise HTTPException(status_code=403, detail="No tiene permisos para ver esta oferta")
        
        # Get allowed states
        estados_permitidos = await OfertasService.get_estados_permitidos(oferta_id)
        
        return {
            "oferta_id": oferta_id,
            "estado_actual": oferta.estado,
            "estados_permitidos": estados_permitidos,
            "puede_cambiar": len(estados_permitidos) > 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estados permitidos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/admin/expirar-ofertas")
async def marcar_ofertas_expiradas(
    timeout_horas: int = Form(20),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Mark expired offers (Admin only)
    
    - **timeout_horas**: Hours after which offers are considered expired (default 20)
    
    This endpoint is typically called by scheduled jobs but can be triggered manually by admins
    """
    try:
        # Check admin permissions
        if current_user.rol != "ADMIN":
            raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar esta acción")
        
        # Validate timeout
        if not (1 <= timeout_horas <= 168):  # 1 hour to 1 week
            raise HTTPException(status_code=400, detail="Timeout debe estar entre 1 y 168 horas")
        
        # Mark expired offers using the scheduled job function
        from jobs.scheduled_jobs import procesar_expiracion_ofertas
        result = await procesar_expiracion_ofertas(
            timeout_horas=timeout_horas,
            redis_client=None  # TODO: Inject Redis client
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marcando ofertas expiradas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")