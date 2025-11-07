"""
Admin endpoints for TeLOO V3 Core API
Handles administrative functions including geographic data import
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from services.geografia_service import GeografiaService
from services.configuracion_service import ConfiguracionService
from services.scheduler_service import scheduler_service
from middleware.auth_middleware import RequireAdmin, RequireSystemManagement, get_current_active_user
from models.user import Usuario

# Helper function for admin user dependency
async def get_current_admin_user(current_user: Usuario = Depends(get_current_active_user)) -> Usuario:
    """Get current admin user with proper validation"""
    if current_user.rol.value not in ['ADMIN', 'SUPPORT']:
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requieren permisos de administrador")
    return current_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/import/areas-metropolitanas")
async def import_areas_metropolitanas(
    file: UploadFile = File(...),
    current_user: Usuario = RequireAdmin
) -> Dict:
    """
    Importa áreas metropolitanas desde archivo Excel
    
    Expected file format: Areas_Metropolitanas_TeLOO.xlsx
    Required columns:
    - area_metropolitana: Nombre del área metropolitana
    - ciudad_nucleo: Ciudad núcleo del área
    - municipio_norm: Municipio normalizado
    
    Optional columns:
    - departamento: Departamento
    - poblacion: Población del municipio
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se proporcionó archivo")
    
    return await GeografiaService.importar_areas_metropolitanas_excel(file)


@router.post("/import/hubs-logisticos")
async def import_hubs_logisticos(
    file: UploadFile = File(...),
    current_user: Usuario = RequireAdmin
) -> Dict:
    """
    Importa hubs logísticos desde archivo Excel
    
    Expected file format: Asignacion_Hubs_200km.xlsx
    Required columns:
    - municipio_norm: Municipio normalizado
    - hub_asignado_norm: Hub logístico asignado normalizado
    
    Optional columns:
    - distancia_km: Distancia al hub en kilómetros
    - tiempo_estimado_horas: Tiempo estimado al hub en horas
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se proporcionó archivo")
    
    return await GeografiaService.importar_hubs_logisticos_excel(file)


@router.get("/geografia/validar-integridad")
async def validar_integridad_geografica(
    current_user: Usuario = RequireSystemManagement
) -> Dict:
    """
    Valida la integridad de los datos geográficos
    Verifica consistencia entre áreas metropolitanas y hubs logísticos
    """
    return await GeografiaService.validar_integridad_geografica()


@router.get("/geografia/estadisticas")
async def get_estadisticas_geograficas(
    current_user: Usuario = RequireSystemManagement
) -> Dict:
    """
    Obtiene estadísticas generales de los datos geográficos
    Incluye información sobre cobertura y distribución
    """
    return await GeografiaService.get_estadisticas_geograficas()


@router.post("/import/geografia")
async def import_geografia_completa(
    areas_file: UploadFile = File(..., description="Archivo de áreas metropolitanas"),
    hubs_file: UploadFile = File(..., description="Archivo de hubs logísticos"),
    current_user: Usuario = RequireAdmin
) -> Dict:
    """
    Importa datos geográficos completos (áreas metropolitanas + hubs logísticos)
    Endpoint combinado para subir ambos archivos Excel de una vez
    """
    
    try:
        # Importar áreas metropolitanas
        resultado_areas = await GeografiaService.importar_areas_metropolitanas_excel(areas_file)
        
        # Importar hubs logísticos
        resultado_hubs = await GeografiaService.importar_hubs_logisticos_excel(hubs_file)
        
        # Validar integridad después de la importación
        integridad = await GeografiaService.validar_integridad_geografica()
        
        return {
            "success": True,
            "message": "Importación geográfica completa exitosa",
            "areas_metropolitanas": resultado_areas,
            "hubs_logisticos": resultado_hubs,
            "validacion_integridad": integridad
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en importación completa: {str(e)}"
        )


@router.get("/configuracion", summary="Obtener configuración del sistema")
async def get_configuracion(
    categoria: Optional[str] = Query(None, description="Categoría específica de configuración"),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Obtiene la configuración actual del sistema
    
    Categorías disponibles:
    - pesos_escalamiento: Pesos del algoritmo de escalamiento
    - umbrales_niveles: Umbrales para clasificación por niveles
    - tiempos_espera_nivel: Tiempos de espera por nivel
    - canales_por_nivel: Canales de notificación por nivel
    - pesos_evaluacion_ofertas: Pesos para evaluación de ofertas
    - parametros_generales: Parámetros generales del sistema
    """
    
    if categoria:
        config = await ConfiguracionService.get_config(categoria)
        return {
            "categoria": categoria,
            "configuracion": config
        }
    else:
        config = await ConfiguracionService.get_config()
        return {
            "configuracion_completa": config
        }


