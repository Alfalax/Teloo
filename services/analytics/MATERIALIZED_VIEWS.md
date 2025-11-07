# Materialized Views for Historical KPIs

This document describes the implementation of materialized views for historical KPIs in the TeLOO V3 Analytics service.

## Overview

The materialized views system provides pre-calculated, cached views of historical data for fast dashboard queries and KPI reporting. The system includes:

- **Two main materialized views** for monthly metrics and advisor rankings
- **Automatic refresh scheduling** at 1:00 AM daily
- **Manual refresh capabilities** via API
- **Comprehensive monitoring** and status reporting

## Materialized Views

### 1. mv_metricas_mensuales

Monthly aggregated metrics for system performance tracking.

**Columns:**
- `mes`: Month (YYYY-MM-01 format)
- `solicitudes_creadas`: Total requests created
- `solicitudes_aceptadas`: Accepted requests
- `solicitudes_rechazadas`: Rejected requests
- `solicitudes_expiradas`: Expired requests
- `solicitudes_sin_ofertas`: Requests without offers
- `tiempo_promedio_cierre_seg`: Average closure time in seconds
- `ofertas_totales`: Total offers submitted
- `ofertas_ganadoras`: Winning offers
- `ofertas_aceptadas`: Accepted offers
- `precio_promedio_ofertas`: Average offer price
- `precio_minimo_ofertas`: Minimum offer price
- `precio_maximo_ofertas`: Maximum offer price
- `tiempo_entrega_promedio`: Average delivery time
- `garantia_promedio_meses`: Average warranty months
- `clientes_activos`: Active clients
- `asesores_activos`: Active advisors
- `marcas_vehiculos_solicitadas`: Vehicle brands requested
- `volumen_transaccional_total`: Total transaction volume
- `tasa_aceptacion_pct`: Acceptance rate percentage
- `tasa_conversion_ofertas_pct`: Offer conversion rate percentage
- `ofertas_promedio_por_solicitud`: Average offers per request

### 2. mv_ranking_asesores

Comprehensive advisor performance rankings by city and nationally.

**Columns:**
- `asesor_id`: Advisor UUID
- `asesor_nombre`: Advisor name
- `asesor_email`: Advisor email
- `ciudad`: City
- `departamento`: Department/State
- `punto_venta`: Sales point
- `confianza`: Trust score
- `nivel_actual`: Current level
- `estado_asesor`: Advisor status
- `actividad_reciente_pct`: Recent activity percentage
- `desempeno_historico_pct`: Historical performance percentage
- `ofertas_historicas_total`: Total historical offers (last 30 days)
- `ofertas_ganadoras`: Winning offers
- `ofertas_aceptadas_cliente`: Client-accepted offers
- `entregas_exitosas`: Successful deliveries
- `tiempo_promedio_respuesta_seg`: Average response time in seconds
- `monto_promedio_ofertas`: Average offer amount
- `volumen_total_ofertas`: Total offer volume
- `confianza_auditada`: Audited trust score
- `auditorias_realizadas`: Number of audits performed
- `ultima_auditoria`: Last audit date
- `notificaciones_recibidas`: Notifications received (last 30 days)
- `notificaciones_respondidas`: Notifications responded to
- `tiempo_promedio_respuesta_notif_seg`: Average notification response time
- `tasa_respuesta_pct`: Response rate percentage
- `tasa_conversion_ofertas_pct`: Offer conversion rate percentage
- `tasa_exito_completo_pct`: Complete success rate percentage
- `ranking_ciudad`: City ranking
- `ranking_nacional`: National ranking
- `percentil_ofertas_ganadoras_ciudad`: City percentile for winning offers
- `percentil_ofertas_ganadoras_nacional`: National percentile for winning offers
- `calculado_at`: Calculation timestamp

## API Endpoints

### Materialized Views Management

- `POST /materialized-views/refresh` - Manually refresh all views
- `GET /materialized-views/status` - Get view status and information
- `GET /materialized-views/health` - Health check for the service

### Data Queries

- `GET /materialized-views/monthly-metrics` - Get monthly metrics
  - Query params: `start_month`, `end_month`, `limit`
- `GET /materialized-views/advisor-rankings` - Get advisor rankings
  - Query params: `ciudad`, `limit`
