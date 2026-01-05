# 🚀 Próximos Pasos en Coolify - ACCIÓN REQUERIDA

## ✅ Cambios Aplicados

Los frontends han sido removidos del `docker-compose.prod.yml` y pusheados a GitHub.

---

## 📋 PASOS A SEGUIR EN COOLIFY

### PASO 1: Redesplegar Backends (5 minutos)

1. Ve a tu recurso actual en Coolify: **Alfalax/Teloo**
2. Click en **"Force Rebuild Without Cache"**
3. Espera 3-5 minutos
4. ✅ Verifica que todos los backends estén corriendo:
   - postgres ✓
   - redis ✓
   - minio ✓
   - core-api ✓
   - agent-ia ✓
   - analytics ✓
   - realtime-gateway ✓
   - files ✓

**Resultado esperado:** 8 servicios corriendo sin errores

---

### PASO 2: Crear Admin Frontend (10 minutos)

#### 2.1 Crear Recurso
```
Dashboard → + Add → New Resource → Public Repository
```

#### 2.2 Configuración Básica
```
Repository URL: https://github.com/Alfalax/Teloo
Branch: develop
Name: teloo-admin-frontend
Build Pack: Dockerfile
Dockerfile Location: frontend/admin/Dockerfile
Docker Build Target: production
```

#### 2.3 Build Arguments (IMPORTANTE)
Agregar estas variables como **Build Arguments** (no Environment Variables):

```bash
VITE_API_URL=https://tu-dominio.com/api
VITE_REALTIME_URL=https://tu-dominio.com/realtime
VITE_ENVIRONMENT=production
```

**⚠️ IMPORTANTE:** Reemplaza `tu-dominio.com` con tu dominio real o IP pública

#### 2.4 Port Mapping
```
Container Port: 80
Public Port: 7000
```

#### 2.5 Network
```
Network: teloo-network
```
(Debe ser la misma red que usan los backends)

#### 2.6 Deploy
```
Click "Save" → Click "Deploy"
```

**Tiempo estimado:** 3-5 minutos

---

### PASO 3: Crear Advisor Frontend (10 minutos)

#### Repetir PASO 2 con estos cambios:

```
Name: teloo-advisor-frontend
Dockerfile Location: frontend/advisor/Dockerfile
Public Port: 7001
```

**Mismas Build Arguments que admin-frontend**

---

## 🎯 Resultado Final Esperado

### En Coolify deberías ver 3 recursos:

```
┌─────────────────────────────────────────┐
│ 1. Alfalax/Teloo (docker-compose)      │
│    Status: Running ✓                    │
│    Services: 8 backends                 │
│    Ports: 7002-7011                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 2. teloo-admin-frontend                 │
│    Status: Running ✓                    │
│    Port: 7000                           │
│    URL: http://tu-ip:7000               │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 3. teloo-advisor-frontend               │
│    Status: Running ✓                    │
│    Port: 7001                           │
│    URL: http://tu-ip:7001               │
└─────────────────────────────────────────┘
```

---

## ✅ Verificación Post-Deployment

### 1. Verificar Backends
```bash
# Core API
curl http://tu-ip:7002/health

# Analytics
curl http://tu-ip:7004/health
```

### 2. Verificar Frontends
```bash
# Admin Frontend
curl http://tu-ip:7000

# Advisor Frontend
curl http://tu-ip:7001
```

### 3. Verificar en Navegador
1. Abre `http://tu-ip:7000` (Admin)
2. Intenta hacer login
3. Verifica que no haya errores en la consola del navegador
4. Repite para `http://tu-ip:7001` (Advisor)

---

## 🐛 Si Algo Sale Mal

### Backend no despliega
**Síntoma:** Build falla en docker-compose

**Solución:**
1. Verifica variables de entorno en Coolify
2. Revisa que `MINIO_ROOT_USER` y `MINIO_ROOT_PASSWORD` estén configurados
3. Mira los logs en Coolify

### Frontend no despliega
**Síntoma:** Build falla en `npm run build:prod`

**Solución:**
1. Verifica que las Build Arguments estén en la sección correcta
2. Asegúrate de que el target sea `production`
3. Si persiste, reduce memoria en Dockerfile:
   ```dockerfile
   ENV NODE_OPTIONS="--max-old-space-size=1024"
   ```

### Frontend no se conecta al backend
**Síntoma:** Errores de red en la consola del navegador

**Solución:**
1. Verifica que `VITE_API_URL` sea accesible públicamente
2. Revisa CORS en backend:
   ```bash
   # En .env.production del backend
   CORS_ORIGINS=http://tu-ip:7000,http://tu-ip:7001
   ```
3. Asegúrate de que todos estén en la misma red: `teloo-network`

---

## 📚 Documentación Adicional

- **Guía detallada:** Ver `COOLIFY_FRONTEND_SETUP_GUIDE.md`
- **Explicación técnica:** Ver `COOLIFY_DEPLOY_FIXED.md`
- **Variables MinIO:** Ver `COOLIFY_VARIABLES_MINIO.md`

---

## 💡 Tips

1. **Builds toman tiempo:** Cada frontend tarda 3-5 minutos en construirse
2. **Usa Force Rebuild:** Si algo falla, usa "Force Rebuild Without Cache"
3. **Logs son tu amigo:** Revisa los logs en Coolify para ver qué está pasando
4. **Network es clave:** Todos los recursos deben estar en `teloo-network`

---

## 🎉 Una Vez Todo Funcione

Tendrás:
- ✅ 8 backends corriendo
- ✅ 2 frontends corriendo
- ✅ Todo en tu VPS Hostinger KVM 4
- ✅ Deployments independientes
- ✅ Sin problemas de memoria

**Total RAM usado:** ~4-5 GB (tu VPS tiene 8 GB, perfecto)

---

**¿Necesitas ayuda?** Revisa las guías o pregúntame cualquier duda.

**Última actualización:** 2026-01-05
