"""
PQR Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from models.enums import TipoPQR, PrioridadPQR, EstadoPQR


class PQRBase(BaseModel):
    tipo: TipoPQR
    prioridad: PrioridadPQR = PrioridadPQR.MEDIA
    resumen: str = Field(..., min_length=10, max_length=200)
    detalle: str = Field(..., min_length=20)


class PQRCreate(PQRBase):
    cliente_id: UUID


class PQRUpdate(BaseModel):
    tipo: Optional[TipoPQR] = None
    prioridad: Optional[PrioridadPQR] = None
    resumen: Optional[str] = Field(None, min_length=10, max_length=200)
    detalle: Optional[str] = Field(None, min_length=20)
    respuesta: Optional[str] = None


class ClienteInfo(BaseModel):
    id: UUID
    nombre_completo: str
    telefono: str
    email: Optional[str] = None


class UsuarioInfo(BaseModel):
    id: UUID
    nombre_completo: str
    email: str


class PQRResponse(PQRBase):
    id: UUID
    estado: EstadoPQR
    cliente: ClienteInfo
    respuesta: Optional[str] = None
    fecha_respuesta: Optional[datetime] = None
    respondido_por: Optional[UsuarioInfo] = None
    tiempo_resolucion_horas: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PQRList(BaseModel):
    data: List[PQRResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class PQRMetrics(BaseModel):
    total_abiertas: int
    total_en_proceso: int
    total_cerradas: int
    tiempo_promedio_resolucion_horas: Decimal
    pqrs_alta_prioridad: int
    pqrs_criticas: int
    tasa_resolucion_24h: Decimal  # Porcentaje de PQRs resueltas en menos de 24h
    distribucion_por_tipo: dict  # {"PETICION": 10, "QUEJA": 5, "RECLAMO": 3}
    distribucion_por_prioridad: dict  # {"BAJA": 8, "MEDIA": 7, "ALTA": 2, "CRITICA": 1}


class PQRNotificationCreate(BaseModel):
    pqr_id: UUID
    tipo_notificacion: str  # "nueva_pqr", "pqr_alta_prioridad", "pqr_critica"
    destinatarios: List[UUID]  # IDs de usuarios a notificar
    mensaje: str