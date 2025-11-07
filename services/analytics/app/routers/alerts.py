"""
Alerts API Router
Endpoints para gestión de alertas del sistema
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.services.alert_manager import alert_manager
from app.models.metrics import AlertaMetrica, HistorialAlerta
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Pydantic models para requests/responses

class AlertCreateRequest(BaseModel):
    nombre: str = Field(..., description="Nombre descriptivo de la alerta")
    metrica_nombre: str = Field(..., description="Nombre de la métrica a monitorear")
    operador: str = Field(..., description="Operador de comparación (>, <, >=, <=, ==, !=)")
    valor_umbral: float = Field(..., description="Valor umbral para disparar la alerta")
    canales_notificacion: List[str] = Field(default=["email"], description="Canales de notificación")

class AlertUpdateRequest(BaseModel):
    nombre: Optional[str] = None
    valor_umbral: Optional[float] = None
    canales_notificacion: Optional[List[str]] = None
    activa: Optional[bool] = None

class AlertResponse(BaseModel):
    id: int
    nombre: str
    metrica_nombre: str
    operador: str
    valor_umbral: float
    canales_notificacion: List[str]
    activa: bool
    creado_en: datetime
    actualizado_en: datetime

class AlertHistoryResponse(BaseModel):
    id: int
    alerta_nombre: str
    metrica_nombre: str
    valor_actual: float
    valor_umbral: float
    mensaje: str
    enviada: bool
    canales_enviados: List[str]
    disparada_en: datetime

class TestNotificationResponse(BaseModel):
    success: bool
    message: str
    details: Dict[str, Any]

@router.get("/", response_model=List[AlertResponse])
async def get_active_alerts():
    """
    Obtener todas las alertas activas configuradas
    """
    try:
        alertas = await alert_manager.get_active_alerts()
        return [AlertResponse(**alerta) for alerta in alertas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo alertas: {str(e)}")

@router.post("/", response_model=AlertResponse)
async def create_alert(alert_request: AlertCreateRequest):
    """
    Crear una nueva alerta personalizada
    """
    try:
        # Validar operador
        valid_operators = [">", "<", ">=", "<=", "==", "!="]
        if alert_request.operador not in valid_operators:
            raise HTTPException(
                status_code=400, 
                detail=f"Operador inválido. Debe ser uno de: {valid_operators}"
            )
        
        # Validar canales
        valid_channels = ["email", "slack"]
        invalid_channels = [ch for ch in alert_request.canales_notificacion if ch not in valid_channels]
        if invalid_channels:
            raise HTTPException(
                status_code=400,
                detail=f"Canales inválidos: {invalid_channels}. Canales válidos: {valid_channels}"
            )
        
        alerta = await alert_manager.create_custom_alert(
            nombre=alert_request.nombre,
            metrica_nombre=alert_request.metrica_nombre,
            operador=alert_request.operador,
            valor_umbral=alert_request.valor_umbral,
            canales=alert_request.canales_notificacion
        )
        
        return AlertResponse(
            id=alerta.id,
            nombre=alerta.nombre,
            metrica_nombre=alerta.metrica_nombre,
            operador=alerta.operador,
            valor_umbral=alerta.valor_umbral,
            canales_notificacion=alerta.canales_notificacion,
            activa=alerta.activa,
            creado_en=alerta.creado_en,
            actualizado_en=alerta.actualizado_en
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando alerta: {str(e)}")

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(alert_id: int, alert_request: AlertUpdateRequest):
    """
    Actualizar una alerta existente
    """
    try:
        alerta = await AlertaMetrica.get_or_none(id=alert_id)
        if not alerta:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        
        # Actualizar campos si se proporcionan
        if alert_request.nombre is not None:
            alerta.nombre = alert_request.nombre
        if alert_request.valor_umbral is not None:
            alerta.valor_umbral = alert_request.valor_umbral
        if alert_request.canales_notificacion is not None:
            # Validar canales
            valid_channels = ["email", "slack"]
            invalid_channels = [ch for ch in alert_request.canales_notificacion if ch not in valid_channels]
            if invalid_channels:
                raise HTTPException(
                    status_code=400,
                    detail=f"Canales inválidos: {invalid_channels}. Canales válidos: {valid_channels}"
                )
            alerta.canales_notificacion = alert_request.canales_notificacion
        if alert_request.activa is not None:
            alerta.activa = alert_request.activa
        
        await alerta.save()
        
        return AlertResponse(
            id=alerta.id,
            nombre=alerta.nombre,
            metrica_nombre=alerta.metrica_nombre,
            operador=alerta.operador,
            valor_umbral=alerta.valor_umbral,
            canales_notificacion=alerta.canales_notificacion,
            activa=alerta.activa,
            creado_en=alerta.creado_en,
            actualizado_en=alerta.actualizado_en
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando alerta: {str(e)}")

@router.delete("/{alert_id}")
async def delete_alert(alert_id: int):
    """
    Eliminar una alerta
    """
    try:
        alerta = await AlertaMetrica.get_or_none(id=alert_id)
        if not alerta:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        
        await alerta.delete()
        return {"message": "Alerta eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando alerta: {str(e)}")

@router.get("/history", response_model=List[AlertHistoryResponse])
async def get_alert_history(days: int = 7):
    """
    Obtener historial de alertas disparadas
    """
    try:
        if days < 1 or days > 90:
            raise HTTPException(status_code=400, detail="El parámetro 'days' debe estar entre 1 y 90")
        
        historial = await alert_manager.get_alert_history(days=days)
        return [AlertHistoryResponse(**item) for item in historial]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")

@router.post("/check")
async def trigger_alert_check(background_tasks: BackgroundTasks):
    """
    Disparar verificación manual de todas las alertas
    """
    try:
        background_tasks.add_task(alert_manager.check_all_alerts)
        return {"message": "Verificación de alertas iniciada en segundo plano"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error iniciando verificación: {str(e)}")

@router.post("/test/email", response_model=TestNotificationResponse)
async def test_email_configuration():
    """
    Probar configuración de email
    """
    try:
        notification_service = NotificationService()
        result = await notification_service.test_email_configuration()
        
        return TestNotificationResponse(
            success=result["success"],
            message=result["message"],
            details={
                "smtp_server": result["smtp_server"],
                "smtp_port": result["smtp_port"],
                "email_from": result["email_from"],
                "email_to": result["email_to"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error probando email: {str(e)}")

@router.post("/test/slack", response_model=TestNotificationResponse)
async def test_slack_configuration():
    """
    Probar configuración de Slack
    """
    try:
        notification_service = NotificationService()
        result = await notification_service.test_slack_configuration()
        
        return TestNotificationResponse(
            success=result["success"],
            message=result["message"],
            details={
                "webhook_url": result["webhook_url"],
                "channel": result["channel"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error probando Slack: {str(e)}")

@router.get("/metrics/available")
async def get_available_metrics():
    """
    Obtener lista de métricas disponibles para crear alertas
    """
    return {
        "metrics": [
            {
                "name": "tasa_error",
                "description": "Tasa de error del sistema (%)",
                "unit": "percentage",
                "recommended_thresholds": {
                    "warning": 2.0,
                    "critical": 5.0
                }
            },
            {
                "name": "latencia_promedio",
                "description": "Latencia promedio de respuesta (ms)",
                "unit": "milliseconds",
                "recommended_thresholds": {
                    "warning": 200.0,
                    "critical": 500.0
                }
            },
            {
                "name": "tasa_conversion",
                "description": "Tasa de conversión de solicitudes (%)",
                "unit": "percentage",
                "recommended_thresholds": {
                    "warning": 15.0,
                    "critical": 10.0
                }
            },
            {
                "name": "disponibilidad_sistema",
                "description": "Disponibilidad del sistema (%)",
                "unit": "percentage",
                "recommended_thresholds": {
                    "warning": 98.0,
                    "critical": 95.0
                }
            },
            {
                "name": "solicitudes_sin_ofertas_pct",
                "description": "Porcentaje de solicitudes sin ofertas (%)",
                "unit": "percentage",
                "recommended_thresholds": {
                    "warning": 20.0,
                    "critical": 30.0
                }
            }
        ]
    }

@router.get("/status")
async def get_alert_system_status():
    """
    Obtener estado del sistema de alertas
    """
    try:
        # Contar alertas activas
        alertas_activas = await AlertaMetrica.filter(activa=True).count()
        
        # Contar alertas disparadas en las últimas 24 horas
        yesterday = datetime.utcnow() - timedelta(days=1)
        alertas_recientes = await HistorialAlerta.filter(
            disparada_en__gte=yesterday
        ).count()
        
        # Obtener última verificación (simulada por ahora)
        ultima_verificacion = datetime.utcnow()
        
        return {
            "status": "active",
            "alertas_activas": alertas_activas,
            "alertas_disparadas_24h": alertas_recientes,
            "ultima_verificacion": ultima_verificacion,
            "configuracion": {
                "intervalo_verificacion": "5 minutos",
                "canales_disponibles": ["email", "slack"],
                "metricas_monitoreadas": 5
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")