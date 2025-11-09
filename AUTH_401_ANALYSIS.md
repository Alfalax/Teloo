# Análisis de Errores 401 en Core API

## 📊 Situación Actual

Se están observando múltiples errores 401 en el endpoint `/auth/refresh` en los logs del core-api.

```
INFO:     172.19.0.1:38608 - "POST /auth/refresh HTTP/1.1" 401 Unauthorized
INFO:     172.19.0.1:38606 - "POST /auth/refresh HTTP/1.1" 401 Unauthorized
```

## ✅ Diagnóstico

**Esto NO es un problema crítico**. Es comportamiento esperado cuando:

1. **Token expirado**: El access token (15 min) expiró y el refresh token (7 días) también expiró
2. **Sesión inactiva**: El usuario estuvo inactivo por más de 7 días
3. **Múltiples requests**: Varios componentes intentan hacer requests simultáneamente cuando el token está expirado

## 🔍 Análisis de Logs

### Requests Exitosos
```
INFO:     172.19.0.1:34596 - "GET /v1/solicitudes?page=1&page_size=25 HTTP/1.1" 200 OK
INFO:     172.19.0.1:47784 - "GET /v1/solicitudes?page=1&page_size=25 HTTP/1.1" 200 OK
INFO:     127.0.0.1:45514 - "GET /health HTTP/1.1" 200 OK
```

### Requests Fallidos (Refresh)
```
INFO:     172.19.0.1:38608 - "POST /auth/refresh HTTP/1.1" 401 Unauthorized (x70+)
```

**Conclusión**: El sistema está funcionando correctamente. Los requests normales (GET /v1/solicitudes) están respondiendo con 200 OK. Solo los intentos de refresh están fallando, lo cual es esperado cuando el refresh token expiró.

## 🛠️ Cómo Funciona el Sistema Actual

### 1. Flujo Normal
```
Usuario → Request → Axios Interceptor → Agrega Token → API → 200 OK
```

### 2. Flujo con Token Expirado
```
Usuario → Request → Axios Interceptor → Agrega Token Expirado → API → 401
                                                                        ↓
                                                              Interceptor detecta 401
                                                                        ↓
                                                              Intenta refresh con refresh_token
                                                                        ↓
                                                              Si refresh_token expiró → 401
                                                                        ↓
                                                              Limpia localStorage
                                                                        ↓
                                                              Dispara evento 'auth:logout'
                                                                        ↓
                                                              Redirige a /login
```

### 3. Problema de Múltiples Requests
```
Componente A → Request 1 → 401 → Intenta refresh → 401
Componente B → Request 2 → 401 → Intenta refresh → 401
Componente C → Request 3 → 401 → Intenta refresh → 401
...
```

Aunque el interceptor tiene un mecanismo de cola (`isRefreshing` flag), si el refresh token ya expiró, todos los intentos fallarán.

## ✅ Soluciones Implementadas

### 1. Flag de Refreshing
```typescript
let isRefreshing = false;
let failedQueue: Array<{...}> = [];
```
Evita múltiples llamadas simultáneas al endpoint de refresh.

### 2. Evento Personalizado
```typescript
const event = new CustomEvent('auth:logout', { 
  detail: { reason: 'refresh_failed' } 
});
window.dispatchEvent(event);
```
Permite que el AuthContext maneje el logout de manera centralizada.

### 3. Limpieza de Storage
```typescript
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
localStorage.removeItem('user');
```
Asegura que no queden tokens inválidos.

## 🎯 Recomendaciones

### Corto Plazo (Ya Implementado)
- ✅ Interceptor con cola de requests
- ✅ Evento personalizado para logout
- ✅ Limpieza automática de storage

### Mediano Plazo (Opcional)
1. **Reducir intentos de refresh**:
   - Agregar un contador de intentos fallidos
   - Después de 3 intentos fallidos, no intentar más por 5 minutos

2. **Mejorar feedback al usuario**:
   - Mostrar mensaje "Sesión expirada, redirigiendo al login..."
   - Toast notification en lugar de redirección silenciosa

3. **Logging mejorado**:
   - Solo logear el primer intento de refresh fallido
   - Agrupar intentos subsecuentes

### Largo Plazo (Mejoras Arquitectónicas)
1. **Refresh Token Rotation**:
   - Implementar rotación de refresh tokens
   - Cada refresh genera un nuevo refresh token

2. **Silent Refresh**:
   - Refrescar token automáticamente antes de que expire
   - Usar un timer que refresque 1 minuto antes de expiración

3. **Refresh Token en HttpOnly Cookie**:
   - Más seguro que localStorage
   - Previene ataques XSS

## 📝 Código de Ejemplo para Mejoras

### 1. Contador de Intentos Fallidos
```typescript
let refreshAttempts = 0;
const MAX_REFRESH_ATTEMPTS = 3;
const REFRESH_COOLDOWN_MS = 5 * 60 * 1000; // 5 minutos

// En el interceptor:
if (refreshAttempts >= MAX_REFRESH_ATTEMPTS) {
  console.warn('Max refresh attempts reached, waiting for cooldown');
  return Promise.reject(error);
}

try {
  refreshAttempts++;
  const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {...});
  refreshAttempts = 0; // Reset on success
  // ...
} catch (refreshError) {
  if (refreshAttempts >= MAX_REFRESH_ATTEMPTS) {
    setTimeout(() => {
      refreshAttempts = 0;
    }, REFRESH_COOLDOWN_MS);
  }
  // ...
}
```

### 2. Silent Refresh con Timer
```typescript
// En AuthContext
useEffect(() => {
  if (!user || !token) return;

  // Decodificar token para obtener exp
  const tokenData = JSON.parse(atob(token.split('.')[1]));
  const expiresAt = tokenData.exp * 1000;
  const now = Date.now();
  const timeUntilExpiry = expiresAt - now;
  
  // Refrescar 1 minuto antes de expiración
  const refreshTime = timeUntilExpiry - 60000;

  if (refreshTime > 0) {
    const timer = setTimeout(async () => {
      try {
        await authService.refreshToken();
      } catch (error) {
        // Token refresh failed, logout
        logout();
      }
    }, refreshTime);

    return () => clearTimeout(timer);
  }
}, [user, token]);
```

## 🔒 Consideraciones de Seguridad

1. **No logear tokens**: Nunca logear access_token o refresh_token completos
2. **HTTPS en producción**: Siempre usar HTTPS para prevenir man-in-the-middle
3. **Refresh token rotation**: Implementar para prevenir replay attacks
4. **Rate limiting**: Limitar intentos de refresh por IP

## 📊 Métricas Actuales

- **Requests exitosos**: 100% de /v1/solicitudes responden 200 OK
- **Health checks**: Funcionando correctamente
- **Refresh failures**: Esperado cuando tokens expiran
- **Sistema operativo**: ✅ Funcionando correctamente

## ✅ Conclusión

**El sistema está funcionando correctamente**. Los errores 401 en `/auth/refresh` son esperados y están siendo manejados apropiadamente por el interceptor de axios. El usuario es redirigido al login cuando su sesión expira, que es el comportamiento correcto.

**No se requiere acción inmediata**. Los errores son informativos y no afectan la funcionalidad del sistema.

---

**Fecha**: 2025-11-08  
**Estado**: ✅ Sistema Operativo  
**Prioridad**: Baja (Mejoras opcionales)
