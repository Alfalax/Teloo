"""
Oferta, OfertaDetalle, AdjudicacionRepuesto and Evaluacion models for TeLOO V3
"""

from tortoise import fields
from decimal import Decimal
from .base import BaseModel
from .enums import EstadoOferta, OrigenOferta


def validate_precio_unitario(value: Decimal) -> Decimal:
    """Validate price range 1,000 - 50,000,000 COP"""
    if not (1000 <= value <= 50000000):
        raise ValueError("Precio unitario debe estar entre 1,000 y 50,000,000 COP")
    return value


def validate_garantia_meses(value: int) -> int:
    """Validate warranty range 1-60 months"""
    if not (1 <= value <= 60):
        raise ValueError("Garantía debe estar entre 1 y 60 meses")
    return value


def validate_tiempo_entrega(value: int) -> int:
    """Validate delivery time 0-90 days"""
    if not (0 <= value <= 90):
        raise ValueError("Tiempo de entrega debe estar entre 0 y 90 días")
    return value


class Oferta(BaseModel):
    """
    Oferta realizada por un asesor para una solicitud específica
    """
    
    solicitud = fields.ForeignKeyField(
        "models.Solicitud",
        related_name="ofertas",
        on_delete=fields.CASCADE
    )
    asesor = fields.ForeignKeyField(
        "models.Asesor",
        related_name="ofertas",
        on_delete=fields.CASCADE
    )
    
    # Información general de la oferta
    tiempo_entrega_dias = fields.IntField(validators=[validate_tiempo_entrega])
    observaciones = fields.TextField(null=True)
    
    # Estado y control
    estado = fields.CharEnumField(EstadoOferta, default=EstadoOferta.ENVIADA)
    origen = fields.CharEnumField(OrigenOferta, default=OrigenOferta.FORM)
    
    # Métricas calculadas
    monto_total = fields.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0
    )
    cantidad_repuestos = fields.IntField(default=0)
    cobertura_porcentaje = fields.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0
    )  # Porcentaje de repuestos cubiertos
    
    # Puntaje de evaluación (calculado durante evaluación)
    puntaje_total = fields.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True
    )
    
    # Timestamps de control
    fecha_vista_asesor = fields.DatetimeField(null=True)
    fecha_evaluacion = fields.DatetimeField(null=True)
    fecha_expiracion = fields.DatetimeField(null=True)
    
    # Relaciones
    detalles = fields.ReverseRelation["OfertaDetalle"]
    adjudicaciones = fields.ReverseRelation["AdjudicacionRepuesto"]
    
    class Meta:
        table = "ofertas"
        
    def __str__(self):
        return f"Oferta {self.id} - {self.asesor.usuario.nombre_completo} - {self.estado}"
        
    @property
    def codigo_oferta(self) -> str:
        """Genera código legible para la oferta"""
        return f"OF-{str(self.id)[:8].upper()}"
        
    def is_activa(self) -> bool:
        """Verifica si la oferta está activa (puede ser evaluada)"""
        return self.estado == EstadoOferta.ENVIADA
        
    def is_ganadora(self) -> bool:
        """Verifica si la oferta fue seleccionada como ganadora"""
        return self.estado == EstadoOferta.GANADORA
        
    def is_aceptada_cliente(self) -> bool:
        """Verifica si el cliente aceptó la oferta"""
        return self.estado == EstadoOferta.ACEPTADA
        
    async def calcular_monto_total(self) -> Decimal:
        """Calcula el monto total de la oferta"""
        detalles = await self.detalles.all()
        total = sum(
            detalle.precio_unitario * detalle.cantidad 
            for detalle in detalles
        )
        return Decimal(str(total))
        
    async def calcular_cobertura(self) -> Decimal:
        """Calcula el porcentaje de cobertura de repuestos"""
        # Cargar la solicitud si no está cargada
        if not hasattr(self, '_solicitud_id'):
            await self.fetch_related('solicitud')
        
        # Contar repuestos solicitados
        from models.solicitud import RepuestoSolicitado
        total_repuestos = await RepuestoSolicitado.filter(solicitud_id=self.solicitud_id).count()
        
        if total_repuestos == 0:
            return Decimal('0.00')
        
        # Contar detalles de la oferta
        repuestos_cubiertos = await OfertaDetalle.filter(oferta_id=self.id).count()
        cobertura = (repuestos_cubiertos / total_repuestos) * 100
        return Decimal(str(round(cobertura, 2)))


