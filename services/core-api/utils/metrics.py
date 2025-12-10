"""
Métricas de Prometheus para observabilidad
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry
from typing import Optional
import time

# Registry global para métricas
registry = CollectorRegistry()

# Información del servicio
service_info = Info('teloo_service', 'Información del servicio TeLOO', registry=registry)
service_info.info({
    'service': 'core-api',
    'version': '3.0.0',
    'environment': 'production'
})

# Métricas HTTP
http_requests_total = Counter(
    'http_requests_total',
    'Total de requests HTTP',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Duración de requests HTTP en segundos',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
    registry=registry
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Requests HTTP en progreso',
    ['method', 'endpoint'],
    registry=registry
)

# Métricas de negocio - Solicitudes
solicitudes_created_total = Counter(
    'solicitudes_created_total',
    'Total de solicitudes creadas',
    ['ciudad', 'estado'],
    registry=registry
)

solicitudes_active = Gauge(
    'solicitudes_active',
    'Solicitudes activas por estado',
    ['estado'],
    registry=registry
)

solicitudes_processing_duration_seconds = Histogram(
    'solicitudes_processing_duration_seconds',
    'Tiempo de procesamiento de solicitudes',
    ['estado_final'],
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400, 28800, 86400),  # 1min a 1 día
    registry=registry
)

# Métricas de negocio - Ofertas
ofertas_created_total = Counter(
    'ofertas_created_total',
    'Total de ofertas creadas',
    ['tipo', 'estado'],
    registry=registry
)

ofertas_active = Gauge(
    'ofertas_active',
    'Ofertas activas por estado',
    ['estado'],
    registry=registry
)

ofertas_evaluation_duration_seconds = Histogram(
    'ofertas_evaluation_duration_seconds',
    'Tiempo de evaluación de ofertas',
    buckets=(0.1, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0),
    registry=registry
)

# Métricas de negocio - Escalamiento
escalamiento_oleadas_total = Counter(
    'escalamiento_oleadas_total',
    'Total de oleadas de escalamiento',
    ['nivel', 'canal'],
    registry=registry
)

escalamiento_asesores_notificados = Counter(
    'escalamiento_asesores_notificados',
    'Asesores notificados por nivel',
    ['nivel'],
    registry=registry
)

escalamiento_duration_seconds = Histogram(
    'escalamiento_duration_seconds',
    'Tiempo de ejecución de escalamiento',
    ['nivel'],
    buckets=(1, 5, 10, 30, 60, 120, 300),
    registry=registry
)

# Métricas de base de datos
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Duración de queries a base de datos',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=registry
)

db_connections_active = Gauge(
    'db_connections_active',
    'Conexiones activas a base de datos',
    registry=registry
)

db_errors_total = Counter(
    'db_errors_total',
    'Total de errores de base de datos',
    ['operation', 'error_type'],
    registry=registry
)

# Métricas de Redis
redis_operations_total = Counter(
    'redis_operations_total',
    'Total de operaciones Redis',
    ['operation', 'status'],
    registry=registry
)

redis_operation_duration_seconds = Histogram(
    'redis_operation_duration_seconds',
    'Duración de operaciones Redis',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
    registry=registry
)

# Métricas de servicios externos
external_api_requests_total = Counter(
    'external_api_requests_total',
    'Total de requests a APIs externas',
    ['service', 'endpoint', 'status'],
    registry=registry
)

external_api_duration_seconds = Histogram(
    'external_api_duration_seconds',
    'Duración de requests a APIs externas',
    ['service', 'endpoint'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=registry
)

external_api_errors_total = Counter(
    'external_api_errors_total',
    'Total de errores en APIs externas',
    ['service', 'error_type'],
    registry=registry
)

# Métricas de circuit breaker
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Estado del circuit breaker (0=closed, 1=open, 2=half_open)',
    ['service'],
    registry=registry
)

circuit_breaker_failures_total = Counter(
    'circuit_breaker_failures_total',
    'Total de fallos en circuit breaker',
    ['service'],
    registry=registry
)

# Métricas de sistema
system_errors_total = Counter(
    'system_errors_total',
    'Total de errores del sistema',
    ['error_type', 'component'],
    registry=registry
)

system_warnings_total = Counter(
    'system_warnings_total',
    'Total de warnings del sistema',
    ['warning_type', 'component'],
    registry=registry
)


class MetricsCollector:
    """
    Colector de métricas para facilitar el uso
    """
    
    @staticmethod
    def record_http_request(method: str, endpoint: str, status: int, duration: float):
        """Registra una request HTTP"""
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    @staticmethod
    def record_solicitud_created(ciudad: str, estado: str):
        """Registra creación de solicitud"""
        solicitudes_created_total.labels(ciudad=ciudad, estado=estado).inc()
    
    @staticmethod
    def update_solicitudes_active(estado: str, count: int):
        """Actualiza contador de solicitudes activas"""
        solicitudes_active.labels(estado=estado).set(count)
    
    @staticmethod
    def record_solicitud_processing(estado_final: str, duration_seconds: float):
        """Registra tiempo de procesamiento de solicitud"""
        solicitudes_processing_duration_seconds.labels(estado_final=estado_final).observe(duration_seconds)
    
    @staticmethod
    def record_oferta_created(tipo: str, estado: str):
        """Registra creación de oferta"""
        ofertas_created_total.labels(tipo=tipo, estado=estado).inc()
    
    @staticmethod
    def update_ofertas_active(estado: str, count: int):
        """Actualiza contador de ofertas activas"""
        ofertas_active.labels(estado=estado).set(count)
    
    @staticmethod
    def record_oferta_evaluation(duration_seconds: float):
        """Registra tiempo de evaluación de oferta"""
        ofertas_evaluation_duration_seconds.observe(duration_seconds)
    
    @staticmethod
    def record_escalamiento_oleada(nivel: int, canal: str):
        """Registra oleada de escalamiento"""
        escalamiento_oleadas_total.labels(nivel=str(nivel), canal=canal).inc()
    
    @staticmethod
    def record_escalamiento_notificacion(nivel: int, count: int = 1):
        """Registra notificaciones de escalamiento"""
        escalamiento_asesores_notificados.labels(nivel=str(nivel)).inc(count)
    
    @staticmethod
    def record_escalamiento_duration(nivel: int, duration_seconds: float):
        """Registra duración de escalamiento"""
        escalamiento_duration_seconds.labels(nivel=str(nivel)).observe(duration_seconds)
    
    @staticmethod
    def record_db_query(operation: str, table: str, duration_seconds: float):
        """Registra query a base de datos"""
        db_query_duration_seconds.labels(operation=operation, table=table).observe(duration_seconds)
    
    @staticmethod
    def update_db_connections(count: int):
        """Actualiza conexiones activas a BD"""
        db_connections_active.set(count)
    
    @staticmethod
    def record_db_error(operation: str, error_type: str):
        """Registra error de base de datos"""
        db_errors_total.labels(operation=operation, error_type=error_type).inc()
    
    @staticmethod
    def record_redis_operation(operation: str, status: str, duration_seconds: float):
        """Registra operación Redis"""
        redis_operations_total.labels(operation=operation, status=status).inc()
        redis_operation_duration_seconds.labels(operation=operation).observe(duration_seconds)
    
    @staticmethod
    def record_external_api_request(service: str, endpoint: str, status: int, duration_seconds: float):
        """Registra request a API externa"""
        external_api_requests_total.labels(service=service, endpoint=endpoint, status=str(status)).inc()
        external_api_duration_seconds.labels(service=service, endpoint=endpoint).observe(duration_seconds)
    
    @staticmethod
    def record_external_api_error(service: str, error_type: str):
        """Registra error en API externa"""
        external_api_errors_total.labels(service=service, error_type=error_type).inc()
    
    @staticmethod
    def update_circuit_breaker_state(service: str, state: int):
        """Actualiza estado de circuit breaker (0=closed, 1=open, 2=half_open)"""
        circuit_breaker_state.labels(service=service).set(state)
    
    @staticmethod
    def record_circuit_breaker_failure(service: str):
        """Registra fallo en circuit breaker"""
        circuit_breaker_failures_total.labels(service=service).inc()
    
    @staticmethod
    def record_system_error(error_type: str, component: str):
        """Registra error del sistema"""
        system_errors_total.labels(error_type=error_type, component=component).inc()
    
    @staticmethod
    def record_system_warning(warning_type: str, component: str):
        """Registra warning del sistema"""
        system_warnings_total.labels(warning_type=warning_type, component=component).inc()


def get_metrics() -> bytes:
    """
    Obtiene las métricas en formato Prometheus
    
    Returns:
        Métricas en formato texto de Prometheus
    """
    return generate_latest(registry)


def get_metrics_content_type() -> str:
    """
    Obtiene el content type para las métricas
    
    Returns:
        Content type de Prometheus
    """
    return CONTENT_TYPE_LATEST


# Instancia global del colector
metrics_collector = MetricsCollector()
