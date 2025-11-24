"""
Service-to-Service Authentication Middleware
Valida que las peticiones entre servicios sean autenticadas y autorizadas
"""

import os
from fastapi import Header, HTTPException, status
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# API Keys para servicios internos (deben estar en .env)
SERVICE_API_KEYS = {
    "agent-ia": os.getenv("AGENT_IA_API_KEY", ""),
    "analytics": os.getenv("ANALYTICS_API_KEY", ""),
}


async def verify_service_api_key(
    x_service_api_key: Optional[str] = Header(None, alias="X-Service-API-Key"),
    x_service_name: Optional[str] = Header(None, alias="X-Service-Name")
) -> str:
    """
    Verifica que la petición venga de un servicio autorizado
    
    Args:
        x_service_api_key: API key del servicio
        x_service_name: Nombre del servicio (agent-ia, analytics, etc.)
        
    Returns:
        str: Nombre del servicio autenticado
        
    Raises:
        HTTPException: Si la autenticación falla
    """
    
    # Validar que se proporcionen ambos headers
    if not x_service_api_key or not x_service_name:
        logger.warning("Service authentication failed: Missing headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Service authentication required. Missing X-Service-API-Key or X-Service-Name headers"
        )
    
    # Validar que el servicio exista
    if x_service_name not in SERVICE_API_KEYS:
        logger.warning(f"Service authentication failed: Unknown service '{x_service_name}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unknown service: {x_service_name}"
        )
    
    # Validar que la API key sea correcta
    expected_key = SERVICE_API_KEYS[x_service_name]
    
    if not expected_key:
        logger.error(f"Service API key not configured for: {x_service_name}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service authentication not properly configured"
        )
    
    if x_service_api_key != expected_key:
        logger.warning(f"Service authentication failed: Invalid API key for '{x_service_name}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service API key"
        )
    
    # Autenticación exitosa
    logger.info(f"Service authenticated: {x_service_name}")
    return x_service_name


async def verify_agent_ia_service(
    service_name: str = Header(..., alias="X-Service-Name", dependencies=[verify_service_api_key])
) -> None:
    """
    Verifica que la petición venga específicamente del servicio agent-ia
    Útil para endpoints que solo deben ser accesibles por el bot
    """
    if service_name != "agent-ia":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only accessible by agent-ia service"
        )
