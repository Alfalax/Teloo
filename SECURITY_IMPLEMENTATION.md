# 🔒 Implementación de Seguridad para Producción

## Resumen

Se ha implementado un sistema completo de autenticación y seguridad para la comunicación entre servicios (agent-ia ↔ core-api), listo para producción.

## ✅ Componentes Implementados

### 1. Autenticación de Servicios (Service-to-Service Auth)

**Archivo:** `services/core-api/middleware/service_auth.py`

- ✅ Validación mediante API Keys únicas por servicio
- ✅ Headers requeridos: `X-Service-Name` y `X-Service-API-Key`
- ✅ Logging completo de intentos de autenticación
- ✅ Mensajes de error descriptivos sin exponer información sensible

**Uso:**
```python
from middleware.service_auth import verify_service_api_key

@router.post("/services/endpoint")
async def secure_endpoint(
    service_name: str = Depends(verify_service_api_key)
):
    # Solo servicios autenticados pueden acceder
    pass
```

### 2. Rate Limiting

**Archivo:** `services/core-api/middleware/rate_limiter.py`

- ✅ Límite de 60 peticiones por minuto por servicio
- ✅ Ventana deslizante de 60 segundos
- ✅ Respuesta HTTP 429 cuando se excede el límite
- ✅ Header `Retry-After` para indicar cuándo reintentar

**Nota:** Para producción con múltiples instancias, migrar a Redis.

### 3. Endpoints Seguros

**Archivo:** `services/core-api/routers/solicitudes.py`

#### `/v1/solicitudes/services/municipio` (GET)
- Buscar municipios por nombre
- Requiere autenticación de servicio
- Logging de todas las búsquedas

#### `/v1/solicitudes/services/bot` (POST)
- Crear solicitudes desde bots (Telegram/WhatsApp)
- Requiere autenticación de servicio
- Logging completo para auditoría
- Validación de datos de entrada

### 4. Cliente Seguro (Agent-IA)

**Archivo:** `services/agent-ia/app/services/telegram_message_processor.py`

- ✅ Envía headers de autenticación en todas las peticiones
- ✅ Manejo de errores 401 (no autenticado) y 429 (rate limit)
- ✅ Configuración desde variables de entorno

## 🔑 Configuración de API Keys

### Generar API Keys Seguras

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Variables de Entorno

#### Core API (`services/core-api/.env`)
```env
AGENT_IA_API_KEY=m4YQECAHqUZl_4O9p3ZG8YlYjvFF_IAbxiFu6l_6epk
ANALYTICS_API_KEY=wHe7MRSvi1prmjG9H75CmiDxaRON7mDDbe9fKQ8bt0E
```

#### Agent IA (`services/agent-ia/.env`)
```env
SERVICE_NAME=agent-ia
SERVICE_API_KEY=m4YQECAHqUZl_4O9p3ZG8YlYjvFF_IAbxiFu6l_6epk
```

**⚠️ IMPORTANTE:** Las API keys deben coincidir entre servicios.

## 🛡️ Características de Seguridad

### ✅ Implementado

1. **Autenticación de Servicios**
   - API Keys únicas por servicio
   - Validación en cada petición
   - No hay endpoints públicos sin autenticación

2. **Rate Limiting**
   - Protección contra abuso
   - Límites configurables
   - Respuestas estándar HTTP 429

3. **Logging y Auditoría**
   - Todas las peticiones se registran
   - Incluye: servicio, acción, resultado
   - Útil para debugging y auditoría

4. **Validación de Datos**
   - Validación de entrada con Pydantic
   - Mensajes de error descriptivos
   - Prevención de inyección de datos

5. **Manejo de Errores**
   - Errores descriptivos sin exponer detalles internos
   - Códigos HTTP estándar
   - Stack traces solo en desarrollo

### 🔄 Recomendaciones para Producción

1. **Migrar Rate Limiting a Redis**
   ```python
   # Para múltiples instancias de core-api
   from redis import Redis
   redis_client = Redis(host='redis', port=6379)
   ```

