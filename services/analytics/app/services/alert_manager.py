"""
Alert Manager Service
Gestiona alertas automáticas basadas en umbrales configurables de KPIs críticos
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

from app.models.metrics import AlertaMetrica, HistorialAlerta, MetricaCalculada
from app.models.events import EventoSistema
from app.core.redis import redis_manager
from app.core.config import settings
from app.services.metrics_calculator import MetricsCalculator
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class AlertSeverity(str, Enum):
    """Niveles de severidad de alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertOperator(str, Enum):
    """Operadores para comparación de umbrales"""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="

class AlertManager:
    """
    Gestor de alertas automáticas para KPIs críticos
    """
    
    def __init__(self):
        self.metrics_calculator = MetricsCalculator()
        self.notification_service = NotificationService()
        self.alert_cache_prefix = "alerts:"
        
        # Configuración de alertas por defecto
        self.default_alerts = {
            "error_rate": {
                "nombre": "Tasa de Error Alta",
                "metrica_nombre": "tasa_error",
                "operador": AlertOperator.GREATER_THAN,
                "valor_umbral": settings.ALERT_THRESHOLDS["error_rate"],
                "severidad": AlertSeverity.HIGH,
                "canales": ["email", "slack"]
            },
            "latency_p95": {
                "nombre": "Latencia P95 Alta",
                "metrica_nombre": "latencia_promedio",
                "operador": AlertOperator.GREATER_THAN,
                "valor_umbral": settings.ALERT_THRESHOLDS["latency_p95"],
                "severidad": AlertSeverity.MEDIUM,
                "canales": ["slack"]
            },
            "conversion_rate_low": {
                "nombre": "Tasa de Conversión Baja",
                "metrica_nombre": "tasa_conversion",
                "operador": AlertOperator.LESS_THAN,
                "valor_umbral": settings.ALERT_THRESHOLDS["conversion_rate"],
                "severidad": AlertSeverity.MEDIUM,
                "canales": ["email"]
            },
            "system_availability": {
                "nombre": "Disponibilidad del Sistema Baja",
                "metrica_nombre": "disponibilidad_sistema",
                "operador": AlertOperator.LESS_THAN,
                "valor_umbral": 99.0,  # 99%
                "severidad": AlertSeverity.CRITICAL,
                "canales": ["email", "slack"]
            },
            "solicitudes_sin_ofertas": {
                "nombre": "Alto Porcentaje de Solicitudes sin Ofertas",
                "metrica_nombre": "solicitudes_sin_ofertas_pct",
                "operador": AlertOperator.GREATER_THAN,
                "valor_umbral": 30.0,  # 30%
                "severidad": AlertSeverity.HIGH,
                "canales": ["email", "slack"]
            }
        }
    
    async def initialize_default_alerts(self):
        """
        Inicializar alertas por defecto si no existen
        """
        try:
            for alert_key, config in self.default_alerts.items():
                # Verificar si la alerta ya existe
                existing_alert = await AlertaMetrica.filter(
                    metrica_nombre=config["metrica_nombre"],
                    operador=config["operador"].value,
                    valor_umbral=config["valor_umbral"]
                ).first()
                
                if not existing_alert:
                    await AlertaMetrica.create(
                        nombre=config["nombre"],
                        metrica_nombre=config["metrica_nombre"],
                        operador=config["operador"].value,
                        valor_umbral=config["valor_umbral"],
                        canales_notificacion=config["canales"],
                        activa=True
                    )
                    logger.info(f"Alerta por defecto creada: {config['nombre']}")
                    
        except Exception as e:
            logger.error(f"Error inicializando alertas por defecto: {e}")
    
    async def check_all_alerts(self):
        """
        Verificar todas las alertas activas contra las métricas actuales
        """
        try:
            # Obtener todas las alertas activas
            alertas_activas = await AlertaMetrica.filter(activa=True).all()
            
            if not alertas_activas:
                logger.info("No hay alertas activas configuradas")
                return
            
            logger.info(f"Verificando {len(alertas_activas)} alertas activas")
            
            # Verificar cada alerta
            for alerta in alertas_activas:
                await self._check_single_alert(alerta)
                
        except Exception as e:
            logger.error(f"Error verificando alertas: {e}")
    
    async def _check_single_alert(self, alerta: AlertaMetrica):
        """
        Verificar una alerta específica
        """
        try:
            # Obtener el valor actual de la métrica
            valor_actual = await self._get_metric_value(alerta.metrica_nombre)
            
            if valor_actual is None:
                logger.warning(f"No se pudo obtener valor para métrica: {alerta.metrica_nombre}")
                return
            
            # Evaluar la condición de la alerta
            should_trigger = self._evaluate_alert_condition(
                valor_actual, 
                alerta.operador, 
                alerta.valor_umbral
            )
            
            if should_trigger:
                # Verificar si ya se disparó recientemente (evitar spam)
                if not await self._should_suppress_alert(alerta):
                    await self._trigger_alert(alerta, valor_actual)
                    
        except Exception as e:
            logger.error(f"Error verificando alerta {alerta.nombre}: {e}")
    
    async def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """
        Obtener el valor actual de una métrica
        """
        try:
            # Intentar obtener del cache primero
            cache_key = f"{self.alert_cache_prefix}metric:{metric_name}"
            cached_value = await redis_manager.get_cache(cache_key)
            
            if cached_value and "value" in cached_value:
                return float(cached_value["value"])
            
            # Calcular métrica según el tipo
            now = datetime.utcnow()
            last_hour = now - timedelta(hours=1)
            
            if metric_name == "tasa_error":
                salud = await self.metrics_calculator.get_salud_marketplace(last_hour, now)
                value = salud.get("tasa_error", 0.0)
            elif metric_name == "latencia_promedio":
                salud = await self.metrics_calculator.get_salud_marketplace(last_hour, now)
                value = salud.get("latencia_promedio", 0.0)
            elif metric_name == "tasa_conversion":
                kpis = await self.metrics_calculator.get_kpis_principales(last_hour, now)
                conversion_data = kpis.get("tasa_conversion", {})
                value = conversion_data.get("tasa_conversion", 0.0) if isinstance(conversion_data, dict) else 0.0
            elif metric_name == "disponibilidad_sistema":
                salud = await self.metrics_calculator.get_salud_marketplace(last_hour, now)
                value = salud.get("disponibilidad_sistema", 100.0)
            elif metric_name == "solicitudes_sin_ofertas_pct":
                value = await self._calculate_solicitudes_sin_ofertas_pct(last_hour, now)
            else:
                logger.warning(f"Métrica no reconocida: {metric_name}")
                return None
            
            # Cachear el valor por 5 minutos
            await redis_manager.set_cache(
                cache_key, 
                {"value": value, "timestamp": now.isoformat()}, 
                ttl=300
            )
            
            return float(value)
            
        except Exception as e:
            logger.error(f"Error obteniendo valor de métrica {metric_name}: {e}")
            return None
    
    async def _calculate_solicitudes_sin_ofertas_pct(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        """
        Calcular porcentaje de solicitudes sin ofertas
        """
        try:
            embudo = await self.metrics_calculator.get_embudo_operativo(fecha_inicio, fecha_fin)
            solicitudes_recibidas = embudo.get("solicitudes_recibidas", 0)
            solicitudes_procesadas = embudo.get("solicitudes_procesadas", 0)
            
            if solicitudes_recibidas == 0:
                return 0.0
            
            solicitudes_sin_ofertas = solicitudes_recibidas - solicitudes_procesadas
            porcentaje = (solicitudes_sin_ofertas / solicitudes_recibidas) * 100
            
            return round(porcentaje, 2)
            
        except Exception as e:
            logger.error(f"Error calculando porcentaje de solicitudes sin ofertas: {e}")
            return 0.0
    
    def _evaluate_alert_condition(self, valor_actual: float, operador: str, valor_umbral: float) -> bool:
        """
        Evaluar si se cumple la condición de la alerta
        """
        try:
            if operador == AlertOperator.GREATER_THAN.value:
                return valor_actual > valor_umbral
            elif operador == AlertOperator.LESS_THAN.value:
                return valor_actual < valor_umbral
            elif operador == AlertOperator.GREATER_EQUAL.value:
                return valor_actual >= valor_umbral
            elif operador == AlertOperator.LESS_EQUAL.value:
                return valor_actual <= valor_umbral
            elif operador == AlertOperator.EQUAL.value:
                return abs(valor_actual - valor_umbral) < 0.001  # Tolerancia para floats
            elif operador == AlertOperator.NOT_EQUAL.value:
                return abs(valor_actual - valor_umbral) >= 0.001
            else:
                logger.error(f"Operador no reconocido: {operador}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluando condición de alerta: {e}")
            return False
    
    async def _should_suppress_alert(self, alerta: AlertaMetrica) -> bool:
        """
        Verificar si se debe suprimir la alerta para evitar spam
        """
        try:
            # Buscar alertas recientes (última hora)
            recent_threshold = datetime.utcnow() - timedelta(hours=1)
            
            recent_alert = await HistorialAlerta.filter(
                alerta=alerta,
                disparada_en__gte=recent_threshold,
                enviada=True
            ).first()
            
            return recent_alert is not None
            
        except Exception as e:
            logger.error(f"Error verificando supresión de alerta: {e}")
            return False
    
    async def _trigger_alert(self, alerta: AlertaMetrica, valor_actual: float):
        """
        Disparar una alerta
        """
        try:
            # Crear mensaje de alerta
            mensaje = self._create_alert_message(alerta, valor_actual)
            
            # Registrar en historial
            historial = await HistorialAlerta.create(
                alerta=alerta,
                valor_actual=valor_actual,
                mensaje=mensaje,
                enviada=False,
                canales_enviados=[]
            )
            
            # Enviar notificaciones
            canales_exitosos = []
            for canal in alerta.canales_notificacion:
                try:
                    if canal == "email":
                        await self.notification_service.send_email_alert(alerta, valor_actual, mensaje)
                        canales_exitosos.append("email")
                    elif canal == "slack":
                        await self.notification_service.send_slack_alert(alerta, valor_actual, mensaje)
                        canales_exitosos.append("slack")
                    else:
                        logger.warning(f"Canal de notificación no soportado: {canal}")
                        
                except Exception as e:
                    logger.error(f"Error enviando alerta por {canal}: {e}")
            
            # Actualizar historial
            historial.enviada = len(canales_exitosos) > 0
            historial.canales_enviados = canales_exitosos
            await historial.save()
            
            # Registrar evento del sistema
            await EventoSistema.create(
                tipo_evento="alerta.disparada",
                entidad_tipo="AlertaMetrica",
                entidad_id=alerta.id,
                datos={
                    "alerta_nombre": alerta.nombre,
                    "metrica_nombre": alerta.metrica_nombre,
                    "valor_actual": valor_actual,
                    "valor_umbral": alerta.valor_umbral,
                    "operador": alerta.operador,
                    "canales_enviados": canales_exitosos
                }
            )
            
            logger.info(f"Alerta disparada: {alerta.nombre} - Valor: {valor_actual}")
            
        except Exception as e:
            logger.error(f"Error disparando alerta {alerta.nombre}: {e}")
    
    def _create_alert_message(self, alerta: AlertaMetrica, valor_actual: float) -> str:
        """
        Crear mensaje de alerta
        """
        severity_emoji = {
            AlertSeverity.LOW: "🟡",
            AlertSeverity.MEDIUM: "🟠", 
            AlertSeverity.HIGH: "🔴",
            AlertSeverity.CRITICAL: "🚨"
        }
        
        # Determinar severidad basada en la métrica
        severity = self._determine_alert_severity(alerta.metrica_nombre, valor_actual, alerta.valor_umbral)
        emoji = severity_emoji.get(severity, "⚠️")
        
        mensaje = f"""
{emoji} **ALERTA TeLOO V3**: {alerta.nombre}

**Métrica**: {alerta.metrica_nombre}
**Valor Actual**: {valor_actual}
**Umbral**: {alerta.operador} {alerta.valor_umbral}
**Severidad**: {severity.value.upper()}
**Timestamp**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

**Descripción**: La métrica {alerta.metrica_nombre} ha superado el umbral configurado.
        """.strip()
        
        return mensaje
    
    def _determine_alert_severity(self, metric_name: str, valor_actual: float, valor_umbral: float) -> AlertSeverity:
        """
        Determinar la severidad de la alerta basada en qué tan lejos está del umbral
        """
        try:
            if metric_name == "tasa_error":
                if valor_actual > valor_umbral * 3:  # 3x el umbral
                    return AlertSeverity.CRITICAL
                elif valor_actual > valor_umbral * 2:  # 2x el umbral
                    return AlertSeverity.HIGH
                else:
                    return AlertSeverity.MEDIUM
                    
            elif metric_name == "latencia_promedio":
                if valor_actual > valor_umbral * 2:
                    return AlertSeverity.HIGH
                else:
                    return AlertSeverity.MEDIUM
                    
            elif metric_name == "disponibilidad_sistema":
                if valor_actual < 95.0:  # Menos del 95%
                    return AlertSeverity.CRITICAL
                elif valor_actual < 98.0:  # Menos del 98%
                    return AlertSeverity.HIGH
                else:
                    return AlertSeverity.MEDIUM
                    
            else:
                return AlertSeverity.MEDIUM
                
        except Exception:
            return AlertSeverity.MEDIUM
    
    async def create_custom_alert(self, 
                                nombre: str,
                                metrica_nombre: str,
                                operador: str,
                                valor_umbral: float,
                                canales: List[str]) -> AlertaMetrica:
        """
        Crear una alerta personalizada
        """
        try:
            alerta = await AlertaMetrica.create(
                nombre=nombre,
                metrica_nombre=metrica_nombre,
                operador=operador,
                valor_umbral=valor_umbral,
                canales_notificacion=canales,
                activa=True
            )
            
            logger.info(f"Alerta personalizada creada: {nombre}")
            return alerta
            
        except Exception as e:
            logger.error(f"Error creando alerta personalizada: {e}")
            raise
    
    async def update_alert_threshold(self, alert_id: int, nuevo_umbral: float):
        """
        Actualizar el umbral de una alerta existente
        """
        try:
            alerta = await AlertaMetrica.get(id=alert_id)
            alerta.valor_umbral = nuevo_umbral
            await alerta.save()
            
            logger.info(f"Umbral de alerta actualizado: {alerta.nombre} -> {nuevo_umbral}")
            
        except Exception as e:
            logger.error(f"Error actualizando umbral de alerta: {e}")
            raise
    
    async def get_alert_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Obtener historial de alertas de los últimos días
        """
        try:
            fecha_inicio = datetime.utcnow() - timedelta(days=days)
            
            historial = await HistorialAlerta.filter(
                disparada_en__gte=fecha_inicio
            ).prefetch_related("alerta").order_by("-disparada_en").all()
            
            return [
                {
                    "id": h.id,
                    "alerta_nombre": h.alerta.nombre,
                    "metrica_nombre": h.alerta.metrica_nombre,
                    "valor_actual": h.valor_actual,
                    "valor_umbral": h.alerta.valor_umbral,
                    "mensaje": h.mensaje,
                    "enviada": h.enviada,
                    "canales_enviados": h.canales_enviados,
                    "disparada_en": h.disparada_en
                }
                for h in historial
            ]
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de alertas: {e}")
            return []
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Obtener todas las alertas activas configuradas
        """
        try:
            alertas = await AlertaMetrica.filter(activa=True).all()
            
            return [
                {
                    "id": a.id,
                    "nombre": a.nombre,
                    "metrica_nombre": a.metrica_nombre,
                    "operador": a.operador,
                    "valor_umbral": a.valor_umbral,
                    "canales_notificacion": a.canales_notificacion,
                    "creado_en": a.creado_en,
                    "actualizado_en": a.actualizado_en
                }
                for a in alertas
            ]
            
        except Exception as e:
            logger.error(f"Error obteniendo alertas activas: {e}")
            return []

# Instancia global del gestor de alertas
alert_manager = AlertManager()