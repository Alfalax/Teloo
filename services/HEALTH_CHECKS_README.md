# Health Checks Implementation Guide

## Overview

This document describes the health check implementation for all TeLOO V3 microservices. Each service implements three types of health check endpoints to support different monitoring and orchestration scenarios.

## Health Check Endpoints

### 1. Full Health Check: `GET /health`

**Purpose**: Comprehensive health check that validates all service dependencies.

**When to Use**:
- Manual health verification
- Detailed troubleshooting
- Monitoring dashboards
- Health status reporting

**Response**:
- `200 OK`: All critical dependencies are healthy
- `503 Service Unavailable`: One or more critical dependencies are unhealthy

**Example Response**:
```json
{
  "status": "healthy",
  "service": "core-api",
  "version": "3.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "redis": {
      "status": "healthy",
      "message": "Redis connection successful"
    },
    "scheduler": {
      "status": "healthy",
      "message": "Scheduler operational",
      "details": {
        "status": "running",
        "jobs": 5
      }
    }
  }
}
```

### 2. Readiness Probe: `GET /health/ready`

**Purpose**: Determines if the service is ready to accept traffic.

**When to Use**:
- Kubernetes readiness probes
- Load balancer health checks
- Service mesh routing decisions
- Rolling deployment validation

**Response**:
- `200 OK`: Service is ready to accept traffic
- `503 Service Unavailable`: Service is not ready

**Example Response**:
```json
{
  "status": "ready",
  "service": "core-api",
  "checks": {
    "database": "ready",
    "scheduler": "ready"
  }
}
```

### 3. Liveness Probe: `GET /health/live`

**Purpose**: Determines if the service is alive and should not be restarted.

**When to Use**:
- Kubernetes liveness probes
- Container restart policies
- Lightweight health monitoring
- Quick availability checks

**Response**:
- `200 OK`: Service is alive

**Example Response**:
```json
{
  "status": "alive",
  "service": "core-api",
  "version": "3.0.0"
}
```

## Service-Specific Implementation

### Core API Service

**Port**: 8000

**Dependencies Checked**:
- PostgreSQL database (critical)
- Redis cache (critical)
- Scheduler service (non-critical)

**Implementation Details**:
```python
# Full health check
@app.get("/health")
async def health_check():
    # Check database connection
    conn = connections.get("default")
    await conn.execute_query("SELECT 1")
    
    # Check Redis connection
    redis_client = aioredis.from_url(redis_url)
    await redis_client.ping()
    
    # Check scheduler status
    scheduler_status = scheduler_service.get_job_status()
    
    return health_status
```

### Agent IA Service

**Port**: 8001

**Dependencies Checked**:
- Redis connection (critical)
- Core API connectivity (non-critical)
- WhatsApp configuration (non-critical)

**Implementation Details**:
```python
# Readiness check
@app.get("/health/ready")
async def readiness_check():
    # Check Redis is accessible
    await redis_manager.redis_client.ping()
    
    return {"status": "ready"}
```

### Analytics Service

**Port**: 8002

**Dependencies Checked**:
- PostgreSQL read replica (critical)
- Redis connection (critical)
- Event collector status (critical)
- Scheduler status (non-critical)
- Alert system status (non-critical)

### Files Service

**Port**: 8003

**Dependencies Checked**:
- MinIO object storage (critical)
- ClamAV antivirus (non-critical, if enabled)
- Upload directory accessibility (critical)

### Realtime Gateway Service

**Port**: 8004

**Dependencies Checked**:
- Redis connection (critical)
- WebSocket server status (critical)
- Event listener status (critical)

## Dependency Status Levels

### Healthy
- Dependency is fully operational
- All checks passed
- Service can operate normally

### Degraded
- Dependency has issues but service can continue
- Non-critical features may be affected
- Service remains operational

### Unhealthy
- Critical dependency has failed
- Service cannot operate properly
- Requires immediate attention

### Disabled
- Feature is intentionally disabled
- Not an error condition
- Example: ClamAV antivirus when not configured

## Testing Health Checks

### Manual Testing

```bash
# Test all services
./test_health_checks.sh

# Test specific service
curl http://localhost:8000/health | jq

# Test with timeout
curl --max-time 5 http://localhost:8000/health

# Test readiness
curl http://localhost:8000/health/ready

# Test liveness
curl http://localhost:8000/health/live
```

### Automated Testing

```bash
# Python test script
python3 test_health_checks.py

# Results saved to health_check_results.json
cat health_check_results.json | jq
```

### Integration Testing

