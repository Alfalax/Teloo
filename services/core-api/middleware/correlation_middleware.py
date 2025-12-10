"""
Middleware para gestionar correlation IDs en requests HTTP
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable

from utils.logger import set_correlation_id, clear_correlation_id, get_correlation_id


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware que gestiona correlation IDs para trazabilidad de requests
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa el request y gestiona el correlation ID
        
        Args:
            request: Request HTTP
            call_next: Siguiente middleware/handler
        
        Returns:
            Response HTTP con correlation ID en headers
        """
        # Obtener correlation ID del header o generar uno nuevo
        correlation_id = request.headers.get('X-Correlation-ID')
        correlation_id = set_correlation_id(correlation_id)
        
        try:
            # Procesar request
            response = await call_next(request)
            
            # Agregar correlation ID al response
            response.headers['X-Correlation-ID'] = correlation_id
            
            return response
            
        finally:
            # Limpiar correlation ID del contexto
            clear_correlation_id()
