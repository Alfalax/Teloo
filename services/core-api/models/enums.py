"""
Enums for TeLOO V3 system
"""

from enum import Enum


class RolUsuario(str, Enum):
    """Roles de usuario en el sistema"""
    ADMIN = "ADMIN"
    ADVISOR = "ADVISOR"
    ANALYST = "ANALYST"
    SUPPORT = "SUPPORT"
    CLIENT = "CLIENT"


class EstadoUsuario(str, Enum):
    """Estados de usuario"""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    SUSPENDIDO = "SUSPENDIDO"
    BLOQUEADO = "BLOQUEADO"


class EstadoSolicitud(str, Enum):
    """Estados de solicitud"""
    ABIERTA = "ABIERTA"
    EVALUADA = "EVALUADA"
    OFERTAS_ACEPTADAS = "OFERTAS_ACEPTADAS"
    OFERTAS_RECHAZADAS = "OFERTAS_RECHAZADAS"
    CERRADA_SIN_OFERTAS = "CERRADA_SIN_OFERTAS"


class EstadoOferta(str, Enum):
    """Estados simplificados de oferta"""
    ENVIADA = "ENVIADA"
    GANADORA = "GANADORA"
    NO_SELECCIONADA = "NO_SELECCIONADA"
    EXPIRADA = "EXPIRADA"
    RECHAZADA = "RECHAZADA"
    ACEPTADA = "ACEPTADA"


class EstadoAsesor(str, Enum):
    """Estados de asesor"""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    SUSPENDIDO = "SUSPENDIDO"


class TipoPQR(str, Enum):
    """Tipos de PQR"""
    PETICION = "PETICION"
    QUEJA = "QUEJA"
    RECLAMO = "RECLAMO"


class PrioridadPQR(str, Enum):
    """Prioridades de PQR"""
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class EstadoPQR(str, Enum):
    """Estados de PQR"""
    ABIERTA = "ABIERTA"
    EN_PROCESO = "EN_PROCESO"
    CERRADA = "CERRADA"


class TipoTransaccion(str, Enum):
    """Tipos de transacción financiera"""
    VENTA = "VENTA"
    COMISION = "COMISION"
    DEVOLUCION = "DEVOLUCION"


class EstadoTransaccion(str, Enum):
    """Estados de transacción"""
    PENDIENTE = "PENDIENTE"
    COMPLETADA = "COMPLETADA"
    FALLIDA = "FALLIDA"


class TipoEvento(str, Enum):
    """Tipos de eventos del sistema"""
    SOLICITUD_CREADA = "solicitud.creada"
    SOLICITUD_ESCALADA = "solicitud.escalada"
    OFERTA_CREADA = "oferta.creada"
    OFERTA_BULK_UPLOADED = "oferta.bulk_uploaded"
    EVALUACION_COMPLETADA = "evaluacion.completada"
    CLIENTE_ACEPTO = "cliente.acepto"
    CLIENTE_RECHAZO = "cliente.rechazo"


class CanalNotificacion(str, Enum):
    """Canales de notificación"""
    WHATSAPP = "WHATSAPP"
    PUSH = "PUSH"
    EMAIL = "EMAIL"
    SMS = "SMS"


class OrigenOferta(str, Enum):
    """Origen de la oferta"""
    FORM = "FORM"
    EXCEL = "EXCEL"


class EstadoAuditoria(str, Enum):
    """Estados de auditoría de tienda"""
    APROBADA = "APROBADA"
    OBSERVACIONES = "OBSERVACIONES"
    RECHAZADA = "RECHAZADA"