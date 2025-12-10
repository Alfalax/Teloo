"""
JWT Authentication for WebSocket connections
"""

import jwt
from typing import Optional, Dict
from datetime import datetime
from .config import settings
import logging

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


def load_public_key() -> str:
    """Load JWT public key from file"""
    try:
        with open(settings.jwt_public_key_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Public key file not found at {settings.jwt_public_key_path}, using secret key")
        return settings.jwt_secret_key


def verify_token(token: str) -> Dict:
    """
    Verify JWT token and extract payload
    
    Args:
        token: JWT token string
        
    Returns:
        Dict with user information
        
    Raises:
        AuthenticationError: If token is invalid
    """
    try:
        # Try to load public key for RS256, fallback to secret key for HS256
        if settings.jwt_algorithm == "RS256":
            try:
                key = load_public_key()
            except Exception:
                key = settings.jwt_secret_key
        else:
            key = settings.jwt_secret_key
        
        # Decode and verify token
        payload = jwt.decode(
            token,
            key,
            algorithms=[settings.jwt_algorithm, "HS256"],  # Support both algorithms
            options={"verify_exp": True}
        )
        
        # Validate required fields
        if 'sub' not in payload:
            raise AuthenticationError("Token missing 'sub' claim")
        
        # Extract user information
        user_data = {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'role': payload.get('role', 'CLIENT'),
            'nombre': payload.get('nombre'),
            'exp': payload.get('exp')
        }
        
        logger.info(f"Token verified for user {user_data['user_id']} with role {user_data['role']}")
        return user_data
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        raise AuthenticationError(f"Authentication failed: {str(e)}")


def extract_token_from_auth(auth_header: Optional[str]) -> Optional[str]:
    """
    Extract token from Authorization header
    
    Args:
        auth_header: Authorization header value (e.g., "Bearer <token>")
        
    Returns:
        Token string or None
    """
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def get_user_room(role: str) -> str:
    """
    Get room name for user based on role
    
    Args:
        role: User role (ADMIN, ADVISOR, ANALYST, SUPPORT, CLIENT)
        
    Returns:
        Room name string
    """
    role_rooms = {
        'ADMIN': 'admin',
        'ADVISOR': 'advisor',
        'ANALYST': 'admin',  # Analysts join admin room
        'SUPPORT': 'admin',  # Support joins admin room
        'CLIENT': 'client'
    }
    
    return role_rooms.get(role.upper(), 'client')
