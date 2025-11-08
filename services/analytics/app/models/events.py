"""
Event models for Analytics Service
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from typing import Dict, Any
import json

class EventoSistema(Model):
    """
    Modelo para capturar todos los eventos del sistema
    """
    id = fields.IntField(pk=True)
    
    # Información del evento
    tipo_evento = fields.CharField(max_length=100)  # solicitud.created, oferta.submitted, etc.
    entidad_tipo = fields.CharField(max_length=50)  # Solicitud, Oferta, Cliente, etc.
    entidad_id = fields.IntField()
    
    # Datos del evento
    datos = fields.JSONField()  # Datos específicos del evento
    metadatos = fields.JSONField(default=dict)  # IP, user_agent, etc.
    
    # Auditoría
    usuario_id = fields.IntField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    # Índices para consultas rápidas
    class Meta:
        table = "eventos_sistema"
        indexes = [
            ("tipo_evento", "created_at"),
            ("entidad_tipo", "entidad_id"),
            ("created_at",),
        ]
    
    def __str__(self):
        return f"{self.tipo_evento} - {self.entidad_tipo}:{self.entidad_id}"

class EventoMetrica(Model):
    """
    Modelo para eventos específicos de métricas en tiempo real
    """
    id = fields.IntField(pk=True)
    
    # Información de la métrica
    metrica_nombre = fields.CharField(max_length=100)
    valor = fields.FloatField()
    unidad = fields.CharField(max_length=20, default="count")
    
    # Dimensiones para filtrado
    dimensiones = fields.JSONField(default=dict)  # {ciudad: "Bogotá", asesor_id: 123}
    
    # Timestamp
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "eventos_metricas"
        indexes = [
            ("metrica_nombre", "created_at"),
            ("created_at",),
        ]
    
    def __str__(self):
        return f"{self.metrica_nombre}: {self.valor} {self.unidad}"