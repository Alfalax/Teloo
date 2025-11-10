"""
Analytics and metrics models for TeLOO V3
Handles historical data, events, metrics calculation, and system auditing
"""

from tortoise import fields
from tortoise.models import Model
from decimal import Decimal
from datetime import datetime, date
from .base import BaseModel
from .enums import (
    TipoPQR, PrioridadPQR, EstadoPQR, 
    TipoTransaccion, EstadoTransaccion,
    TipoEvento, EstadoAuditoria
)


class HistorialRespuestaOferta(BaseModel):
    """
    Historial de respuestas de asesores para cálculo de actividad reciente
    """
    
    asesor = fields.ForeignKeyField(
        "models.Asesor",
        related_name="historial_respuestas",
        on_delete=fields.CASCADE
    )
    solicitud = fields.ForeignKeyField(
        "models.Solicitud",
        related_name="historial_respuestas",
        on_delete=fields.CASCADE
    )
    
    # Timestamps de actividad
    fecha_envio = fields.DatetimeField()  # Cuándo se le envió la notificación
    fecha_vista = fields.DatetimeField(null=True)  # Cuándo vio la solicitud
    fecha_respuesta = fields.DatetimeField(null=True)  # Cuándo respondió (oferta o rechazo)
    
    # Información de respuesta
    respondio = fields.BooleanField(default=False)
    tiempo_respuesta_seg = fields.IntField(null=True)  # Tiempo en segundos desde envío hasta respuesta
    
    # Tipo de respuesta
    tipo_respuesta = fields.CharField(max_length=20, null=True)  # "oferta", "rechazo", "timeout"
    
    class Meta:
        table = "historial_respuestas_ofertas"
        
    def __str__(self):
        return f"Respuesta {self.asesor.usuario.nombre_completo} - {self.solicitud.codigo_solicitud}"
        
    @property
    def tiempo_respuesta_min(self) -> float:
        """Retorna tiempo de respuesta en minutos"""
        if self.tiempo_respuesta_seg:
            return self.tiempo_respuesta_seg / 60.0
        return 0.0
        
    def calcular_tiempo_respuesta(self):
        """Calcula y actualiza el tiempo de respuesta"""
        if self.fecha_respuesta and self.fecha_envio:
            delta = self.fecha_respuesta - self.fecha_envio
            self.tiempo_respuesta_seg = int(delta.total_seconds())


class OfertaHistorica(BaseModel):
    """
    Historial de ofertas para cálculo de desempeño histórico
    """
    
    asesor = fields.ForeignKeyField(
        "models.Asesor",
        related_name="ofertas_historicas",
        on_delete=fields.CASCADE
    )
    solicitud = fields.ForeignKeyField(
        "models.Solicitud",
        related_name="ofertas_historicas",
        on_delete=fields.CASCADE
    )
    
    # Información de la oferta
    fecha = fields.DateField()
    monto_total = fields.DecimalField(max_digits=15, decimal_places=2)
    cantidad_repuestos = fields.IntField()
    tiempo_respuesta_seg = fields.IntField()
    
    # Resultados
    adjudicada = fields.BooleanField(default=False)  # Fue seleccionada como ganadora
    aceptada_cliente = fields.BooleanField(default=False)  # Cliente aceptó la oferta
    entrega_exitosa = fields.BooleanField(default=False)  # Se completó la entrega
    
    # Información geográfica
    ciudad_solicitud = fields.CharField(max_length=100)
    ciudad_asesor = fields.CharField(max_length=100)
    
    # Metadata adicional
    metadata_oferta = fields.JSONField(default=dict)
    
    class Meta:
        table = "ofertas_historicas"
        
    def __str__(self):
        return f"Histórica {self.asesor.usuario.nombre_completo} - {self.fecha}"
        
    @property
    def fue_exitosa(self) -> bool:
        """Verifica si la oferta fue completamente exitosa"""
        return self.adjudicada and self.aceptada_cliente and self.entrega_exitosa