2. **Rotar API Keys Periódicamente**
   - Cada 90 días mínimo
   - Usar secretos de Kubernetes/Docker Swarm
   - Nunca hardcodear en código

3. **Monitoreo**
   - Alertas de intentos de autenticación fallidos
   - Métricas de rate limiting
   - Dashboard de uso por servicio

4. **HTTPS en Producción**
   - Certificados SSL/TLS
   - Nginx como reverse proxy
   - Headers de seguridad (HSTS, CSP, etc.)

## 📊 Flujo de Autenticación

```
┌─────────────┐                    ┌─────────────┐
│  Agent-IA   │                    │  Core-API   │
│   (Bot)     │                    │             │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │  POST /services/bot              │
       │  Headers:                        │
       │    X-Service-Name: agent-ia      │
       │    X-Service-API-Key: xxx        │
       ├─────────────────────────────────>│
       │                                  │
       │                                  │ 1. Verificar headers
       │                                  │ 2. Validar API key
       │                                  │ 3. Check rate limit
       │                                  │ 4. Procesar solicitud
       │                                  │ 5. Log auditoría
       │                                  │
       │  201 Created                     │
       │  {solicitud_id: "xxx"}           │
       │<─────────────────────────────────┤
       │                                  │
```

## 🧪 Testing

### Test Manual

```bash
# Sin autenticación (debe fallar)
curl -X POST http://localhost:8000/v1/solicitudes/services/bot \
  -H "Content-Type: application/json" \
  -d '{"cliente": {...}}'

# Respuesta: 401 Unauthorized

# Con autenticación (debe funcionar)
curl -X POST http://localhost:8000/v1/solicitudes/services/bot \
  -H "Content-Type: application/json" \
  -H "X-Service-Name: agent-ia" \
  -H "X-Service-API-Key: m4YQECAHqUZl_4O9p3ZG8YlYjvFF_IAbxiFu6l_6epk" \
  -d '{"cliente": {...}}'

# Respuesta: 201 Created
```

### Test de Rate Limiting

```bash
# Hacer 61 peticiones rápidas
for i in {1..61}; do
  curl -X GET http://localhost:8000/v1/solicitudes/services/municipio?ciudad=Bogota \
    -H "X-Service-Name: agent-ia" \
    -H "X-Service-API-Key: xxx"
done

# La petición 61 debe retornar: 429 Too Many Requests
```

## 🔄 Migración desde Endpoints Públicos

### Antes (Inseguro)
```python
# ❌ Cualquiera puede acceder
@router.post("/public/bot")
async def create_solicitud(request: CreateSolicitudRequest):
    pass
```

### Después (Seguro)
```python
# ✅ Solo servicios autenticados
@router.post("/services/bot")
async def create_solicitud(
    request: CreateSolicitudRequest,
    service_name: str = Depends(verify_service_api_key)
):
    pass
```

## 📝 Checklist de Seguridad

- [x] Autenticación de servicios implementada
- [x] Rate limiting implementado
- [x] Logging y auditoría completa
- [x] API keys generadas y configuradas
- [x] Endpoints públicos eliminados
- [x] Validación de datos de entrada
- [x] Manejo de errores seguro
- [x] Documentación completa
- [ ] Tests automatizados de seguridad
- [ ] Migrar rate limiting a Redis (para múltiples instancias)
- [ ] Configurar HTTPS en producción
- [ ] Implementar rotación de API keys
- [ ] Configurar alertas de seguridad

## 🚀 Próximos Pasos

1. **WhatsApp Integration**
   - Usar los mismos endpoints seguros
   - Misma autenticación de servicio
   - Reutilizar toda la lógica implementada

2. **Analytics Service**
   - Agregar autenticación similar
   - Usar `ANALYTICS_API_KEY`
   - Endpoints `/services/analytics/*`

3. **Monitoreo**
   - Prometheus metrics
   - Grafana dashboards
   - Alertas de seguridad

## 📚 Referencias

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
