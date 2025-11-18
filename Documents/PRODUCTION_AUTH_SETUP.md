# Configuración de Autenticación para Producción

## Resumen

La solución actual funciona bien para **desarrollo**, pero necesita mejoras para **producción**. Este documento describe los pasos necesarios.

## Estado Actual vs Producción

| Característica | Desarrollo | Producción Requerida |
|----------------|------------|---------------------|
| Refresh automático | ✅ | ✅ |
| Manejo de 401 | ✅ | ✅ |
| Persistencia de tokens | ❌ | ✅ Requerido |
| Sincronización multi-tab | ❌ | ✅ Recomendado |
| Logging de seguridad | ❌ | ✅ Requerido |
| Rate limiting | ❌ | ✅ Requerido |
| Device fingerprinting | ❌ | ⚠️ Opcional |
| Rotación de tokens | ❌ | ✅ Recomendado |

## Implementación Paso a Paso

### Paso 1: Configurar Redis para Tokens (Backend)

**Prioridad: ALTA** - Sin esto, los tokens se pierden al reiniciar el servidor.

```bash
# docker-compose.yml
services:
  redis-auth:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    volumes:
      - redis-auth-data:/data
    command: redis-server --appendonly yes

volumes:
  redis-auth-data:
```

```python
# services/core-api/core/redis_auth.py
import redis
from typing import Optional
from datetime import timedelta

class RefreshTokenStore:
    def __init__(self):
        self.redis = redis.Redis(
            host='redis-auth',
            port=6379,
            db=0,
            decode_responses=True
        )
    
    def store(self, token: str, user_id: str, expires_in: int = 2592000):
        """Store refresh token with 30 days expiration"""
        key = f"refresh_token:{token}"
        self.redis.setex(key, expires_in, user_id)
    
    def validate(self, token: str) -> Optional[str]:
        """Validate and return user_id"""
        key = f"refresh_token:{token}"
        return self.redis.get(key)
    
    def revoke(self, token: str):
        """Revoke a refresh token"""
        key = f"refresh_token:{token}"
        self.redis.delete(key)
    
    def revoke_all_user_tokens(self, user_id: str):
        """Revoke all tokens for a user"""
        pattern = f"refresh_token:*"
        for key in self.redis.scan_iter(pattern):
            if self.redis.get(key) == user_id:
                self.redis.delete(key)

refresh_token_store = RefreshTokenStore()
```

```python
# services/core-api/services/auth_service.py
from core.redis_auth import refresh_token_store

def create_refresh_token(user_id: str) -> str:
    """Create and store refresh token"""
    refresh_token = secrets.token_urlsafe(32)
    refresh_token_store.store(refresh_token, user_id)
    return refresh_token

def validate_refresh_token(refresh_token: str) -> Optional[str]:
    """Validate refresh token"""
    return refresh_token_store.validate(refresh_token)

def revoke_refresh_token(refresh_token: str):
    """Revoke refresh token"""
    refresh_token_store.revoke(refresh_token)
```

### Paso 2: Implementar Rotación de Tokens (Backend)

**Prioridad: MEDIA** - Mejora la seguridad.

```python
# services/core-api/routers/auth.py

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token with token rotation"""
    
    # Validate old refresh token
    user_id = validate_refresh_token(request.refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Revoke old refresh token (one-time use)
    revoke_refresh_token(request.refresh_token)
    
    # Generate new tokens
    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,  # ← Nuevo token
        "token_type": "bearer"
    }
```

```typescript
// frontend/admin/src/lib/axios.ts
// Actualizar para guardar el nuevo refresh token

try {
  const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
    refresh_token: refreshToken,
  });

  const { access_token, refresh_token: new_refresh_token } = response.data;

  // Save both tokens
  localStorage.setItem('access_token', access_token);
  if (new_refresh_token) {
    localStorage.setItem('refresh_token', new_refresh_token);
  }

  // ... rest of code
}
```

### Paso 3: Sincronización Multi-Tab (Frontend)

**Prioridad: MEDIA** - Mejora UX.

