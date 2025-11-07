"""
Authentication router for TeLOO V3
Handles login, refresh token, and authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from models.auth import LoginRequest, TokenResponse, RefreshTokenRequest, UserInfo
from models.user import Usuario
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
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
    user.ultimo_login = datetime.utcnow()
    await user.save()
    
    # Create token pair
    tokens = AuthService.create_token_pair(user)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=900  # 15 minutes
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token (15min) and refresh token (7 days)
    """
    try:
        # Verify refresh token
        payload = AuthService.verify_token(refresh_data.refresh_token, token_type="refresh")
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
        
        # Create new token pair
        tokens = AuthService.create_token_pair(user)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=900  # 15 minutes
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
        id=user.id,
        email=user.email,
        nombre=user.nombre,
        apellido=user.apellido,
        rol=user.rol,
        estado=user.estado.value,
        ultimo_login=user.ultimo_login.isoformat() if user.ultimo_login else None
    )


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user (client-side token invalidation)
    
    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the tokens from storage
    """
    # In a production system, you might want to maintain a blacklist
    # of invalidated tokens in Redis or database
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