"""
Socket.IO Manager with Redis adapter for scalability
"""

import socketio
import logging
from typing import Dict, Set, Optional
from .config import settings
from .auth import verify_token, extract_token_from_auth, get_user_room, AuthenticationError
from .redis_client import redis_client
import json

logger = logging.getLogger(__name__)


class SocketManager:
    """Manages Socket.IO connections and rooms"""
    
    def __init__(self):
        # Create Socket.IO server with Redis adapter for scalability
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins=settings.cors_origins_list,
            ping_interval=settings.ws_ping_interval,
            ping_timeout=settings.ws_ping_timeout,
            max_http_buffer_size=1000000,
            logger=True,
            engineio_logger=True
        )
        
        # Track connected users
        self.connected_users: Dict[str, Dict] = {}  # sid -> user_data
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of sids
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register Socket.IO event handlers"""
        
        @self.sio.event
        async def connect(sid, environ, auth):
            """Handle client connection"""
            try:
                # Extract token from auth or query params
                token = None
                if auth and isinstance(auth, dict):
                    token = auth.get('token')
                
                if not token:
                    # Try to get from query params
                    query_string = environ.get('QUERY_STRING', '')
                    for param in query_string.split('&'):
                        if param.startswith('token='):
                            token = param.split('=', 1)[1]
                            break
                
                if not token:
                    logger.warning(f"Connection rejected for {sid}: No token provided")
                    return False
                
                # Verify token
                user_data = verify_token(token)
                
                # Store user data
                self.connected_users[sid] = user_data
                user_id = user_data['user_id']
                
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = set()
                self.user_sessions[user_id].add(sid)
                
                # Join role-based room
                room = get_user_room(user_data['role'])
                await self.sio.enter_room(sid, room)
                
                # Join personal room
                await self.sio.enter_room(sid, f"user_{user_id}")
                
                logger.info(f"Client {sid} connected as {user_data['email']} (role: {user_data['role']}, room: {room})")
                
                # Send welcome message
                await self.sio.emit('connected', {
                    'message': 'Connected to TeLOO Realtime Gateway',
                    'user_id': user_id,
                    'role': user_data['role'],
                    'room': room
                }, room=sid)
                
                # Notify room about new connection
                await self.sio.emit('user_joined', {
                    'user_id': user_id,
                    'role': user_data['role']
                }, room=room, skip_sid=sid)
                
                return True
                
            except AuthenticationError as e:
                logger.warning(f"Authentication failed for {sid}: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"Error during connection for {sid}: {str(e)}")
                return False
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            try:
                user_data = self.connected_users.get(sid)
                if user_data:
                    user_id = user_data['user_id']
                    role = user_data['role']
                    room = get_user_room(role)
                    
                    # Remove from tracking
                    if user_id in self.user_sessions:
                        self.user_sessions[user_id].discard(sid)
                        if not self.user_sessions[user_id]:
                            del self.user_sessions[user_id]
                    
                    del self.connected_users[sid]
                    
                    # Notify room about disconnection
                    await self.sio.emit('user_left', {
                        'user_id': user_id,
                        'role': role
                    }, room=room)
                    
                    logger.info(f"Client {sid} disconnected (user: {user_id})")
                else:
                    logger.info(f"Client {sid} disconnected (unknown user)")
                    
            except Exception as e:
                logger.error(f"Error during disconnection for {sid}: {str(e)}")
        
        @self.sio.event
        async def ping(sid):
            """Handle ping from client"""
            await self.sio.emit('pong', {'timestamp': str(datetime.now())}, room=sid)
        
        @self.sio.event
        async def subscribe_solicitud(sid, data):
            """Subscribe to solicitud-specific updates"""
            try:
                solicitud_id = data.get('solicitud_id')
                if not solicitud_id:
                    await self.sio.emit('error', {'message': 'solicitud_id required'}, room=sid)
                    return
                
                room_name = f"solicitud_{solicitud_id}"
                await self.sio.enter_room(sid, room_name)
                
                logger.info(f"Client {sid} subscribed to {room_name}")
                await self.sio.emit('subscribed', {'room': room_name}, room=sid)
                
            except Exception as e:
                logger.error(f"Error subscribing to solicitud: {str(e)}")
                await self.sio.emit('error', {'message': str(e)}, room=sid)
        
        @self.sio.event
        async def unsubscribe_solicitud(sid, data):
            """Unsubscribe from solicitud-specific updates"""
            try:
                solicitud_id = data.get('solicitud_id')
                if not solicitud_id:
                    await self.sio.emit('error', {'message': 'solicitud_id required'}, room=sid)
                    return
                
                room_name = f"solicitud_{solicitud_id}"
                await self.sio.leave_room(sid, room_name)
                
                logger.info(f"Client {sid} unsubscribed from {room_name}")
                await self.sio.emit('unsubscribed', {'room': room_name}, room=sid)
                
            except Exception as e:
                logger.error(f"Error unsubscribing from solicitud: {str(e)}")
                await self.sio.emit('error', {'message': str(e)}, room=sid)
    
    async def broadcast_to_role(self, role: str, event: str, data: dict):
        """Broadcast message to all users with specific role"""
        room = get_user_room(role)
        await self.sio.emit(event, data, room=room)
        logger.debug(f"Broadcasted {event} to room {room}")
    
    async def broadcast_to_user(self, user_id: str, event: str, data: dict):
        """Broadcast message to specific user (all their sessions)"""
        room = f"user_{user_id}"
        await self.sio.emit(event, data, room=room)
        logger.debug(f"Broadcasted {event} to user {user_id}")
    
    async def broadcast_to_solicitud(self, solicitud_id: str, event: str, data: dict):
        """Broadcast message to all users subscribed to a solicitud"""
        room = f"solicitud_{solicitud_id}"
        await self.sio.emit(event, data, room=room)
        logger.debug(f"Broadcasted {event} to solicitud {solicitud_id}")
    
    async def get_connected_users_count(self) -> int:
        """Get count of connected users"""
        return len(self.connected_users)
    
    async def get_connected_users_by_role(self, role: str) -> int:
        """Get count of connected users by role"""
        return sum(1 for user in self.connected_users.values() if user['role'] == role)
    
    async def is_user_connected(self, user_id: str) -> bool:
        """Check if user is connected"""
        return user_id in self.user_sessions and len(self.user_sessions[user_id]) > 0


# Global socket manager instance
socket_manager = SocketManager()


# Import datetime for ping handler
from datetime import datetime