class AuditoriaTienda(BaseModel):
    """
    Auditorías de tiendas/asesores para nivel de confianza
    """
    
    asesor = fields.ForeignKeyField(
        "models.Asesor",
        related_name="auditorias_tienda",
        on_delete=fields.CASCADE
    )
    auditor = fields.ForeignKeyField(
        "models.Usuario",
        related_name="auditorias_realizadas",
        on_delete=fields.SET_NULL,
        null=True
    )
    
    # Información de la auditoría
    fecha_revision = fields.DatetimeField()
    estado = fields.CharEnumField(EstadoAuditoria)
    puntaje_confianza = fields.DecimalField(max_digits=3, decimal_places=1)  # 1.0-5.0
    
    # Detalles de la auditoría
    observaciones = fields.TextField(null=True)
    criterios_evaluados = fields.JSONField(default=dict)  # Criterios específicos evaluados
    
    # Vigencia
    fecha_vencimiento = fields.DatetimeField(null=True)  # Cuándo vence esta auditoría
    
    class Meta:
        table = "auditorias_tiendas"
        
    def __str__(self):
        return f"Auditoría {self.asesor.usuario.nombre_completo} - {self.puntaje_confianza}"
        
    def is_vigente(self) -> bool:
        """Verifica si la auditoría está vigente"""
        if not self.fecha_vencimiento:
            return True
        return datetime.now() < self.fecha_vencimiento
        
    def dias_hasta_vencimiento(self) -> int:
        """Días hasta que venza la auditoría"""
        if not self.fecha_vencimiento:
            return 999  # Sin vencimiento
        delta = self.fecha_vencimiento - datetime.now()
        return max(0, delta.days)


class EventoSistema(BaseModel):
    """
    Eventos del sistema para analytics en tiempo real
    """
    
    # Información del evento
    tipo_evento = fields.CharEnumField(TipoEvento)
    entidad = fields.CharField(max_length=50)  # "solicitud", "oferta", "cliente", etc.
    entidad_id = fields.UUIDField()
    
    # Datos del evento
    datos_evento = fields.JSONField(default=dict)
    
    # Información del usuario (si aplica)
    usuario = fields.ForeignKeyField(
        "models.Usuario",
        related_name="eventos_generados",
        on_delete=fields.SET_NULL,
        null=True
    )
    ip_address = fields.CharField(max_length=45, null=True)
    user_agent = fields.TextField(null=True)
    
    # Información adicional
    session_id = fields.CharField(max_length=100, null=True)
    
    class Meta:
        table = "eventos_sistema"
        
    def __str__(self):
        return f"Evento {self.tipo_evento} - {self.entidad}:{self.entidad_id}"


class MetricaCalculada(BaseModel):
    """
    Cache de métricas calculadas para dashboards
    """
    
    # Identificación de la métrica
    nombre_metrica = fields.CharField(max_length=100)
    periodo = fields.CharField(max_length=20)  # "diario", "semanal", "mensual", "tiempo_real"
    fecha_periodo = fields.DateField()
    
    # Valores calculados
    valor_numerico = fields.DecimalField(max_digits=15, decimal_places=4, null=True)
    valor_json = fields.JSONField(default=dict)  # Para métricas complejas
    
    # Metadata del cálculo
    calculado_at = fields.DatetimeField(auto_now=True)
    tiempo_calculo_ms = fields.IntField(null=True)
    version_algoritmo = fields.CharField(max_length=10, default="1.0")
    
    # Filtros aplicados (para métricas segmentadas)
    filtros = fields.JSONField(default=dict)
    
    class Meta:
        table = "metricas_calculadas"
        unique_together = (("nombre_metrica", "periodo", "fecha_periodo", "filtros"),)
        
    def __str__(self):
        return f"Métrica {self.nombre_metrica} - {self.periodo} - {self.fecha_periodo}"
        
    def is_cache_valido(self, ttl_minutes: int = 60) -> bool:
        """Verifica si el cache sigue siendo válido"""
        if not self.calculado_at:
            return False
        delta = datetime.now() - self.calculado_at
        return delta.total_seconds() < (ttl_minutes * 60)


