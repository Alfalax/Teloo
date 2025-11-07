# Analytics Batch Jobs

Este documento describe el sistema de jobs batch implementado para el cálculo de métricas complejas en el servicio de Analytics.

## Descripción General

El sistema de batch jobs permite ejecutar cálculos pesados de métricas de forma programada, evitando impactar el rendimiento del sistema durante las horas de mayor actividad.

## Jobs Implementados

### 1. Job Diario (2 AM)
**ID:** `daily_metrics_batch`
**Frecuencia:** Diario a las 2:00 AM
**Duración estimada:** 2-5 minutos

**Métricas calculadas:**
- **Ranking de asesores**: Clasificación por desempeño basada en ofertas ganadoras, tiempo de respuesta y valor promedio
- **Especialización por repuesto**: Análisis de especialización de asesores por categoría de repuesto
- **Conversión por ciudad**: Métricas de conversión y valor promedio por ciudad
- **Tiempo de respuesta por asesor**: Estadísticas de tiempo de respuesta individual

### 2. Job Semanal (Lunes 3 AM)
**ID:** `weekly_metrics_batch`
**Frecuencia:** Semanal, lunes a las 3:00 AM
**Duración estimada:** 5-10 minutos

**Análisis realizados:**
- **Tendencias de solicitudes**: Análisis de crecimiento/decrecimiento semanal
- **Evolución de asesores**: Seguimiento del desempeño de asesores en el tiempo
- **Patrones de demanda**: Análisis de demanda por tipo de repuesto y patrones temporales
- **Métricas de satisfacción**: Cálculo de tasas de satisfacción y calidad del servicio

### 3. Job de Limpieza (Domingo 4 AM)
**ID:** `cleanup_metrics`
**Frecuencia:** Semanal, domingo a las 4:00 AM
**Duración estimada:** 1-2 minutos

**Tareas de limpieza:**
- Eliminación de métricas expiradas
- Limpieza de eventos antiguos (>30 días)
- Optimización de almacenamiento

## Almacenamiento de Resultados

Los resultados se almacenan en la tabla `MetricaCalculada` con la siguiente estructura:

```sql
CREATE TABLE metricas_calculadas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    valor FLOAT NOT NULL,
    descripcion TEXT,
    unidad VARCHAR(20) DEFAULT 'count',
    dimensiones JSONB DEFAULT '{}',
    periodo_inicio TIMESTAMP NOT NULL,
    periodo_fin TIMESTAMP NOT NULL,
    calculado_en TIMESTAMP DEFAULT NOW(),
    expira_en TIMESTAMP NOT NULL
);
```

## API Endpoints

### Estado de Jobs
```http
GET /dashboards/batch-jobs/status
```
Retorna el estado actual de todos los jobs programados.

### Ejecución Manual
```http
POST /dashboards/batch-jobs/trigger/{job_id}
```
Ejecuta manualmente un job específico.

### Job Diario Manual
```http
POST /dashboards/batch-jobs/daily?fecha=2024-01-15
```
Ejecuta el job diario para una fecha específica.

### Job Semanal Manual
```http
POST /dashboards/batch-jobs/weekly?fecha_fin=2024-01-15
```
Ejecuta el job semanal para un período específico.

### Consultar Métricas Calculadas
```http
GET /dashboards/metrics/calculated?nombre_metrica=ranking_asesores_diario&limit=50
```
Consulta métricas calculadas con filtros opcionales.

## Configuración

Las configuraciones principales se encuentran en `app/core/config.py`:

```python
# Hora de ejecución del job diario (24h format)
BATCH_JOB_HOUR: int = 2  # 2 AM

# TTL del cache de métricas (segundos)
METRICS_CACHE_TTL: int = 300  # 5 minutos
```

## Monitoreo

### Health Check
El endpoint `/health` incluye información sobre el estado del scheduler:

```json
{
  "status": "healthy",
  "components": {
    "scheduler": "running",
    "batch_jobs": 3
  }
}
```

### Logs
Los jobs generan logs detallados que incluyen:
- Tiempo de ejecución
- Número de registros procesados
- Errores específicos por métrica
- Estadísticas de rendimiento

### Ejemplo de Log
```
2024-01-15 02:00:01 - INFO - Iniciando job diario de métricas para 2024-01-14
2024-01-15 02:02:15 - INFO - Job diario completado en 134.23s
2024-01-15 02:02:15 - INFO - Ranking calculado para 45 asesores
2024-01-15 02:02:15 - INFO - Especialización calculada para 32 asesores
```

## Manejo de Errores

### Estrategias Implementadas
1. **Tolerancia a fallos**: Si una métrica falla, las demás continúan ejecutándose
2. **Timeouts**: Jobs con timeout de 30 minutos para evitar bloqueos
3. **Reintentos**: Configuración de misfire_grace_time de 30 minutos
4. **Logging detallado**: Cada error se registra con contexto completo

### Recuperación
- Los jobs pueden ejecutarse manualmente si fallan
- Las métricas tienen TTL para evitar datos obsoletos
- Sistema de limpieza automática previene acumulación de datos

## Testing

Para probar el sistema de batch jobs:

```bash
cd services/analytics
python test_batch_jobs.py
```

Este script verifica:
- Inicialización correcta del scheduler
- Ejecución de jobs diarios y semanales
- Almacenamiento de métricas
- Estado del sistema

## Consideraciones de Rendimiento

### Optimizaciones Implementadas
1. **Consultas optimizadas**: Uso de índices y agregaciones SQL eficientes
2. **Procesamiento por lotes**: Cálculo de múltiples métricas en una sola consulta
3. **Cache inteligente**: TTL diferenciado según tipo de métrica
4. **Limpieza automática**: Prevención de crecimiento descontrolado de datos

### Recursos Estimados
- **CPU**: Picos de 50-70% durante ejecución
- **Memoria**: 200-500 MB adicionales durante procesamiento
- **I/O**: Consultas intensivas por 2-10 minutos
- **Almacenamiento**: ~1-5 MB por día de métricas calculadas

## Troubleshooting

### Problemas Comunes

1. **Job no se ejecuta**
   - Verificar que el scheduler esté iniciado
   - Revisar logs de inicialización
   - Comprobar configuración de zona horaria

2. **Métricas vacías**
   - Verificar conexión a base de datos principal
   - Comprobar que existan datos para el período
   - Revisar permisos de consulta

3. **Timeouts**
   - Aumentar `misfire_grace_time` si es necesario
   - Optimizar consultas SQL problemáticas
   - Considerar particionado de datos grandes

4. **Memoria insuficiente**
   - Reducir tamaño de lotes en consultas
   - Implementar procesamiento streaming
   - Aumentar recursos del contenedor

### Comandos de Diagnóstico

```bash
# Ver estado del scheduler
curl http://localhost:8002/dashboards/batch-jobs/status

# Ejecutar job manualmente
curl -X POST http://localhost:8002/dashboards/batch-jobs/trigger/daily_metrics_batch

# Ver métricas recientes
curl http://localhost:8002/dashboards/metrics/calculated?limit=10

# Health check completo
curl http://localhost:8002/health
```