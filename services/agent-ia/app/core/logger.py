"""
Logging estructurado con formato JSON y correlation IDs para Agent IA
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
import uuid

# Context variable para correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class JSONFormatter(logging.Formatter):
    """
    Formateador JSON para logs estructurados
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Agregar correlation ID si existe
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data['correlation_id'] = correlation_id
        
        # Agregar campos extra
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Agregar exception info si existe
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    """
    Configura logging estructurado para el servicio
    
    Args:
        service_name: Nombre del servicio
        level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado
    """
    # Crear logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Limpiar handlers existentes
    logger.handlers.clear()
    
    # Crear handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    # No propagar a root logger
    logger.propagate = False
    
    return logger


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Establece correlation ID para el contexto actual
    
    Args:
        correlation_id: ID de correlación (se genera uno si no se proporciona)
    
    Returns:
        Correlation ID establecido
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Obtiene el correlation ID del contexto actual
    
    Returns:
        Correlation ID o None si no está establecido
    """
    return correlation_id_var.get()


def clear_correlation_id():
    """
    Limpia el correlation ID del contexto actual
    """
    correlation_id_var.set(None)


class StructuredLogger:
    """
    Logger estructurado con soporte para campos adicionales
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def _log(self, level: int, message: str, **kwargs):
        """
        Log con campos adicionales
        """
        extra = {'extra_fields': kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log nivel DEBUG"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log nivel INFO"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log nivel WARNING"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log nivel ERROR"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log nivel CRITICAL"""
        self._log(logging.CRITICAL, message, **kwargs)


# Logger global para el servicio
_service_logger: Optional[StructuredLogger] = None


def get_logger() -> StructuredLogger:
    """
    Obtiene el logger estructurado del servicio
    
    Returns:
        StructuredLogger configurado
    """
    global _service_logger
    
    if _service_logger is None:
        # Configuración por defecto
        base_logger = setup_logging("agent-ia", "INFO")
        _service_logger = StructuredLogger(base_logger)
    
    return _service_logger


def init_logger(service_name: str, level: str = "INFO") -> StructuredLogger:
    """
    Inicializa el logger del servicio
    
    Args:
        service_name: Nombre del servicio
        level: Nivel de log
    
    Returns:
        StructuredLogger configurado
    """
    global _service_logger
    
    base_logger = setup_logging(service_name, level)
    _service_logger = StructuredLogger(base_logger)
    
    return _service_logger
