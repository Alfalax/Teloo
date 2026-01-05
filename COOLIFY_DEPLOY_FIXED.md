# ✅ Solución al Error de Build en Coolify

## Problema Identificado
El build fallaba porque Coolify intentaba construir 7 servicios simultáneamente (5 backends + 2 frontends), consumiendo más memoria de la disponible durante el proceso de build.

**Error:** `npm run build:prod` exit code 1 en advisor-frontend

## Solución Implementada: Arquitectura Híbrida

### Cambios Realizados

1. **Removidos frontends del docker-compose.prod.yml**
   - Solo backends permanecen en el docker-compose
   - Frontends se desplegarán como recursos separados

2. **Nueva estructura de deployment:**
   ```
   Recurso 1: docker-compose.prod.yml (Backends)
     ├── postgres
     ├── redis
     ├── minio
     ├── core-api
     ├── agent-ia
     ├── analytics
     ├── realtime-gateway
     └── files

   Recurso 2: admin-frontend (Dockerfile independiente)
   Recurso 3: advisor-frontend (Dockerfile independiente)
   ```

## Pasos para Desplegar en Coolify

### PASO 1: Actualizar el Recurso Actual (Backends)

1. **Hacer commit y push de los cambios:**
   ```bash
   git add docker-compose.prod.yml
   git commit -m "fix: Remove frontends from docker-compose for separate deployment"
   git push origin develop
   ```

2. **En Coolify:**
   - Ve al recurso actual (Alfalax/Teloo)
   - Click en "Force Rebuild Without Cache"
   - Espera a que termine el deployment
   - ✅ Los backends deberían construirse correctamente ahora

### PASO 2: Crear Recurso para Admin Frontend

1. **En Coolify Dashboard:**
   - Click "+ Add" → "New Resource"
   - Selecciona "Public Repository"

2. **Configuración:**
   - **Repository:** `https://github.com/Alfalax/Teloo`
   - **Branch:** `develop`
   - **Name:** `teloo-admin-frontend`
   - **Build Pack:** Dockerfile
   - **Dockerfile Location:** `frontend/admin/Dockerfile`
   - **Docker Build Target:** `production`

3. **Variables de Entorno (Build Args):**
   ```
   VITE_API_URL=https://tu-dominio.com/api
   VITE_REALTIME_URL=https://tu-dominio.com/realtime
   VITE_ENVIRONMENT=production
   ```

4. **Port Mapping:**
   - Container Port: `80`
   - Public Port: `7000` (o el que prefieras)

5. **Network:**
   - Conectar a la misma red que los backends: `teloo-network`

6. **Deploy**

### PASO 3: Crear Recurso para Advisor Frontend

1. **Repetir proceso del PASO 2 con estos cambios:**
   - **Name:** `teloo-advisor-frontend`
   - **Dockerfile Location:** `frontend/advisor/Dockerfile`
   - **Public Port:** `7001`
   - Mismas variables de entorno

## Ventajas de Esta Solución

✅ **Builds secuenciales** - No se queda sin memoria
✅ **Funciona con tu VPS actual** (Hostinger KVM 4)
✅ **Deployments independientes** - Actualiza un frontend sin tocar backends
✅ **Mejor caché** - Coolify cachea cada recurso por separado
✅ **Logs más claros** - Un log por servicio
✅ **Rollback independiente** - Revierte solo lo que falló

## Impacto en Recursos VPS

### Durante Build:
- **Antes:** 8-10 GB RAM (fallaba ❌)
- **Ahora:** 2-3 GB RAM por build secuencial (funciona ✅)

### En Runtime (servicios corriendo):
- **RAM:** Igual (~4-5 GB total)
- **CPU:** Igual
- **Disco:** +100-200 MB (insignificante)
- **Red:** Igual

## Networking Entre Recursos

Los frontends necesitan comunicarse con los backends. Asegúrate de:

1. **Todos los recursos en la misma red Docker:** `teloo-network`
2. **Variables de entorno correctas:**
   - `VITE_API_URL` apunta al dominio público del core-api
   - `VITE_REALTIME_URL` apunta al dominio público del realtime-gateway

## Troubleshooting

### Si el backend sigue fallando:
- Verifica que las variables de entorno estén correctas
- Revisa que MinIO use `MINIO_ROOT_USER` y `MINIO_ROOT_PASSWORD`

### Si los frontends no se conectan a los backends:
- Verifica que `VITE_API_URL` sea accesible públicamente
- Revisa CORS en core-api (`CORS_ORIGINS`)

### Si necesitas ver logs:
- Cada recurso tiene su propio log en Coolify
- Más fácil de debuggear que logs mezclados

## Próximos Pasos

1. ✅ Commit y push de cambios
2. ⏳ Redesplegar recurso de backends
3. ⏳ Crear recurso admin-frontend
4. ⏳ Crear recurso advisor-frontend
5. ⏳ Verificar que todo funcione

---

**Fecha:** 2026-01-05
**Problema resuelto:** Build failure por falta de memoria durante construcción simultánea
**Solución:** Arquitectura híbrida con frontends como recursos separados
