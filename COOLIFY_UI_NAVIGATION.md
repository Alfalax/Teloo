# 🎯 Cómo Navegar en Coolify

## Estructura de Coolify con Docker Compose

Cuando despliegas un `docker-compose.yml`, Coolify lo trata como **UN SOLO RECURSO**, no como servicios separados.

---

## 📍 Dónde Encontrar Tu Proyecto

### 1. Dashboard Principal
```
Coolify Dashboard
  └── Projects (o "Resources")
      └── TeLOO (o el nombre que le diste)
          └── [AQUÍ ESTÁ TODO]
```

### 2. Dentro del Proyecto TeLOO

Deberías ver:
- **Logs** - Logs de TODOS los servicios juntos
- **Environment Variables** - Variables compartidas
- **Deploy** o **Redeploy** - Botón para redesplegar
- **Settings** - Configuración del proyecto

---

## 🔧 Cómo Forzar Redeploy (Sin Acceso a Servicios Individuales)

### Opción 1: Desde la Vista Principal del Proyecto

1. **Ve a tu proyecto TeLOO en Coolify**
   - Dashboard → Projects → TeLOO

2. **Busca el botón de acciones:**
   - Puede estar arriba a la derecha
   - O en una pestaña "Actions" o "Deployments"

3. **Click en "Redeploy" o "Force Redeploy":**
   - Si hay opciones, marca:
     - ✅ "Force Rebuild"
     - ✅ "No Cache"
     - ✅ "Pull Latest"

4. **Confirma y espera**
   - El deploy puede tardar 2-5 minutos

### Opción 2: Stop y Start

Si no ves "Force Redeploy":

1. **Stop el proyecto:**
   - Busca botón "Stop" o "Pause"
   - Espera que todos los contenedores se detengan

2. **Start de nuevo:**
   - Click en "Start" o "Deploy"
   - Esto debería hacer pull del código nuevo

### Opción 3: Desde Git (Más Confiable)

Si Coolify no está tomando el código:

```bash
# En tu terminal local
git commit --allow-empty -m "chore: force Coolify rebuild"
git push origin develop
```

Luego en Coolify:
- Ve a tu proyecto
- Click en "Deploy" o "Redeploy"
- Coolify debería detectar el nuevo commit

---

## 📋 Configurar Variables de Entorno

### Dónde Están:

1. **Ve a tu proyecto TeLOO**
2. **Busca pestaña "Environment Variables" o "Settings"**
3. **Agrega/edita las variables:**

```bash
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=tu_password
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=tu_password
```

4. **Guarda y Redeploy**

---

## 🔍 Ver Logs de Servicios Específicos

Aunque Coolify muestra todos los logs juntos, puedes filtrar:

### En la Vista de Logs:

1. **Busca el nombre del servicio en los logs:**
   - `core-api` - Logs del Core API
   - `minio` - Logs de MinIO
   - `postgres` - Logs de PostgreSQL

2. **Usa Ctrl+F para buscar:**
   - Busca "core-api" para ver solo esos logs
   - Busca "WARNING" para ver warnings
   - Busca "Error" para ver errores

### Logs en Tiempo Real:

- La mayoría de Coolify tiene opción "Live Logs" o "Follow"
- Esto muestra logs en tiempo real mientras se despliega

---

## 🚨 Si No Encuentras Nada

### Verifica que estés en el lugar correcto:

1. **Dashboard de Coolify** (URL principal)
2. **Click en "Projects" o "Resources"** (menú lateral)
3. **Busca "TeLOO" o el nombre de tu proyecto**
4. **Click en el proyecto**

### Si aún no lo ves:

- Puede estar en "All Resources" o "All Projects"
- Puede estar filtrado por "Status" (activo/inactivo)
- Verifica que estés logueado con el usuario correcto

---

## ✅ Checklist Rápido

Para forzar que Coolify tome el código nuevo:

- [ ] Ve a tu proyecto TeLOO en Coolify
- [ ] Configura las 4 variables de MinIO (si no están)
- [ ] Click en "Stop" (si está disponible)
- [ ] Click en "Redeploy" o "Force Rebuild"
- [ ] Espera 2-5 minutos
- [ ] Ve a "Logs" y verifica que diga "Repuestos" (no "AutoPartes")

---

## 💡 Tip: Commit Vacío

Si nada funciona, el método más confiable es:

```bash
git commit --allow-empty -m "chore: force rebuild"
git push origin develop
```

Esto garantiza que Coolify detecte un cambio y haga pull del código nuevo.
