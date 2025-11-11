"""
User, Cliente and Asesor models for TeLOO V3
"""

from tortoise import fields
from tortoise.validators import RegexValidator
import re
from decimal import Decimal
from .base import BaseModel
from .enums import RolUsuario, EstadoUsuario, EstadoAsesor


# Validators
def validate_colombian_phone(value: str) -> str:
    """Validate Colombian phone number format +57XXXXXXXXXX"""
    pattern = r'^\+57[0-9]{10}$'
    if not re.match(pattern, value):
        raise ValueError("Teléfono debe tener formato colombiano +57XXXXXXXXXX")
    return value


def validate_email(value: str) -> str:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, value):
        raise ValueError("Email debe tener formato válido")
    return value


class Usuario(BaseModel):
    """
    Usuario base del sistema
    Maneja autenticación y información básica
    """
    
    email = fields.CharField(
        max_length=255, 
        unique=True,
        validators=[validate_email]
    )
    password_hash = fields.CharField(max_length=255)
    nombre = fields.CharField(max_length=100)
    apellido = fields.CharField(max_length=100)
    telefono = fields.CharField(
        max_length=15,
        validators=[validate_colombian_phone]
    )
    rol = fields.CharEnumField(RolUsuario, default=RolUsuario.CLIENT)
    estado = fields.CharEnumField(EstadoUsuario, default=EstadoUsuario.ACTIVO)
    ultimo_login = fields.DatetimeField(null=True)
    
    # Relaciones
    cliente = fields.ReverseRelation["Cliente"]
    asesor = fields.ReverseRelation["Asesor"]
    
    class Meta:
        table = "usuarios"
        
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.email})"
        
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"
        
    def is_active(self) -> bool:
        return self.estado == EstadoUsuario.ACTIVO


class Cliente(BaseModel):
    """
    Cliente que solicita repuestos a través de WhatsApp
    """
    
    usuario = fields.OneToOneField(
        "models.Usuario", 
        related_name="cliente",
        on_delete=fields.CASCADE
    )
    
    # Ubicación geográfica - FUENTE ÚNICA DE VERDAD
    municipio = fields.ForeignKeyField(
        "models.Municipio",
        related_name="clientes",
        on_delete=fields.RESTRICT,
        description="Municipio del cliente (FK a tabla municipios - fuente única de verdad)"
    )
    
    # Campos de texto para display (NO usar para lógica de negocio)
    ciudad = fields.CharField(
        max_length=100,
        description="Nombre de ciudad para display (NO usar para lógica)"
    )
    departamento = fields.CharField(
        max_length=100,
        description="Nombre de departamento para display (NO usar para lógica)"
    )
    
    direccion = fields.TextField(null=True)
    
    # Métricas del cliente
    total_solicitudes = fields.IntField(default=0)
    total_aceptadas = fields.IntField(default=0)
    monto_total_compras = fields.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Relaciones
    solicitudes = fields.ReverseRelation["Solicitud"]
    pqrs = fields.ReverseRelation["PQR"]
    
    class Meta:
        table = "clientes"
        
    def __str__(self):
        return f"Cliente: {self.usuario.nombre_completo} - {self.ciudad}"
        
    @property
    def tasa_conversion(self) -> float:
        """Calcula la tasa de conversión del cliente"""
        if self.total_solicitudes == 0:
            return 0.0
        return (self.total_aceptadas / self.total_solicitudes) * 100


class Asesor(BaseModel):
    """
    Asesor/Proveedor que ofrece repuestos
    """
    
    usuario = fields.OneToOneField(
        "models.Usuario",
        related_name="asesor", 
        on_delete=fields.CASCADE
    )
    
    # Ubicación geográfica - FUENTE ÚNICA DE VERDAD
    municipio = fields.ForeignKeyField(
        "models.Municipio",
        related_name="asesores",
        on_delete=fields.RESTRICT,
        description="Municipio del asesor (FK a tabla municipios - fuente única de verdad)"
    )
    
    # Campos de texto para display (NO usar para lógica de negocio)
    ciudad = fields.CharField(
        max_length=100,
        description="Nombre de ciudad para display (NO usar para lógica)"
    )
    departamento = fields.CharField(
        max_length=100,
        description="Nombre de departamento para display (NO usar para lógica)"
    )
    
    punto_venta = fields.CharField(max_length=200)
    direccion_punto_venta = fields.TextField(null=True)
    
    # Métricas de escalamiento
    confianza = fields.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        default=Decimal('3.0')
    )  # 1.0-5.0
    nivel_actual = fields.IntField(default=3)  # 1-5
    actividad_reciente_pct = fields.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00')
    )  # 0-100
    desempeno_historico_pct = fields.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00')
    )  # 0-100
    
    # Estado del asesor
    estado = fields.CharEnumField(EstadoAsesor, default=EstadoAsesor.ACTIVO)
    
    # Métricas de negocio
    total_ofertas = fields.IntField(default=0)
    ofertas_ganadoras = fields.IntField(default=0)
    monto_total_ventas = fields.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Relaciones
    ofertas = fields.ReverseRelation["Oferta"]
    auditorias_tienda = fields.ReverseRelation["AuditoriaTienda"]
    historial_respuestas = fields.ReverseRelation["HistorialRespuestaOferta"]
    ofertas_historicas = fields.ReverseRelation["OfertaHistorica"]
    evaluaciones_temp = fields.ReverseRelation["EvaluacionAsesorTemp"]
    
    class Meta:
        table = "asesores"
        
    def __str__(self):
        return f"Asesor: {self.usuario.nombre_completo} - {self.punto_venta}"
        
    @property
    def tasa_adjudicacion(self) -> float:
        """Calcula la tasa de adjudicación del asesor"""
        if self.total_ofertas == 0:
            return 0.0
        return (self.ofertas_ganadoras / self.total_ofertas) * 100
        
    def is_active(self) -> bool:
        """Verifica si el asesor está activo"""
        return (
            self.estado == EstadoAsesor.ACTIVO and 
            self.usuario.estado == EstadoUsuario.ACTIVO
        )
        
    def cumple_confianza_minima(self, minima: float = 2.0) -> bool:
        """Verifica si cumple el nivel mínimo de confianza"""
        return float(self.confianza) >= minima