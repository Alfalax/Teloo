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
from middleware.service_auth import verify_service_api_key
from services.solicitudes_service import SolicitudesService
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import pandas as pd
import io
import logging

router = APIRouter(prefix="/v1/solicitudes", tags=["solicitudes"])
logger = logging.getLogger(__name__)


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
    municipio_id: str = Field(..., description="ID del municipio de origen")
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
    municipio_id: Optional[str] = None
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
                "municipio_id": None,
                "ciudad": None,
                "departamento": None
            }
        
        return {
            "found": True,
            "cliente_id": str(cliente.id),
            "nombre": usuario.nombre_completo,
            "email": usuario.email,
            "telefono": usuario.telefono,
            "municipio_id": str(cliente.municipio_id) if cliente.municipio_id else None,
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
    Obtener métricas del asesor para el dashboard (MES ACTUAL)
    
    - repuestos_adjudicados: Total de repuestos en TODAS las solicitudes asignadas
    - monto_total_ganado: Suma de montos que los clientes han aceptado (solo ganadas)
    - pendientes_por_oferta: Solicitudes asignadas pendientes por ofertar
    - tasa_conversion: Porcentaje de monto aceptado vs monto ofertado
    - tasa_oferta: Porcentaje de repuestos ofertados vs repuestos asignados
    """
    try:
        from models.user import Asesor
        from models.oferta import Oferta, AdjudicacionRepuesto
        from models.enums import EstadoOferta
        from models.geografia import EvaluacionAsesorTemp
        from utils.datetime_utils import now_utc
        from datetime import datetime
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 Calculando métricas para: {current_user.email}")
        
        # Get asesor
        asesor = await Asesor.get_or_none(usuario_id=current_user.id)
        if not asesor:
            logger.warning(f"⚠️ No se encontró asesor para usuario {current_user.email}")
            return {
                "repuestos_adjudicados": 0,
                "monto_total_ganado": 0.0,
                "pendientes_por_oferta": 0,
                "tasa_conversion": 0.0,
                "tasa_oferta": 0.0
            }
        
        # Obtener fecha de inicio del mes actual
        now = now_utc()
        inicio_mes = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
        
        logger.info(f"📅 Calculando métricas del mes: {inicio_mes.strftime('%Y-%m')}")
        
        # 1. REPUESTOS ASIGNADOS (mes actual)
        # Total de repuestos en TODAS las solicitudes asignadas al asesor
        from tortoise import connections
        conn = connections.get("default")
        
        repuestos_query = """
            SELECT COALESCE(SUM(rs.cantidad), 0) as total_repuestos
            FROM solicitudes s
            JOIN evaluaciones_asesores_temp e ON e.solicitud_id = s.id
            JOIN repuestos_solicitados rs ON rs.solicitud_id = s.id
            WHERE e.asesor_id = $1
              AND s.created_at >= $2
        """
        
        result = await conn.execute_query_dict(repuestos_query, [str(asesor.id), inicio_mes])
        repuestos_adjudicados = result[0]['total_repuestos'] if result else 0
        
        # 2. MONTO TOTAL GANADO (mes actual)
        # Suma de montos de adjudicaciones donde la oferta fue ACEPTADA
        adjudicaciones_aceptadas = await AdjudicacionRepuesto.filter(
            oferta__asesor_id=asesor.id,
            oferta__estado=EstadoOferta.ACEPTADA,
            created_at__gte=inicio_mes
        ).all()
        
        monto_total_ganado = sum(
            float(adj.precio_adjudicado) * adj.cantidad_adjudicada 
            for adj in adjudicaciones_aceptadas
        )
        
        # 3. PENDIENTES POR OFERTA (mes actual)
        # Solicitudes ABIERTAS asignadas al asesor que NO tienen oferta aún
        from tortoise import connections
        conn = connections.get("default")
        
        pendientes_query = """
            SELECT COUNT(DISTINCT s.id)
            FROM solicitudes s
            JOIN evaluaciones_asesores_temp e ON e.solicitud_id = s.id
            WHERE e.asesor_id = $1
              AND s.estado = 'ABIERTA'
              AND s.nivel_actual >= e.nivel_entrega
              AND s.created_at >= $2
              AND NOT EXISTS (
                SELECT 1 FROM ofertas o 
                WHERE o.solicitud_id = s.id 
                AND o.asesor_id = $1
              )
        """
        
        result = await conn.execute_query_dict(pendientes_query, [str(asesor.id), inicio_mes])
        pendientes_por_oferta = result[0]['count'] if result else 0
        
        # 4. TASA DE CONVERSIÓN (mes actual)
        # Porcentaje de monto aceptado vs monto ofertado
        ofertas_mes = await Oferta.filter(
            asesor_id=asesor.id,
            created_at__gte=inicio_mes
        ).all()
        
        monto_ofertado = sum(float(o.monto_total) for o in ofertas_mes)
        
        ofertas_aceptadas_mes = await Oferta.filter(
            asesor_id=asesor.id,
            estado=EstadoOferta.ACEPTADA,
            created_at__gte=inicio_mes
        ).all()
        
        monto_aceptado = sum(float(o.monto_total) for o in ofertas_aceptadas_mes)
        
        tasa_conversion = 0.0
        if monto_ofertado > 0:
            tasa_conversion = (monto_aceptado / monto_ofertado) * 100
        
        # 5. TASA DE OFERTA (mes actual)
        # Porcentaje de repuestos ofertados vs repuestos asignados
        repuestos_ofertados_query = """
            SELECT COALESCE(SUM(od.cantidad), 0) as total_ofertados
            FROM ofertas o
            JOIN ofertas_detalle od ON od.oferta_id = o.id
            WHERE o.asesor_id = $1
              AND o.created_at >= $2
        """
        
        result = await conn.execute_query_dict(repuestos_ofertados_query, [str(asesor.id), inicio_mes])
        repuestos_ofertados = result[0]['total_ofertados'] if result else 0
        
        tasa_oferta = 0.0
        if repuestos_adjudicados > 0:
            tasa_oferta = (repuestos_ofertados / repuestos_adjudicados) * 100
        
        logger.info(f"✅ Métricas calculadas - Asignados: {repuestos_adjudicados}, Ofertados: {repuestos_ofertados}, Tasa Oferta: {tasa_oferta:.1f}%, Monto: ${monto_total_ganado:,.0f}, Pendientes: {pendientes_por_oferta}, Conversión: {tasa_conversion:.1f}%")
        
        return {
            "repuestos_adjudicados": repuestos_adjudicados,
            "monto_total_ganado": round(monto_total_ganado, 2),
            "pendientes_por_oferta": pendientes_por_oferta,
            "tasa_conversion": round(tasa_conversion, 2),
            "tasa_oferta": round(tasa_oferta, 2)
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
            municipio_id=request.municipio_id,
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


@router.get("/services/municipio")
async def buscar_municipio_servicio(
    ciudad: str = Query(..., description="Nombre de la ciudad a buscar"),
    service_name: str = Depends(verify_service_api_key)
):
    """
    Buscar municipio por nombre - Endpoint para servicios autenticados
    Retorna el primer municipio que coincida con el nombre
    
    Requiere autenticación de servicio mediante:
    - Header: X-Service-Name (ej: "agent-ia")
    - Header: X-Service-API-Key (API key del servicio)
    """
    try:
        from models.geografia import Municipio
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"Service '{service_name}' searching for municipio: {ciudad}")
        
        # Normalizar búsqueda (quitar tildes y convertir a mayúsculas)
        ciudad_norm = Municipio.normalizar_ciudad(ciudad)
        
        # Estrategia de búsqueda en orden de prioridad:
        # 1. Coincidencia exacta
        municipio = await Municipio.filter(municipio_norm=ciudad_norm).first()
        
        # 2. Coincidencia que empiece con el término buscado
        if not municipio:
            municipio = await Municipio.filter(municipio_norm__istartswith=ciudad_norm).first()
        
        # 3. Coincidencia parcial (para casos como "BOGOTA" -> "BOGOTA, D.C.")
        if not municipio:
            municipio = await Municipio.filter(municipio_norm__icontains=ciudad_norm).first()
        
        if not municipio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Municipio '{ciudad}' no encontrado"
            )
        
        return {
            "id": str(municipio.id),
            "municipio": municipio.municipio,
            "departamento": municipio.departamento,
            "hub_logistico": municipio.hub_logistico
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error buscando municipio: {str(e)}"
        )


@router.post("/services/bot", response_model=SolicitudResponse, status_code=status.HTTP_201_CREATED)
async def create_solicitud_from_bot(
    request: CreateSolicitudRequest,
    service_name: str = Depends(verify_service_api_key)
):
    """
    Crear solicitud desde bot (Telegram/WhatsApp) - Endpoint seguro para servicios
    
    Requiere autenticación de servicio mediante:
    - Header: X-Service-Name (ej: "agent-ia")
    - Header: X-Service-API-Key (API key del servicio)
    
    Este endpoint está protegido con:
    - Autenticación de servicio
    - Rate limiting
    - Logging completo para auditoría
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Logging para auditoría
        logger.info(f"Service '{service_name}' creating solicitud for client: {request.cliente.nombre}")
        logger.debug(f"Solicitud data: municipio_id={request.municipio_id}, repuestos_count={len(request.repuestos)}")
        
        # Convert request to dict
        cliente_data = request.cliente.model_dump()
        repuestos_data = [rep.model_dump() for rep in request.repuestos]
        
        solicitud = await SolicitudesService.create_solicitud(
            cliente_data=cliente_data,
            municipio_id=request.municipio_id,
            ciudad_origen=request.ciudad_origen,
            departamento_origen=request.departamento_origen,
            repuestos=repuestos_data
        )
        
        # Log éxito
        logger.info(f"Solicitud created successfully by '{service_name}': {solicitud['id']}")
        
        return solicitud
        
    except ValueError as e:
        logger.warning(f"Validation error from '{service_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        logger.error(f"Error creating solicitud from '{service_name}': {str(e)}")
        logger.error(traceback.format_exc())
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






# ============================================================================
# CLIENT RESPONSE ENDPOINTS
# ============================================================================

class RespuestaClienteRequest(BaseModel):
    """Request model for client response to offers"""
    respuesta_texto: str = Field(..., min_length=1, description="Client's response text")
    usar_nlp: bool = Field(True, description="Whether to use NLP for intent detection")


class RespuestaClienteResponse(BaseModel):
    """Response model for client response processing"""
    success: bool
    solicitud_id: str
    tipo_respuesta: str
    mensaje: str
    repuestos_aceptados: Optional[List[str]] = None
    repuestos_rechazados: Optional[List[str]] = None


@router.post("/{solicitud_id}/respuesta-cliente", response_model=RespuestaClienteResponse)
async def procesar_respuesta_cliente(
    solicitud_id: uuid.UUID,
    request: RespuestaClienteRequest,
    _: str = Depends(verify_service_api_key)
):
    """
    Process client response to winning offers
    
    This endpoint is called by Agent IA service when client responds
    to the offers notification via WhatsApp/Telegram.
    
    Supports:
    - Total acceptance: "acepto", "acepto todo"
    - Total rejection: "rechazo", "no"
    - Partial acceptance: "acepto 1,3,5"
    - Partial rejection: "rechazo 2"
    """
    try:
        from services.respuesta_cliente_service import RespuestaClienteService
        
        resultado = await RespuestaClienteService.procesar_respuesta(
            solicitud_id=str(solicitud_id),
            respuesta_texto=request.respuesta_texto,
            usar_nlp=request.usar_nlp
        )
        
        if not resultado['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=resultado.get('error', 'Error procesando respuesta')
            )
        
        return RespuestaClienteResponse(
            success=True,
            solicitud_id=resultado['solicitud_id'],
            tipo_respuesta=resultado['tipo_respuesta'],
            mensaje=resultado['mensaje'],
            repuestos_aceptados=resultado.get('repuestos_aceptados'),
            repuestos_rechazados=resultado.get('repuestos_rechazados')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint respuesta-cliente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando respuesta del cliente: {str(e)}"
        )


@router.get("/{solicitud_id}/pdf-ofertas")
async def descargar_pdf_ofertas(
    solicitud_id: uuid.UUID,
    _: str = Depends(verify_service_api_key)
):
    """
    Download PDF with winning offers
    
    This endpoint is called by Agent IA service to get the PDF
    for sending to clients via WhatsApp/Telegram.
    """
    try:
        from services.pdf_generator_service import PDFGeneratorService
        from fastapi.responses import StreamingResponse
        
        # Generate PDF
        pdf_buffer = await PDFGeneratorService.generar_pdf_ofertas_ganadoras(
            str(solicitud_id)
        )
        
        # Return as streaming response
        pdf_buffer.seek(0)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Propuesta_{solicitud_id}.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando PDF: {str(e)}"
        )
