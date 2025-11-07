"""
Metrics models for Analytics Service
"""
from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from enum import Enum

class TipoMetrica(str, Enum):
    """Tipos de métricas"""
    KPI = "kpi"
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"

class MetricaCalculada(Model):
    """
    Modelo para almacenar métricas calculadas y cacheadas
    """
    id = fields.IntField(pk=True)
    
    # Información de la métrica
    nombre = fields.CharField(max_length=100)
    tipo = fields.CharEnumField(TipoMetrica, default=TipoMetrica.KPI)
    valor = fields.FloatField()
    
    # Metadatos
    descripcion = fields.TextField(null=True)
    unidad = fields.CharField(max_length=20, default="count")
    
    # Dimensiones y filtros
    dimensiones = fields.JSONField(default=dict)  # {periodo: "mensual", ciudad: "Bogotá"}
    
    # Período de validez
    periodo_inicio = fields.DatetimeField()
    periodo_fin = fields.DatetimeField()
    
    # Control de cache
    calculado_en = fields.DatetimeField(auto_now_add=True)
    expira_en = fields.DatetimeField()
    
    class Meta:
        table = "metricas_calculadas"
        indexes = [
            ("nombre", "periodo_inicio", "periodo_fin"),
            ("expira_en",),
            ("calculado_en",),
        ]
    
    def __str__(self):
        return f"{self.nombre}: {self.valor} {self.unidad}"

class AlertaMetrica(Model):
    """
    Modelo para configurar alertas sobre métricas
    """
    id = fields.IntField(pk=True)
    
    # Configuración de la alerta
    nombre = fields.CharField(max_length=100)
    metrica_nombre = fields.CharField(max_length=100)
    
    # Condiciones
    operador = fields.CharField(max_length=10)  # >, <, >=, <=, ==
    valor_umbral = fields.FloatField()
    
    # Configuración de notificación
    activa = fields.BooleanField(default=True)
    canales_notificacion = fields.JSONField(default=list)  # ["email", "slack"]
    
    # Auditoría
    creado_en = fields.DatetimeField(auto_now_add=True)
    actualizado_en = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "alertas_metricas"
    
    def __str__(self):
        return f"{self.nombre} - {self.metrica_nombre} {self.operador} {self.valor_umbral}"

class HistorialAlerta(Model):
    """
    Modelo para registrar disparos de alertas
    """
    id = fields.IntField(pk=True)
    
    # Referencia a la alerta
    alerta = fields.ForeignKeyField("models.AlertaMetrica", related_name="historial")
    
    # Información del disparo
    valor_actual = fields.FloatField()
    mensaje = fields.TextField()
    
    # Estado
    enviada = fields.BooleanField(default=False)
    canales_enviados = fields.JSONField(default=list)
    
    # Timestamp
    disparada_en = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "historial_alertas"
        indexes = [
            ("disparada_en",),
            ("enviada",),
        ]
    
    def __str__(self):
        return f"Alerta {self.alerta.nombre} - {self.valor_actual}"