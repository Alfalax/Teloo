# Testing Auth Integration - Checklist

## Pre-requisitos
- [ ] Backend corriendo en `http://localhost:8000`
- [ ] Frontend corriendo en `http://localhost:3001`
- [ ] Base de datos inicializada con datos de prueba

## Test 1: Login Normal
**Objetivo**: Verificar que el login funciona con el nuevo apiClient

1. [ ] Abrir `http://localhost:3001/login`
2. [ ] Ingresar credenciales: `admin@teloo.com` / `admin123`
3. [ ] Click en "Iniciar Sesión"
4. [ ] **Esperado**: Redirige al dashboard sin errores
5. [ ] **Verificar en DevTools**: 
   - Network tab muestra `POST /auth/login` con status 200
   - localStorage tiene `access_token` y `refresh_token`

## Test 2: Navegación con Token Válido
**Objetivo**: Verificar que las peticiones incluyen el token automáticamente

1. [ ] Estando logueado, navegar a "Asesores"
2. [ ] **Verificar en DevTools Network**:
   - Request a `/asesores` incluye header `Authorization: Bearer <token>`
   - Status 200
3. [ ] Navegar a "PQR"
4. [ ] **Verificar en DevTools Network**:
   - Request a `/pqr` incluye header `Authorization: Bearer <token>`
   - Status 200

## Test 3: Token Expirado (Simulado)
**Objetivo**: Verificar que el refresh automático funciona

### Opción A: Modificar token manualmente
1. [ ] Abrir DevTools → Application → Local Storage
2. [ ] Modificar `access_token` a un valor inválido: `"invalid_token_123"`
3. [ ] Navegar a cualquier página (ej: Asesores)
4. [ ] **Esperado**: 
   - Se intenta refresh automáticamente
   - Si refresh falla, redirige a `/login`
   - Se muestra mensaje en consola

### Opción B: Esperar expiración natural
1. [ ] Login normalmente
2. [ ] Esperar 15 minutos (tiempo de expiración del access token)
3. [ ] Hacer una acción (ej: navegar a otra página)
4. [ ] **Esperado**:
   - Interceptor detecta 401
   - Intenta refresh automáticamente
   - Si refresh exitoso, continúa sin interrupciones
   - Usuario no nota nada

## Test 4: Reinicio del Servidor (Problema Original)
**Objetivo**: Verificar el comportamiento cuando se reinicia el backend

1. [ ] Login normalmente
2. [ ] Verificar que puedes navegar sin problemas
3. [ ] **Reiniciar el servidor backend** (Ctrl+C y volver a iniciar)
4. [ ] En el frontend, intentar navegar o hacer una acción
5. [ ] **Esperado**:
   - Primera petición falla con 401
   - Interceptor intenta refresh
   - Refresh falla (tokens no persisten en backend actual)
   - Usuario es redirigido a `/login` automáticamente
   - localStorage se limpia
6. [ ] Login de nuevo
7. [ ] **Esperado**: Todo funciona normalmente

## Test 5: Logout
**Objetivo**: Verificar que el logout limpia todo correctamente

1. [ ] Estando logueado, click en "Cerrar Sesión"
2. [ ] **Esperado**:
   - Redirige a `/login`
   - localStorage está vacío (no hay tokens)
   - Intentar acceder a rutas protegidas redirige a login

## Test 6: Múltiples Tabs (Bonus)
**Objetivo**: Verificar sincronización entre pestañas

1. [ ] Abrir 2 tabs del frontend
2. [ ] Login en tab 1
3. [ ] **Verificar**: Tab 2 también muestra como logueado (refresh)
4. [ ] Logout en tab 1
5. [ ] **Esperado**: Tab 2 detecta el logout y redirige a login

## Test 7: Peticiones Concurrentes
**Objetivo**: Verificar que múltiples peticiones simultáneas no causan múltiples refreshes

1. [ ] Login normalmente
2. [ ] Modificar `access_token` a valor inválido
3. [ ] Abrir DevTools → Network
4. [ ] Navegar rápidamente entre varias páginas (Asesores → PQR → Dashboard)
5. [ ] **Esperado**:
   - Solo UNA petición de refresh
   - Las demás peticiones esperan en cola
   - Todas se reintentan con el nuevo token

## Resultados Esperados

### ✅ Comportamiento Correcto:
- Login funciona sin errores
- Tokens se incluyen automáticamente en todas las peticiones
- Refresh automático funciona cuando el token expira
- Logout limpia todo correctamente
- Redirige a login cuando no hay forma de recuperar la sesión

### ❌ Problemas Conocidos (Esperados):
- **Reinicio del servidor**: Requiere re-login (normal sin persistencia en backend)
- **Refresh token expirado**: Requiere re-login (normal después de 30 días)

## Verificación en Consola

Durante las pruebas, verificar en la consola del navegador:

```javascript
// Verificar que apiClient está configurado
console.log('Interceptores request:', window.apiClient?.interceptors.request.handlers.length);
console.log('Interceptores response:', window.apiClient?.interceptors.response.handlers.length);

// Verificar tokens
console.log('Access Token:', localStorage.getItem('access_token'));
console.log('Refresh Token:', localStorage.getItem('refresh_token'));
```

## Troubleshooting

### Problema: "Cannot find apiClient"
**Solución**: Verificar que todos los servicios importan `import apiClient from '@/lib/axios'`

### Problema: "401 Unauthorized" en todas las peticiones
**Solución**: 
1. Verificar que el token se guarda en localStorage después del login
2. Verificar que el interceptor agrega el header Authorization
3. Verificar que el backend acepta el token

### Problema: Refresh loop infinito
**Solución**: 
1. Verificar que el endpoint `/auth/refresh` no está protegido
2. Verificar que `originalRequest._retry` se está marcando correctamente

### Problema: No redirige a login después de 401
**Solución**:
1. Verificar que AuthContext escucha el evento `auth:logout`
2. Verificar que el interceptor dispara el evento correctamente

## Comandos Útiles

```bash
# Ver logs del backend
docker-compose logs -f core-api

# Limpiar localStorage desde consola
localStorage.clear()

# Ver todas las cookies
document.cookie

# Simular token expirado
localStorage.setItem('access_token', 'invalid_token')
```

## Conclusión

Si todos los tests pasan:
- ✅ La integración está correcta
- ✅ El manejo de autenticación es robusto
- ✅ La experiencia de usuario es fluida
- ⚠️ Para producción, implementar persistencia de tokens en backend
