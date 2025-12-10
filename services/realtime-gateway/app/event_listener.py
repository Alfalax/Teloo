"""
Redis Event Listener - Listens to events from Core API and broadcasts via WebSocket
"""

import asyncio
import json
import logging
from typing import Dict, Any
from .redis_client import redis_client
from .socket_manager import socket_manager

logger = logging.getLogger(__name__)


class EventListener:
    """Listens to Redis pub/sub events and broadcasts to WebSocket clients"""
    
    def __init__(self):
        self.running = False
        self.task: asyncio.Task = None
    
    async def start(self):
        """Start listening to Redis events"""
        if self.running:
            logger.warning("Event listener already running")
            return
        
        self.running = True
        
        # Subscribe to relevant channels
        await redis_client.subscribe(
            'solicitud.*',
            'oferta.*',
            'evaluacion.*',
            'cliente.*',
            'notificacion.*'
        )
        
        # Start listening task
        self.task = asyncio.create_task(self._listen())
        logger.info("Event listener started")
    
    async def stop(self):
        """Stop listening to Redis events"""
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event listener stopped")
    
    async def _listen(self):
        """Main listening loop"""
        while self.running:
            try:
                message = await redis_client.get_message(timeout=1.0)
                
                if message and message['type'] == 'message':
                    await self._handle_message(message)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event listener: {str(e)}")
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming Redis message"""
        try:
            channel = message['channel']
            data = json.loads(message['data']) if isinstance(message['data'], str) else message['data']
            
            logger.debug(f"Received event on channel {channel}: {data}")
            
            # Route message based on channel
            if channel.startswith('solicitud.'):
                await self._handle_solicitud_event(channel, data)
            elif channel.startswith('oferta.'):
                await self._handle_oferta_event(channel, data)
            elif channel.startswith('evaluacion.'):
                await self._handle_evaluacion_event(channel, data)
            elif channel.startswith('cliente.'):
                await self._handle_cliente_event(channel, data)
            elif channel.startswith('notificacion.'):
                await self._handle_notificacion_event(channel, data)
            else:
                logger.warning(f"Unknown channel: {channel}")
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    async def _handle_solicitud_event(self, channel: str, data: Dict):
        """Handle solicitud events"""
        event_type = channel.split('.')[1] if '.' in channel else 'update'
        solicitud_id = data.get('solicitud_id')
        
        # Broadcast to admins
        await socket_manager.broadcast_to_role('ADMIN', f'solicitud_{event_type}', data)
        
        # Broadcast to specific solicitud subscribers
        if solicitud_id:
            await socket_manager.broadcast_to_solicitud(solicitud_id, f'solicitud_{event_type}', data)
        
        # If it's a new solicitud or oleada, notify advisors
        if event_type in ['created', 'oleada']:
            await socket_manager.broadcast_to_role('ADVISOR', f'solicitud_{event_type}', data)
    
    async def _handle_oferta_event(self, channel: str, data: Dict):
        """Handle oferta events"""
        event_type = channel.split('.')[1] if '.' in channel else 'update'
        solicitud_id = data.get('solicitud_id')
        asesor_id = data.get('asesor_id')
        
        # Broadcast to admins
        await socket_manager.broadcast_to_role('ADMIN', f'oferta_{event_type}', data)
        
        # Broadcast to specific solicitud subscribers
        if solicitud_id:
            await socket_manager.broadcast_to_solicitud(solicitud_id, f'oferta_{event_type}', data)
        
        # Notify the advisor who created the oferta
        if asesor_id:
            await socket_manager.broadcast_to_user(asesor_id, f'oferta_{event_type}', data)
    
    async def _handle_evaluacion_event(self, channel: str, data: Dict):
        """Handle evaluacion events"""
        event_type = channel.split('.')[1] if '.' in channel else 'update'
        solicitud_id = data.get('solicitud_id')
        
        # Broadcast to admins
        await socket_manager.broadcast_to_role('ADMIN', f'evaluacion_{event_type}', data)
        
        # Broadcast to specific solicitud subscribers
        if solicitud_id:
            await socket_manager.broadcast_to_solicitud(solicitud_id, f'evaluacion_{event_type}', data)
        
        # Notify all advisors who participated
        asesores_ids = data.get('asesores_participantes', [])
        for asesor_id in asesores_ids:
            await socket_manager.broadcast_to_user(asesor_id, f'evaluacion_{event_type}', data)
    
    async def _handle_cliente_event(self, channel: str, data: Dict):
        """Handle cliente events"""
        event_type = channel.split('.')[1] if '.' in channel else 'update'
        cliente_id = data.get('cliente_id')
        
        # Broadcast to admins
        await socket_manager.broadcast_to_role('ADMIN', f'cliente_{event_type}', data)
        
        # Notify the specific client
        if cliente_id:
            await socket_manager.broadcast_to_user(cliente_id, f'cliente_{event_type}', data)
    
    async def _handle_notificacion_event(self, channel: str, data: Dict):
        """Handle notificacion events"""
        event_type = channel.split('.')[1] if '.' in channel else 'update'
        user_id = data.get('user_id')
        role = data.get('role')
        
        # If targeted to specific user
        if user_id:
            await socket_manager.broadcast_to_user(user_id, f'notificacion_{event_type}', data)
        # If targeted to role
        elif role:
            await socket_manager.broadcast_to_role(role, f'notificacion_{event_type}', data)
        # Broadcast to all
        else:
            await socket_manager.broadcast_to_role('ADMIN', f'notificacion_{event_type}', data)
            await socket_manager.broadcast_to_role('ADVISOR', f'notificacion_{event_type}', data)


# Global event listener instance
event_listener = EventListener()
