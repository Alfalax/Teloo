# 🚀 Deploy de Fixes en Coolify

## Cambios Realizados (Listos para Deploy)

### ✅ Archivos Modificados:
1. `services/core-api/init_data.py` - Fix municipio_id en clientes
2. `docker-compose.prod.yml` - Variables MinIO actualizadas
3. `.env.production` - Variables MinIO actualizadas

---

## 📋 Pasos para Deployar en Coolify

### 1️⃣ Commit y Push de los Cambios

```bash
# Agregar los archivos modificados
git add services/core-api/init_data.py
git add docker-compose.prod.yml
git add .env.production

# Hacer commit
git commit -m "fix: Actualizar variables MinIO y corregir municipio_id en init_data"

# Push al repositorio
git push origin main
```

### 2️⃣ En Coolify

**Opción A: Deploy Automático**
- Si tienes auto-deploy habilitado, Coolify detectará el push y desplegará automáticamente
- Espera 2-3 minutos y verifica los logs

**Opción B: Deploy Manual**
1. Ve a tu proyecto en Coolify
2. Click en "Deploy" o "Redeploy"
3. Coolify hará pull del código y reconstruirá los servicios

### 3️⃣ Verificar Variables de Entorno en Coolify

**IMPORTANTE:** Asegúrate de que estas variables estén configuradas en Coolify:

```bash
# Variables MinIO (nuevas)
MINIO_ROOT_USER=tu_usuario_minio
MINIO_ROOT_PASSWORD=tu_password_minio

# Variables MinIO (legacy - para compatibilidad)
MINIO_ACCESS_KEY=tu_usuario_minio
MINIO_SECRET_KEY=tu_password_minio
```

**Cómo configurarlas:**
1. En Coolify, ve a tu servicio
2. Click en "Environment Variables"
3. Agrega/actualiza las variables
4. Guarda y redeploy

---

## 🔍 Verificar el Deploy

Después del deploy, verifica los logs:

```bash
# En Coolify, ve a "Logs" y busca:

# ✅ MinIO debe mostrar:
# "MinIO Object Storage Server" (sin warnings de deprecation)

# ✅ Core API debe mostrar:
# "Default data initialized" (sin error de municipio_id)
# "Core API service started successfully"
```

---

## 🎯 Resultado Esperado

Después del deploy:
- ✅ MinIO sin warnings de variables deprecadas
- ✅ Core API crea clientes de prueba correctamente
- ✅ Todos los servicios funcionando al 100%

---

## 📝 Notas Importantes

1. **Coolify usa Git**: Los cambios deben estar en el repositorio
2. **Variables de entorno**: Configúralas en la UI de Coolify, no solo en .env
3. **Build cache**: Si hay problemas, usa "Force Rebuild" en Coolify
4. **Logs en tiempo real**: Monitorea el deploy desde la UI de Coolify
