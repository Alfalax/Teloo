"""
Solicitud and RepuestoSolicitado models for TeLOO V3
"""

from tortoise import fields
from datetime import datetime
from .base import BaseModel
from .enums import EstadoSolicitud


def validate_anio_vehiculo(value: int) -> int:
    """Validate vehicle year between 1980-2025"""
    current_year = datetime.now().year
    if not (1980 <= value <= 2025):
        raise ValueError(f"Año del vehículo debe estar entre 1980 y 2025")
    return value


class Solicitud(BaseModel):
    """
    Solicitud de repuestos realizada por un cliente
    """
    
    cliente = fields.ForeignKeyField(
        "models.Cliente",
        related_name="solicitudes",
        on_delete=fields.CASCADE
    )
    
    # Estado y control de flujo
    estado = fields.CharEnumField(EstadoSolicitud, default=EstadoSolicitud.ABIERTA)
    nivel_actual = fields.IntField(default=1)  # 1-5 para escalamiento
    
    # Ubicación geográfica - FUENTE ÚNICA DE VERDAD
    municipio = fields.ForeignKeyField(
        "models.Municipio",
        related_name="solicitudes",
        on_delete=fields.RESTRICT,
        description="Municipio de origen (FK a tabla municipios - fuente única de verdad)"
    )
    
    # Campos de texto para display (NO usar para lógica de negocio)
    ciudad_origen = fields.CharField(
        max_length=100,
        description="Nombre de ciudad para display (NO usar para lógica)"
    )
    departamento_origen = fields.CharField(
        max_length=100,
        description="Nombre de departamento para display (NO usar para lógica)"
    )
    
    # Configuración de escalamiento
    ofertas_minimas_deseadas = fields.IntField(default=2)
    timeout_horas = fields.IntField(default=20)  # Timeout para expiración
    
    # Timestamps de control
    fecha_escalamiento = fields.DatetimeField(null=True)
    fecha_evaluacion = fields.DatetimeField(null=True)
    fecha_expiracion = fields.DatetimeField(null=True)
    
    # Metadata adicional (JSON para flexibilidad)
    metadata_json = fields.JSONField(default=dict)
    
    # Métricas calculadas
    total_repuestos = fields.IntField(default=0)
    monto_total_adjudicado = fields.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0
    )
    
    # Relaciones
    repuestos_solicitados = fields.ReverseRelation["RepuestoSolicitado"]
    ofertas = fields.ReverseRelation["Oferta"]
    adjudicaciones = fields.ReverseRelation["AdjudicacionRepuesto"]
    evaluaciones = fields.ReverseRelation["Evaluacion"]
    evaluaciones_asesores = fields.ReverseRelation["EvaluacionAsesorTemp"]
    
    class Meta:
        table = "solicitudes"
        
    def __str__(self):
        return f"Solicitud {self.id} - {self.estado} - {self.ciudad_origen}"
        
    @property
    def codigo_solicitud(self) -> str:
        """Genera código legible para la solicitud"""
        return f"SOL-{str(self.id)[:8].upper()}"
        
    def is_abierta(self) -> bool:
        """Verifica si la solicitud está abierta para recibir ofertas"""
        return self.estado == EstadoSolicitud.ABIERTA
        
    def is_evaluable(self) -> bool:
        """Verifica si la solicitud puede ser evaluada"""
        return self.estado in [EstadoSolicitud.ABIERTA, EstadoSolicitud.EVALUADA]
        
    def puede_escalar(self) -> bool:
        """Verifica si puede escalar al siguiente nivel"""
        return self.is_abierta() and self.nivel_actual < 5
        
    async def contar_ofertas_activas(self) -> int:
        """Cuenta ofertas en estado ENVIADA"""
        from .oferta import Oferta
        from .enums import EstadoOferta
        
        return await Oferta.filter(
            solicitud=self,
            estado=EstadoOferta.ENVIADA
        ).count()
        
    async def tiene_ofertas_minimas(self) -> bool:
        """Verifica si tiene el mínimo de ofertas deseadas"""
        count = await self.contar_ofertas_activas()
        return count >= self.ofertas_minimas_deseadas


class RepuestoSolicitado(BaseModel):
    """
    Repuesto específico solicitado dentro de una solicitud
    """
    
    solicitud = fields.ForeignKeyField(
        "models.Solicitud",
        related_name="repuestos_solicitados",
        on_delete=fields.CASCADE
    )
    
    # Información del repuesto
    nombre = fields.CharField(max_length=200)
    codigo = fields.CharField(max_length=50, null=True)  # Código interno si existe
    descripcion = fields.TextField(null=True)
    cantidad = fields.IntField(default=1)
    
    # Información del vehículo
    marca_vehiculo = fields.CharField(max_length=50)
    linea_vehiculo = fields.CharField(max_length=100)
    anio_vehiculo = fields.IntField(validators=[validate_anio_vehiculo])
    
    # Información adicional
    observaciones = fields.TextField(null=True)
    es_urgente = fields.BooleanField(default=False)
    
    # Metadata para información extraída por IA
    metadata_extraccion = fields.JSONField(default=dict)
    
    # Relaciones
    ofertas_detalle = fields.ReverseRelation["OfertaDetalle"]
    adjudicaciones = fields.ReverseRelation["AdjudicacionRepuesto"]
    
    class Meta:
        table = "repuestos_solicitados"
        
    def __str__(self):
        return f"{self.nombre} - {self.marca_vehiculo} {self.linea_vehiculo} {self.anio_vehiculo}"
        
    @property
    def vehiculo_completo(self) -> str:
        """Retorna descripción completa del vehículo"""
        return f"{self.marca_vehiculo} {self.linea_vehiculo} {self.anio_vehiculo}"
        
    @property
    def descripcion_completa(self) -> str:
        """Retorna descripción completa del repuesto"""
        desc = f"{self.nombre}"
        if self.codigo:
            desc += f" (Código: {self.codigo})"
        if self.cantidad > 1:
            desc += f" x{self.cantidad}"
        return desc
        
    def is_vehiculo_reciente(self) -> bool:
        """Verifica si el vehículo es de los últimos 10 años"""
        current_year = datetime.now().year
        return (current_year - self.anio_vehiculo) <= 10