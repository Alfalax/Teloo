"""
Role-Based Access Control (RBAC) Service for TeLOO V3
Defines permissions and role-based authorization logic
"""

from enum import Enum
from typing import List, Set, Dict
from models.enums import RolUsuario


class Permission(str, Enum):
    """System permissions"""
    # User management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Solicitud management
    CREATE_SOLICITUD = "create_solicitud"
    READ_SOLICITUD = "read_solicitud"
    UPDATE_SOLICITUD = "update_solicitud"
    DELETE_SOLICITUD = "delete_solicitud"
    ESCALATE_SOLICITUD = "escalate_solicitud"
    
    # Oferta management
    CREATE_OFERTA = "create_oferta"
    READ_OFERTA = "read_oferta"
    UPDATE_OFERTA = "update_oferta"
    DELETE_OFERTA = "delete_oferta"
    BULK_UPLOAD_OFERTAS = "bulk_upload_ofertas"
    
    # Evaluation and selection
    EVALUATE_OFERTAS = "evaluate_ofertas"
    SELECT_OFERTA = "select_oferta"
    
    # Analytics and reporting
    VIEW_ANALYTICS = "view_analytics"
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"
    
    # System administration
    MANAGE_SYSTEM = "manage_system"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_CONFIGURATIONS = "manage_configurations"
    
    # PQR management
    CREATE_PQR = "create_pqr"
    READ_PQR = "read_pqr"
    UPDATE_PQR = "update_pqr"
    RESOLVE_PQR = "resolve_pqr"
    
    # Financial operations
    VIEW_TRANSACTIONS = "view_transactions"
    PROCESS_PAYMENTS = "process_payments"


class RBACService:
    """Role-Based Access Control service"""
    
    # Define permissions for each role
    ROLE_PERMISSIONS: Dict[RolUsuario, Set[Permission]] = {
        RolUsuario.ADMIN: {
            # Full system access
            Permission.CREATE_USER,
            Permission.READ_USER,
            Permission.UPDATE_USER,
            Permission.DELETE_USER,
            Permission.CREATE_SOLICITUD,
            Permission.READ_SOLICITUD,
            Permission.UPDATE_SOLICITUD,
            Permission.DELETE_SOLICITUD,
            Permission.ESCALATE_SOLICITUD,
            Permission.CREATE_OFERTA,
            Permission.READ_OFERTA,
            Permission.UPDATE_OFERTA,
            Permission.DELETE_OFERTA,
            Permission.BULK_UPLOAD_OFERTAS,
            Permission.EVALUATE_OFERTAS,
            Permission.SELECT_OFERTA,
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_REPORTS,
            Permission.EXPORT_DATA,
            Permission.MANAGE_SYSTEM,
            Permission.VIEW_AUDIT_LOGS,
            Permission.MANAGE_CONFIGURATIONS,
            Permission.CREATE_PQR,
            Permission.READ_PQR,
            Permission.UPDATE_PQR,
            Permission.RESOLVE_PQR,
            Permission.VIEW_TRANSACTIONS,
            Permission.PROCESS_PAYMENTS,
        },
        
        RolUsuario.ADVISOR: {
            # Asesor permissions - can manage their own offers and view solicitudes
            Permission.READ_USER,  # Own profile only
            Permission.UPDATE_USER,  # Own profile only
            Permission.READ_SOLICITUD,
            Permission.CREATE_OFERTA,
            Permission.READ_OFERTA,
            Permission.UPDATE_OFERTA,  # Own offers only
            Permission.BULK_UPLOAD_OFERTAS,
            Permission.CREATE_PQR,
            Permission.READ_PQR,  # Own PQRs only
            Permission.VIEW_TRANSACTIONS,  # Own transactions only
        },
        
        RolUsuario.ANALYST: {
            # Analyst permissions - evaluation and analytics
            Permission.READ_USER,
            Permission.READ_SOLICITUD,
            Permission.UPDATE_SOLICITUD,
            Permission.ESCALATE_SOLICITUD,
            Permission.READ_OFERTA,
            Permission.EVALUATE_OFERTAS,
            Permission.SELECT_OFERTA,
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_REPORTS,
            Permission.EXPORT_DATA,
            Permission.READ_PQR,
            Permission.UPDATE_PQR,
            Permission.VIEW_TRANSACTIONS,
        },
        
        RolUsuario.SUPPORT: {
            # Support permissions - customer service and PQR management
            Permission.READ_USER,
            Permission.UPDATE_USER,  # Limited user updates
            Permission.READ_SOLICITUD,
            Permission.UPDATE_SOLICITUD,
            Permission.READ_OFERTA,
            Permission.CREATE_PQR,
            Permission.READ_PQR,
            Permission.UPDATE_PQR,
            Permission.RESOLVE_PQR,
            Permission.VIEW_REPORTS,  # Limited reports
        },
        
        RolUsuario.CLIENT: {
            # Client permissions - basic access to own data
            Permission.READ_USER,  # Own profile only
            Permission.UPDATE_USER,  # Own profile only
            Permission.CREATE_SOLICITUD,
            Permission.READ_SOLICITUD,  # Own solicitudes only
            Permission.READ_OFERTA,  # For own solicitudes only
            Permission.SELECT_OFERTA,  # For own solicitudes only
            Permission.CREATE_PQR,
            Permission.READ_PQR,  # Own PQRs only
        }
    }
    
    @classmethod
    def get_role_permissions(cls, role: RolUsuario) -> Set[Permission]:
        """Get all permissions for a role"""
        return cls.ROLE_PERMISSIONS.get(role, set())
    
    @classmethod
    def has_permission(cls, role: RolUsuario, permission: Permission) -> bool:
        """Check if a role has a specific permission"""
        role_permissions = cls.get_role_permissions(role)
        return permission in role_permissions
    
    @classmethod
    def has_any_permission(cls, role: RolUsuario, permissions: List[Permission]) -> bool:
        """Check if a role has any of the specified permissions"""
        role_permissions = cls.get_role_permissions(role)
        return any(permission in role_permissions for permission in permissions)
    
    @classmethod
    def has_all_permissions(cls, role: RolUsuario, permissions: List[Permission]) -> bool:
        """Check if a role has all of the specified permissions"""
        role_permissions = cls.get_role_permissions(role)
        return all(permission in role_permissions for permission in permissions)
    
    @classmethod
    def can_access_resource(cls, user_role: RolUsuario, resource_owner_id: int, 
                          current_user_id: int, permission: Permission) -> bool:
        """
        Check if user can access a resource based on ownership and permissions
        
        Args:
            user_role: Role of the current user
            resource_owner_id: ID of the resource owner
            current_user_id: ID of the current user
            permission: Required permission
        
        Returns:
            True if access is allowed, False otherwise
        """
        # Check if user has the permission
        if not cls.has_permission(user_role, permission):
            return False
        
        # Admin can access everything
        if user_role == RolUsuario.ADMIN:
            return True
        
        # Analyst can access most resources for evaluation
        if user_role == RolUsuario.ANALYST and permission in [
            Permission.READ_SOLICITUD, Permission.READ_OFERTA, 
            Permission.EVALUATE_OFERTAS, Permission.VIEW_ANALYTICS
        ]:
            return True
        
        # Support can access resources for customer service
        if user_role == RolUsuario.SUPPORT and permission in [
            Permission.READ_SOLICITUD, Permission.READ_OFERTA, 
            Permission.READ_PQR, Permission.UPDATE_PQR
        ]:
            return True
        
        # For other roles, check ownership
        return resource_owner_id == current_user_id