class OfertaDetalle(BaseModel):
    """
    Detalle específico de una oferta por repuesto
    """
    
    oferta = fields.ForeignKeyField(
        "models.Oferta",
        related_name="detalles",
        on_delete=fields.CASCADE
    )
    repuesto_solicitado = fields.ForeignKeyField(
        "models.RepuestoSolicitado",
        related_name="ofertas_detalle",
        on_delete=fields.CASCADE
    )
    
    # Información comercial
    precio_unitario = fields.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[validate_precio_unitario]
    )
    cantidad = fields.IntField(default=1)
    garantia_meses = fields.IntField(validators=[validate_garantia_meses])
    tiempo_entrega_dias = fields.IntField(validators=[validate_tiempo_entrega])
    
    # Información adicional del producto
    marca_repuesto = fields.CharField(max_length=100, null=True)
    modelo_repuesto = fields.CharField(max_length=100, null=True)
    origen_repuesto = fields.CharField(max_length=50, null=True)  # Original, Alterno, etc.
    
    # Observaciones específicas del repuesto
    observaciones = fields.TextField(null=True)
    
    # Puntaje individual (calculado durante evaluación)
    puntaje_precio = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    puntaje_tiempo = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    puntaje_garantia = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    puntaje_total = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    
    # Relaciones
    adjudicacion = fields.ReverseRelation["AdjudicacionRepuesto"]
    
    class Meta:
        table = "ofertas_detalle"
        unique_together = (("oferta", "repuesto_solicitado"),)
        
    def __str__(self):
        return f"Detalle: {self.repuesto_solicitado.nombre} - ${self.precio_unitario:,.0f}"
        
    @property
    def monto_total_detalle(self) -> Decimal:
        """Calcula el monto total de este detalle"""
        return self.precio_unitario * self.cantidad
        
    @property
    def descripcion_garantia(self) -> str:
        """Retorna descripción legible de la garantía"""
        if self.garantia_meses == 1:
            return "1 mes"
        elif self.garantia_meses < 12:
            return f"{self.garantia_meses} meses"
        else:
            años = self.garantia_meses // 12
            meses_restantes = self.garantia_meses % 12
            if meses_restantes == 0:
                return f"{años} año{'s' if años > 1 else ''}"
            else:
                return f"{años} año{'s' if años > 1 else ''} y {meses_restantes} mes{'es' if meses_restantes > 1 else ''}"
                
    @property
    def descripcion_entrega(self) -> str:
        """Retorna descripción legible del tiempo de entrega"""
        if self.tiempo_entrega_dias == 0:
            return "Inmediato"
        elif self.tiempo_entrega_dias == 1:
            return "1 día"
        else:
            return f"{self.tiempo_entrega_dias} días"


