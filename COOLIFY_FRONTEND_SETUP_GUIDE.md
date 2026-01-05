# 📋 Guía Paso a Paso: Configurar Frontends en Coolify

## Contexto
Los frontends ahora se despliegan como recursos separados del docker-compose principal para evitar problemas de memoria durante el build.

---

## 🎯 RECURSO 1: Admin Frontend

### Paso 1: Crear Nuevo Recurso
1. En Coolify Dashboard, click **"+ Add"**
2. Selecciona **"New Resource"**
3. Elige **"Public Repository"**

### Paso 2: Configuración del Repositorio
```
Repository URL: https://github.com/Alfalax/Teloo
Branch: develop
```

### Paso 3: Configuración del Build
```
Name: teloo-admin-frontend
Build Pack: Dockerfile
Dockerfile Location: frontend/admin/Dockerfile
Docker Build Target: production
Base Directory: (dejar vacío)
```

### Paso 4: Variables de Entorno (Build Arguments)

**IMPORTANTE:** Estas son Build Args, no Environment Variables

```bash
# API Configuration
VITE_API_URL=https://api.tudominio.com
VITE_REALTIME_URL=https://realtime.tudominio.com
VITE_ENVIRONMENT=production

# Opcional: Si usas analytics
VITE_ANALYTICS_URL=https://analytics.tudominio.com
```

**Cómo agregar Build Args en Coolify:**
1. En la configuración del recurso, busca **"Build Arguments"**
2. Click **"+ Add Build Argument"**
3. Agrega cada variable una por una

### Paso 5: Port Mapping
```
Container Port: 80
Public Port: 7000
```

### Paso 6: Networking
```
Network: teloo-network
```
**Nota:** Debe ser la misma red que usan los backends

### Paso 7: Health Check (Opcional pero recomendado)
```
Health Check Command: curl -f http://localhost:80 || exit 1
Interval: 30s
Timeout: 10s
Retries: 3
```

### Paso 8: Deploy
1. Click **"Save"**
2. Click **"Deploy"**
3. Espera 3-5 minutos (el build de Vite toma tiempo)

---

## 🎯 RECURSO 2: Advisor Frontend

### Repetir todos los pasos anteriores con estos cambios:

```
Name: teloo-advisor-frontend
Dockerfile Location: frontend/advisor/Dockerfile
Public Port: 7001
```

**Mismas variables de entorno que admin-frontend**

---

## 🔗 Configuración de Dominios (Opcional)

Si quieres usar dominios personalizados:

### Admin Frontend
```
Domain: admin.tudominio.com
Port: 7000
SSL: Enabled (Let's Encrypt)
```

### Advisor Frontend
```
Domain: advisor.tudominio.com
Port: 7001
SSL: Enabled (Let's Encrypt)
```

---

## ✅ Verificación Post-Deployment

### 1. Verificar que los contenedores estén corriendo
En cada recurso, ve a la pestaña **"Logs"** y busca:
```
✓ Built in XXXms
Server running on http://0.0.0.0:80
```

### 2. Verificar conectividad con backends
Abre el frontend en el navegador y verifica:
- ✅ Login funciona
- ✅ Dashboard carga datos
- ✅ No hay errores de CORS en la consola

### 3. Verificar health checks
En Coolify, cada recurso debe mostrar:
```
Status: Running ✓
Health: Healthy ✓
```

---

## 🐛 Troubleshooting

### Error: "Cannot connect to API"
**Causa:** `VITE_API_URL` incorrecta o no accesible

**Solución:**
1. Verifica que `VITE_API_URL` apunte al dominio público del core-api
2. Asegúrate de que core-api esté corriendo
3. Verifica CORS en core-api:
   ```bash
   # En .env.production del backend
   CORS_ORIGINS=https://admin.tudominio.com,https://advisor.tudominio.com
   ```

### Error: "Build failed - npm run build:prod"
**Causa:** Falta de memoria o error en el código

**Solución:**
1. Verifica que el Dockerfile tenga:
   ```dockerfile
   ENV NODE_OPTIONS="--max-old-space-size=2048"
   ```
2. Si persiste, reduce a 1024:
   ```dockerfile
   ENV NODE_OPTIONS="--max-old-space-size=1024"
   ```

### Error: "Network teloo-network not found"
**Causa:** La red no existe o el nombre es diferente

**Solución:**
1. Ve al recurso de backends (docker-compose)
2. Copia el nombre exacto de la red
3. Úsalo en los frontends

### Frontend carga pero muestra página en blanco
**Causa:** Build Args no se pasaron correctamente

**Solución:**
1. Ve a la configuración del recurso
2. Verifica que las Build Args estén en la sección correcta
3. Haz un "Force Rebuild Without Cache"

---

## 📊 Monitoreo

### Recursos Esperados por Frontend:
```
RAM: ~100-200 MB en runtime
CPU: <5% en idle
Disco: ~50-100 MB
```

### Tiempo de Build Esperado:
```
Admin Frontend: 3-5 minutos
Advisor Frontend: 3-5 minutos
```

---

## 🔄 Actualizaciones Futuras

Para actualizar un frontend:

1. Haz push de cambios a GitHub
2. En Coolify, ve al recurso del frontend
3. Click **"Redeploy"**
4. Espera el build
5. ✅ Listo

**Ventaja:** No necesitas redesplegar los backends

---

## 📝 Checklist de Deployment

### Antes de empezar:
- [ ] Backends desplegados y funcionando
- [ ] Dominios configurados (si aplica)
- [ ] Variables de entorno preparadas

### Admin Frontend:
- [ ] Recurso creado
- [ ] Build Args configurados
- [ ] Port mapping correcto (7000)
- [ ] Network configurada (teloo-network)
- [ ] Deployment exitoso
- [ ] Health check passing
- [ ] Login funciona

### Advisor Frontend:
- [ ] Recurso creado
- [ ] Build Args configurados
- [ ] Port mapping correcto (7001)
- [ ] Network configurada (teloo-network)
- [ ] Deployment exitoso
- [ ] Health check passing
- [ ] Login funciona

---

## 🎉 Resultado Final

Deberías tener 3 recursos en Coolify:

```
1. teloo-backends (docker-compose)
   ├── Status: Running ✓
   └── Services: 8 (postgres, redis, minio, 5 backends)

2. teloo-admin-frontend
   ├── Status: Running ✓
   └── Port: 7000

3. teloo-advisor-frontend
   ├── Status: Running ✓
   └── Port: 7001
```

**Total RAM usado:** ~4-5 GB
**Total servicios:** 10 contenedores

---

**Última actualización:** 2026-01-05