```python
import httpx
import pytest

@pytest.mark.asyncio
async def test_core_api_health():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
```

## Docker Compose Configuration

### Basic Health Check

```yaml
services:
  core-api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### With Dependencies

```yaml
services:
  core-api:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
```

### Complete Configuration

See `docker-compose.healthchecks.yml` for full configuration.

## Kubernetes Configuration

### Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3
```

### Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 20
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Startup Probe

```yaml
startupProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 12  # 120 seconds total
```

### Complete Configuration

See `kubernetes-healthchecks.yaml` for full configuration.

## Monitoring and Alerting

### Prometheus Metrics

Health check metrics are exposed via `/metrics`:

```
# HELP teloo_health_check_status Overall health status (1=healthy, 0=unhealthy)
# TYPE teloo_health_check_status gauge
teloo_health_check_status{service="core-api"} 1

# HELP teloo_dependency_status Dependency health status
# TYPE teloo_dependency_status gauge
teloo_dependency_status{service="core-api",dependency="database"} 1
teloo_dependency_status{service="core-api",dependency="redis"} 1
```

### Grafana Dashboard

Import `services/core-api/grafana-dashboard.json` for visualization:
- Service health status over time
- Dependency availability
- Health check response times
- Alert history

### Alert Rules

Configure in `services/core-api/prometheus-alerts.yml`:

```yaml
groups:
  - name: health_checks
    rules:
      - alert: ServiceUnhealthy
        expr: teloo_health_check_status == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.service }} is unhealthy"
          
      - alert: DependencyUnhealthy
        expr: teloo_dependency_status == 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Dependency {{ $labels.dependency }} is unhealthy"
```

## Troubleshooting

### Service Shows Unhealthy

1. **Check detailed health status**:
   ```bash
   curl http://localhost:8000/health | jq
   ```

2. **Identify failing dependency**:
   ```json
   {
     "checks": {
       "database": {
         "status": "unhealthy",
         "message": "Database connection failed: connection refused"
       }
     }
   }
   ```

3. **Check dependency logs**:
   ```bash
   docker-compose logs postgres
   ```

4. **Verify dependency is running**:
   ```bash
   docker-compose ps
   ```

### Readiness Probe Failing

1. **Check initialization status**:
   ```bash
   docker-compose logs core-api | grep "started successfully"
   ```

2. **Verify dependencies are ready**:
   ```bash
   curl http://localhost:5432  # PostgreSQL
   curl http://localhost:6379  # Redis
   ```

3. **Increase startup time**:
   ```yaml
   readinessProbe:
     initialDelaySeconds: 40  # Increase from 20
   ```

### Liveness Probe Causing Restarts

1. **Check if service is hung**:
   ```bash
   docker-compose exec core-api ps aux
   ```

2. **Review application logs**:
   ```bash
   docker-compose logs --tail=100 core-api
   ```

3. **Adjust probe timing**:
   ```yaml
   livenessProbe:
     periodSeconds: 60  # Increase from 30
     timeoutSeconds: 10  # Increase from 5
   ```

### Connection Timeouts

1. **Check network connectivity**:
   ```bash
   docker-compose exec core-api ping postgres
   ```

2. **Verify service is listening**:
   ```bash
   docker-compose exec core-api netstat -tlnp
   ```

3. **Check firewall rules**:
   ```bash
   sudo iptables -L
   ```

## Best Practices

### 1. Health Check Design

- **Liveness**: Keep lightweight, only check if process is alive
- **Readiness**: Check critical dependencies, but keep fast (<5s)
- **Full Health**: Comprehensive checks, can be slower

### 2. Dependency Classification

- **Critical**: Must be healthy for service to operate (database, Redis)
- **Non-Critical**: Service can operate with degraded functionality
- **Optional**: Features that can be disabled (ClamAV)

### 3. Timeout Configuration

- Set appropriate timeouts for each dependency
- Use circuit breakers for external services
- Fail fast to avoid cascading failures

### 4. Probe Timing

- **Initial Delay**: Allow time for service initialization
- **Period**: Balance between responsiveness and load
- **Timeout**: Shorter than period to avoid overlap
- **Failure Threshold**: Allow for transient failures

### 5. Monitoring

- Monitor health check response times
- Alert on repeated failures
- Track dependency availability over time
- Use metrics for capacity planning

## References

- [Kubernetes Probes Documentation](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Docker Compose Healthcheck](https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck)
- [Prometheus Monitoring](https://prometheus.io/docs/introduction/overview/)
- [Health Check Pattern](https://microservices.io/patterns/observability/health-check-api.html)