class AdjudicacionRepuesto(BaseModel):
    """
    Adjudicación de un repuesto específico a una oferta ganadora
    Permite ofertas mixtas donde diferentes repuestos van a diferentes asesores
    """
    
    solicitud = fields.ForeignKeyField(
        "models.Solicitud",
        related_name="adjudicaciones",
        on_delete=fields.CASCADE
    )
    oferta = fields.ForeignKeyField(
        "models.Oferta",
        related_name="adjudicaciones",
        on_delete=fields.CASCADE
    )
    repuesto_solicitado = fields.ForeignKeyField(
        "models.RepuestoSolicitado",
        related_name="adjudicaciones",
        on_delete=fields.CASCADE
    )
    
    # Información de la adjudicación
    puntaje_obtenido = fields.DecimalField(max_digits=5, decimal_places=2)
    precio_adjudicado = fields.DecimalField(max_digits=12, decimal_places=2)
    tiempo_entrega_adjudicado = fields.IntField()
    garantia_adjudicada = fields.IntField()
    cantidad_adjudicada = fields.IntField()
    
    # Información de la evaluación
    motivo_adjudicacion = fields.CharField(max_length=100, null=True)  # "mejor_puntaje", "unica_oferta", etc.
    cobertura_oferta = fields.DecimalField(max_digits=5, decimal_places=2)
    
    # Relación con el detalle específico
    oferta_detalle = fields.OneToOneField(
        "models.OfertaDetalle",
        related_name="adjudicacion",
        on_delete=fields.CASCADE
    )
    
    class Meta:
        table = "adjudicaciones_repuesto"
        unique_together = (("solicitud", "repuesto_solicitado"),)
        
    def __str__(self):
        return f"Adjudicación: {self.repuesto_solicitado.nombre} → {self.oferta.asesor.usuario.nombre_completo}"
        
    @property
    def monto_total_adjudicado(self) -> Decimal:
        """Calcula el monto total adjudicado"""
        return self.precio_adjudicado * self.cantidad_adjudicada
        
    @property
    def asesor_ganador(self):
        """Retorna el asesor que ganó este repuesto"""
        return self.oferta.asesor


class Evaluacion(BaseModel):
    """
    Registro de evaluación completa de una solicitud
    Para auditoría y trazabilidad del proceso
    """
    
    solicitud = fields.ForeignKeyField(
        "models.Solicitud",
        related_name="evaluaciones",
        on_delete=fields.CASCADE
    )
    
    # Información de la evaluación
    total_ofertas_evaluadas = fields.IntField()
    total_repuestos_adjudicados = fields.IntField()
    monto_total_adjudicado = fields.DecimalField(max_digits=15, decimal_places=2)
    
    # Configuración usada en la evaluación
    peso_precio = fields.DecimalField(max_digits=3, decimal_places=2)  # 0.50
    peso_tiempo = fields.DecimalField(max_digits=3, decimal_places=2)  # 0.35
    peso_garantia = fields.DecimalField(max_digits=3, decimal_places=2)  # 0.15
    cobertura_minima = fields.DecimalField(max_digits=3, decimal_places=2)  # 0.50
    
    # Métricas de la evaluación
    tiempo_evaluacion_ms = fields.IntField()  # Tiempo que tomó la evaluación
    ofertas_con_cobertura_suficiente = fields.IntField()
    ofertas_por_excepcion = fields.IntField()  # Adjudicadas por ser únicas
    
    # Resultado
    es_adjudicacion_mixta = fields.BooleanField(default=False)
    asesores_ganadores = fields.IntField()  # Número de asesores diferentes que ganaron
    
    # Metadata de la evaluación
    detalles_evaluacion = fields.JSONField(default=dict)
    
    class Meta:
        table = "evaluaciones"
        
    def __str__(self):
        return f"Evaluación {self.solicitud.codigo_solicitud} - {self.total_ofertas_evaluadas} ofertas"
        
    @property
    def duracion_evaluacion_seg(self) -> float:
        """Retorna la duración en segundos"""
        return self.tiempo_evaluacion_ms / 1000.0
        
    @property
    def tasa_adjudicacion(self) -> float:
        """Porcentaje de repuestos que fueron adjudicados"""
        total_repuestos = self.solicitud.total_repuestos
        if total_repuestos == 0:
            return 0.0
        return (self.total_repuestos_adjudicados / total_repuestos) * 100
        
    def is_evaluacion_exitosa(self) -> bool:
        """Verifica si la evaluación fue exitosa (al menos 1 adjudicación)"""
        return self.total_repuestos_adjudicados > 0