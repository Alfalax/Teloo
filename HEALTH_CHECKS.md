# TeLOO V3 Health Checks Documentation

## Overview

All TeLOO V3 services implement comprehensive health checks with three endpoints:
- `/health` - Full health check with dependency validation
- `/health/ready` - Readiness probe for orchestration platforms
- `/health/live` - Liveness probe for orchestration platforms

## Health Check Endpoints

### 1. Full Health Check: `/health`

**Purpose**: Comprehensive health check that validates all service dependencies

**Response Codes**:
- `200 OK` - All critical dependencies are healthy
- `503 Service Unavailable` - One or more critical dependencies are unhealthy

**Response Format**:
```json
{
  "status": "healthy|unhealthy",
  "service": "service-name",
  "version": "3.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "checks": {
    "dependency_name": {
      "status": "healthy|unhealthy|degraded|disabled",
      "message": "Detailed status message",
      "details": {}
    }
  }
}
```

### 2. Readiness Probe: `/health/ready`

**Purpose**: Determines if the service is ready to accept traffic

**Use Case**: 
- Kubernetes readiness probes
- Docker Compose health checks
- Load balancer health checks

**Response Codes**:
- `200 OK` - Service is ready to accept traffic
- `503 Service Unavailable` - Service is not ready

**Response Format**:
```json
{
  "status": "ready|not_ready",
  "service": "service-name",
  "checks": {
    "dependency": "ready|not_ready"
  },
  "error": "Error message if not ready"
}
```

### 3. Liveness Probe: `/health/live`

**Purpose**: Determines if the service is alive and should not be restarted

**Use Case**:
- Kubernetes liveness probes
- Container restart policies
- Lightweight health monitoring

**Response Codes**:
- `200 OK` - Service is alive

**Response Format**:
```json
{
  "status": "alive",
  "service": "service-name",
  "version": "3.0.0"
}
```

## Service-Specific Health Checks

### Core API Service (Port 8000)

**Dependencies Checked**:
- PostgreSQL database connection
- Redis cache connection
- Scheduler service status

**Example**:
```bash
# Full health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/health/ready

# Liveness check
curl http://localhost:8000/health/live
```

**Critical Dependencies**:
- Database: Required for all operations
- Redis: Required for caching and pub/sub

### Agent IA Service (Port 8001)

**Dependencies Checked**:
- Redis connection
- Core API connectivity
- WhatsApp configuration

**Example**:
```bash
curl http://localhost:8001/health
```

**Critical Dependencies**:
- Redis: Required for rate limiting and caching
- Core API: Required for creating solicitudes

### Analytics Service (Port 8002)

**Dependencies Checked**:
- PostgreSQL read replica connection
- Redis connection
- Event collector status
- Scheduler status
- Alert system status

**Example**:
```bash
curl http://localhost:8002/health
```

**Critical Dependencies**:
- Database: Required for metrics calculation
- Redis: Required for event collection
- Event Collector: Required for real-time metrics

### Files Service (Port 8003)

**Dependencies Checked**:
- MinIO object storage connection
- ClamAV antivirus status (if enabled)
- Upload directory accessibility

**Example**:
```bash
curl http://localhost:8003/health
```

**Critical Dependencies**:
- MinIO: Required for file storage

### Realtime Gateway Service (Port 8004)

**Dependencies Checked**:
- Redis connection
- WebSocket server status
- Event listener status

**Example**:
```bash
curl http://localhost:8004/health
```

**Critical Dependencies**:
- Redis: Required for pub/sub and session management

## Docker Compose Configuration

Use the provided `docker-compose.healthchecks.yml` file to configure health checks:

```bash
docker-compose -f docker-compose.yml -f docker-compose.healthchecks.yml up
```

**Health Check Configuration**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
  interval: 30s      # Check every 30 seconds
  timeout: 10s       # Timeout after 10 seconds
  retries: 3         # Retry 3 times before marking unhealthy
  start_period: 40s  # Grace period during startup
