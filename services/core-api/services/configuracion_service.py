"""
Configuration Service for TeLOO V3
Manages system parameters with validation and Redis caching
"""

from typing import Dict, Any, Optional
from decimal import Decimal
import logging
from fastapi import HTTPException
from models.analytics import ParametroConfig
from models.user import Usuario

logger = logging.getLogger(__name__)


class ConfiguracionService:
    """
    Service for managing system configuration parameters
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        'pesos_escalamiento': {
            'proximidad': 0.40,
            'actividad': 0.25,
            'desempeno': 0.20,
            'confianza': 0.15
        },
        'umbrales_niveles': {
            'nivel1_min': 4.5,
            'nivel2_min': 4.0,
            'nivel3_min': 3.5,
            'nivel4_min': 3.0
        },
        'tiempos_espera_nivel': {
            1: 15,  # minutos
            2: 20,
            3: 25,
            4: 30,
            5: 35
        },
        'canales_por_nivel': {
            1: 'WHATSAPP',
            2: 'WHATSAPP',
            3: 'PUSH',
            4: 'PUSH',
            5: 'PUSH'
        },
        'pesos_evaluacion_ofertas': {
            'precio': 0.50,
            'tiempo_entrega': 0.35,
            'garantia': 0.15
        },
        'parametros_generales': {
            'ofertas_minimas_deseadas': 2,
            'precio_minimo_oferta': 1000,
            'precio_maximo_oferta': 50000000,
            'garantia_minima_meses': 1,
            'garantia_maxima_meses': 60,
            'tiempo_entrega_minimo_dias': 0,
            'tiempo_entrega_maximo_dias': 90,
            'cobertura_minima_porcentaje': 50,
            'timeout_evaluacion_segundos': 5,
            'vigencia_auditoria_dias': 30,
            'timeout_ofertas_horas': 20,
            'notificacion_expiracion_horas_antes': 2,
            'confianza_minima_operar': 2.0,
            'periodo_actividad_reciente_dias': 30,
            'periodo_desempeno_historico_meses': 6,
            'fallback_actividad_asesores_nuevos': 3.0,
            'fallback_desempeno_asesores_nuevos': 3.0,
            'puntaje_defecto_asesores_nuevos': 50
        }
    }
    
    @staticmethod
    async def get_config(categoria: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene configuración del sistema
        
        Args:
            categoria: Categoría específica (opcional)
            
        Returns:
            Dict: Configuración completa o de categoría específica
        """
        
        if categoria:
            # Para parametros_generales, construir desde registros individuales
            if categoria == 'parametros_generales':
                parametros = {}
                default_params = ConfiguracionService.DEFAULT_CONFIG.get('parametros_generales', {})
                for key in default_params.keys():
                    valor = await ParametroConfig.get_valor(key, default_params.get(key))
                    parametros[key] = valor
                return parametros
            else:
                # Obtener configuración específica
                config = await ParametroConfig.get_valor(
                    categoria, 
                    ConfiguracionService.DEFAULT_CONFIG.get(categoria, {})
                )
                return config
        else:
            # Obtener toda la configuración
            config_completa = {}
            for cat, default_val in ConfiguracionService.DEFAULT_CONFIG.items():
                if cat == 'parametros_generales':
                    # Construir parametros_generales desde registros individuales
                    parametros = {}
                    for key in default_val.keys():
                        valor = await ParametroConfig.get_valor(key, default_val.get(key))
                        parametros[key] = valor
                    config_completa[cat] = parametros
                else:
                    config_completa[cat] = await ParametroConfig.get_valor(cat, default_val)
            
            return config_completa
    
    @staticmethod
    async def update_config(
        categoria: str,
        nuevos_valores: Dict[str, Any],
        usuario: Optional[Usuario] = None
    ) -> Dict[str, Any]:
        """
        Actualiza configuración del sistema con validaciones
        
        Uses atomic transaction when updating multiple parameters
        to ensure all changes are committed together.
        
        Args:
            categoria: Categoría de configuración
            nuevos_valores: Nuevos valores a establecer
            usuario: Usuario que realiza el cambio
            
        Returns:
            Dict: Configuración actualizada
            
        Raises:
            HTTPException: Si la validación falla
        """
        
        # Validar categoría
        if categoria not in ConfiguracionService.DEFAULT_CONFIG:
            raise HTTPException(
                status_code=400,
                detail=f"Categoría '{categoria}' no válida"
            )
        
        # Validar según categoría
        if categoria == 'pesos_escalamiento':
            ConfiguracionService._validar_pesos_escalamiento(nuevos_valores)
        elif categoria == 'umbrales_niveles':
            ConfiguracionService._validar_umbrales_niveles(nuevos_valores)
        elif categoria == 'pesos_evaluacion_ofertas':
            ConfiguracionService._validar_pesos_evaluacion(nuevos_valores)
        elif categoria == 'tiempos_espera_nivel':
            ConfiguracionService._validar_tiempos_espera(nuevos_valores)
        elif categoria == 'canales_por_nivel':
            ConfiguracionService._validar_canales_nivel(nuevos_valores)
        elif categoria == 'parametros_generales':
            ConfiguracionService._validar_parametros_generales(nuevos_valores)
            # Para parametros_generales, guardar cada parámetro individualmente con transacción
            from tortoise.transactions import in_transaction
            async with in_transaction() as conn:
                for clave, valor in nuevos_valores.items():
                    # Get or create with transaction
                    param = await ParametroConfig.filter(clave=clave).using_db(conn).first()
                    if param:
                        param.valor_json = valor
                        param.modificado_por = usuario
                        param.descripcion = f"Parámetro {clave} actualizado"
                        await param.save(using_db=conn)
                    else:
                        await ParametroConfig.create(
                            clave=clave,
                            valor_json=valor,
                            descripcion=f"Parámetro {clave} actualizado",
                            modificado_por=usuario,
                            using_db=conn
                        )
            logger.info(f"Parámetros generales actualizados por {usuario.nombre_completo if usuario else 'Sistema'}")
            return nuevos_valores
        
        # Guardar configuración (para otras categorías que usan JSON)
        await ParametroConfig.set_valor(
            categoria,
            nuevos_valores,
            usuario,
            f"Configuración de {categoria} actualizada"
        )
        
        # TODO: Invalidar cache en Redis
        # await redis_client.delete(f"config:{categoria}")
        
        logger.info(f"Configuración '{categoria}' actualizada por {usuario.nombre_completo if usuario else 'Sistema'}")
        
        return nuevos_valores
    
    @staticmethod
    def _validar_pesos_escalamiento(pesos: Dict[str, float]) -> None:
        """Valida pesos de escalamiento"""
        
        required_keys = {'proximidad', 'actividad', 'desempeno', 'confianza'}
        if set(pesos.keys()) != required_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Pesos deben incluir exactamente: {required_keys}"
            )
        
        # Validar que todos sean números positivos
        for key, value in pesos.items():
            if not isinstance(value, (int, float)) or value < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Peso '{key}' debe ser un número positivo"
                )
        
        # Validar que sumen 1.0 con tolerancia
        suma = sum(pesos.values())
        if abs(suma - 1.0) > 1e-6:
            raise HTTPException(
                status_code=400,
                detail=f"Los pesos deben sumar 1.0 (suma actual: {suma:.6f})"
            )
    
    @staticmethod
    def _validar_umbrales_niveles(umbrales: Dict[str, float]) -> None:
        """Valida umbrales de niveles"""
        
        required_keys = {'nivel1_min', 'nivel2_min', 'nivel3_min', 'nivel4_min'}
        if set(umbrales.keys()) != required_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Umbrales deben incluir exactamente: {required_keys}"
            )
        
        # Validar rangos (1.0 - 5.0)
        for key, value in umbrales.items():
            if not isinstance(value, (int, float)) or not (1.0 <= value <= 5.0):
                raise HTTPException(
                    status_code=400,
                    detail=f"Umbral '{key}' debe estar entre 1.0 y 5.0"
                )
        
        # Validar que sean decrecientes
        valores = [
            umbrales['nivel1_min'],
            umbrales['nivel2_min'],
            umbrales['nivel3_min'],
            umbrales['nivel4_min']
        ]
        
        for i in range(len(valores) - 1):
            if valores[i] <= valores[i + 1]:
                raise HTTPException(
                    status_code=400,
                    detail="Los umbrales deben ser decrecientes (nivel1_min > nivel2_min > nivel3_min > nivel4_min)"
                )
    
    @staticmethod
    def _validar_pesos_evaluacion(pesos: Dict[str, float]) -> None:
        """Valida pesos de evaluación de ofertas"""
        
        required_keys = {'precio', 'tiempo_entrega', 'garantia'}
        if set(pesos.keys()) != required_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Pesos deben incluir exactamente: {required_keys}"
            )
        
        # Validar que todos sean números positivos
        for key, value in pesos.items():
            if not isinstance(value, (int, float)) or value < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Peso '{key}' debe ser un número positivo"
                )
        
        # Validar que sumen 1.0 con tolerancia
        suma = sum(pesos.values())
        if abs(suma - 1.0) > 1e-6:
            raise HTTPException(
                status_code=400,
                detail=f"Los pesos deben sumar 1.0 (suma actual: {suma:.6f})"
            )
    
    @staticmethod
    def _validar_tiempos_espera(tiempos: Dict[int, int]) -> None:
        """Valida tiempos de espera por nivel"""
        
        # Convertir claves a enteros si vienen como strings
        tiempos_int = {}
        for key, value in tiempos.items():
            try:
                nivel_int = int(key) if isinstance(key, str) else key
                tiempo_int = int(value) if isinstance(value, str) else value
                tiempos_int[nivel_int] = tiempo_int
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail=f"Nivel '{key}' y tiempo '{value}' deben ser números"
                )
        
        required_keys = {1, 2, 3, 4, 5}
        if set(tiempos_int.keys()) != required_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Tiempos deben incluir niveles: {required_keys}. Recibido: {set(tiempos_int.keys())}"
            )
        
        # Validar que todos sean números positivos
        for nivel, tiempo in tiempos_int.items():
            if tiempo <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tiempo para nivel {nivel} debe ser un entero positivo (minutos)"
                )
            
            if tiempo > 120:  # Máximo 2 horas
                raise HTTPException(
                    status_code=400,
                    detail=f"Tiempo para nivel {nivel} no puede exceder 120 minutos"
                )
    
    @staticmethod
    def _validar_canales_nivel(canales: Dict[int, str]) -> None:
        """Valida canales de notificación por nivel"""
        
        # Convertir claves a enteros si vienen como strings
        canales_int = {}
        for key, value in canales.items():
            try:
                nivel_int = int(key) if isinstance(key, str) else key
                canales_int[nivel_int] = value
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail=f"Nivel '{key}' debe ser un número"
                )
        
        required_keys = {1, 2, 3, 4, 5}
        if set(canales_int.keys()) != required_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Canales deben incluir niveles: {required_keys}. Recibido: {set(canales_int.keys())}"
            )
        
        valid_channels = {'WHATSAPP', 'PUSH', 'EMAIL', 'SMS'}
        
        for nivel, canal in canales_int.items():
            if canal not in valid_channels:
                raise HTTPException(
                    status_code=400,
                    detail=f"Canal '{canal}' para nivel {nivel} no es válido. Opciones: {valid_channels}"
                )
    
    @staticmethod
    def _validar_parametros_generales(params: Dict[str, Any]) -> None:
        """Valida parámetros generales del sistema"""
        
        # Validaciones específicas por parámetro
        validaciones = {
            'ofertas_minimas_deseadas': lambda x: isinstance(x, int) and 1 <= x <= 10,
            'timeout_evaluacion_seg': lambda x: isinstance(x, int) and 1 <= x <= 30,
            'vigencia_auditoria_dias': lambda x: isinstance(x, int) and 1 <= x <= 365,
            'periodo_actividad_dias': lambda x: isinstance(x, int) and 1 <= x <= 90,
            'periodo_desempeno_meses': lambda x: isinstance(x, int) and 1 <= x <= 24,
            'confianza_minima_operar': lambda x: isinstance(x, (int, float)) and 1.0 <= x <= 5.0,
            'cobertura_minima_pct': lambda x: isinstance(x, (int, float)) and 0 <= x <= 100,
            'timeout_ofertas_horas': lambda x: isinstance(x, int) and 1 <= x <= 168,
            'notificacion_expiracion_horas_antes': lambda x: isinstance(x, int) and 1 <= x <= 12
        }
        
        for key, value in params.items():
            if key in validaciones:
                if not validaciones[key](value):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Valor inválido para '{key}': {value}"
                    )
    
    @staticmethod
    async def reset_to_defaults(categoria: Optional[str] = None, usuario: Optional[Usuario] = None) -> Dict:
        """
        Resetea configuración a valores por defecto
        
        Args:
            categoria: Categoría específica (opcional, si no se especifica resetea todo)
            usuario: Usuario que realiza el reset
            
        Returns:
            Dict: Configuración reseteada
        """
        
        if categoria:
            if categoria not in ConfiguracionService.DEFAULT_CONFIG:
                raise HTTPException(
                    status_code=400,
                    detail=f"Categoría '{categoria}' no válida"
                )
            
            default_value = ConfiguracionService.DEFAULT_CONFIG[categoria]
            await ParametroConfig.set_valor(
                categoria,
                default_value,
                usuario,
                f"Reset a valores por defecto: {categoria}"
            )
            
            logger.info(f"Configuración '{categoria}' reseteada a valores por defecto")
            return {categoria: default_value}
        
        else:
            # Reset completo
            result = {}
            for cat, default_val in ConfiguracionService.DEFAULT_CONFIG.items():
                await ParametroConfig.set_valor(
                    cat,
                    default_val,
                    usuario,
                    f"Reset completo a valores por defecto"
                )
                result[cat] = default_val
            
            logger.info("Configuración completa reseteada a valores por defecto")
            return result
    
    @staticmethod
    async def get_config_summary() -> Dict[str, Any]:
        """
        Obtiene resumen de configuración actual
        
        Returns:
            Dict: Resumen de configuración con metadatos
        """
        
        config = await ConfiguracionService.get_config()
        
        # Calcular estadísticas
        total_params = sum(len(cat_config) if isinstance(cat_config, dict) else 1 
                          for cat_config in config.values())
        
        # Obtener última modificación con relación de usuario
        ultimo_cambio = await ParametroConfig.all().order_by('-updated_at').prefetch_related('modificado_por').first()
        
        # Obtener nombre del usuario que modificó
        modificado_por_nombre = None
        if ultimo_cambio and ultimo_cambio.modificado_por:
            try:
                modificado_por_nombre = ultimo_cambio.modificado_por.nombre_completo
            except Exception:
                modificado_por_nombre = "Sistema"
        
        return {
            'configuracion_actual': config,
            'estadisticas': {
                'total_categorias': len(config),
                'total_parametros': total_params,
                'ultima_modificacion': ultimo_cambio.updated_at if ultimo_cambio else None,
                'modificado_por': modificado_por_nombre
            },
            'validaciones_activas': {
                'pesos_suman_1': True,
                'umbrales_decrecientes': True,
                'rangos_validos': True
            }
        }
    

    @staticmethod
    async def get_metadata(categoria: str) -> Dict[str, Any]:
        """
        Obtiene metadatos de validación para una categoría específica
        
        Args:
            categoria: Categoría de configuración
            
        Returns:
            Dict: Metadatos de validación (min, max, default, unit, description)
        """
        param = await ParametroConfig.filter(clave=categoria).first()
        
        if param and param.metadata_json:
            return param.metadata_json
        
        return {}
    
    @staticmethod
    async def get_all_metadata() -> Dict[str, Dict[str, Any]]:
        """
        Obtiene todos los metadatos de validación
        
        Returns:
            Dict: Metadatos por categoría
        """
        # Metadata estático para parametros_generales
        PARAMETROS_METADATA = {
            'ofertas_minimas_deseadas': {
                'min': 1,
                'max': 10,
                'default': 2,
                'unit': 'ofertas',
                'description': 'Número mínimo de ofertas deseadas por solicitud'
            },
            'precio_minimo_oferta': {
                'min': 100,
                'max': 1000000,
                'default': 1000,
                'unit': 'COP',
                'description': 'Precio mínimo aceptable para una oferta'
            },
            'precio_maximo_oferta': {
                'min': 1000,
                'max': 100000000,
                'default': 50000000,
                'unit': 'COP',
                'description': 'Precio máximo aceptable para una oferta'
            },
            'garantia_minima_meses': {
                'min': 0,
                'max': 120,
                'default': 1,
                'unit': 'meses',
                'description': 'Garantía mínima requerida'
            },
            'garantia_maxima_meses': {
                'min': 1,
                'max': 120,
                'default': 60,
                'unit': 'meses',
                'description': 'Garantía máxima permitida'
            },
            'tiempo_entrega_minimo_dias': {
                'min': 0,
                'max': 365,
                'default': 0,
                'unit': 'días',
                'description': 'Tiempo de entrega mínimo'
            },
            'tiempo_entrega_maximo_dias': {
                'min': 1,
                'max': 365,
                'default': 90,
                'unit': 'días',
                'description': 'Tiempo de entrega máximo permitido'
            },
            'cobertura_minima_porcentaje': {
                'min': 0,
                'max': 100,
                'default': 50,
                'unit': '%',
                'description': 'Porcentaje mínimo de cobertura requerido'
            },
            'timeout_evaluacion_segundos': {
                'min': 1,
                'max': 30,
                'default': 5,
                'unit': 'segundos',
                'description': 'Tiempo máximo para evaluación automática'
            },
            'vigencia_auditoria_dias': {
                'min': 1,
                'max': 365,
                'default': 30,
                'unit': 'días',
                'description': 'Días de vigencia de una auditoría'
            },
            'timeout_ofertas_horas': {
                'min': 1,
                'max': 168,
                'default': 20,
                'unit': 'horas',
                'description': 'Tiempo máximo para que expire una oferta'
            },
            'notificacion_expiracion_horas_antes': {
                'min': 1,
                'max': 24,
                'default': 2,
                'unit': 'horas',
                'description': 'Horas antes de expiración para notificar'
            },
            'confianza_minima_operar': {
                'min': 1.0,
                'max': 5.0,
                'default': 2.0,
                'unit': 'estrellas',
                'description': 'Confianza mínima para que un asesor opere'
            },
            'periodo_actividad_reciente_dias': {
                'min': 1,
                'max': 90,
                'default': 30,
                'unit': 'días',
                'description': 'Período para calcular actividad reciente'
            },
            'periodo_desempeno_historico_meses': {
                'min': 1,
                'max': 24,
                'default': 6,
                'unit': 'meses',
                'description': 'Período para calcular desempeño histórico'
            },
            'fallback_actividad_asesores_nuevos': {
                'min': 0.0,
                'max': 5.0,
                'default': 3.0,
                'unit': 'puntos',
                'description': 'Puntaje de actividad por defecto para asesores nuevos'
            },
            'fallback_desempeno_asesores_nuevos': {
                'min': 0.0,
                'max': 5.0,
                'default': 3.0,
                'unit': 'puntos',
                'description': 'Puntaje de desempeño por defecto para asesores nuevos'
            },
            'puntaje_defecto_asesores_nuevos': {
                'min': 0,
                'max': 100,
                'default': 50,
                'unit': 'puntos',
                'description': 'Puntaje general por defecto para asesores nuevos'
            }
        }
        
        params = await ParametroConfig.all()
        
        metadata = {}
        for param in params:
            if param.metadata_json:
                metadata[param.clave] = param.metadata_json
        
        # Añadir metadata estático de parametros_generales si no existe
        for key, meta in PARAMETROS_METADATA.items():
            if key not in metadata:
                metadata[key] = meta
        
        return metadata
    
    @staticmethod
    async def update_metadata(
        categoria: str,
        nuevos_metadatos: Dict[str, Any],
        usuario: Optional[Usuario] = None
    ) -> Dict[str, Any]:
        """
        Actualiza metadatos de validación para una categoría
        
        Args:
            categoria: Categoría de configuración
            nuevos_metadatos: Nuevos metadatos (min, max, default, unit, description)
            usuario: Usuario que realiza el cambio
            
        Returns:
            Dict: Metadatos actualizados
        """
        param = await ParametroConfig.filter(clave=categoria).first()
        
        if not param:
            raise HTTPException(
                status_code=404,
                detail=f"Categoría '{categoria}' no encontrada"
            )
        
        # Actualizar metadatos
        param.metadata_json = nuevos_metadatos
        param.modificado_por = usuario
        await param.save()
        
        logger.info(f"Metadatos de '{categoria}' actualizados por {usuario.nombre_completo if usuario else 'Sistema'}")
        
        return nuevos_metadatos