class Transaccion(BaseModel):
    """
    Transacciones financieras para métricas financieras
    """
    
    # Relaciones
    solicitud = fields.ForeignKeyField(
        "models.Solicitud",
        related_name="transacciones",
        on_delete=fields.CASCADE,
        null=True
    )
    asesor = fields.ForeignKeyField(
        "models.Asesor",
        related_name="transacciones",
        on_delete=fields.CASCADE,
        null=True
    )
    
    # Información de la transacción
    tipo = fields.CharEnumField(TipoTransaccion)
    monto = fields.DecimalField(max_digits=15, decimal_places=2)
    estado = fields.CharEnumField(EstadoTransaccion, default=EstadoTransaccion.PENDIENTE)
    
    # Timestamps
    fecha_transaccion = fields.DatetimeField()
    fecha_completada = fields.DatetimeField(null=True)
    
    # Referencias externas
    referencia_externa = fields.CharField(max_length=100, null=True)
    gateway_pago = fields.CharField(max_length=50, null=True)
    
    # Metadata adicional
    metadata_json = fields.JSONField(default=dict)
    
    class Meta:
        table = "transacciones"
        
    def __str__(self):
        return f"Transacción {self.tipo} - ${self.monto:,.0f} - {self.estado}"


class PQR(BaseModel):
    """
    Peticiones, Quejas y Reclamos para métricas de satisfacción
    """
    
    cliente = fields.ForeignKeyField(
        "models.Cliente",
        related_name="pqrs",
        on_delete=fields.CASCADE
    )
    
    # Información de la PQR
    tipo = fields.CharEnumField(TipoPQR)
    prioridad = fields.CharEnumField(PrioridadPQR, default=PrioridadPQR.MEDIA)
    estado = fields.CharEnumField(EstadoPQR, default=EstadoPQR.ABIERTA)
    
    # Contenido
    resumen = fields.CharField(max_length=200)
    detalle = fields.TextField()
    
    # Respuesta
    respuesta = fields.TextField(null=True)
    fecha_respuesta = fields.DatetimeField(null=True)
    respondido_por = fields.ForeignKeyField(
        "models.Usuario",
        related_name="pqrs_respondidas",
        on_delete=fields.SET_NULL,
        null=True
    )
    
    # Métricas de tiempo
    tiempo_resolucion_horas = fields.IntField(null=True)
    
    class Meta:
        table = "pqrs"
        
    def __str__(self):
        return f"PQR {self.tipo} - {self.cliente.usuario.nombre_completo}"
        
    def calcular_tiempo_resolucion(self):
        """Calcula el tiempo de resolución en horas"""
        if self.fecha_respuesta:
            delta = self.fecha_respuesta - self.created_at
            self.tiempo_resolucion_horas = int(delta.total_seconds() / 3600)


class Notificacion(BaseModel):
    """
    Notificaciones del sistema para usuarios
    """
    
    usuario = fields.ForeignKeyField(
        "models.Usuario",
        related_name="notificaciones",
        on_delete=fields.CASCADE
    )
    
    # Contenido de la notificación
    tipo = fields.CharField(max_length=50)
    titulo = fields.CharField(max_length=200)
    mensaje = fields.TextField()
    
    # Estado
    leida = fields.BooleanField(default=False)
    fecha_leida = fields.DatetimeField(null=True)
    
    # Datos adicionales
    datos_adicionales = fields.JSONField(default=dict)
    url_accion = fields.CharField(max_length=500, null=True)
    
    class Meta:
        table = "notificaciones"
        
    def __str__(self):
        return f"Notificación {self.titulo} - {self.usuario.nombre_completo}"
        
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        self.leida = True
        self.fecha_leida = datetime.now()


