"""
Authentication router for TeLOO V3
Handles login, refresh token, and authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from models.auth import LoginRequest, TokenResponse, RefreshTokenRequest, UserInfo
from models.user import Usuario
from services.auth_service import AuthService
from middleware.rate_limiter import check_login_rate_limit

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# Explicit OPTIONS handler for CORS preflight
@router.options("/login")
@router.options("/refresh")
@router.options("/me")
@router.options("/logout")
async def options_handler():
    """Handle CORS preflight requests"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Requested-With, Accept, Origin",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",
        }
    )



class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, login_data: LoginRequest, _=Depends(check_login_rate_limit)):
    """
    Authenticate user and return JWT tokens
    
    - **email**: User email address
    - **password**: User password
    
    Returns access token (15min) and refresh token (7 days)
    """
    # Authenticate user
    user = await AuthService.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    from utils.datetime_utils import now_utc
    user.ultimo_login = now_utc()
    await user.save()
    
    # Create token pair
    tokens = AuthService.create_token_pair(user)
    
    # Create user info
    user_info = UserInfo(
        id=str(user.id),
        email=user.email,
        nombre=user.nombre,
        apellido=user.apellido,
        rol=user.rol,
        estado=user.estado.value,
        ultimo_login=user.ultimo_login.isoformat() if user.ultimo_login else None
    )
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=900,  # 15 minutes
        user=user_info
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token (15min) and refresh token (7 days)
    """
    try:
        # Verify refresh token (also checks blacklist)
        payload = await AuthService.verify_token(refresh_data.refresh_token, token_type="refresh")
        email = payload.get("sub")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Get user
        user = await Usuario.get_or_none(email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Blacklist old refresh token before issuing new pair (rotation)
        await AuthService.blacklist_token(refresh_data.refresh_token)

        # Issue new token pair
        tokens = AuthService.create_token_pair(user)

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=900
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current authenticated user information
    
    Requires valid access token in Authorization header
    """
    token = credentials.credentials
    user = await AuthService.get_current_user(token)
    
    return UserInfo(
        id=str(user.id),
        email=user.email,
        nombre=user.nombre,
        apellido=user.apellido,
        rol=user.rol,
        estado=user.estado.value,
        ultimo_login=user.ultimo_login.isoformat() if user.ultimo_login else None
    )


@router.post("/logout")
async def logout(
    logout_data: LogoutRequest = LogoutRequest(),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Logout user — blacklists access token and optionally the refresh token in Redis.
    Tokens remain cryptographically valid until expiry but are rejected on every request.
    """
    await AuthService.blacklist_token(credentials.credentials)
    if logout_data.refresh_token:
        await AuthService.blacklist_token(logout_data.refresh_token)
    return {"message": "Successfully logged out"}


# Dependency for getting current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Usuario:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    return await AuthService.get_current_user(token)


# Dependency for getting current active user
async def get_current_active_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Dependency to get current active user"""
    if not current_user.is_active():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user