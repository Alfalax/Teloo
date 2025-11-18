# Solución al Problema de Cache de Autenticación

## Problema
Cuando se reinicia el servidor backend, los tokens JWT almacenados en el navegador se vuelven inválidos, causando errores 401 en todas las peticiones.

## Solución Implementada

### 1. Cliente Axios Global (`frontend/admin/src/lib/axios.ts`)

Creamos un cliente axios centralizado que maneja automáticamente:

- **Inyección de tokens**: Agrega el token de acceso a todas las peticiones
- **Detección de 401**: Intercepta errores de autenticación
- **Refresh automático**: Intenta renovar el token usando el refresh token
- **Cola de peticiones**: Mientras se renueva el token, las peticiones se encolan
- **Logout automático**: Si el refresh falla, limpia el storage y redirige al login

### 2. Flujo de Manejo de Errores 401

```
Petición → 401 Error
    ↓
¿Hay refresh token?
    ↓ Sí
Intentar refresh
    ↓
¿Refresh exitoso?
    ↓ Sí                    ↓ No
Guardar nuevo token    Limpiar storage
Reintentar petición    Redirect a /login
```

### 3. Ventajas

- **Transparente**: Los componentes no necesitan manejar 401s manualmente
- **Automático**: El usuario es redirigido al login solo cuando es necesario
- **Eficiente**: Evita múltiples llamadas de refresh simultáneas
- **Centralizado**: Un solo lugar para manejar autenticación

## Uso

Todos los servicios deben importar y usar `apiClient`:

```typescript
import apiClient from '@/lib/axios';

// Ejemplo
const response = await apiClient.get('/solicitudes');
const data = await apiClient.post('/solicitudes', payload);
```

## Comportamiento Esperado

### Escenario 1: Token válido
- Las peticiones funcionan normalmente
- No hay intervención del interceptor

### Escenario 2: Token expirado pero refresh válido
- Primera petición falla con 401
- Interceptor intenta refresh automáticamente
- Nuevo token se guarda
- Petición original se reintenta con nuevo token
- Usuario no nota nada

### Escenario 3: Servidor reiniciado (ambos tokens inválidos)
- Primera petición falla con 401
- Interceptor intenta refresh
- Refresh falla con 401
- Storage se limpia automáticamente
- Usuario es redirigido a /login
- Usuario debe iniciar sesión nuevamente

## Alternativas Consideradas

### Opción A: Persistencia de Tokens en Backend
- Guardar tokens en base de datos
- Más complejo
- Requiere cambios en backend

### Opción B: Tokens de larga duración
- Menos seguro
- No resuelve el problema de reinicio

### Opción C: Solución actual (Implementada)
- Simple
- Segura
- Transparente para el usuario
- Solo requiere re-login después de reinicio del servidor

## Mejoras para Producción

### 1. Persistencia de Refresh Tokens (Backend)

**Problema**: Cuando el servidor se reinicia, los refresh tokens en memoria se pierden.

**Solución**:
```python
# services/core-api/services/auth_service.py

import redis
from datetime import timedelta

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def store_refresh_token(user_id: str, refresh_token: str, expires_in: int = 2592000):
    """Store refresh token in Redis with 30 days expiration"""
    key = f"refresh_token:{refresh_token}"
    redis_client.setex(
        key,
        timedelta(seconds=expires_in),
        user_id
    )

def validate_refresh_token(refresh_token: str) -> Optional[str]:
    """Validate refresh token and return user_id"""
    key = f"refresh_token:{refresh_token}"
    user_id = redis_client.get(key)
    return user_id.decode() if user_id else None

def revoke_refresh_token(refresh_token: str):
    """Revoke a refresh token"""
    key = f"refresh_token:{refresh_token}"
    redis_client.delete(key)
```

### 2. Manejo de Múltiples Tabs/Ventanas

**Problema**: Si el usuario tiene múltiples tabs abiertas, el logout en una no afecta las otras.

**Solución**: Usar `localStorage` events
```typescript
// En AuthContext.tsx
useEffect(() => {
  const handleStorageChange = (e: StorageEvent) => {
    if (e.key === 'access_token' && !e.newValue) {
      // Token was removed in another tab
      dispatch({ type: 'CLEAR_AUTH' });
      window.location.href = '/login';
    }
  };

  window.addEventListener('storage', handleStorageChange);
  return () => window.removeEventListener('storage', handleStorageChange);
}, []);
```

### 3. Logging y Monitoreo (Producción)

**Implementar**:
- Log de intentos de refresh fallidos
- Alertas cuando hay muchos 401s
- Métricas de sesiones activas

```typescript
// En axios.ts
if (IS_PRODUCTION) {
  // Send to monitoring service (e.g., Sentry, DataDog)
  logSecurityEvent('token_refresh_failed', {
    timestamp: new Date().toISOString(),
    error: refreshError
  });
}
```

### 4. Tokens con Fingerprinting (Seguridad)

**Problema**: Los tokens pueden ser robados y usados desde otro dispositivo.

**Solución**: Agregar device fingerprinting
```python
# Backend: Incluir device fingerprint en el token
def create_access_token(user_id: str, device_fingerprint: str):
    payload = {
        "sub": user_id,
        "device": device_fingerprint,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

### 5. Rotación de Refresh Tokens

**Mejor práctica**: Cada vez que se usa un refresh token, generar uno nuevo.

```python
# Backend
def refresh_access_token(refresh_token: str):
    # Validate old refresh token
    user_id = validate_refresh_token(refresh_token)
    
    # Revoke old refresh token
    revoke_refresh_token(refresh_token)
    
    # Generate new tokens
    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    
    # Store new refresh token
    store_refresh_token(user_id, new_refresh_token)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }
```

## Checklist para Producción

- [ ] Implementar persistencia de refresh tokens en Redis
- [ ] Agregar rotación de refresh tokens
- [ ] Implementar sincronización entre tabs
- [ ] Configurar logging de eventos de seguridad
- [ ] Agregar rate limiting en endpoint de refresh
- [ ] Implementar device fingerprinting (opcional)
- [ ] Configurar alertas para intentos de refresh fallidos
- [ ] Documentar proceso de revocación manual de tokens
- [ ] Implementar endpoint para listar sesiones activas del usuario
- [ ] Agregar opción "Cerrar todas las sesiones"

## Testing

Para probar la solución:

1. Iniciar sesión en la aplicación
2. Reiniciar el servidor backend
3. Intentar navegar o hacer una acción
4. Verificar que se redirige automáticamente al login
5. Iniciar sesión nuevamente
6. Verificar que todo funciona correctamente