class SesionUsuario(BaseModel):
    """
    Sesiones de usuario para analytics de uso
    """
    
    usuario = fields.ForeignKeyField(
        "models.Usuario",
        related_name="sesiones",
        on_delete=fields.CASCADE
    )
    
    # Información de la sesión
    inicio_sesion = fields.DatetimeField()
    fin_sesion = fields.DatetimeField(null=True)
    ip_address = fields.CharField(max_length=45)
    user_agent = fields.TextField()
    
    # Métricas de actividad
    duracion_seg = fields.IntField(null=True)
    acciones_realizadas = fields.IntField(default=0)
    paginas_visitadas = fields.IntField(default=0)
    
    # Información adicional
    dispositivo = fields.CharField(max_length=50, null=True)
    navegador = fields.CharField(max_length=50, null=True)
    
    class Meta:
        table = "sesiones_usuarios"
        
    def __str__(self):
        return f"Sesión {self.usuario.nombre_completo} - {self.inicio_sesion}"
        
    def calcular_duracion(self):
        """Calcula la duración de la sesión"""
        if self.fin_sesion:
            delta = self.fin_sesion - self.inicio_sesion
            self.duracion_seg = int(delta.total_seconds())


class LogAuditoria(BaseModel):
    """
    Logs de auditoría para trazabilidad completa
    """
    
    # Actor que realizó la acción
    actor = fields.ForeignKeyField(
        "models.Usuario",
        related_name="acciones_auditoria",
        on_delete=fields.SET_NULL,
        null=True
    )
    
    # Información de la acción
    accion = fields.CharField(max_length=100)  # "crear", "actualizar", "eliminar", etc.
    entidad = fields.CharField(max_length=50)  # "solicitud", "oferta", "asesor", etc.
    entidad_id = fields.UUIDField()
    
    # Cambios realizados
    diff_json = fields.JSONField(default=dict)  # Diferencias antes/después
    
    # Información adicional
    ip_address = fields.CharField(max_length=45, null=True)
    user_agent = fields.TextField(null=True)
    
    # Timestamp preciso
    ts = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "logs_auditoria"
        
    def __str__(self):
        actor_name = self.actor.nombre_completo if self.actor else "Sistema"
        return f"Auditoría {actor_name} - {self.accion} {self.entidad}:{self.entidad_id}"


class ParametroConfig(Model):
    """
    Parámetros de configuración del sistema
    """
    
    # Clave única del parámetro
    clave = fields.CharField(max_length=100, pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # Valor del parámetro (JSON para flexibilidad)
    valor_json = fields.JSONField()
    
    # Metadata de validación (min, max, default, unit, description)
    metadata_json = fields.JSONField(null=True)
    
    # Metadata
    descripcion = fields.TextField(null=True)
    categoria = fields.CharField(max_length=50, null=True)  # "escalamiento", "evaluacion", etc.
    
    # Control de cambios
    modificado_por = fields.ForeignKeyField(
        "models.Usuario",
        related_name="configuraciones_modificadas",
        on_delete=fields.SET_NULL,
        null=True
    )
    
    class Meta:
        table = "parametros_config"
        
    def __str__(self):
        return f"Config {self.clave}: {self.valor_json}"
        
    @classmethod
    async def get_valor(cls, clave: str, default=None):
        """Obtiene el valor de un parámetro de configuración"""
        param = await cls.filter(clave=clave).first()
        return param.valor_json if param else default
        
    @classmethod
    async def set_valor(cls, clave: str, valor, usuario=None, descripcion=None):
        """Establece el valor de un parámetro de configuración"""
        param, created = await cls.get_or_create(
            clave=clave,
            defaults={
                "valor_json": valor,
                "descripcion": descripcion,
                "modificado_por": usuario
            }
        )
        
        if not created:
            param.valor_json = valor
            param.modificado_por = usuario
            if descripcion:
                param.descripcion = descripcion
            await param.save()
            
        return param