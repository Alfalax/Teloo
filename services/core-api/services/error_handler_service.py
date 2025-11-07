"""
Error Handler Service for TeLOO V3
Provides robust error handling, timeout management, and fallback mechanisms
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

from models.enums import EstadoSolicitud, EstadoOferta
from services.configuracion_service import ConfiguracionService

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Custom timeout error"""
    pass


class FallbackError(Exception):
    """Error when all fallback mechanisms fail"""
    pass


class ErrorHandlerService:
    """Service for robust error handling and timeout management"""
    
    @staticmethod
    async def execute_with_timeout(
        func: Callable,
        timeout_seconds: int,
        operation_name: str,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute function with timeout handling
        
        Args:
            func: Function to execute
            timeout_seconds: Timeout in seconds
            operation_name: Name of operation for logging
            *args, **kwargs: Arguments for the function
            
        Returns:
            Dict with result or timeout error
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting {operation_name} with {timeout_seconds}s timeout")
            
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=timeout_seconds
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"{operation_name} completed successfully in {duration:.2f}s")
            
            return {
                'success': True,
                'result': result,
                'duration_seconds': duration,
                'operation': operation_name
            }
            
        except asyncio.TimeoutError:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"{operation_name} timed out after {timeout_seconds}s"
            
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': 'timeout',
                'error_message': error_msg,
                'timeout_seconds': timeout_seconds,
                'duration_seconds': duration,
                'operation': operation_name
            }
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"{operation_name} failed: {str(e)}"
            
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': 'execution_error',
                'error_message': error_msg,
                'exception_type': type(e).__name__,
                'duration_seconds': duration,
                'operation': operation_name
            }
    
    @staticmethod
    async def handle_geographic_fallback(ciudad: str) -> Dict[str, Any]:
        """
        Handle fallback for cities without AM or HUB coverage
        
        Args:
            ciudad: City name that lacks geographic coverage
            
        Returns:
            Dict with fallback values and warning information
        """
        logger.warning(
            f"Ciudad '{ciudad}' no encontrada en áreas metropolitanas ni hubs logísticos. "
            f"Aplicando proximidad por defecto (3.0)."
        )
        
        # TODO: Implement admin notification system
        # await NotificationService.notify_admin_missing_geographic_coverage(ciudad)
        
        fallback_data = {
            'proximidad': Decimal('3.0'),
            'criterio': 'sin_cobertura_geografica',
            'ciudad_problema': ciudad,
            'timestamp': datetime.now().isoformat(),
            'accion_requerida': 'Agregar ciudad a áreas metropolitanas o hubs logísticos'
        }
        
        # Log to a special file for geographic issues
        await ErrorHandlerService._log_geographic_issue(ciudad, fallback_data)
        
        return fallback_data
    
    @staticmethod
    async def handle_missing_metrics_fallback(
        asesor_id: str,
        missing_metrics: List[str]
    ) -> Dict[str, Decimal]:
        """
        Handle fallback for missing advisor metrics
        
        Args:
            asesor_id: Advisor ID
            missing_metrics: List of missing metric names
            
        Returns:
            Dict with fallback metric values
        """
        fallback_values = {
            'actividad_reciente': Decimal('1.0'),  # Neutral activity
            'desempeno_historico': Decimal('1.0'),  # Neutral performance
            'nivel_confianza': Decimal('3.0')  # Medium confidence
        }
        
        applied_fallbacks = {}
        for metric in missing_metrics:
            if metric in fallback_values:
                applied_fallbacks[metric] = fallback_values[metric]
        
        logger.warning(
            f"Aplicando fallbacks para asesor {asesor_id}: "
            f"métricas faltantes {missing_metrics}, "
            f"valores aplicados: {applied_fallbacks}"
        )
        
        # Log missing metrics for analysis
        await ErrorHandlerService._log_missing_metrics(asesor_id, missing_metrics, applied_fallbacks)
        
        return applied_fallbacks
    
    @staticmethod
    async def handle_evaluation_timeout(
        solicitud_id: str,
        timeout_seconds: int,
        ofertas_count: int
    ) -> Dict[str, Any]:
        """
        Handle evaluation timeout scenario
        
        Args:
            solicitud_id: Solicitud ID that timed out
            timeout_seconds: Timeout that was applied
            ofertas_count: Number of offers that were being evaluated
            
        Returns:
            Dict with timeout handling result
        """
        logger.error(
            f"Evaluación de solicitud {solicitud_id} excedió timeout de {timeout_seconds}s "
            f"con {ofertas_count} ofertas"
        )
        
        # Mark solicitud as having evaluation error
        try:
            from models.solicitud import Solicitud
            solicitud = await Solicitud.get_or_none(id=solicitud_id)
            if solicitud:
                await solicitud.update_from_dict({
                    'estado': EstadoSolicitud.CERRADA_SIN_OFERTAS,  # Temporary state
                    'observaciones': f'Evaluación cancelada por timeout ({timeout_seconds}s)',
                    'updated_at': datetime.now()
                })
        except Exception as e:
            logger.error(f"Error updating solicitud after timeout: {e}")
        
        timeout_data = {
            'solicitud_id': solicitud_id,
            'timeout_seconds': timeout_seconds,
            'ofertas_count': ofertas_count,
            'timestamp': datetime.now().isoformat(),
            'action_taken': 'solicitud_marked_as_closed',
            'recovery_suggestion': 'Revisar complejidad de evaluación y ajustar timeout'
        }
        
        # Log timeout for analysis
        await ErrorHandlerService._log_evaluation_timeout(timeout_data)
        
        return timeout_data
    
    @staticmethod
    async def handle_circuit_breaker_fallback(
        service_name: str,
        operation: str,
        fallback_result: Any = None
    ) -> Dict[str, Any]:
        """
        Handle circuit breaker fallback scenarios
        
        Args:
            service_name: Name of the service with circuit breaker open
            operation: Operation that was attempted
            fallback_result: Fallback result to return
            
        Returns:
            Dict with fallback handling result
        """
        logger.warning(
            f"Circuit breaker OPEN for {service_name} during {operation}. "
            f"Applying fallback mechanism."
        )
        
        fallback_data = {
            'service_name': service_name,
            'operation': operation,
            'fallback_applied': True,
            'fallback_result': fallback_result,
            'timestamp': datetime.now().isoformat(),
            'recovery_action': f'Monitor {service_name} health and reset circuit breaker when stable'
        }
        
        # Log circuit breaker activation
        await ErrorHandlerService._log_circuit_breaker_event(fallback_data)
        
        return fallback_data
    
    @staticmethod
    async def validate_configuration_parameters() -> Dict[str, Any]:
        """
        Validate system configuration parameters for consistency
        
        Returns:
            Dict with validation results
        """
        try:
            # Get all configuration
            config_pesos = await ConfiguracionService.get_config('pesos_escalamiento')
            config_umbrales = await ConfiguracionService.get_config('umbrales_niveles')
            config_tiempos = await ConfiguracionService.get_config('tiempos_espera_niveles')
            config_general = await ConfiguracionService.get_config('parametros_generales')
            
            validation_errors = []
            warnings = []
            
            # Validate weights sum to 1.0
            peso_total = sum(config_pesos.values())
            if abs(peso_total - 1.0) > 1e-6:
                validation_errors.append(
                    f"Pesos de escalamiento no suman 1.0: {peso_total:.6f}"
                )
            
            # Validate thresholds are descending
            umbrales = [
                config_umbrales['nivel1_min'],
                config_umbrales['nivel2_min'],
                config_umbrales['nivel3_min'],
                config_umbrales['nivel4_min']
            ]
            
            for i in range(len(umbrales) - 1):
                if umbrales[i] <= umbrales[i + 1]:
                    validation_errors.append(
                        f"Umbrales no son decrecientes: nivel{i+1}_min ({umbrales[i]}) <= nivel{i+2}_min ({umbrales[i+1]})"
                    )
            
            # Validate timeout values are reasonable
            timeout_evaluacion = config_general.get('timeout_evaluacion_seg', 5)
            if timeout_evaluacion < 1 or timeout_evaluacion > 60:
                warnings.append(
                    f"Timeout de evaluación ({timeout_evaluacion}s) fuera del rango recomendado (1-60s)"
                )
            
            # Validate coverage minimum
            cobertura_min = config_general.get('cobertura_minima_pct', 50)
            if cobertura_min < 0 or cobertura_min > 100:
                validation_errors.append(
                    f"Cobertura mínima ({cobertura_min}%) debe estar entre 0-100%"
                )
            
            return {
                'valid': len(validation_errors) == 0,
                'errors': validation_errors,
                'warnings': warnings,
                'validated_at': datetime.now().isoformat(),
                'configurations_checked': [
                    'pesos_escalamiento',
                    'umbrales_niveles', 
                    'tiempos_espera_niveles',
                    'parametros_generales'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
            return {
                'valid': False,
                'errors': [f"Error accessing configuration: {str(e)}"],
                'warnings': [],
                'validated_at': datetime.now().isoformat()
            }
    
    @staticmethod
    async def _log_geographic_issue(ciudad: str, fallback_data: Dict[str, Any]):
        """Log geographic coverage issues for analysis"""
        try:
            log_entry = {
                'type': 'geographic_coverage_missing',
                'ciudad': ciudad,
                'fallback_data': fallback_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # In a real implementation, this would go to a special log file or database
            logger.info(f"GEOGRAPHIC_ISSUE: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Error logging geographic issue: {e}")
    
    @staticmethod
    async def _log_missing_metrics(
        asesor_id: str, 
        missing_metrics: List[str], 
        applied_fallbacks: Dict[str, Decimal]
    ):
        """Log missing metrics for analysis"""
        try:
            log_entry = {
                'type': 'missing_advisor_metrics',
                'asesor_id': asesor_id,
                'missing_metrics': missing_metrics,
                'applied_fallbacks': {k: float(v) for k, v in applied_fallbacks.items()},
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"MISSING_METRICS: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Error logging missing metrics: {e}")
    
    @staticmethod
    async def _log_evaluation_timeout(timeout_data: Dict[str, Any]):
        """Log evaluation timeouts for analysis"""
        try:
            log_entry = {
                'type': 'evaluation_timeout',
                'timeout_data': timeout_data
            }
            
            logger.error(f"EVALUATION_TIMEOUT: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Error logging evaluation timeout: {e}")
    
    @staticmethod
    async def _log_circuit_breaker_event(fallback_data: Dict[str, Any]):
        """Log circuit breaker events for analysis"""
        try:
            log_entry = {
                'type': 'circuit_breaker_fallback',
                'fallback_data': fallback_data
            }
            
            logger.warning(f"CIRCUIT_BREAKER: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Error logging circuit breaker event: {e}")


def timeout_handler(timeout_seconds: int, operation_name: str):
    """
    Decorator for adding timeout handling to async functions
    
    Args:
        timeout_seconds: Timeout in seconds
        operation_name: Name of operation for logging
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await ErrorHandlerService.execute_with_timeout(
                func, timeout_seconds, operation_name, *args, **kwargs
            )
        return wrapper
    return decorator


def fallback_on_error(fallback_value: Any, log_error: bool = True):
    """
    Decorator for providing fallback values on errors
    
    Args:
        fallback_value: Value to return on error
        log_error: Whether to log the error
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {e}, using fallback: {fallback_value}")
                return fallback_value
        return wrapper
    return decorator