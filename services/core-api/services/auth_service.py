"""
Authentication Service for TeLOO V3
Handles JWT token generation, validation, and user authentication
"""

import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from models.user import Usuario
from models.enums import RolUsuario, EstadoUsuario
from utils.secrets import get_jwt_config

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    pwd_context.hash("test")
except Exception:
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# FORCE PBKDF2 removed - going back to default behavior

JWT_CONFIG = get_jwt_config()
SECRET_KEY = JWT_CONFIG.get("secret_key")
ALGORITHM = JWT_CONFIG.get("algorithm", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(JWT_CONFIG.get("access_token_expire_minutes", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(JWT_CONFIG.get("refresh_token_expire_days", 7))

def _jwt_algorithm() -> str:
    try:
        if ALGORITHM.startswith("RS"):
            if isinstance(SECRET_KEY, str) and "BEGIN" in SECRET_KEY:
                return ALGORITHM
            return "HS256"
        return ALGORITHM
    except Exception:
        return "HS256"


class AuthService:
    """Authentication service for handling JWT tokens and user authentication"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        # Ensure password is not too long for bcrypt (max 72 bytes)
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire_timestamp = time.time() + expires_delta.total_seconds()
        else:
            expire_timestamp = time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)

        to_encode.update({
            "exp": int(expire_timestamp),
            "type": "access",
            "jti": str(uuid.uuid4()),
        })
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=_jwt_algorithm())
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire_timestamp = time.time() + (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        to_encode.update({
            "exp": int(expire_timestamp),
            "type": "refresh",
            "jti": str(uuid.uuid4()),
        })
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=_jwt_algorithm())
        return encoded_jwt

    @staticmethod
    async def blacklist_token(token: str) -> None:
        """Add a token's JTI to the Redis blacklist with TTL = remaining lifetime."""
        try:
            from utils.redis_client import get_redis
            redis = await get_redis()
            if redis is None:
                return
            payload = jwt.decode(
                token, SECRET_KEY,
                algorithms=[_jwt_algorithm()],
                options={"verify_exp": False},
            )
            jti = payload.get("jti")
            exp = payload.get("exp")
            if not jti or not exp:
                return
            ttl = max(1, int(exp - time.time()))
            await redis.set(f"token:blacklist:{jti}", "1", ex=ttl)
        except Exception:
            pass  # Never block logout due to Redis errors

    @staticmethod
    async def is_blacklisted(jti: str) -> bool:
        """Check if a token JTI has been blacklisted."""
        try:
            from utils.redis_client import get_redis
            redis = await get_redis()
            if redis is None:
                return False
            return await redis.exists(f"token:blacklist:{jti}") == 1
        except Exception:
            return False  # Fail-open: never deny access due to Redis unavailability

    @staticmethod
    async def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token, checking blacklist."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[_jwt_algorithm()])

            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            jti = payload.get("jti")
            if jti and await AuthService.is_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )

            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[Usuario]:
        """Authenticate user with email and password"""
        try:
            user = await Usuario.get(email=email)
            if not user or not AuthService.verify_password(password, user.password_hash):
                return None
            
            # Check if user is active
            if user.estado != EstadoUsuario.ACTIVO:
                return None
                
            return user
        except:
            return None
    
    @staticmethod
    async def get_current_user(token: str) -> Usuario:
        """Get current user from JWT token"""
        payload = await AuthService.verify_token(token)
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        user = await Usuario.get_or_none(email=email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    
    @staticmethod
    def create_token_pair(user: Usuario) -> Dict[str, str]:
        """Create access and refresh token pair for user"""
        token_data = {
            "sub": user.email,
            "user_id": str(user.id),  # Convert UUID to string
            "role": user.rol.value,
            "name": f"{user.nombre} {user.apellido}"
        }
        
        access_token = AuthService.create_access_token(token_data)
        refresh_token = AuthService.create_refresh_token({"sub": user.email, "user_id": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