@router.put("/configuracion/{categoria}", summary="Actualizar configuración")
async def update_configuracion(
    categoria: str,
    nuevos_valores: Dict[str, Any],
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Actualiza configuración de una categoría específica
    
    Validaciones automáticas:
    - Pesos deben sumar 1.0 (±1e-6)
    - Umbrales deben ser decrecientes
    - Rangos válidos para cada parámetro
    """
    
    try:
        config_actualizada = await ConfiguracionService.update_config(
            categoria,
            nuevos_valores,
            current_user
        )
        
        return {
            "success": True,
            "message": f"Configuración '{categoria}' actualizada exitosamente",
            "configuracion": config_actualizada
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando configuración: {str(e)}"
        )


@router.post("/configuracion/reset", summary="Resetear configuración")
async def reset_configuracion(
    categoria: Optional[str] = Query(None, description="Categoría a resetear (opcional)"),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Resetea configuración a valores por defecto
    
    Si no se especifica categoría, resetea toda la configuración
    """
    
    try:
        config_reseteada = await ConfiguracionService.reset_to_defaults(
            categoria,
            current_user
        )
        
        return {
            "success": True,
            "message": f"Configuración {'completa' if not categoria else categoria} reseteada a valores por defecto",
            "configuracion": config_reseteada
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reseteando configuración: {str(e)}"
        )


@router.get("/configuracion/summary", summary="Resumen de configuración")
async def get_configuracion_summary(
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Obtiene resumen completo de la configuración actual con metadatos
    """
    
    try:
        summary = await ConfiguracionService.get_config_summary()
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo resumen de configuración: {str(e)}"
        )

# Scheduler Management Endpoints

@router.get("/scheduler/status", summary="Estado del scheduler")
async def get_scheduler_status(
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Obtiene el estado actual del scheduler y todos los jobs programados
    """
    try:
        status = scheduler_service.get_job_status()
        return {
            "success": True,
            "scheduler_status": status
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estado del scheduler: {str(e)}"
        )


@router.post("/scheduler/jobs/{job_id}/trigger", summary="Ejecutar job manualmente")
async def trigger_job_manually(
    job_id: str,
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Ejecuta un job programado manualmente
    
    Jobs disponibles:
    - procesar_expiracion_ofertas: Procesa expiración de ofertas
    - advertencias_expiracion: Envía advertencias de expiración
    - limpiar_notificaciones: Limpia notificaciones expiradas
    """
    try:
        result = await scheduler_service.trigger_job_manually(job_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando job {job_id}: {str(e)}"
        )


@router.post("/scheduler/ofertas/procesar-expiracion", summary="Procesar expiración de ofertas")
async def procesar_expiracion_ofertas_manual(
    timeout_horas: Optional[int] = Query(None, description="Horas de timeout (usa configuración si no se especifica)"),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Procesa manualmente la expiración de ofertas
    Marca como EXPIRADA las ofertas que han superado el timeout configurado
    """
    try:
        from services.ofertas_service import OfertasService
        from services.configuracion_service import ConfiguracionService
        
        # Get timeout from config if not provided
        if timeout_horas is None:
            config = await ConfiguracionService.get_config('parametros_generales')
            timeout_horas = config.get('timeout_ofertas_horas', 20)
        
        # Process expiration
        result = await OfertasService.marcar_ofertas_expiradas(
            horas_expiracion=timeout_horas,
            redis_client=scheduler_service.redis_client
        )
        
        return {
            "success": True,
            "message": "Proceso de expiración ejecutado manualmente",
            "resultado": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando expiración: {str(e)}"
        )


@router.get("/scheduler/ofertas/proximas-expirar", summary="Ofertas próximas a expirar")
async def get_ofertas_proximas_expirar(
    horas_restantes: int = Query(2, description="Horas restantes para considerar próxima expiración"),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Obtiene ofertas que están próximas a expirar
    """
    try:
        from models.oferta import Oferta
        from models.enums import EstadoOferta
        from datetime import datetime, timedelta
        
        # Calculate cutoff time
        cutoff_time = datetime.now() + timedelta(hours=horas_restantes)
        
        # Find offers expiring soon
        ofertas_proximas = await Oferta.filter(
            estado=EstadoOferta.ENVIADA,
            fecha_expiracion__lte=cutoff_time,
            fecha_expiracion__gte=datetime.now()
        ).prefetch_related(
            'solicitud__cliente__usuario',
            'asesor__usuario'
        ).order_by('fecha_expiracion')
        
        ofertas_data = []
        for oferta in ofertas_proximas:
            time_remaining = oferta.fecha_expiracion - datetime.now()
            hours_remaining = max(0, int(time_remaining.total_seconds() / 3600))
            
            ofertas_data.append({
                'oferta_id': str(oferta.id),
                'codigo_oferta': oferta.codigo_oferta,
                'solicitud_id': str(oferta.solicitud.id),
                'cliente_nombre': oferta.solicitud.cliente.usuario.nombre_completo,
                'asesor_nombre': oferta.asesor.usuario.nombre_completo,
                'monto_total': float(oferta.monto_total),
                'fecha_expiracion': oferta.fecha_expiracion.isoformat(),
                'horas_restantes': hours_remaining,
                'created_at': oferta.created_at.isoformat()
            })
        
        return {
            "success": True,
            "ofertas_proximas_expirar": ofertas_data,
            "total": len(ofertas_data),
            "horas_filtro": horas_restantes
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo ofertas próximas a expirar: {str(e)}"
        )