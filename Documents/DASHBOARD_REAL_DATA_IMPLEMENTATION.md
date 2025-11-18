# Implementación de Datos Reales en el Dashboard

## Resumen

Se ha conectado el dashboard de inicio (Tab "Resumen") a la base de datos real, eliminando todos los datos mock y hardcodeados.

## Cambios Realizados

### 1. Backend - Analytics Service (`services/analytics/app/services/metrics_calculator.py`)

#### KPIs Principales
Se implementaron consultas SQL reales para los 4 KPIs superiores:

- **Ofertas Totales Asignadas**: Cuenta todas las ofertas creadas en el período
- **Monto Total Aceptado**: Suma el valor total de ofertas ganadoras
- **Solicitudes Abiertas**: Cuenta solicitudes en estado ABIERTA
- **Tasa de Conversión**: Calcula el porcentaje de solicitudes aceptadas

#### Cálculo de Cambios Porcentuales
Se agregó lógica para calcular cambios porcentuales comparando con el período anterior:
```python
def _calcular_cambio_porcentual(self, valor_actual: float, valor_anterior: float) -> float:
    if valor_anterior == 0:
        return 0.0 if valor_actual == 0 else 100.0
    return round(((valor_actual - valor_anterior) / valor_anterior) * 100, 2)
```

#### Gráficos del Mes
Ya estaba implementado con consultas SQL reales que generan series de tiempo diarias.

#### Top Solicitudes Abiertas
Se corrigió la consulta SQL para usar `MAX()` en los campos agregados y se eliminó el fallback a datos mock.

### 2. Frontend - Dashboard Page (`frontend/admin/src/pages/DashboardPage.tsx`)

#### Eliminación de Datos Mock
Se eliminó la sección "Actividad Reciente" que contenía datos hardcodeados:
```typescript
// ELIMINADO:
[
  'Nueva solicitud creada: SOL-123',
  'Oferta ganadora: Asesor Juan Pérez',
  ...
]
```

### 3. Métodos Implementados con Consultas Reales

Todos los métodos placeholder ahora consultan la base de datos:

- `_calcular_ofertas_totales()`: Cuenta ofertas en el período
- `_calcular_asesores_contactados()`: Cuenta asesores únicos en escalamientos
- `_calcular_tasa_respuesta_asesores()`: Calcula % de escalamientos respondidos
- `_calcular_ofertas_recibidas()`: Cuenta ofertas totales
- `_calcular_ofertas_por_solicitud()`: Promedio de ofertas por solicitud
- `_calcular_solicitudes_evaluadas()`: Cuenta solicitudes evaluadas
- `_calcular_tiempo_evaluacion()`: Tiempo promedio de evaluación
- `_calcular_ofertas_ganadoras()`: Cuenta ofertas ganadoras
- `_calcular_tasa_aceptacion_cliente()`: % de solicitudes aceptadas
- `_calcular_solicitudes_cerradas()`: Cuenta solicitudes cerradas
- `_calcular_asesores_activos()`: Cuenta asesores con ofertas en el período

## Componentes del Dashboard

### Tab "Resumen" - Datos Reales

1. **4 KPIs Superiores** ✅ Conectados a BD
   - Ofertas Totales Asignadas
   - Monto Total Aceptado
   - Solicitudes Abiertas
   - Tasa de Conversión

2. **Gráfico "Solicitudes del Mes"** ✅ Conectado a BD
   - Evolución diaria de solicitudes
   - Solicitudes aceptadas
   - Solicitudes cerradas sin ofertas

3. **Top Solicitudes Abiertas** ✅ Conectado a BD
   - Solicitudes con mayor tiempo en proceso
   - Información del vehículo
   - Cliente y ciudad
   - Cantidad de repuestos

4. **Actividad Reciente** ❌ Eliminado
   - Era 100% hardcodeado, se eliminó

## Manejo de Errores

Si hay un error al consultar la base de datos, el sistema ahora retorna valores en cero en lugar de datos mock:

```python
except Exception as e:
    logger.error(f"Error calculando KPIs principales: {e}", exc_info=True)
    return {
        "ofertas_totales": 0,
        "ofertas_cambio": 0,
        "monto_total": 0,
        "monto_cambio": 0,
        "solicitudes_abiertas": 0,
        "solicitudes_cambio": 0,
        "tasa_conversion": 0,
        "conversion_cambio": 0,
    }
```

## Pruebas

### Script de Prueba
Se creó `services/analytics/test_dashboard_real_data.py` para verificar que los datos se obtienen correctamente de la BD.

### Ejecutar Pruebas

```bash
# Desde la raíz del proyecto
cd services/analytics
python test_dashboard_real_data.py
```

El script mostrará:
- Los 4 KPIs principales con sus cambios porcentuales
- Datos de los gráficos del mes
- Top 5 solicitudes abiertas
- Verificación de si hay datos reales en la BD

## Requisitos

### Base de Datos
La base de datos debe tener datos para que el dashboard muestre información. Si está vacía:

```bash
# Ejecutar script de inicialización
python services/core-api/init_data.py
```

### Servicios Necesarios
- PostgreSQL (puerto 5432)
- Redis (puerto 6379)
- Analytics Service (puerto 8002)

### Docker Compose
```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs del servicio de analytics
docker-compose logs -f analytics
```

## Verificación

### 1. Verificar que el servicio de Analytics está corriendo
```bash
curl http://localhost:8002/health
```

### 2. Probar endpoint de KPIs principales
```bash
curl http://localhost:8002/v1/dashboards/principal
```

### 3. Verificar en el frontend
1. Abrir http://localhost:3000
2. Iniciar sesión
3. Ir al Dashboard (página de inicio)
4. Verificar que los números no sean 1234, 45200000, etc. (datos mock)

## Notas Importantes

1. **Cache**: Los KPIs se cachean por 5 minutos en Redis para mejorar el rendimiento
2. **Período por defecto**: Si no se especifica, usa los últimos 30 días
3. **Zona horaria**: Todas las fechas usan UTC
4. **Métricas de sistema**: Disponibilidad, latencia y carga del sistema aún usan valores placeholder (TODO)

## Próximos Pasos

Para completar la implementación:

1. Implementar métricas reales de sistema:
   - `_calcular_disponibilidad_sistema()`
   - `_calcular_latencia_promedio()`
   - `_calcular_tasa_error()`
   - `_calcular_carga_sistema()`

2. Agregar logs de auditoría para actividad reciente (opcional)

3. Implementar alertas cuando los KPIs caen por debajo de umbrales

## Troubleshooting

### El dashboard muestra ceros
- Verificar que la BD tiene datos: `python services/core-api/init_data.py`
- Verificar conexión a PostgreSQL
- Revisar logs del servicio de analytics

### Error de conexión a Analytics
- Verificar que el servicio está corriendo en puerto 8002
- Verificar variable de entorno `VITE_ANALYTICS_API_URL` en el frontend
- Revisar configuración de CORS en el backend

### Datos no se actualizan
- El cache de Redis dura 5 minutos
- Hacer clic en "Actualizar" en el dashboard
- O esperar 5 minutos para que expire el cache
