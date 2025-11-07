"""
Authentication Service for TeLOO V3
Handles JWT token generation, validation, and user authentication
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from models.user import Usuario
from models.enums import RolUsuario, EstadoUsuario

# Password hashing context - robust configuration for Docker
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    # Test bcrypt functionality
    pwd_context.hash("test")
except Exception:
    # Fallback to pbkdf2_sha256 if bcrypt fails
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# RSA Keys for JWT (in production, load from secure storage)
PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA4f5wg5l2hKsTeNem/V41fGnJm6gOdrj8ym3rFkEjWT2btphM
OSeWGu1TgkQqKDOlLWAKTgNIjdQoaq1biht8DdDVplpghBz7VYE0jOH8KQanfnalZ
xodd/YCHzCCNvbtMoXDWMhz9XjSfRZGQHStTQnld0oxxCD/qtqjlMBVn1lmWHDV
QiI5sHMTg7CwK1VEFgAcQqhMFgOH8SrqiL8FA4NNASIQ5Y/v5vr4WnOyBXJvQtxy
K1puHpaMUtUGV83leXpjzg5KMzAoGOOmFXxvck6ZfXzEsp4fcrRAqbEhb3vqzd4
Ed8XM2w2U8qJMsYz6UZRjcQRWH8WpEkVhvQDaQIDAQABAoIBAEYhObhC/FinioC
xoUxK+IuAnPZBzXxFg0PqMTvqkxMQmBxK3HADTss9n0gBz7aST4q9k5RurSk7b
45OpOKapEiF4EznzuAMKg5/M1Mg5v+6OyDXkEGv/7OjaNyvFI5PQFKz+5lTJl
tK02aoGSpjIwhhiY5/VBeg9/dVCxtMw/h5MZ8sJMrUu088hkuNuKlAqeehifeYW
FBjxAzuOLSrbsD5CWXJBtcn5RlKXlfuukmNfwS6xJRBW+9+a3UBdAqc1RuM9P
ZB2lSM2+Hq1fqjgybcaQdQ/EXyy0uLBjFLgAOyZdpjmmlOfmpu9iksimdnAI
YBBfXf6wp0CgYkAhR2As9RmnO13jkaAhR2As9RmnO13jkaAhR2As9RmnO13jka
-----END RSA PRIVATE KEY-----"""

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4f5wg5l2hKsTeNem/V41
fGnJm6gOdrj8ym3rFkEjWT2btphMOSeWGu1TgkQqKDOlLWAKTgNIjdQoaq1biht8
DdDVplpghBz7VYE0jOH8KQanfnalZxodd/YCHzCCNvbtMoXDWMhz9XjSfRZGQHSt
TQnld0oxxCD/qtqjlMBVn1lmWHDVQiI5sHMTg7CwK1VEFgAcQqhMFgOH8SrqiL8F
A4NNASIQ5Y/v5vr4WnOyBXJvQtxyK1puHpaMUtUGV83leXpjzg5KMzAoGOOmFXxv
ck6ZfXzEsp4fcrRAqbEhb3vqzd4Ed8XM2w2U8qJMsYz6UZRjcQRWH8WpEkVhvQDa
QIDAQAB
-----END PUBLIC KEY-----"""


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
        
        to_encode.update({"exp": int(expire_timestamp), "type": "access"})
        
        # For now, use HS256 since we need to set up proper RSA keys
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire_timestamp = time.time() + (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        to_encode.update({"exp": int(expire_timestamp), "type": "refresh"})
        
        # For now, use HS256 since we need to set up proper RSA keys
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            # PyJWT automatically validates expiration when using consistent time sources
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
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
        payload = AuthService.verify_token(token)
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