- `GET /materialized-views/top-advisors` - Get top advisors by metric
  - Query params: `ciudad`, `metric`, `limit`
- `GET /materialized-views/city-summary` - Get summary by city

### Scheduler Management

- `GET /materialized-views/scheduler/status` - Get scheduler status
- `POST /materialized-views/scheduler/trigger-refresh` - Trigger manual refresh
- `PUT /materialized-views/scheduler/reschedule` - Reschedule daily refresh time

## Setup Instructions

### 1. Database Setup

Run the SQL migration to create the materialized views:

```bash
cd services/analytics
python setup_materialized_views.py
```

This script will:
- Create the enhanced materialized views
- Set up the refresh function
- Configure pg_cron if available
- Test the views

### 2. Application Setup

The materialized views service is automatically started with the analytics service:

```bash
cd services/analytics
python main.py
```

### 3. Testing

Test the materialized views functionality:

```bash
cd services/analytics
python test_materialized_views.py
```

## Refresh Schedule

### Automatic Refresh

- **Daily at 1:00 AM** (America/Bogota timezone)
- Uses APScheduler for reliable scheduling
- Fallback to pg_cron if available
- Comprehensive error handling and logging

### Manual Refresh

- Via API: `POST /materialized-views/refresh`
- Via scheduler: `POST /materialized-views/scheduler/trigger-refresh`
- Direct SQL: `SELECT refresh_all_mv();`

## Monitoring

### Health Checks

The service provides multiple health check endpoints:

- `/health` - Overall analytics service health
- `/materialized-views/health` - Specific to materialized views
- `/materialized-views/status` - Detailed view information

### Logging

All operations are logged with appropriate levels:

- `INFO`: Normal operations (refresh start/complete)
- `ERROR`: Failures and exceptions
- `WARNING`: Performance issues or degraded state

### Metrics

The refresh function returns detailed metrics:

- Refresh status per view
- Duration in milliseconds
- Row counts affected
- Error messages if any

## Performance Considerations

### Indexes

The views include optimized indexes for common query patterns:

- Time-based queries (month, calculation timestamp)
- Geographic queries (city, department)
- Ranking queries (city ranking, national ranking)
- Performance metrics (offers won, response rates)

### Refresh Performance

- Views refresh concurrently when possible
- Typical refresh time: 100-500ms per view
- Scales with data volume
- Monitor via `/materialized-views/scheduler/status`

### Query Performance

- Sub-second response times for most queries
- Efficient for dashboard loading
- Supports pagination via `limit` parameters
- Pre-calculated percentiles and rankings

## Troubleshooting

### Common Issues

1. **Views not refreshing**
   - Check scheduler status: `GET /materialized-views/scheduler/status`
   - Check logs for errors
   - Verify database connectivity

2. **Empty views**
   - Ensure base tables have data
   - Run manual refresh: `POST /materialized-views/refresh`
   - Check view population: `GET /materialized-views/status`

3. **Performance issues**
   - Monitor refresh duration in logs
   - Check database load during refresh
   - Consider adjusting refresh schedule

### Debug Commands

```sql
-- Check view status
SELECT * FROM get_mv_stats();

-- Manual refresh with details
SELECT * FROM refresh_all_mv();

-- Check row counts
SELECT COUNT(*) FROM mv_metricas_mensuales;
SELECT COUNT(*) FROM mv_ranking_asesores;
```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `ENVIRONMENT`: development/production (affects logging)

### Scheduler Configuration

The scheduler can be reconfigured via API:

```bash
# Change refresh time to 2:30 AM
curl -X PUT "http://localhost:8002/materialized-views/scheduler/reschedule?hour=2&minute=30"
```

## Integration

### Dashboard Integration

The materialized views are designed for dashboard consumption:

```python
# Get monthly trends
monthly_data = await materialized_views_service.get_monthly_metrics(limit=12)

# Get top performers
top_advisors = await materialized_views_service.get_advisor_rankings(limit=10)
```

### Real-time Updates

While the views refresh daily, real-time metrics are available through:

- Event collector for immediate updates
- Cached metrics for frequently accessed data
- Direct database queries for critical real-time needs

## Future Enhancements

Planned improvements include:

- Additional specialized views for specific KPIs
- Incremental refresh capabilities
- Cross-service view federation
- Advanced alerting on view refresh failures
- Performance optimization based on usage patterns