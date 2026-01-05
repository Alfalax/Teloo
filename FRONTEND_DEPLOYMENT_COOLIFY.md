# 🚀 Desplegar Frontends en Coolify (Recursos Separados)

## ⚠️ Por Qué Separados

Los frontends de React/Vite requieren mucha memoria para construir. Si se incluyen en el docker-compose principal, pueden causar que Coolify falle por falta de recursos.

**Solución:** Desplegar cada frontend como un recurso independiente en Coolify.

---

## 📋 Opción 1: Usar Coolify UI (RECOMENDADO)

### 1️⃣ Crear Recurso para Admin Frontend

1. **En Coolify Dashboard:**
   - Click en "+ New" o "Add Resource"
   - Selecciona "Docker Image" o "Dockerfile"

2. **Configuración Básica:**
   ```
   Name: teloo-admin-frontend
   Source: GitHub
   Repository: Alfalax/Teloo (tu repo)
   Branch: develop
   ```

3. **Build Configuration:**
   ```
   Dockerfile Location: frontend/admin/Dockerfile
   Build Context: frontend/admin
   Target Stage: production
   ```

4. **Build Arguments:**
   ```
   VITE_API_URL=http://TU_IP_SERVIDOR:7002
   VITE_REALTIME_URL=http://TU_IP_SERVIDOR:7005
   VITE_ENVIRONMENT=production
   ```

5. **Port Mapping:**
   ```
   Container Port: 80
   Public Port: 3000 (o el que prefieras)
   ```

6. **Deploy**

### 2️⃣ Crear Recurso para Advisor Frontend

Repite el proceso:

```
Name: teloo-advisor-frontend
Dockerfile Location: frontend/advisor/Dockerfile
Build Context: frontend/advisor
Target Stage: production
Public Port: 3001
```

**Build Arguments (iguales):**
```
VITE_API_URL=http://TU_IP_SERVIDOR:7002
VITE_REALTIME_URL=http://TU_IP_SERVIDOR:7005
VITE_ENVIRONMENT=production
```

---

## 📋 Opción 2: Usar Docker Compose Separado

Si prefieres un docker-compose, crea uno solo para frontends:

### Crear `docker-compose.frontends.yml`

```yaml
version: '3.8'

services:
  admin-frontend:
    build:
      context: ./frontend/admin
      dockerfile: Dockerfile
      target: production
      args:
        - VITE_API_URL=http://TU_IP:7002
        - VITE_REALTIME_URL=http://TU_IP:7005
        - VITE_ENVIRONMENT=production
    ports:
      - "3000:80"
    restart: unless-stopped

  advisor-frontend:
    build:
      context: ./frontend/advisor
      dockerfile: Dockerfile
      target: production
      args:
        - VITE_API_URL=http://TU_IP:7002
        - VITE_REALTIME_URL=http://TU_IP:7005
        - VITE_ENVIRONMENT=production
    ports:
      - "3001:80"
    restart: unless-stopped
```

Luego en Coolify, crea un nuevo recurso apuntando a este archivo.

---

## 🔧 Configurar URLs del Backend

**IMPORTANTE:** Reemplaza `TU_IP_SERVIDOR` con:

### Opción A: IP Pública del Servidor
```bash
VITE_API_URL=http://123.456.789.0:7002
```

### Opción B: Dominio (si tienes)
```bash
VITE_API_URL=https://api.tudominio.com
```

### Opción C: Localhost (solo para pruebas locales)
```bash
VITE_API_URL=http://localhost:7002
```

---

## ✅ Verificar Deployment

Después del deploy:

1. **Admin Frontend:** `http://TU_IP:3000`
2. **Advisor Frontend:** `http://TU_IP:3001`

Deberías ver las interfaces de login.

---

## 🐛 Troubleshooting

### Error: "Cannot connect to API"
- Verifica que `VITE_API_URL` apunte a la IP/dominio correcto
- Verifica que el puerto 7002 esté accesible
- Revisa CORS en el backend

### Error: "Build failed - Out of memory"
- Aumenta memoria en Coolify (Settings > Resources)
- O usa pre-built images (ver abajo)

### Solución: Pre-Build Localmente

Si Coolify no tiene recursos para construir:

```bash
# Build localmente
cd frontend/admin
docker build -t teloo-admin:latest --target production .

# Push a Docker Hub
docker tag teloo-admin:latest tuusuario/teloo-admin:latest
docker push tuusuario/teloo-admin:latest
```

Luego en Coolify, usa la imagen pre-construida en lugar de Dockerfile.

---

## 📝 Resumen

- ✅ Backend ya desplegado (docker-compose.prod.yml)
- ✅ Frontends se despliegan por separado
- ✅ Cada frontend es un recurso independiente en Coolify
- ✅ URLs del backend configuradas en build args
