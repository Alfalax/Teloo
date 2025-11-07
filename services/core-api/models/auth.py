"""
Authentication models for TeLOO V3
Pydantic models for authentication requests and responses
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from models.enums import RolUsuario


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str


class UserInfo(BaseModel):
    """User information model for token payload"""
    id: int
    email: str
    nombre: str
    apellido: str
    rol: RolUsuario
    estado: str
    ultimo_login: Optional[str] = None
    
    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    """JWT token payload model"""
    sub: str  # subject (email)
    user_id: int
    role: str
    name: str
    exp: int
    type: str  # access or refresh