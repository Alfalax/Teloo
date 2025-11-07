"""
Authentication Tests for TeLOO V3
Tests for token generation, validation, and role-based permissions
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
import jwt
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch, MagicMock

# Import models and services
from models.user import Usuario, Cliente, Asesor
from models.enums import RolUsuario, EstadoUsuario, EstadoAsesor
from services.auth_service import AuthService, SECRET_KEY
from jwt.exceptions import ExpiredSignatureError
from services.rbac_service import RBACService, Permission
from middleware.auth_middleware import (
    get_current_user, get_current_active_user,
    require_role, require_permission, require_all_permissions
)


class TestAuthService:
    """Test AuthService functionality"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        
        # Test password hashing
        hashed = AuthService.get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        
        # Test password verification
        assert AuthService.verify_password(password, hashed) is True
        assert AuthService.verify_password("wrong_password", hashed) is False
    
    def test_create_access_token(self):
        """Test JWT access token creation"""
        test_data = {
            "sub": "test@teloo.com",
            "user_id": 1,
            "role": "ADMIN",
            "name": "Test User"
        }
        
        # Create token
        token = AuthService.create_access_token(test_data)
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are long
        
        # Decode and verify token content
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == "test@teloo.com"
        assert payload["user_id"] == 1
        assert payload["role"] == "ADMIN"
        assert payload["name"] == "Test User"
        assert payload["type"] == "access"
        assert "exp" in payload
    
    def test_create_refresh_token(self):
        """Test JWT refresh token creation"""
        test_data = {
            "sub": "test@teloo.com",
            "user_id": 1
        }
        
        # Create refresh token
        token = AuthService.create_refresh_token(test_data)
        assert isinstance(token, str)
        
        # Decode and verify token content
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == "test@teloo.com"
        assert payload["user_id"] == 1
        assert payload["type"] == "refresh"
        assert "exp" in payload
    
    def test_create_token_with_custom_expiry(self):
        """Test token creation with custom expiry"""
        test_data = {"sub": "test@teloo.com"}
        custom_expiry = timedelta(minutes=30)
        
        token = AuthService.create_access_token(test_data, expires_delta=custom_expiry)
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # Check that expiry is approximately 30 minutes from now
        import time
        current_time = time.time()
        expected_exp = current_time + custom_expiry.total_seconds()
        time_diff = abs(payload["exp"] - expected_exp)
        assert time_diff < 5  # Allow 5 seconds tolerance
    
    def test_verify_token_success(self):
        """Test successful token verification"""
        test_data = {
            "sub": "test@teloo.com",
            "user_id": 1,
            "role": "ADMIN"
        }
        
        # Create and verify access token with longer expiry for testing
        access_token = AuthService.create_access_token(test_data, expires_delta=timedelta(hours=1))
        payload = AuthService.verify_token(access_token, "access")
        
        assert payload["sub"] == "test@teloo.com"
        assert payload["user_id"] == 1
        assert payload["role"] == "ADMIN"
        assert payload["type"] == "access"
        
        # Create and verify refresh token
        refresh_token = AuthService.create_refresh_token(test_data)
        payload = AuthService.verify_token(refresh_token, "refresh")
        
        assert payload["sub"] == "test@teloo.com"
        assert payload["user_id"] == 1
        assert payload["type"] == "refresh"
    
    def test_verify_token_invalid_type(self):
        """Test token verification with wrong token type"""
        test_data = {"sub": "test@teloo.com"}
        
        # Create access token but verify as refresh
        access_token = AuthService.create_access_token(test_data)
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.verify_token(access_token, "refresh")
        
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in str(exc_info.value.detail)
    
    def test_verify_token_invalid_signature(self):
        """Test token verification with invalid signature"""
        # Create token with wrong secret
        fake_token = jwt.encode(
            {"sub": "test@teloo.com", "type": "access"}, 
            "wrong_secret", 
            algorithm="HS256"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.verify_token(fake_token, "access")
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    def test_verify_token_expired(self):
        """Test token verification with expired token"""
        # Create token that expires immediately using time.time() for consistency
        import time
        past_timestamp = time.time() - 60  # 1 minute ago
        test_data = {
            "sub": "test@teloo.com",
            "exp": int(past_timestamp),
            "type": "access"
        }
        
        expired_token = jwt.encode(test_data, SECRET_KEY, algorithm="HS256")
        
        # Should raise HTTPException for expired token
        with pytest.raises(HTTPException) as exc_info:
            AuthService.verify_token(expired_token, "access")
        
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful user authentication"""
        # Mock user with correct password
        mock_user = MagicMock()
        mock_user.email = "test@teloo.com"
        mock_user.password_hash = AuthService.get_password_hash("correct_password")
        mock_user.estado = EstadoUsuario.ACTIVO
        
        with patch('services.auth_service.Usuario.get', new_callable=AsyncMock, return_value=mock_user):
            result = await AuthService.authenticate_user("test@teloo.com", "correct_password")
            assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password"""
        # Mock user with different password
        mock_user = MagicMock()
        mock_user.email = "test@teloo.com"
        mock_user.password_hash = AuthService.get_password_hash("correct_password")
        mock_user.estado = EstadoUsuario.ACTIVO
        
        with patch('services.auth_service.Usuario.get', new_callable=AsyncMock, return_value=mock_user):
            result = await AuthService.authenticate_user("test@teloo.com", "wrong_password")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self):
        """Test authentication with inactive user"""
        # Mock inactive user
        mock_user = MagicMock()
        mock_user.email = "test@teloo.com"
        mock_user.password_hash = AuthService.get_password_hash("correct_password")
        mock_user.estado = EstadoUsuario.INACTIVO
        
        with patch('services.auth_service.Usuario.get', new_callable=AsyncMock, return_value=mock_user):
            result = await AuthService.authenticate_user("test@teloo.com", "correct_password")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user"""
        with patch('services.auth_service.Usuario.get', new_callable=AsyncMock, side_effect=Exception("User not found")):
            result = await AuthService.authenticate_user("nonexistent@teloo.com", "password")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test getting current user from valid token"""
        # Mock user
        mock_user = MagicMock()
        mock_user.email = "test@teloo.com"
        mock_user.id = 1
        
        # Create valid token with longer expiry for testing
        token_data = {"sub": "test@teloo.com", "user_id": 1}
        token = AuthService.create_access_token(token_data, expires_delta=timedelta(hours=1))
        
        with patch('services.auth_service.Usuario.get_or_none', new_callable=AsyncMock, return_value=mock_user):
            result = await AuthService.get_current_user(token)
            assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.get_current_user("invalid_token")
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self):
        """Test getting current user when user doesn't exist"""
        # Create valid token for non-existent user with longer expiry for testing
        token_data = {"sub": "nonexistent@teloo.com", "user_id": 999}
        token = AuthService.create_access_token(token_data, expires_delta=timedelta(hours=1))
        
        with patch('services.auth_service.Usuario.get_or_none', new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.get_current_user(token)
            
            assert exc_info.value.status_code == 401
            assert "User not found" in str(exc_info.value.detail)
    
    def test_create_token_pair(self):
        """Test creating access and refresh token pair"""
        # Mock user
        mock_user = MagicMock()
        mock_user.email = "test@teloo.com"
        mock_user.id = 1
        mock_user.rol = RolUsuario.ADMIN
        mock_user.nombre_completo = "Test User"
        
        tokens = AuthService.create_token_pair(mock_user)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        
        # Verify access token content
        access_payload = jwt.decode(
            tokens["access_token"], 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        assert access_payload["sub"] == "test@teloo.com"
        assert access_payload["user_id"] == 1
        assert access_payload["role"] == "ADMIN"
        assert access_payload["type"] == "access"
        
        # Verify refresh token content
        refresh_payload = jwt.decode(
            tokens["refresh_token"], 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        assert refresh_payload["sub"] == "test@teloo.com"
        assert refresh_payload["user_id"] == 1
        assert refresh_payload["type"] == "refresh"


class TestRBACService:
    """Test Role-Based Access Control functionality"""
    
    def test_get_role_permissions(self):
        """Test getting permissions for each role"""
        # Test ADMIN permissions
        admin_perms = RBACService.get_role_permissions(RolUsuario.ADMIN)
        assert Permission.CREATE_USER in admin_perms
        assert Permission.MANAGE_SYSTEM in admin_perms
        assert Permission.VIEW_AUDIT_LOGS in admin_perms
        assert len(admin_perms) > 20  # Admin should have many permissions
        
        # Test ADVISOR permissions
        advisor_perms = RBACService.get_role_permissions(RolUsuario.ADVISOR)
        assert Permission.CREATE_OFERTA in advisor_perms
        assert Permission.BULK_UPLOAD_OFERTAS in advisor_perms
        assert Permission.READ_SOLICITUD in advisor_perms
        assert Permission.MANAGE_SYSTEM not in advisor_perms  # Should not have admin perms
        
        # Test CLIENT permissions
        client_perms = RBACService.get_role_permissions(RolUsuario.CLIENT)
        assert Permission.CREATE_SOLICITUD in client_perms
        assert Permission.CREATE_PQR in client_perms
        assert Permission.CREATE_OFERTA not in client_perms  # Clients can't create offers
        
        # Test ANALYST permissions
        analyst_perms = RBACService.get_role_permissions(RolUsuario.ANALYST)
        assert Permission.EVALUATE_OFERTAS in analyst_perms
        assert Permission.VIEW_ANALYTICS in analyst_perms
        assert Permission.ESCALATE_SOLICITUD in analyst_perms
        
        # Test SUPPORT permissions
        support_perms = RBACService.get_role_permissions(RolUsuario.SUPPORT)
        assert Permission.RESOLVE_PQR in support_perms
        assert Permission.READ_PQR in support_perms
        assert Permission.UPDATE_PQR in support_perms
    
    def test_has_permission(self):
        """Test checking if role has specific permission"""
        # Test positive cases
        assert RBACService.has_permission(RolUsuario.ADMIN, Permission.CREATE_USER) is True
        assert RBACService.has_permission(RolUsuario.ADVISOR, Permission.CREATE_OFERTA) is True
        assert RBACService.has_permission(RolUsuario.CLIENT, Permission.CREATE_SOLICITUD) is True
        assert RBACService.has_permission(RolUsuario.ANALYST, Permission.EVALUATE_OFERTAS) is True
        assert RBACService.has_permission(RolUsuario.SUPPORT, Permission.RESOLVE_PQR) is True
        
        # Test negative cases
        assert RBACService.has_permission(RolUsuario.CLIENT, Permission.CREATE_OFERTA) is False
        assert RBACService.has_permission(RolUsuario.ADVISOR, Permission.MANAGE_SYSTEM) is False
        assert RBACService.has_permission(RolUsuario.SUPPORT, Permission.DELETE_USER) is False
    
    def test_has_any_permission(self):
        """Test checking if role has any of specified permissions"""
        # Test ADMIN (should have all)
        admin_test_perms = [Permission.CREATE_USER, Permission.MANAGE_SYSTEM]
        assert RBACService.has_any_permission(RolUsuario.ADMIN, admin_test_perms) is True
        
        # Test ADVISOR (should have some)
        advisor_test_perms = [Permission.CREATE_OFERTA, Permission.MANAGE_SYSTEM]
        assert RBACService.has_any_permission(RolUsuario.ADVISOR, advisor_test_perms) is True
        
        # Test CLIENT (should have none of admin perms)
        client_test_perms = [Permission.DELETE_USER, Permission.MANAGE_SYSTEM]
        assert RBACService.has_any_permission(RolUsuario.CLIENT, client_test_perms) is False
    
    def test_has_all_permissions(self):
        """Test checking if role has all specified permissions"""
        # Test ADMIN (should have all)
        admin_test_perms = [Permission.CREATE_USER, Permission.READ_USER, Permission.UPDATE_USER]
        assert RBACService.has_all_permissions(RolUsuario.ADMIN, admin_test_perms) is True
        
        # Test ADVISOR (should not have all admin perms)
        advisor_test_perms = [Permission.CREATE_OFERTA, Permission.MANAGE_SYSTEM]
        assert RBACService.has_all_permissions(RolUsuario.ADVISOR, advisor_test_perms) is False
        
        # Test CLIENT (should have basic perms)
        client_test_perms = [Permission.CREATE_SOLICITUD, Permission.CREATE_PQR]
        assert RBACService.has_all_permissions(RolUsuario.CLIENT, client_test_perms) is True
    
    def test_can_access_resource_admin(self):
        """Test admin can access any resource"""
        # Admin should access any resource regardless of ownership
        assert RBACService.can_access_resource(
            RolUsuario.ADMIN, 999, 1, Permission.READ_USER
        ) is True
        
        assert RBACService.can_access_resource(
            RolUsuario.ADMIN, 999, 1, Permission.UPDATE_SOLICITUD
        ) is True
    
    def test_can_access_resource_analyst(self):
        """Test analyst can access evaluation resources"""
        # Analyst should access evaluation resources regardless of ownership
        assert RBACService.can_access_resource(
            RolUsuario.ANALYST, 999, 1, Permission.READ_SOLICITUD
        ) is True
        
        assert RBACService.can_access_resource(
            RolUsuario.ANALYST, 999, 1, Permission.EVALUATE_OFERTAS
        ) is True
        
        # But not user management
        assert RBACService.can_access_resource(
            RolUsuario.ANALYST, 999, 1, Permission.DELETE_USER
        ) is False
    
    def test_can_access_resource_support(self):
        """Test support can access customer service resources"""
        # Support should access PQR resources regardless of ownership
        assert RBACService.can_access_resource(
            RolUsuario.SUPPORT, 999, 1, Permission.READ_PQR
        ) is True
        
        assert RBACService.can_access_resource(
            RolUsuario.SUPPORT, 999, 1, Permission.UPDATE_PQR
        ) is True
    
    def test_can_access_resource_ownership(self):
        """Test resource access based on ownership"""
        # User should access their own resources
        assert RBACService.can_access_resource(
            RolUsuario.CLIENT, 1, 1, Permission.READ_SOLICITUD
        ) is True
        
        assert RBACService.can_access_resource(
            RolUsuario.ADVISOR, 1, 1, Permission.UPDATE_OFERTA
        ) is True
        
        # User should not access others' resources
        assert RBACService.can_access_resource(
            RolUsuario.CLIENT, 999, 1, Permission.READ_SOLICITUD
        ) is False
        
        assert RBACService.can_access_resource(
            RolUsuario.ADVISOR, 999, 1, Permission.UPDATE_OFERTA
        ) is False
    
    def test_can_access_resource_no_permission(self):
        """Test resource access when user lacks permission"""
        # Client trying to access admin permission
        assert RBACService.can_access_resource(
            RolUsuario.CLIENT, 1, 1, Permission.MANAGE_SYSTEM
        ) is False
        
        # Advisor trying to access evaluation permission
        assert RBACService.can_access_resource(
            RolUsuario.ADVISOR, 1, 1, Permission.EVALUATE_OFERTAS
        ) is False


class TestAuthMiddleware:
    """Test authentication middleware and dependencies"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_dependency(self):
        """Test get_current_user dependency"""
        # Mock credentials and user
        mock_credentials = AsyncMock()
        mock_credentials.credentials = "valid_token"
        
        mock_user = AsyncMock()
        mock_user.email = "test@teloo.com"
        
        with patch('services.auth_service.AuthService.get_current_user', return_value=mock_user):
            result = await get_current_user(mock_credentials)
            assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_dependency(self):
        """Test get_current_active_user dependency"""
        # Mock active user
        mock_user = AsyncMock()
        mock_user.is_active.return_value = True
        
        result = await get_current_active_user(mock_user)
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self):
        """Test get_current_active_user with inactive user"""
        # Mock inactive user
        mock_user = MagicMock()
        mock_user.is_active.return_value = False
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Inactive user" in str(exc_info.value.detail)
    
    def test_require_role_dependency(self):
        """Test require_role dependency factory"""
        # Create role checker for ADMIN
        admin_checker = require_role([RolUsuario.ADMIN])
        
        # Mock admin user
        mock_admin = AsyncMock()
        mock_admin.rol = RolUsuario.ADMIN
        
        # Should pass for admin
        result = admin_checker(mock_admin)
        assert result == mock_admin
        
        # Mock client user
        mock_client = AsyncMock()
        mock_client.rol = RolUsuario.CLIENT
        
        # Should fail for client
        with pytest.raises(HTTPException) as exc_info:
            admin_checker(mock_client)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in str(exc_info.value.detail)
    
    def test_require_permission_dependency(self):
        """Test require_permission dependency factory"""
        # Create permission checker
        perm_checker = require_permission([Permission.CREATE_OFERTA])
        
        # Mock advisor user (has CREATE_OFERTA permission)
        mock_advisor = AsyncMock()
        mock_advisor.rol = RolUsuario.ADVISOR
        
        with patch.object(RBACService, 'has_any_permission', return_value=True):
            result = perm_checker(mock_advisor)
            assert result == mock_advisor
        
        # Mock client user (doesn't have CREATE_OFERTA permission)
        mock_client = AsyncMock()
        mock_client.rol = RolUsuario.CLIENT
        
        with patch.object(RBACService, 'has_any_permission', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                perm_checker(mock_client)
            
            assert exc_info.value.status_code == 403
            assert "Access denied" in str(exc_info.value.detail)
    
    def test_require_all_permissions_dependency(self):
        """Test require_all_permissions dependency factory"""
        # Create permission checker requiring multiple permissions
        perm_checker = require_all_permissions([
            Permission.CREATE_USER, 
            Permission.DELETE_USER
        ])
        
        # Mock admin user (has all permissions)
        mock_admin = AsyncMock()
        mock_admin.rol = RolUsuario.ADMIN
        
        with patch.object(RBACService, 'has_all_permissions', return_value=True):
            result = perm_checker(mock_admin)
            assert result == mock_admin
        
        # Mock support user (doesn't have all permissions)
        mock_support = AsyncMock()
        mock_support.rol = RolUsuario.SUPPORT
        
        with patch.object(RBACService, 'has_all_permissions', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                perm_checker(mock_support)
            
            assert exc_info.value.status_code == 403
            assert "Access denied" in str(exc_info.value.detail)


class TestRolePermissionMatrix:
    """Test the complete role-permission matrix for compliance with requirements"""
    
    def test_admin_permissions_complete(self):
        """Test that ADMIN has all required permissions"""
        admin_perms = RBACService.get_role_permissions(RolUsuario.ADMIN)
        
        # Admin should have all system permissions
        required_admin_perms = [
            Permission.CREATE_USER, Permission.READ_USER, Permission.UPDATE_USER, Permission.DELETE_USER,
            Permission.CREATE_SOLICITUD, Permission.READ_SOLICITUD, Permission.UPDATE_SOLICITUD, Permission.DELETE_SOLICITUD,
            Permission.CREATE_OFERTA, Permission.READ_OFERTA, Permission.UPDATE_OFERTA, Permission.DELETE_OFERTA,
            Permission.EVALUATE_OFERTAS, Permission.SELECT_OFERTA,
            Permission.VIEW_ANALYTICS, Permission.VIEW_REPORTS, Permission.EXPORT_DATA,
            Permission.MANAGE_SYSTEM, Permission.VIEW_AUDIT_LOGS, Permission.MANAGE_CONFIGURATIONS,
            Permission.RESOLVE_PQR, Permission.PROCESS_PAYMENTS
        ]
        
        for perm in required_admin_perms:
            assert perm in admin_perms, f"ADMIN missing required permission: {perm}"
    
    def test_advisor_permissions_restricted(self):
        """Test that ADVISOR has only appropriate permissions"""
        advisor_perms = RBACService.get_role_permissions(RolUsuario.ADVISOR)
        
        # Advisor should have these permissions
        required_advisor_perms = [
            Permission.READ_SOLICITUD, Permission.CREATE_OFERTA, Permission.READ_OFERTA,
            Permission.UPDATE_OFERTA, Permission.BULK_UPLOAD_OFERTAS,
            Permission.CREATE_PQR, Permission.READ_PQR
        ]
        
        for perm in required_advisor_perms:
            assert perm in advisor_perms, f"ADVISOR missing required permission: {perm}"
        
        # Advisor should NOT have these permissions
        forbidden_advisor_perms = [
            Permission.DELETE_USER, Permission.MANAGE_SYSTEM, Permission.VIEW_AUDIT_LOGS,
            Permission.EVALUATE_OFERTAS, Permission.PROCESS_PAYMENTS
        ]
        
        for perm in forbidden_advisor_perms:
            assert perm not in advisor_perms, f"ADVISOR should not have permission: {perm}"
    
    def test_client_permissions_minimal(self):
        """Test that CLIENT has only basic permissions"""
        client_perms = RBACService.get_role_permissions(RolUsuario.CLIENT)
        
        # Client should have these basic permissions
        required_client_perms = [
            Permission.CREATE_SOLICITUD, Permission.READ_SOLICITUD,
            Permission.READ_OFERTA, Permission.SELECT_OFERTA,
            Permission.CREATE_PQR, Permission.READ_PQR
        ]
        
        for perm in required_client_perms:
            assert perm in client_perms, f"CLIENT missing required permission: {perm}"
        
        # Client should NOT have these permissions
        forbidden_client_perms = [
            Permission.CREATE_OFERTA, Permission.EVALUATE_OFERTAS,
            Permission.MANAGE_SYSTEM, Permission.DELETE_USER,
            Permission.PROCESS_PAYMENTS, Permission.VIEW_AUDIT_LOGS
        ]
        
        for perm in forbidden_client_perms:
            assert perm not in client_perms, f"CLIENT should not have permission: {perm}"
    
    def test_analyst_permissions_evaluation_focused(self):
        """Test that ANALYST has evaluation and analytics permissions"""
        analyst_perms = RBACService.get_role_permissions(RolUsuario.ANALYST)
        
        # Analyst should have these permissions
        required_analyst_perms = [
            Permission.READ_SOLICITUD, Permission.UPDATE_SOLICITUD, Permission.ESCALATE_SOLICITUD,
            Permission.READ_OFERTA, Permission.EVALUATE_OFERTAS, Permission.SELECT_OFERTA,
            Permission.VIEW_ANALYTICS, Permission.VIEW_REPORTS, Permission.EXPORT_DATA
        ]
        
        for perm in required_analyst_perms:
            assert perm in analyst_perms, f"ANALYST missing required permission: {perm}"
        
        # Analyst should NOT have these permissions
        forbidden_analyst_perms = [
            Permission.DELETE_USER, Permission.CREATE_OFERTA,
            Permission.MANAGE_SYSTEM, Permission.PROCESS_PAYMENTS
        ]
        
        for perm in forbidden_analyst_perms:
            assert perm not in analyst_perms, f"ANALYST should not have permission: {perm}"
    
    def test_support_permissions_customer_service(self):
        """Test that SUPPORT has customer service permissions"""
        support_perms = RBACService.get_role_permissions(RolUsuario.SUPPORT)
        
        # Support should have these permissions
        required_support_perms = [
            Permission.READ_USER, Permission.UPDATE_USER,
            Permission.READ_SOLICITUD, Permission.UPDATE_SOLICITUD,
            Permission.READ_OFERTA, Permission.CREATE_PQR,
            Permission.READ_PQR, Permission.UPDATE_PQR, Permission.RESOLVE_PQR
        ]
        
        for perm in required_support_perms:
            assert perm in support_perms, f"SUPPORT missing required permission: {perm}"
        
        # Support should NOT have these permissions
        forbidden_support_perms = [
            Permission.DELETE_USER, Permission.EVALUATE_OFERTAS,
            Permission.MANAGE_SYSTEM, Permission.PROCESS_PAYMENTS,
            Permission.VIEW_AUDIT_LOGS
        ]
        
        for perm in forbidden_support_perms:
            assert perm not in support_perms, f"SUPPORT should not have permission: {perm}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])