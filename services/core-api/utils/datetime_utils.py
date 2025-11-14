"""
Utilidades para manejo consistente de fechas y horas
Siempre usar UTC en backend, convertir a local en frontend
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def now_utc() -> datetime:
    """
    Retorna la fecha/hora actual en UTC con timezone aware
    
    Returns:
        datetime: Fecha/hora actual en UTC
    """
    return datetime.now(timezone.utc)


def from_timestamp(timestamp: float) -> datetime:
    """
    Convierte un timestamp Unix a datetime UTC
    
    Args:
        timestamp: Timestamp Unix (segundos desde epoch)
        
    Returns:
        datetime: Fecha/hora en UTC
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def to_iso_string(dt: datetime) -> str:
    """
    Convierte datetime a string ISO 8601 con UTC
    
    Args:
        dt: Datetime a convertir
        
    Returns:
        str: String en formato ISO 8601
    """
    if dt.tzinfo is None:
        # Si no tiene timezone, asumimos UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def add_hours(dt: datetime, hours: int) -> datetime:
    """
    Agrega horas a un datetime
    
    Args:
        dt: Datetime base
        hours: Horas a agregar (puede ser negativo)
        
    Returns:
        datetime: Nuevo datetime
    """
    return dt + timedelta(hours=hours)


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """
    Agrega minutos a un datetime
    
    Args:
        dt: Datetime base
        minutes: Minutos a agregar (puede ser negativo)
        
    Returns:
        datetime: Nuevo datetime
    """
    return dt + timedelta(minutes=minutes)


def add_days(dt: datetime, days: int) -> datetime:
    """
    Agrega días a un datetime
    
    Args:
        dt: Datetime base
        days: Días a agregar (puede ser negativo)
        
    Returns:
        datetime: Nuevo datetime
    """
    return dt + timedelta(days=days)


def hours_between(dt1: datetime, dt2: datetime) -> float:
    """
    Calcula las horas entre dos datetimes
    
    Args:
        dt1: Datetime inicial
        dt2: Datetime final
        
    Returns:
        float: Horas de diferencia (puede ser negativo)
    """
    delta = dt2 - dt1
    return delta.total_seconds() / 3600


def minutes_between(dt1: datetime, dt2: datetime) -> int:
    """
    Calcula los minutos entre dos datetimes
    
    Args:
        dt1: Datetime inicial
        dt2: Datetime final
        
    Returns:
        int: Minutos de diferencia (puede ser negativo)
    """
    delta = dt2 - dt1
    return int(delta.total_seconds() / 60)


def is_expired(dt: datetime, hours: int) -> bool:
    """
    Verifica si un datetime ha expirado después de X horas
    
    Args:
        dt: Datetime a verificar
        hours: Horas de expiración
        
    Returns:
        bool: True si ha expirado
    """
    expiration_time = add_hours(dt, hours)
    return now_utc() > expiration_time


def time_until_expiration(dt: datetime, hours: int) -> Optional[timedelta]:
    """
    Calcula el tiempo restante hasta la expiración
    
    Args:
        dt: Datetime base
        hours: Horas hasta expiración
        
    Returns:
        timedelta: Tiempo restante (None si ya expiró)
    """
    expiration_time = add_hours(dt, hours)
    remaining = expiration_time - now_utc()
    return remaining if remaining.total_seconds() > 0 else None
