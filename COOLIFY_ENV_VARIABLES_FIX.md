# Fix de Variables de Entorno en Coolify

## Problema Identificado

El frontend no puede conectarse al backend porque la variable de entorno `VITE_API_URL` no está configurada correctamente en Coolify.

## Causa Raíz

- El código usa `VITE_API_URL` para obtener la URL del backend
- Esta variable debe estar disponible durante el **BUILD TIME** (no runtime)
- En Coolify, las variables de entorno deben configurarse en la sección de Build

## Solución

### 1. Configurar Variables de Entorno en Coolify - Frontend Admin

1. Ve a tu aplicación **frontend-admin** en Coolify
2. Click en la pestaña **"Environment Variables"**
3. Asegúrate de que estén en la sección **"Build"** (no "Runtime")
4. Agrega/verifica estas variables:

```bash
# CRÍTICO: URL del backend
VITE_API_URL=https://tu-backend.dominio.com

# Otras URLs (si aplica)
VITE_ANALYTICS_API_URL=https://tu-backend.dominio.com/analytics
VITE_REALTIME_URL=https://tu-backend.dominio.com/realtime
VITE_FILES_URL=https://tu-backend.dominio.com/files

# Configuración de la app
VITE_APP_NAME=TeLOO Admin
VITE_APP_VERSION=3.0.0
VITE_ENVIRONMENT=production
```

### 2. Configurar Variables de Entorno - Frontend Advisor (cuando lo despliegues)

Mismas variables pero para el frontend de asesores:

```bash
VITE_API_URL=https://tu-backend.dominio.com
VITE_ANALYTICS_API_URL=https://tu-backend.dominio.com/analytics
VITE_REALTIME_URL=https://tu-backend.dominio.com/realtime
VITE_FILES_URL=https://tu-backend.dominio.com/files
VITE_APP_NAME=TeLOO Advisor
VITE_APP_VERSION=3.0.0
VITE_ENVIRONMENT=production
```

### 3. Verificar URL del Backend

Asegúrate de que la URL del backend sea la correcta. Opciones:

**Opción A: Backend con dominio propio**
```bash
VITE_API_URL=https://api.teloo.com
```

**Opción B: Backend en subdominio de Coolify**
```bash
VITE_API_URL=https://teloo-backend-xyz.coolify.io
```

**Opción C: Backend en IP con puerto**
```bash
VITE_API_URL=http://123.456.789.0:8000
```

### 4. Rebuild del Frontend

Después de configurar las variables:

1. En Coolify, ve a tu aplicación frontend-admin
2. Click en **"Redeploy"** o **"Force Rebuild"**
3. Espera a que termine el build
4. Verifica los logs del build para confirmar que las variables se están usando

### 5. Verificar en el Navegador

Una vez desplegado:

1. Abre las DevTools del navegador (F12)
2. Ve a la pestaña **Console**
3. Escribe: `import.meta.env.VITE_API_URL`
4. Deberías ver la URL correcta del backend

Si ves `undefined`, significa que la variable no se configuró correctamente durante el build.

## Verificación del Backend

Antes de intentar login, verifica que el backend esté funcionando:

### Test 1: Health Check
```bash
curl https://tu-backend.dominio.com/health
```

Debería responder:
```json
{"status": "healthy"}
```

### Test 2: Endpoint de Login
```bash
curl -X POST https://tu-backend.dominio.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@teloo.com","password":"tu_password"}'
```

Si el backend responde correctamente, el problema es solo de configuración del frontend.

## Checklist de Verificación

- [ ] Variables de entorno configuradas en Coolify (sección Build)
- [ ] `VITE_API_URL` apunta a la URL correcta del backend
- [ ] Backend está corriendo y responde en esa URL
- [ ] Frontend rebuildeado después de configurar variables
- [ ] Verificado en navegador que `import.meta.env.VITE_API_URL` tiene valor
- [ ] CORS configurado en el backend para aceptar requests del frontend
- [ ] Base de datos inicializada con usuario admin

## Problemas Comunes

### 1. "Network Error" o "Failed to fetch"

**Causa**: El frontend no puede alcanzar el backend
**Solución**: 
- Verifica que `VITE_API_URL` sea correcta
- Verifica que el backend esté corriendo
- Revisa configuración de CORS en el backend

### 2. "401 Unauthorized" inmediatamente

**Causa**: Credenciales incorrectas o usuario no existe
**Solución**:
- Verifica que la base de datos esté inicializada
- Ejecuta el script de inicialización: `python services/core-api/init_data.py`
- Usa las credenciales por defecto: admin@teloo.com / Admin123!

### 3. Variables no se aplican después de rebuild

**Causa**: Coolify cachea el build
**Solución**:
- Usa "Force Rebuild" en lugar de "Redeploy"
- O limpia el cache en la configuración de la aplicación

## Configuración CORS en Backend

Si el backend está en un dominio diferente al frontend, asegúrate de que CORS esté configurado:

En el backend (FastAPI), verifica que `CORS_ORIGINS` incluya la URL del frontend:

```python
# En services/core-api/main.py
CORS_ORIGINS = [
    "https://admin.teloo.com",  # Tu dominio del frontend
    "https://teloo-admin-xyz.coolify.io",  # O el dominio de Coolify
]
```

## Próximos Pasos

Una vez que el login funcione:

1. Verificar que todos los endpoints del backend respondan correctamente
2. Configurar el frontend advisor con las mismas variables
3. Configurar dominios personalizados (opcional)
4. Configurar SSL/HTTPS si no está ya configurado
5. Configurar variables de producción para servicios adicionales (MinIO, Redis, etc.)
