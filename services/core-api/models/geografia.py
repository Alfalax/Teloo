"""
Geographic support models for TeLOO V3
Handles metropolitan areas, logistics hubs, and advisor evaluation temp data
"""

from tortoise import fields
from decimal import Decimal
from .base import BaseModel
from .enums import CanalNotificacion


class Municipio(BaseModel):
    """
    Municipios de Colombia con información geográfica unificada
    Importados desde archivo Excel DIVIPOLA_Municipios.xlsx
    Incluye: departamento, área metropolitana (si aplica) y hub logístico
    """
    
    codigo_dane = fields.CharField(max_length=10, unique=True, null=True)
    municipio = fields.CharField(max_length=100)  # Nombre original
    municipio_norm = fields.CharField(max_length=100, index=True)  # Normalizado (UPPERCASE, sin tildes)
    departamento = fields.CharField(max_length=100, index=True)
    area_metropolitana = fields.CharField(max_length=100, null=True, index=True)  # NULL si no pertenece
    hub_logistico = fields.CharField(max_length=100, index=True)
    
    class Meta:
        table = "municipios"
        
    def __str__(self):
        return f"{self.municipio} - {self.departamento}"
        
    @staticmethod
    def normalizar_ciudad(ciudad: str) -> str:
        """
        Normaliza nombre de ciudad: uppercase, sin tildes, trim
        """
        import unicodedata
        
        # Convertir a uppercase y trim
        ciudad_norm = ciudad.strip().upper()
        
        # Remover tildes y caracteres especiales
        ciudad_norm = unicodedata.normalize('NFD', ciudad_norm)
        ciudad_norm = ''.join(
            char for char in ciudad_norm 
            if unicodedata.category(char) != 'Mn'
        )
        
        return ciudad_norm
        
    @classmethod
    async def get_by_ciudad(cls, ciudad: str):
        """
        Obtiene el municipio por nombre (normalizado)
        """
        ciudad_norm = cls.normalizar_ciudad(ciudad)
        return await cls.filter(municipio_norm=ciudad_norm).first()
        
    @classmethod
    async def get_municipios_area_metropolitana(cls, ciudad: str) -> list:
        """
        Obtiene todos los municipios del área metropolitana de una ciudad
        """
        municipio = await cls.get_by_ciudad(ciudad)
        if not municipio or not municipio.area_metropolitana:
            return []
            
        # Obtener todos los municipios de esa área metropolitana
        municipios = await cls.filter(
            area_metropolitana=municipio.area_metropolitana
        ).values_list('municipio_norm', flat=True)
        
        return list(municipios)
        
    @classmethod
    async def get_municipios_hub(cls, ciudad: str) -> list:
        """
        Obtiene todos los municipios del mismo hub logístico de una ciudad
        """
        municipio = await cls.get_by_ciudad(ciudad)
        if not municipio:
            return []
            
        # Obtener todos los municipios de ese hub
        municipios = await cls.filter(
            hub_logistico=municipio.hub_logistico
        ).values_list('municipio_norm', flat=True)
        
        return list(municipios)
        
    @classmethod
    async def get_hub_ciudad(cls, ciudad: str) -> str:
        """
        Obtiene el hub asignado a una ciudad específica
        """
        municipio = await cls.get_by_ciudad(ciudad)
        return municipio.hub_logistico if municipio else None


class EvaluacionAsesorTemp(BaseModel):
    """
    Evaluación temporal de asesores para cálculos de escalamiento
    Se crea para cada solicitud y se usa para clasificar por niveles
    """
    
    solicitud = fields.ForeignKeyField(
        "models.Solicitud",
        related_name="evaluaciones_asesores",
        on_delete=fields.CASCADE
    )
    asesor = fields.ForeignKeyField(
        "models.Asesor",
        related_name="evaluaciones_temp",
        on_delete=fields.CASCADE
    )
    
    # Variables del algoritmo de escalamiento (escala 1-5)
    proximidad = fields.DecimalField(max_digits=3, decimal_places=1)  # 3.0, 3.5, 4.0, 5.0
    actividad_reciente_5 = fields.DecimalField(max_digits=3, decimal_places=2)  # 1.00-5.00
    desempeno_historico_5 = fields.DecimalField(max_digits=3, decimal_places=2)  # 1.00-5.00
    nivel_confianza = fields.DecimalField(max_digits=3, decimal_places=1)  # 1.0-5.0
    
    # Puntaje total calculado
    puntaje_total = fields.DecimalField(max_digits=4, decimal_places=2)
    
    # Clasificación por nivel
    nivel_entrega = fields.IntField()  # 1-5
    canal = fields.CharEnumField(CanalNotificacion)  # WHATSAPP, PUSH
    tiempo_espera_min = fields.IntField()  # Tiempo de espera configurado para el nivel
    
    # Información de proximidad geográfica
    criterio_proximidad = fields.CharField(max_length=50)  # "misma_ciudad", "area_metropolitana", "hub_logistico"
    ciudad_asesor = fields.CharField(max_length=100)
    ciudad_solicitud = fields.CharField(max_length=100)
    
    # Timestamps de control
    fecha_notificacion = fields.DatetimeField(null=True)
    fecha_timeout = fields.DatetimeField(null=True)
    
    # Metadata de cálculo
    detalles_calculo = fields.JSONField(default=dict)
    
    class Meta:
        table = "evaluaciones_asesores_temp"
        unique_together = (("solicitud", "asesor"),)
        
    def __str__(self):
        return f"Eval {self.asesor.usuario.nombre_completo} - Nivel {self.nivel_entrega} - Puntaje {self.puntaje_total}"
        
    @property
    def descripcion_proximidad(self) -> str:
        """Retorna descripción legible del criterio de proximidad"""
        criterios = {
            "misma_ciudad": "Misma ciudad",
            "area_metropolitana": "Área metropolitana",
            "hub_logistico": "Hub logístico"
        }
        return criterios.get(self.criterio_proximidad, "Desconocido")
        
    @property
    def pesos_aplicados(self) -> dict:
        """Retorna los pesos aplicados en el cálculo (desde detalles_calculo)"""
        return self.detalles_calculo.get('pesos', {})
        
    def is_notificado(self) -> bool:
        """Verifica si ya fue notificado"""
        return self.fecha_notificacion is not None
        
    def is_timeout_vencido(self) -> bool:
        """Verifica si el timeout ya venció"""
        if not self.fecha_timeout:
            return False
        from datetime import datetime
        return datetime.now() > self.fecha_timeout
        
    @classmethod
    async def get_asesores_por_nivel(cls, solicitud_id: str, nivel: int) -> list:
        """
        Obtiene todos los asesores de un nivel específico para una solicitud
        """
        evaluaciones = await cls.filter(
            solicitud_id=solicitud_id,
            nivel_entrega=nivel
        ).prefetch_related('asesor__usuario')
        
        return [eval.asesor for eval in evaluaciones]
        
    @classmethod
    async def get_estadisticas_niveles(cls, solicitud_id: str) -> dict:
        """
        Obtiene estadísticas de distribución por niveles
        """
        from tortoise.functions import Count
        
        stats = await cls.filter(
            solicitud_id=solicitud_id
        ).group_by('nivel_entrega').annotate(
            count=Count('id')
        ).values('nivel_entrega', 'count')
        
        return {stat['nivel_entrega']: stat['count'] for stat in stats}