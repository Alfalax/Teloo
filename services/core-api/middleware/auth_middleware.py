"""
Authentication and Authorization Middleware for TeLOO V3
Provides decorators and dependencies for endpoint protection
"""

from functools import wraps
from typing import List, Optional, Callable, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.user import Usuario
from models.enums import RolUsuario
from services.auth_service import AuthService
from services.rbac_service import RBACService, Permission

security = HTTPBearer()


# Authentication Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Usuario:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    return await AuthService.get_current_user(token)


async def get_current_active_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Dependency to get current active user"""
    if not current_user.is_active():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# Role-based Dependencies
def require_role(allowed_roles: List[RolUsuario]):
    """Dependency factory for role-based access control"""
    def role_checker(current_user: Usuario = Depends(get_current_active_user)) -> Usuario:
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    return role_checker


def require_permission(required_permissions: List[Permission]):
    """Dependency factory for permission-based access control"""
    def permission_checker(current_user: Usuario = Depends(get_current_active_user)) -> Usuario:
        user_role = current_user.rol
        
        # Check if user has any of the required permissions
        if not RBACService.has_any_permission(user_role, required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permissions: {[perm.value for perm in required_permissions]}"
            )
        return current_user
    return permission_checker


def require_all_permissions(required_permissions: List[Permission]):
    """Dependency factory for requiring all specified permissions"""
    def permission_checker(current_user: Usuario = Depends(get_current_active_user)) -> Usuario:
        user_role = current_user.rol
        
        # Check if user has all required permissions
        if not RBACService.has_all_permissions(user_role, required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permissions: {[perm.value for perm in required_permissions]}"
            )
        return current_user
    return permission_checker


# Resource ownership Dependencies
def require_resource_access(permission: Permission):
    """
    Dependency factory for resource-based access control
    Checks both permission and resource ownership
    """
    def resource_checker(
        resource_owner_id: int,
        current_user: Usuario = Depends(get_current_active_user)
    ) -> Usuario:
        if not RBACService.can_access_resource(
            current_user.rol, 
            resource_owner_id, 
            current_user.id, 
            permission
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Insufficient permissions or not resource owner."
            )
        return current_user
    return resource_checker


# Convenience Dependencies for common role combinations
RequireAdmin = Depends(require_role([RolUsuario.ADMIN]))
RequireAdminOrAnalyst = Depends(require_role([RolUsuario.ADMIN, RolUsuario.ANALYST]))
RequireAdminOrSupport = Depends(require_role([RolUsuario.ADMIN, RolUsuario.SUPPORT]))
RequireStaff = Depends(require_role([RolUsuario.ADMIN, RolUsuario.ANALYST, RolUsuario.SUPPORT]))
RequireAdvisor = Depends(require_role([RolUsuario.ADVISOR]))
RequireClient = Depends(require_role([RolUsuario.CLIENT]))

# Permission-based Dependencies
RequireUserManagement = Depends(require_permission([Permission.CREATE_USER, Permission.UPDATE_USER, Permission.DELETE_USER]))
RequireSolicitudRead = Depends(require_permission([Permission.READ_SOLICITUD]))
RequireOfertaManagement = Depends(require_permission([Permission.CREATE_OFERTA, Permission.UPDATE_OFERTA]))
RequireAnalytics = Depends(require_permission([Permission.VIEW_ANALYTICS, Permission.VIEW_REPORTS]))
RequireSystemManagement = Depends(require_permission([Permission.MANAGE_SYSTEM]))


# Decorator for endpoint-level authorization
def authorize(roles: Optional[List[RolUsuario]] = None, permissions: Optional[List[Permission]] = None):
    """
    Decorator for endpoint authorization
    
    Args:
        roles: List of allowed roles
        permissions: List of required permissions (user needs at least one)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (injected by FastAPI dependency)
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, Usuario):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check roles if specified
            if roles and current_user.rol not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[role.value for role in roles]}"
                )
            
            # Check permissions if specified
            if permissions and not RBACService.has_any_permission(current_user.rol, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required permissions: {[perm.value for perm in permissions]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Utility functions for manual authorization checks
def check_user_permission(user: Usuario, permission: Permission) -> bool:
    """Check if user has a specific permission"""
    return RBACService.has_permission(user.rol, permission)


def check_resource_access(user: Usuario, resource_owner_id: int, permission: Permission) -> bool:
    """Check if user can access a specific resource"""
    return RBACService.can_access_resource(user.rol, resource_owner_id, user.id, permission)