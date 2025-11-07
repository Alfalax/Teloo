"""
TeLOO V3 Core API Models
Modelos de datos usando Tortoise ORM
"""

from .base import BaseModel
from .enums import *
from .user import Usuario, Cliente, Asesor
from .solicitud import Solicitud, RepuestoSolicitado
from .oferta import Oferta, OfertaDetalle, AdjudicacionRepuesto, Evaluacion
from .geografia import AreaMetropolitana, HubLogistico, EvaluacionAsesorTemp
from .analytics import (
    HistorialRespuestaOferta,
    OfertaHistorica,
    AuditoriaTienda,
    EventoSistema,
    MetricaCalculada,
    Transaccion,
    PQR,
    Notificacion,
    SesionUsuario,
    LogAuditoria,
    ParametroConfig
)

__all__ = [
    "BaseModel",
    # Enums
    "RolUsuario",
    "EstadoUsuario",
    "EstadoSolicitud",
    "EstadoOferta",
    "EstadoAsesor",
    "TipoPQR",
    "PrioridadPQR",
    "EstadoPQR",
    "TipoTransaccion",
    "EstadoTransaccion",
    "TipoEvento",
    "CanalNotificacion",
    # Core Models
    "Usuario",
    "Cliente",
    "Asesor",
    "Solicitud",
    "RepuestoSolicitado",
    "Oferta",
    "OfertaDetalle",
    "AdjudicacionRepuesto",
    "Evaluacion",
    # Geografia
    "AreaMetropolitana",
    "HubLogistico",
    "EvaluacionAsesorTemp",
    # Analytics
    "HistorialRespuestaOferta",
    "OfertaHistorica",
    "AuditoriaTienda",
    "EventoSistema",
    "MetricaCalculada",
    "Transaccion",
    "PQR",
    "Notificacion",
    "SesionUsuario",
    "LogAuditoria",
    "ParametroConfig",
]