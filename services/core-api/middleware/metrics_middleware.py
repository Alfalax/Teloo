"""
Middleware para capturar métricas HTTP automáticamente
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import time

from utils.metrics import metrics_collector, http_requests_in_progress


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware que captura métricas de requests HTTP
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa el request y captura métricas
        
        Args:
            request: Request HTTP
            call_next: Siguiente middleware/handler
        
        Returns:
            Response HTTP
        """
        # Extraer información del request
        method = request.method
        path = request.url.path
        
        # Normalizar path para evitar cardinalidad alta
        # (remover IDs y parámetros dinámicos)
        endpoint = self._normalize_path(path)
        
        # Incrementar requests en progreso
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        # Medir tiempo de ejecución
        start_time = time.time()
        
        try:
            # Procesar request
            response = await call_next(request)
            
            # Calcular duración
            duration = time.time() - start_time
            
            # Registrar métricas
            metrics_collector.record_http_request(
                method=method,
                endpoint=endpoint,
                status=response.status_code,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            # Registrar error
            duration = time.time() - start_time
            metrics_collector.record_http_request(
                method=method,
                endpoint=endpoint,
                status=500,
                duration=duration
            )
            metrics_collector.record_system_error(
                error_type=type(e).__name__,
                component='http_handler'
            )
            raise
            
        finally:
            # Decrementar requests en progreso
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
    
    def _normalize_path(self, path: str) -> str:
        """
        Normaliza el path para reducir cardinalidad
        
        Args:
            path: Path original
        
        Returns:
            Path normalizado
        """
        # Excluir endpoints de métricas y health
        if path in ['/metrics', '/health', '/']:
            return path
        
        # Reemplazar UUIDs con placeholder
        import re
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path,
            flags=re.IGNORECASE
        )
        
        # Reemplazar números con placeholder
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path