```typescript
// frontend/admin/src/contexts/AuthContext.tsx

useEffect(() => {
  // Listen for storage changes from other tabs
  const handleStorageChange = (e: StorageEvent) => {
    // If access token was removed in another tab, logout here too
    if (e.key === 'access_token' && !e.newValue) {
      console.log('Token removed in another tab, logging out');
      dispatch({ type: 'CLEAR_AUTH' });
    }
    
    // If new token was set in another tab, update here
    if (e.key === 'access_token' && e.newValue) {
      console.log('Token updated in another tab, refreshing user');
      refreshUser();
    }
  };

  window.addEventListener('storage', handleStorageChange);
  
  return () => {
    window.removeEventListener('storage', handleStorageChange);
  };
}, []);
```

### Paso 4: Rate Limiting (Backend)

**Prioridad: ALTA** - Previene ataques de fuerza bruta.

```python
# services/core-api/middleware/rate_limit.py

from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/refresh")
@limiter.limit("10/minute")  # Max 10 refresh attempts per minute
async def refresh_token(request: Request, token_request: RefreshTokenRequest):
    # ... existing code
```

### Paso 5: Logging y Monitoreo (Backend)

**Prioridad: ALTA** - Detecta problemas de seguridad.

```python
# services/core-api/services/security_logger.py

import logging
from datetime import datetime

security_logger = logging.getLogger('security')

def log_auth_event(event_type: str, user_id: str = None, details: dict = None):
    """Log security events"""
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'details': details or {}
    }
    
    if event_type in ['refresh_failed', 'invalid_token', 'token_expired']:
        security_logger.warning(f"Security event: {log_data}")
    else:
        security_logger.info(f"Auth event: {log_data}")

# Uso en auth_service.py
def validate_refresh_token(refresh_token: str) -> Optional[str]:
    user_id = refresh_token_store.validate(refresh_token)
    
    if not user_id:
        log_auth_event('refresh_failed', details={'reason': 'invalid_token'})
        return None
    
    log_auth_event('refresh_success', user_id=user_id)
    return user_id
```

### Paso 6: Variables de Entorno

```bash
# .env.production

# JWT Configuration
JWT_SECRET_KEY=<strong-random-key-here>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# Redis Configuration
REDIS_AUTH_HOST=redis-auth
REDIS_AUTH_PORT=6379
REDIS_AUTH_DB=0

# Security
ENABLE_TOKEN_ROTATION=true
MAX_REFRESH_ATTEMPTS_PER_MINUTE=10
ENABLE_DEVICE_FINGERPRINTING=false
```

## Orden de Implementación Recomendado

1. **Paso 1** (Redis) - CRÍTICO para producción
2. **Paso 4** (Rate Limiting) - CRÍTICO para seguridad
3. **Paso 5** (Logging) - CRÍTICO para monitoreo
4. **Paso 2** (Rotación) - Recomendado
5. **Paso 3** (Multi-tab) - Nice to have

## Testing en Producción

```bash
# Test 1: Verificar persistencia de tokens
1. Login
2. Reiniciar servidor backend
3. Hacer una petición → Debería funcionar sin re-login

# Test 2: Verificar rate limiting
1. Intentar refresh 15 veces en 1 minuto
2. Debería bloquear después de 10 intentos

# Test 3: Verificar multi-tab
1. Abrir 2 tabs
2. Logout en tab 1
3. Tab 2 debería detectar y hacer logout también

# Test 4: Verificar rotación
1. Login y guardar refresh token
2. Usar refresh token
3. Intentar usar el mismo refresh token de nuevo
4. Debería fallar (one-time use)
```

## Monitoreo en Producción

Métricas a monitorear:

- Tasa de refresh exitosos vs fallidos
- Número de sesiones activas
- Intentos de refresh bloqueados por rate limit
- Tokens revocados manualmente
- Tiempo promedio de sesión

## Rollback Plan

Si algo falla en producción:

1. Revertir a versión anterior del backend
2. Los tokens en Redis persisten
3. Frontend sigue funcionando con refresh automático
4. Usuarios no necesitan re-login

## Conclusión

**Para desarrollo**: La solución actual es suficiente.

**Para producción**: Implementar mínimo los pasos 1, 4 y 5 antes de lanzar.

**Tiempo estimado**: 2-3 días de desarrollo + testing.
