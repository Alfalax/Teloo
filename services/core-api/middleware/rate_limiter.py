"""
Rate Limiting Middleware
Protege los endpoints de abuso mediante límites de peticiones
"""

import time
from fastapi import HTTPException, status, Request
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    Rate limiter simple en memoria
    Para producción con múltiples instancias, usar Redis
    """
    
    def __init__(self):
        # {key: (count, window_start_time)}
        self.requests: Dict[str, Tuple[int, float]] = {}
        self.window_seconds = 60  # Ventana de 1 minuto
        self.max_requests = 60  # 60 peticiones por minuto
    
    def is_allowed(self, key: str) -> bool:
        """
        Verifica si una petición está permitida
        
        Args:
            key: Identificador único (IP, service_name, etc.)
            
        Returns:
            bool: True si está permitida, False si excede el límite
        """
        current_time = time.time()
        
        # Limpiar entradas antiguas
        self._cleanup_old_entries(current_time)
        
        # Obtener contador actual
        if key not in self.requests:
            self.requests[key] = (1, current_time)
            return True
        
        count, window_start = self.requests[key]
        
        # Si estamos en la misma ventana
        if current_time - window_start < self.window_seconds:
            if count >= self.max_requests:
                logger.warning(f"Rate limit exceeded for: {key}")
                return False
            
            self.requests[key] = (count + 1, window_start)
            return True
        
        # Nueva ventana
        self.requests[key] = (1, current_time)
        return True
    
    def _cleanup_old_entries(self, current_time: float):
        """Limpia entradas antiguas para liberar memoria"""
        keys_to_delete = [
            key for key, (_, window_start) in self.requests.items()
            if current_time - window_start > self.window_seconds * 2
        ]
        for key in keys_to_delete:
            del self.requests[key]


# Instancia global del rate limiter
rate_limiter = InMemoryRateLimiter()


async def check_rate_limit(request: Request, identifier: str = None):
    """
    Middleware para verificar rate limiting
    
    Args:
        request: Request de FastAPI
        identifier: Identificador personalizado (opcional, usa IP por defecto)
        
    Raises:
        HTTPException: Si se excede el límite de peticiones
    """
    # Usar identificador personalizado o IP del cliente
    key = identifier or request.client.host
    
    if not rate_limiter.is_allowed(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )
