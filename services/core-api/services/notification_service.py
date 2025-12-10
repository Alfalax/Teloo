"""
Notification Service - Manages push notifications with WhatsApp fallback
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
import httpx
import redis.asyncio as redis
from datetime import datetime
import json

from ..models.user import Usuario
from ..models.solicitud import Solicitud
from ..models.oferta import Oferta
from .events_service import events_service

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Manages internal push notifications with WhatsApp fallback
    
    - Sends notifications via WebSocket (Realtime Gateway)
    - Falls back to WhatsApp when WebSocket is not available
    - Queues notifications in Redis for reliability
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.realtime_gateway_url = "http://realtime-gateway:8003"
        self.agent_ia_url = "http://agent-ia:8002"
    
    async def initialize(self, redis_client: redis.Redis):
        """Initialize notification service with Redis client"""
        self.redis_client = redis_client
        logger.info("Notification service initialized")
    
    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal"
    ) -> bool:
        """
        Send notification to user
        
        Args:
            user_id: Target user ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification (solicitud, oferta, evaluacion, etc.)
            data: Additional data to include
            priority: Priority level (low, normal, high, urgent)
            
        Returns:
            True if notification was sent successfully
        """
        try:
            notification_data = {
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": notification_type,
                "data": data or {},
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Try to send via WebSocket first
            websocket_sent = await self._send_via_websocket(user_id, notification_data)
            
            if websocket_sent:
                logger.info(f"Notification sent via WebSocket to user {user_id}")
                
                # Publish event
                await events_service.publish_event(
                    "notificacion.sent",
                    {
                        "user_id": user_id,
                        "type": notification_type,
                        "channel": "websocket"
                    }
                )
                
                return True
            
            # Fallback to WhatsApp
            logger.info(f"WebSocket unavailable for user {user_id}, falling back to WhatsApp")
            whatsapp_sent = await self._send_via_whatsapp(user_id, notification_data)
            
            if whatsapp_sent:
                logger.info(f"Notification sent via WhatsApp to user {user_id}")
                
                # Publish event
                await events_service.publish_event(
                    "notificacion.sent",
                    {
                        "user_id": user_id,
                        "type": notification_type,
                        "channel": "whatsapp"
                    }
                )
                
                return True
            
            # If both failed, queue for retry
            await self._queue_notification(notification_data)
            logger.warning(f"Notification queued for retry: user {user_id}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    async def send_notification_to_role(
        self,
        role: str,
        title: str,
        message: str,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Send notification to all users with specific role
        
        Args:
            role: Target role (ADMIN, ADVISOR, etc.)
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            data: Additional data
            
        Returns:
            Number of users notified
        """
        try:
            notification_data = {
                "role": role,
                "title": title,
                "message": message,
                "type": notification_type,
                "data": data or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send via WebSocket to all connected users with role
            await self._broadcast_to_role(role, notification_data)
            
            # Publish event
            await events_service.publish_event(
                "notificacion.broadcast",
                {
                    "role": role,
                    "type": notification_type,
                    "channel": "websocket"
                }
            )
            
            logger.info(f"Notification broadcast to role {role}")
            return 1  # Return success indicator
            
        except Exception as e:
            logger.error(f"Error broadcasting notification to role {role}: {str(e)}")
            return 0
    
    async def notify_new_solicitud(self, solicitud: Solicitud, asesores_ids: List[str]):
        """
        Notify asesores about new solicitud
        
        Args:
            solicitud: Solicitud instance
            asesores_ids: List of asesor IDs to notify
        """
        for asesor_id in asesores_ids:
            await self.send_notification(
                user_id=asesor_id,
                title="Nueva Solicitud Disponible",
                message=f"Nueva solicitud de repuestos disponible en tu área",
                notification_type="solicitud_nueva",
                data={
                    "solicitud_id": str(solicitud.id),
                    "ciudad": solicitud.ciudad_origen,
                    "repuestos_count": await solicitud.repuestos.all().count()
                },
                priority="high"
            )
    
    async def notify_oferta_result(self, oferta: Oferta, result: str):
        """
        Notify asesor about oferta result
        
        Args:
            oferta: Oferta instance
            result: Result status (GANADORA, NO_SELECCIONADA, etc.)
        """
        messages = {
            "GANADORA": "¡Felicitaciones! Tu oferta fue seleccionada",
            "NO_SELECCIONADA": "Tu oferta no fue seleccionada en esta ocasión",
            "ACEPTADA": "¡Excelente! El cliente aceptó tu oferta",
            "RECHAZADA": "El cliente rechazó la oferta",
            "EXPIRADA": "La oferta ha expirado"
        }
        
        await self.send_notification(
            user_id=str(oferta.asesor_id),
            title=f"Resultado de Oferta",
            message=messages.get(result, "Estado de oferta actualizado"),
            notification_type="oferta_resultado",
            data={
                "oferta_id": str(oferta.id),
                "solicitud_id": str(oferta.solicitud_id),
                "estado": result
            },
            priority="high"
        )
    
    async def notify_evaluacion_completed(self, solicitud_id: UUID, asesores_ids: List[str]):
        """
        Notify asesores that evaluation is completed
        
        Args:
            solicitud_id: Solicitud ID
            asesores_ids: List of asesor IDs who participated
        """
        for asesor_id in asesores_ids:
            await self.send_notification(
                user_id=asesor_id,
                title="Evaluación Completada",
                message="La evaluación de ofertas ha sido completada",
                notification_type="evaluacion_completada",
                data={
                    "solicitud_id": str(solicitud_id)
                },
                priority="normal"
            )
    
    async def _send_via_websocket(self, user_id: str, notification_data: Dict) -> bool:
        """Send notification via WebSocket (Realtime Gateway)"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Check if user is connected
                response = await client.get(
                    f"{self.realtime_gateway_url}/stats"
                )
                
                if response.status_code != 200:
                    return False
                
                # Publish to Redis for Realtime Gateway to pick up
                if self.redis_client:
                    await self.redis_client.publish(
                        "notificacion.push",
                        json.dumps(notification_data)
                    )
                    return True
                
                return False
                
        except Exception as e:
            logger.debug(f"WebSocket send failed: {str(e)}")
            return False
    
    async def _send_via_whatsapp(self, user_id: str, notification_data: Dict) -> bool:
        """Send notification via WhatsApp (Agent IA)"""
        try:
            # Get user's phone number
            from ..models.user import Usuario
            user = await Usuario.get_or_none(id=user_id)
            
            if not user or not user.telefono:
                logger.warning(f"User {user_id} has no phone number for WhatsApp fallback")
                return False
            
            # Format message for WhatsApp
            whatsapp_message = f"*{notification_data['title']}*\n\n{notification_data['message']}"
            
            # Send via Agent IA service
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.agent_ia_url}/v1/messages/send",
                    json={
                        "to": user.telefono,
                        "message": whatsapp_message,
                        "type": "notification"
                    }
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"WhatsApp send failed: {str(e)}")
            return False
    
    async def _broadcast_to_role(self, role: str, notification_data: Dict) -> bool:
        """Broadcast notification to all users with specific role"""
        try:
            if self.redis_client:
                await self.redis_client.publish(
                    "notificacion.broadcast",
                    json.dumps(notification_data)
                )
                return True
            return False
            
        except Exception as e:
            logger.error(f"Broadcast failed: {str(e)}")
            return False
    
    async def _queue_notification(self, notification_data: Dict):
        """Queue notification for retry"""
        try:
            if self.redis_client:
                await self.redis_client.lpush(
                    "notifications:pending",
                    json.dumps(notification_data)
                )
                logger.info("Notification queued for retry")
                
        except Exception as e:
            logger.error(f"Failed to queue notification: {str(e)}")
    
    async def process_pending_notifications(self) -> int:
        """
        Process pending notifications from queue
        
        Returns:
            Number of notifications processed
        """
        if not self.redis_client:
            return 0
        
        processed = 0
        
        try:
            # Process up to 100 pending notifications
            for _ in range(100):
                notification_json = await self.redis_client.rpop("notifications:pending")
                
                if not notification_json:
                    break
                
                notification_data = json.loads(notification_json)
                user_id = notification_data.get("user_id")
                
                if user_id:
                    success = await self.send_notification(
                        user_id=user_id,
                        title=notification_data.get("title", ""),
                        message=notification_data.get("message", ""),
                        notification_type=notification_data.get("type", "general"),
                        data=notification_data.get("data"),
                        priority=notification_data.get("priority", "normal")
                    )
                    
                    if success:
                        processed += 1
                    else:
                        # Re-queue if still failing
                        await self._queue_notification(notification_data)
            
            if processed > 0:
                logger.info(f"Processed {processed} pending notifications")
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing pending notifications: {str(e)}")
            return processed


# Global notification service instance
notification_service = NotificationService()
