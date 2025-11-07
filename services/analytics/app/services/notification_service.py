"""
Notification Service
Maneja el envío de notificaciones por email y Slack para alertas
"""
import logging
import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings
from app.models.metrics import AlertaMetrica

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Servicio para envío de notificaciones de alertas
    """
    
    def __init__(self):
        # Configuración de email
        self.smtp_server = settings.SMTP_SERVER if hasattr(settings, 'SMTP_SERVER') else "localhost"
        self.smtp_port = settings.SMTP_PORT if hasattr(settings, 'SMTP_PORT') else 587
        self.smtp_username = settings.SMTP_USERNAME if hasattr(settings, 'SMTP_USERNAME') else ""
        self.smtp_password = settings.SMTP_PASSWORD if hasattr(settings, 'SMTP_PASSWORD') else ""
        self.email_from = settings.EMAIL_FROM if hasattr(settings, 'EMAIL_FROM') else "alerts@teloo.com"
        self.email_to = settings.ALERT_EMAIL_TO if hasattr(settings, 'ALERT_EMAIL_TO') else ["admin@teloo.com"]
        
        # Configuración de Slack
        self.slack_webhook_url = settings.SLACK_WEBHOOK_URL if hasattr(settings, 'SLACK_WEBHOOK_URL') else None
        self.slack_channel = settings.SLACK_CHANNEL if hasattr(settings, 'SLACK_CHANNEL') else "#alerts"
        
        # Configuración de timeout
        self.notification_timeout = 30  # 30 segundos
    
    async def send_email_alert(self, alerta: AlertaMetrica, valor_actual: float, mensaje: str) -> bool:
        """
        Enviar alerta por email
        """
        try:
            if not self.smtp_server or not self.email_from:
                logger.warning("Configuración de email no disponible, saltando notificación por email")
                return False
            
            # Crear mensaje de email
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ", ".join(self.email_to) if isinstance(self.email_to, list) else self.email_to
            msg['Subject'] = f"🚨 TeLOO V3 Alert: {alerta.nombre}"
            
            # Crear cuerpo del email en HTML
            html_body = self._create_email_html_body(alerta, valor_actual, mensaje)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Enviar email de forma asíncrona
            await asyncio.get_event_loop().run_in_executor(
                None, 
                self._send_email_sync, 
                msg
            )
            
            logger.info(f"Email de alerta enviado para: {alerta.nombre}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de alerta: {e}")
            return False
    
    def _send_email_sync(self, msg: MIMEMultipart):
        """
        Enviar email de forma síncrona (para ejecutar en thread pool)
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_username and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                
                text = msg.as_string()
                server.sendmail(msg['From'], msg['To'].split(", "), text)
                
        except Exception as e:
            logger.error(f"Error en envío síncrono de email: {e}")
            raise
    
    def _create_email_html_body(self, alerta: AlertaMetrica, valor_actual: float, mensaje: str) -> str:
        """
        Crear cuerpo HTML para el email de alerta
        """
        # Determinar color basado en la severidad
        if "CRITICAL" in mensaje or "🚨" in mensaje:
            color = "#dc3545"  # Rojo
            bg_color = "#f8d7da"
        elif "HIGH" in mensaje or "🔴" in mensaje:
            color = "#fd7e14"  # Naranja
            bg_color = "#ffeaa7"
        else:
            color = "#ffc107"  # Amarillo
            bg_color = "#fff3cd"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>TeLOO V3 Alert</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; }}
                .alert-box {{ background-color: {bg_color}; border-left: 4px solid {color}; padding: 15px; margin: 20px 0; }}
                .metric-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .metric-table th, .metric-table td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                .metric-table th {{ background-color: #f8f9fa; font-weight: bold; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .btn {{ display: inline-block; padding: 10px 20px; background-color: {color}; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 TeLOO V3 Alert</h1>
                    <h2>{alerta.nombre}</h2>
                </div>
                
                <div class="content">
                    <div class="alert-box">
                        <h3>Alert Details</h3>
                        <table class="metric-table">
                            <tr>
                                <th>Metric</th>
                                <td>{alerta.metrica_nombre}</td>
                            </tr>
                            <tr>
                                <th>Current Value</th>
                                <td><strong>{valor_actual}</strong></td>
                            </tr>
                            <tr>
                                <th>Threshold</th>
                                <td>{alerta.operador} {alerta.valor_umbral}</td>
                            </tr>
                            <tr>
                                <th>Triggered At</th>
                                <td>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <h3>Description</h3>
                    <p>The metric <strong>{alerta.metrica_nombre}</strong> has exceeded the configured threshold and requires attention.</p>
                    
                    <h3>Recommended Actions</h3>
                    <ul>
                        {self._get_recommended_actions(alerta.metrica_nombre)}
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="#" class="btn">View Dashboard</a>
                        <a href="#" class="btn">View Logs</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated alert from TeLOO V3 Analytics Service</p>
                    <p>Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _get_recommended_actions(self, metric_name: str) -> str:
        """
        Obtener acciones recomendadas basadas en la métrica
        """
        actions = {
            "tasa_error": """
                <li>Check application logs for error patterns</li>
                <li>Verify database connectivity and performance</li>
                <li>Review recent deployments or configuration changes</li>
                <li>Monitor system resources (CPU, memory, disk)</li>
            """,
            "latencia_promedio": """
                <li>Check database query performance</li>
                <li>Review API endpoint response times</li>
                <li>Monitor network connectivity</li>
                <li>Verify cache hit rates</li>
            """,
            "tasa_conversion": """
                <li>Review recent changes to the escalation algorithm</li>
                <li>Check advisor response rates</li>
                <li>Analyze client feedback and PQRs</li>
                <li>Verify WhatsApp integration status</li>
            """,
            "disponibilidad_sistema": """
                <li>Check all service health endpoints</li>
                <li>Verify database and Redis connectivity</li>
                <li>Review infrastructure monitoring</li>
                <li>Check for ongoing maintenance or deployments</li>
            """,
            "solicitudes_sin_ofertas_pct": """
                <li>Review advisor availability and activity</li>
                <li>Check escalation algorithm performance</li>
                <li>Verify notification delivery (WhatsApp, Push)</li>
                <li>Analyze geographic coverage gaps</li>
            """
        }
        
        return actions.get(metric_name, "<li>Review system logs and metrics</li><li>Contact system administrator</li>")
    
    async def send_slack_alert(self, alerta: AlertaMetrica, valor_actual: float, mensaje: str) -> bool:
        """
        Enviar alerta por Slack
        """
        try:
            if not self.slack_webhook_url:
                logger.warning("Slack webhook URL no configurada, saltando notificación por Slack")
                return False
            
            # Crear payload para Slack
            slack_payload = self._create_slack_payload(alerta, valor_actual, mensaje)
            
            # Enviar a Slack con timeout
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.notification_timeout)) as session:
                async with session.post(self.slack_webhook_url, json=slack_payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert enviado para: {alerta.nombre}")
                        return True
                    else:
                        logger.error(f"Error enviando Slack alert: HTTP {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error("Timeout enviando alerta por Slack")
            return False
        except Exception as e:
            logger.error(f"Error enviando alerta por Slack: {e}")
            return False
    
    def _create_slack_payload(self, alerta: AlertaMetrica, valor_actual: float, mensaje: str) -> Dict[str, Any]:
        """
        Crear payload para Slack
        """
        # Determinar color y emoji basado en severidad
        if "CRITICAL" in mensaje or "🚨" in mensaje:
            color = "danger"
            emoji = "🚨"
        elif "HIGH" in mensaje or "🔴" in mensaje:
            color = "warning"
            emoji = "🔴"
        else:
            color = "good"
            emoji = "🟡"
        
        return {
            "channel": self.slack_channel,
            "username": "TeLOO V3 Alerts",
            "icon_emoji": ":warning:",
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} {alerta.nombre}",
                    "text": f"Alert triggered for metric: *{alerta.metrica_nombre}*",
                    "fields": [
                        {
                            "title": "Current Value",
                            "value": str(valor_actual),
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": f"{alerta.operador} {alerta.valor_umbral}",
                            "short": True
                        },
                        {
                            "title": "Triggered At",
                            "value": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": self._extract_severity_from_message(mensaje),
                            "short": True
                        }
                    ],
                    "footer": "TeLOO V3 Analytics",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }
    
    def _extract_severity_from_message(self, mensaje: str) -> str:
        """
        Extraer severidad del mensaje
        """
        if "CRITICAL" in mensaje:
            return "CRITICAL"
        elif "HIGH" in mensaje:
            return "HIGH"
        elif "MEDIUM" in mensaje:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def test_email_configuration(self) -> Dict[str, Any]:
        """
        Probar configuración de email
        """
        try:
            # Crear mensaje de prueba
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ", ".join(self.email_to) if isinstance(self.email_to, list) else self.email_to
            msg['Subject'] = "TeLOO V3 - Test Email Configuration"
            
            body = "This is a test email to verify the email configuration for TeLOO V3 alerts."
            msg.attach(MIMEText(body, 'plain'))
            
            # Intentar enviar
            await asyncio.get_event_loop().run_in_executor(
                None, 
                self._send_email_sync, 
                msg
            )
            
            return {
                "success": True,
                "message": "Test email sent successfully",
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port,
                "email_from": self.email_from,
                "email_to": self.email_to
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error sending test email: {str(e)}",
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port,
                "email_from": self.email_from,
                "email_to": self.email_to
            }
    
    async def test_slack_configuration(self) -> Dict[str, Any]:
        """
        Probar configuración de Slack
        """
        try:
            if not self.slack_webhook_url:
                return {
                    "success": False,
                    "message": "Slack webhook URL not configured",
                    "webhook_url": None,
                    "channel": self.slack_channel
                }
            
            # Crear payload de prueba
            test_payload = {
                "channel": self.slack_channel,
                "username": "TeLOO V3 Alerts",
                "icon_emoji": ":white_check_mark:",
                "text": "🧪 Test message from TeLOO V3 Analytics Service - Alert configuration is working correctly!"
            }
            
            # Enviar mensaje de prueba
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.notification_timeout)) as session:
                async with session.post(self.slack_webhook_url, json=test_payload) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "message": "Test Slack message sent successfully",
                            "webhook_url": self.slack_webhook_url[:50] + "..." if len(self.slack_webhook_url) > 50 else self.slack_webhook_url,
                            "channel": self.slack_channel
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"HTTP {response.status} error from Slack",
                            "webhook_url": self.slack_webhook_url[:50] + "..." if len(self.slack_webhook_url) > 50 else self.slack_webhook_url,
                            "channel": self.slack_channel
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error testing Slack configuration: {str(e)}",
                "webhook_url": self.slack_webhook_url[:50] + "..." if self.slack_webhook_url and len(self.slack_webhook_url) > 50 else self.slack_webhook_url,
                "channel": self.slack_channel
            }