```

## Kubernetes Configuration

Use the provided `kubernetes-healthchecks.yaml` file for Kubernetes deployments:

```bash
kubectl apply -f kubernetes-healthchecks.yaml
```

**Probe Configuration**:

1. **Liveness Probe**: Checks if container should be restarted
   - Initial delay: 30 seconds
   - Period: 30 seconds
   - Timeout: 5 seconds
   - Failure threshold: 3 attempts

2. **Readiness Probe**: Checks if container should receive traffic
   - Initial delay: 20 seconds
   - Period: 10 seconds
   - Timeout: 5 seconds
   - Failure threshold: 3 attempts

3. **Startup Probe**: Gives container time to start
   - Initial delay: 0 seconds
   - Period: 10 seconds
   - Timeout: 5 seconds
   - Failure threshold: 12 attempts (120 seconds total)

## Monitoring and Alerting

### Prometheus Integration

Health check metrics are automatically exposed via the `/metrics` endpoint (Core API):

```bash
curl http://localhost:8000/metrics
```

**Key Metrics**:
- `teloo_health_check_status{service="core-api"}` - Overall health status
- `teloo_dependency_status{service="core-api",dependency="database"}` - Dependency status
- `teloo_health_check_duration_seconds` - Health check execution time

### Grafana Dashboards

Import the provided `services/core-api/grafana-dashboard.json` for visualization:
- Service health status over time
- Dependency availability
- Health check response times
- Alert history

### Alert Configuration

Configure alerts in `services/core-api/prometheus-alerts.yml`:

```yaml
- alert: ServiceUnhealthy
  expr: teloo_health_check_status == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Service {{ $labels.service }} is unhealthy"
```

## Best Practices

### 1. Health Check Design

- **Liveness**: Keep lightweight, only check if process is alive
- **Readiness**: Check critical dependencies, but keep fast (<5s)
- **Full Health**: Comprehensive checks, can be slower

### 2. Dependency Checks

- **Critical**: Database, Redis - must be healthy
- **Degraded**: External APIs, optional features - can be degraded
- **Disabled**: Optional features like ClamAV

### 3. Timeouts

- Set appropriate timeouts for each dependency
- Use circuit breakers for external services
- Fail fast to avoid cascading failures

### 4. Monitoring

- Monitor health check response times
- Alert on repeated failures
- Track dependency availability over time

## Troubleshooting

### Service Shows Unhealthy

1. Check the `/health` endpoint for detailed status:
   ```bash
   curl http://localhost:8000/health | jq
   ```

2. Identify which dependency is failing:
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

3. Check dependency logs:
   ```bash
   docker-compose logs postgres
   ```

### Readiness Probe Failing

1. Check if service has finished initialization:
   ```bash
   docker-compose logs core-api | grep "started successfully"
   ```

2. Verify dependencies are ready:
   ```bash
   curl http://localhost:5432  # PostgreSQL
   curl http://localhost:6379  # Redis
   ```

3. Increase `initialDelaySeconds` if service needs more startup time

### Liveness Probe Causing Restarts

1. Check if service is actually hung or just slow:
   ```bash
   docker-compose exec core-api ps aux
   ```

2. Review application logs for errors:
   ```bash
   docker-compose logs --tail=100 core-api
   ```

3. Adjust probe timing if service is under heavy load

## Testing Health Checks

### Manual Testing

```bash
# Test all services
for port in 8000 8001 8002 8003 8004; do
  echo "Testing port $port..."
  curl -s http://localhost:$port/health | jq '.status'
done

# Test with timeout
curl --max-time 5 http://localhost:8000/health

# Test readiness
curl http://localhost:8000/health/ready

# Test liveness
curl http://localhost:8000/health/live
```

### Automated Testing

```bash
# Health check test script
#!/bin/bash
set -e

SERVICES=("core-api:8000" "agent-ia:8001" "analytics:8002" "files:8003" "realtime-gateway:8004")

for service in "${SERVICES[@]}"; do
  IFS=':' read -r name port <<< "$service"
  echo "Testing $name..."
  
  # Test liveness
  if ! curl -f -s http://localhost:$port/health/live > /dev/null; then
    echo "❌ $name liveness check failed"
    exit 1
  fi
  
  # Test readiness
  if ! curl -f -s http://localhost:$port/health/ready > /dev/null; then
    echo "⚠️  $name not ready"
  fi
  
  echo "✅ $name is healthy"
done

echo "All services are healthy!"
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Wait for services to be healthy
  run: |
    timeout 120 bash -c 'until curl -f http://localhost:8000/health/ready; do sleep 5; done'
    timeout 120 bash -c 'until curl -f http://localhost:8001/health/ready; do sleep 5; done'

- name: Run integration tests
  run: |
    npm run test:integration
```

### Docker Compose Wait Script

```bash
#!/bin/bash
# wait-for-healthy.sh

services=("core-api" "agent-ia" "analytics" "files" "realtime-gateway")

for service in "${services[@]}"; do
  echo "Waiting for $service to be healthy..."
  while [ "$(docker-compose ps -q $service | xargs docker inspect -f '{{.State.Health.Status}}')" != "healthy" ]; do
    sleep 2
  done
  echo "$service is healthy"
done

echo "All services are healthy!"
```

## References

- [Kubernetes Liveness and Readiness Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Docker Compose Healthcheck](https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck)
- [Prometheus Monitoring](https://prometheus.io/docs/introduction/overview/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
