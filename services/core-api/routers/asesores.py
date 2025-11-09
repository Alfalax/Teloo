"""
Asesores management router for TeLOO V3
Handles CRUD operations for asesores (advisors/providers)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
from tortoise.expressions import Q
from models.user import Usuario, Asesor
from models.enums import EstadoAsesor, EstadoUsuario, RolUsuario
from middleware.auth_middleware import RequireAdmin, get_current_active_user
from services.auth_service import AuthService

router = APIRouter(prefix="/asesores", tags=["Asesores"])

# Pydantic models for request/response
class AsesorCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    telefono: str
    ciudad: str
    departamento: str
    punto_venta: str
    direccion_punto_venta: Optional[str] = None
    password: str

class AsesorUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    punto_venta: Optional[str] = None
    direccion_punto_venta: Optional[str] = None
    estado: Optional[EstadoAsesor] = None

class AsesorResponse(BaseModel):
    id: str
    usuario: Dict[str, Any]
    ciudad: str
    departamento: str
    punto_venta: str
    direccion_punto_venta: Optional[str]
    confianza: float
    nivel_actual: int
    actividad_reciente_pct: float
    desempeno_historico_pct: float
    estado: str
    total_ofertas: int
    ofertas_ganadoras: int
    monto_total_ventas: float
    created_at: str
    updated_at: str

class AsesoresKPIs(BaseModel):
    total_asesores_habilitados: Dict[str, Any]
    total_puntos_venta: Dict[str, Any]
    cobertura_nacional: Dict[str, Any]

class BulkUpdateRequest(BaseModel):
    asesor_ids: List[str]
    estado: EstadoAsesor


@router.get("", summary="Obtener lista de asesores")
async def get_asesores(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Elementos por página"),
    search: Optional[str] = Query(None, description="Búsqueda por nombre, email o punto de venta"),
    estado: Optional[EstadoAsesor] = Query(None, description="Filtrar por estado"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad"),
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene lista paginada de asesores con filtros opcionales
    """
    try:
        # Build query
        query = Asesor.all().prefetch_related('usuario')
        
        # Apply filters
        if search:
            query = query.filter(
                Q(usuario__nombre__icontains=search) |
                Q(usuario__apellido__icontains=search) |
                Q(usuario__email__icontains=search) |
                Q(punto_venta__icontains=search)
            )
        
        if estado:
            query = query.filter(estado=estado)
        
        if ciudad:
            query = query.filter(ciudad=ciudad)
        
        if departamento:
            query = query.filter(departamento=departamento)
        
        # Get total count
        total = await query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        asesores = await query.offset(offset).limit(limit).order_by('-created_at')
        
        # Format response
        asesores_data = []
        for asesor in asesores:
            asesores_data.append({
                "id": str(asesor.id),
                "usuario": {
                    "id": str(asesor.usuario.id),
                    "nombre": asesor.usuario.nombre,
                    "apellido": asesor.usuario.apellido,
                    "email": asesor.usuario.email,
                    "telefono": asesor.usuario.telefono,
                    "estado": asesor.usuario.estado.value
                },
                "ciudad": asesor.ciudad,
                "departamento": asesor.departamento,
                "punto_venta": asesor.punto_venta,
                "direccion_punto_venta": asesor.direccion_punto_venta,
                "confianza": float(asesor.confianza),
                "nivel_actual": asesor.nivel_actual,
                "actividad_reciente_pct": float(asesor.actividad_reciente_pct),
                "desempeno_historico_pct": float(asesor.desempeno_historico_pct),
                "estado": asesor.estado.value,
                "total_ofertas": asesor.total_ofertas,
                "ofertas_ganadoras": asesor.ofertas_ganadoras,
                "monto_total_ventas": float(asesor.monto_total_ventas),
                "created_at": asesor.created_at.isoformat(),
                "updated_at": asesor.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "data": asesores_data,
            "total": total,
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo asesores: {str(e)}")


# Moved to end of file to avoid route conflicts with specific paths like /kpis, /ciudades, etc.


@router.post("", summary="Crear nuevo asesor")
async def create_asesor(
    asesor_data: AsesorCreate,
    current_user: Usuario = RequireAdmin
):
    """
    Crea un nuevo asesor con usuario asociado
    """
    try:
        # Check if email already exists
        existing_user = await Usuario.get_or_none(email=asesor_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        # Create user
        password_hash = AuthService.get_password_hash(asesor_data.password)
        
        usuario = await Usuario.create(
            email=asesor_data.email,
            password_hash=password_hash,
            nombre=asesor_data.nombre,
            apellido=asesor_data.apellido,
            telefono=asesor_data.telefono,
            rol=RolUsuario.ADVISOR,
            estado=EstadoUsuario.ACTIVO
        )
        
        # Create asesor
        asesor = await Asesor.create(
            usuario=usuario,
            ciudad=asesor_data.ciudad,
            departamento=asesor_data.departamento,
            punto_venta=asesor_data.punto_venta,
            direccion_punto_venta=asesor_data.direccion_punto_venta,
            estado=EstadoAsesor.ACTIVO
        )
        
        await asesor.fetch_related('usuario')
        
        return {
            "success": True,
            "data": {
                "id": str(asesor.id),
                "usuario": {
                    "id": str(asesor.usuario.id),
                    "nombre": asesor.usuario.nombre,
                    "apellido": asesor.usuario.apellido,
                    "email": asesor.usuario.email,
                    "telefono": asesor.usuario.telefono,
                    "estado": asesor.usuario.estado.value
                },
                "ciudad": asesor.ciudad,
                "departamento": asesor.departamento,
                "punto_venta": asesor.punto_venta,
                "direccion_punto_venta": asesor.direccion_punto_venta,
                "estado": asesor.estado.value,
                "created_at": asesor.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando asesor: {str(e)}")


@router.put("/{asesor_id}", summary="Actualizar asesor")
async def update_asesor(
    asesor_id: str,
    asesor_data: AsesorUpdate,
    current_user: Usuario = RequireAdmin
):
    """
    Actualiza información de un asesor
    """
    try:
        asesor = await Asesor.get_or_none(id=asesor_id).prefetch_related('usuario')
        
        if not asesor:
            raise HTTPException(status_code=404, detail="Asesor no encontrado")
        
        # Update usuario fields
        usuario_updated = False
        if asesor_data.nombre is not None:
            asesor.usuario.nombre = asesor_data.nombre
            usuario_updated = True
        if asesor_data.apellido is not None:
            asesor.usuario.apellido = asesor_data.apellido
            usuario_updated = True
        if asesor_data.email is not None:
            # Check if email is already taken by another user
            existing_user = await Usuario.get_or_none(email=asesor_data.email)
            if existing_user and existing_user.id != asesor.usuario.id:
                raise HTTPException(status_code=400, detail="El email ya está registrado")
            asesor.usuario.email = asesor_data.email
            usuario_updated = True
        if asesor_data.telefono is not None:
            asesor.usuario.telefono = asesor_data.telefono
            usuario_updated = True
        
        if usuario_updated:
            await asesor.usuario.save()
        
        # Update asesor fields
        asesor_updated = False
        if asesor_data.ciudad is not None:
            asesor.ciudad = asesor_data.ciudad
            asesor_updated = True
        if asesor_data.departamento is not None:
            asesor.departamento = asesor_data.departamento
            asesor_updated = True
        if asesor_data.punto_venta is not None:
            asesor.punto_venta = asesor_data.punto_venta
            asesor_updated = True
        if asesor_data.direccion_punto_venta is not None:
            asesor.direccion_punto_venta = asesor_data.direccion_punto_venta
            asesor_updated = True
        if asesor_data.estado is not None:
            asesor.estado = asesor_data.estado
            asesor_updated = True
        
        if asesor_updated:
            await asesor.save()
        
        return {
            "success": True,
            "data": {
                "id": str(asesor.id),
                "message": "Asesor actualizado exitosamente"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando asesor: {str(e)}")


@router.patch("/{asesor_id}/estado", summary="Actualizar estado del asesor")
async def update_asesor_estado(
    asesor_id: str,
    estado_data: Dict[str, EstadoAsesor],
    current_user: Usuario = RequireAdmin
):
    """
    Actualiza solo el estado de un asesor
    """
    try:
        asesor = await Asesor.get_or_none(id=asesor_id)
        
        if not asesor:
            raise HTTPException(status_code=404, detail="Asesor no encontrado")
        
        asesor.estado = estado_data["estado"]
        await asesor.save()
        
        return {
            "success": True,
            "data": {
                "id": str(asesor.id),
                "estado": asesor.estado.value,
                "message": f"Estado actualizado a {asesor.estado.value}"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando estado: {str(e)}")


@router.delete("/{asesor_id}", summary="Eliminar asesor")
async def delete_asesor(
    asesor_id: str,
    current_user: Usuario = RequireAdmin
):
    """
    Elimina un asesor y su usuario asociado
    """
    try:
        asesor = await Asesor.get_or_none(id=asesor_id).prefetch_related('usuario')
        
        if not asesor:
            raise HTTPException(status_code=404, detail="Asesor no encontrado")
        
        # Delete asesor (this will cascade to usuario due to OneToOne relationship)
        usuario_id = asesor.usuario.id
        await asesor.delete()
        await asesor.usuario.delete()
        
        return {
            "success": True,
            "message": "Asesor eliminado exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando asesor: {str(e)}")


@router.get("/kpis", summary="Obtener KPIs de asesores")
async def get_asesores_kpis(
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene KPIs principales del módulo de asesores
    """
    try:
        # Calculate date range
        if not fecha_fin:
            fecha_fin = datetime.now()
        else:
            fecha_fin = datetime.fromisoformat(fecha_fin)
        
        if not fecha_inicio:
            fecha_inicio = fecha_fin - timedelta(days=30)
        else:
            fecha_inicio = datetime.fromisoformat(fecha_inicio)
        
        # Previous period for comparison
        period_days = (fecha_fin - fecha_inicio).days
        fecha_inicio_prev = fecha_inicio - timedelta(days=period_days)
        fecha_fin_prev = fecha_inicio
        
        # Current period metrics
        total_asesores = await Asesor.filter(estado=EstadoAsesor.ACTIVO).count()
        
        # Calculate unique puntos de venta
        asesores_activos = await Asesor.filter(estado=EstadoAsesor.ACTIVO).all()
        unique_puntos_venta = set(asesor.punto_venta for asesor in asesores_activos if asesor.punto_venta)
        total_puntos_venta = len(unique_puntos_venta)
        
        # Calculate coverage (unique cities/departments)
        unique_cities = set(asesor.ciudad for asesor in asesores_activos if asesor.ciudad)
        cobertura_nacional = len(unique_cities)
        
        # Previous period metrics for comparison
        asesores_prev = await Asesor.filter(
            estado=EstadoAsesor.ACTIVO,
            created_at__lt=fecha_inicio
        ).all()
        total_asesores_prev = len(asesores_prev)
        
        # Calculate unique puntos de venta in previous period
        unique_puntos_venta_prev = set(asesor.punto_venta for asesor in asesores_prev if asesor.punto_venta)
        total_puntos_venta_prev = len(unique_puntos_venta_prev)
        
        # Calculate changes
        cambio_asesores = ((total_asesores - total_asesores_prev) / max(total_asesores_prev, 1)) * 100
        cambio_puntos_venta = ((total_puntos_venta - total_puntos_venta_prev) / max(total_puntos_venta_prev, 1)) * 100
        cambio_cobertura = 0  # Would need historical data for proper calculation
        
        return {
            "success": True,
            "data": {
                "total_asesores_habilitados": {
                    "valor": total_asesores,
                    "cambio_porcentual": round(cambio_asesores, 1),
                    "periodo": f"{fecha_inicio.strftime('%Y-%m-%d')} - {fecha_fin.strftime('%Y-%m-%d')}"
                },
                "total_puntos_venta": {
                    "valor": total_puntos_venta,
                    "cambio_porcentual": round(cambio_puntos_venta, 1),
                    "periodo": f"{fecha_inicio.strftime('%Y-%m-%d')} - {fecha_fin.strftime('%Y-%m-%d')}"
                },
                "cobertura_nacional": {
                    "valor": cobertura_nacional,
                    "cambio_porcentual": round(cambio_cobertura, 1),
                    "periodo": f"{fecha_inicio.strftime('%Y-%m-%d')} - {fecha_fin.strftime('%Y-%m-%d')}"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo KPIs: {str(e)}")


@router.get("/ciudades", summary="Obtener lista de ciudades")
async def get_ciudades(current_user: Usuario = Depends(get_current_active_user)):
    """
    Obtiene lista única de ciudades de asesores
    """
    try:
        asesores = await Asesor.all()
        ciudades = set(asesor.ciudad for asesor in asesores if asesor.ciudad)
        return {
            "success": True,
            "data": sorted(list(ciudades))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo ciudades: {str(e)}")


@router.get("/departamentos", summary="Obtener lista de departamentos")
async def get_departamentos(current_user: Usuario = Depends(get_current_active_user)):
    """
    Obtiene lista única de departamentos de asesores
    """
    try:
        asesores = await Asesor.all()
        departamentos = set(asesor.departamento for asesor in asesores if asesor.departamento)
        return {
            "success": True,
            "data": sorted(list(departamentos))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo departamentos: {str(e)}")


@router.patch("/bulk/estado", summary="Actualización masiva de estado")
async def bulk_update_estado(
    bulk_data: BulkUpdateRequest,
    current_user: Usuario = RequireAdmin
):
    """
    Actualiza el estado de múltiples asesores
    """
    try:
        updated_count = await Asesor.filter(id__in=bulk_data.asesor_ids).update(estado=bulk_data.estado)
        
        return {
            "success": True,
            "message": f"Estado actualizado para {updated_count} asesores",
            "updated": updated_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en actualización masiva: {str(e)}")


@router.post("/import/excel", summary="Importar asesores desde Excel")
async def import_asesores_excel(
    file: UploadFile = File(...),
    current_user: Usuario = RequireAdmin
):
    """
    Importa asesores desde archivo Excel
    
    Formato esperado:
    - nombre, apellido, email, telefono (obligatorios)
    - ciudad, departamento, punto_venta (obligatorios)
    - direccion_punto_venta, password (opcionales)
    """
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Archivo debe ser Excel (.xlsx o .xls)")
    
    from services.asesores_service import AsesoresService
    return await AsesoresService.import_asesores_excel(file)


@router.get("/export/excel", summary="Exportar asesores a Excel")
async def export_asesores_excel(
    search: Optional[str] = Query(None, description="Búsqueda por nombre, email o punto de venta"),
    estado: Optional[EstadoAsesor] = Query(None, description="Filtrar por estado"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad"),
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Exporta asesores a archivo Excel con filtros aplicados
    """
    from services.asesores_service import AsesoresService
    
    excel_file = await AsesoresService.export_asesores_excel(search, estado, ciudad, departamento)
    
    filename = f"asesores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        BytesIO(excel_file.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/template/excel", summary="Descargar plantilla Excel")
async def download_excel_template(
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Descarga plantilla Excel para importación de asesores
    """
    from services.asesores_service import AsesoresService
    
    template_file = await AsesoresService.get_excel_template()
    
    return StreamingResponse(
        BytesIO(template_file.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_asesores.xlsx"}
    )


@router.get("/{asesor_id}/metrics", summary="Obtener métricas del asesor")
async def get_asesor_metrics(
    asesor_id: str,
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene métricas detalladas de un asesor específico
    """
    try:
        asesor = await Asesor.get_or_none(id=asesor_id).prefetch_related('usuario', 'ofertas')
        
        if not asesor:
            raise HTTPException(status_code=404, detail="Asesor no encontrado")
        
        # Calculate date range
        if not fecha_fin:
            fecha_fin = datetime.now()
        else:
            fecha_fin = datetime.fromisoformat(fecha_fin)
        
        if not fecha_inicio:
            fecha_inicio = fecha_fin - timedelta(days=30)
        else:
            fecha_inicio = datetime.fromisoformat(fecha_inicio)
        
        # Get ofertas in date range
        from models.oferta import Oferta
        ofertas_periodo = await Oferta.filter(
            asesor=asesor,
            created_at__gte=fecha_inicio,
            created_at__lte=fecha_fin
        ).prefetch_related('solicitud')
        
        # Calculate metrics
        total_ofertas_periodo = len(ofertas_periodo)
        ofertas_ganadoras_periodo = len([o for o in ofertas_periodo if o.estado.value == 'GANADORA'])
        monto_total_periodo = sum([float(o.monto_total) for o in ofertas_periodo])
        
        tasa_adjudicacion_periodo = 0
        if total_ofertas_periodo > 0:
            tasa_adjudicacion_periodo = (ofertas_ganadoras_periodo / total_ofertas_periodo) * 100
        
        # Response time metrics
        tiempos_respuesta = []
        for oferta in ofertas_periodo:
            if oferta.solicitud and oferta.solicitud.created_at:
                tiempo_respuesta = (oferta.created_at - oferta.solicitud.created_at).total_seconds() / 3600
                tiempos_respuesta.append(tiempo_respuesta)
        
        tiempo_respuesta_promedio = sum(tiempos_respuesta) / len(tiempos_respuesta) if tiempos_respuesta else 0
        
        return {
            "success": True,
            "data": {
                "asesor_info": {
                    "id": str(asesor.id),
                    "nombre": asesor.usuario.nombre_completo,
                    "punto_venta": asesor.punto_venta,
                    "ciudad": asesor.ciudad,
                    "estado": asesor.estado.value
                },
                "metricas_periodo": {
                    "fecha_inicio": fecha_inicio.isoformat(),
                    "fecha_fin": fecha_fin.isoformat(),
                    "total_ofertas": total_ofertas_periodo,
                    "ofertas_ganadoras": ofertas_ganadoras_periodo,
                    "monto_total": monto_total_periodo,
                    "tasa_adjudicacion": round(tasa_adjudicacion_periodo, 2),
                    "tiempo_respuesta_promedio_horas": round(tiempo_respuesta_promedio, 2)
                },
                "metricas_historicas": {
                    "total_ofertas": asesor.total_ofertas,
                    "ofertas_ganadoras": asesor.ofertas_ganadoras,
                    "monto_total_ventas": float(asesor.monto_total_ventas),
                    "tasa_adjudicacion_historica": asesor.tasa_adjudicacion,
                    "confianza": float(asesor.confianza),
                    "nivel_actual": asesor.nivel_actual,
                    "actividad_reciente_pct": float(asesor.actividad_reciente_pct),
                    "desempeno_historico_pct": float(asesor.desempeno_historico_pct)
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo métricas: {str(e)}")


# Dynamic route - must be at the end to avoid conflicts with specific paths
@router.get("/{asesor_id}", summary="Obtener asesor por ID")
async def get_asesor(
    asesor_id: str,
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene un asesor específico por ID
    """
    try:
        asesor = await Asesor.get_or_none(id=asesor_id).prefetch_related('usuario')
        
        if not asesor:
            raise HTTPException(status_code=404, detail="Asesor no encontrado")
        
        return {
            "success": True,
            "data": {
                "id": str(asesor.id),
                "usuario": {
                    "id": str(asesor.usuario.id),
                    "nombre": asesor.usuario.nombre,
                    "apellido": asesor.usuario.apellido,
                    "email": asesor.usuario.email,
                    "telefono": asesor.usuario.telefono,
                    "estado": asesor.usuario.estado.value
                },
                "ciudad": asesor.ciudad,
                "departamento": asesor.departamento,
                "punto_venta": asesor.punto_venta,
                "direccion_punto_venta": asesor.direccion_punto_venta,
                "confianza": float(asesor.confianza),
                "nivel_actual": asesor.nivel_actual,
                "actividad_reciente_pct": float(asesor.actividad_reciente_pct),
                "desempeno_historico_pct": float(asesor.desempeno_historico_pct),
                "estado": asesor.estado.value,
                "total_ofertas": asesor.total_ofertas,
                "ofertas_ganadoras": asesor.ofertas_ganadoras,
                "monto_total_ventas": float(asesor.monto_total_ventas),
                "created_at": asesor.created_at.isoformat(),
                "updated_at": asesor.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo asesor: {str(e)}")
