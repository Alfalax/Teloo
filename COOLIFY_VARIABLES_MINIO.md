# 🔧 Configurar Variables MinIO en Coolify

## ⚠️ Importante: Diferencia entre ACCESS_KEY y SECRET_KEY

- **`MINIO_ACCESS_KEY`** = **Usuario** (ejemplo: "teloo_minio")
- **`MINIO_SECRET_KEY`** = **Contraseña** (ejemplo: "teloo_minio_password_seguro")

**NO son iguales**, son como username y password.

---

## 📋 Variables a Configurar en Coolify

### En la UI de Coolify > Environment Variables:

```bash
# ===== VARIABLES MINIO (NUEVAS) =====
# Estas son las que MinIO usa internamente
MINIO_ROOT_USER=teloo_minio
MINIO_ROOT_PASSWORD=teloo_minio_password_seguro_123

# ===== VARIABLES MINIO (LEGACY) =====
# Estas son las que usan los servicios (core-api, files)
MINIO_ACCESS_KEY=teloo_minio
MINIO_SECRET_KEY=teloo_minio_password_seguro_123
```

**IMPORTANTE:** Los valores deben coincidir:
- `MINIO_ROOT_USER` = `MINIO_ACCESS_KEY` (mismo usuario)
- `MINIO_ROOT_PASSWORD` = `MINIO_SECRET_KEY` (misma contraseña)

---

## 🚀 Pasos en Coolify

### 1. Configurar Variables de Entorno

1. Ve a tu proyecto TeLOO en Coolify
2. Click en "Environment Variables" o "Settings"
3. Agrega/actualiza estas 4 variables:
   ```
   MINIO_ROOT_USER=teloo_minio
   MINIO_ROOT_PASSWORD=tu_password_seguro_aqui
   MINIO_ACCESS_KEY=teloo_minio
   MINIO_SECRET_KEY=tu_password_seguro_aqui
   ```
4. Click en "Save"

### 2. Force Redeploy

1. Ve a la sección de "Deployments" o "Actions"
2. Click en "Force Rebuild" o "Redeploy"
3. Marca "Clear Build Cache" si está disponible
4. Click en "Deploy"

### 3. Verificar en Logs

Después del deploy, verifica:

**MinIO logs:**
```
✅ NO debe aparecer:
"WARNING: MINIO_ACCESS_KEY and MINIO_SECRET_KEY are deprecated"

✅ Debe aparecer:
"MinIO Object Storage Server"
"API: http://..."
```

**Core API logs:**
```
✅ NO debe aparecer:
"⚠️ Error creating sample data: null value in column municipio_id"

✅ Debe aparecer:
"Default data initialized"
"Core API service started successfully"
```

---

## 🔐 Recomendación de Seguridad

Para producción, usa contraseñas fuertes:

```bash
# Ejemplo de valores seguros:
MINIO_ROOT_USER=teloo_prod_minio
MINIO_ROOT_PASSWORD=M1n10_Pr0d_S3cur3_P@ssw0rd_2026!

MINIO_ACCESS_KEY=teloo_prod_minio
MINIO_SECRET_KEY=M1n10_Pr0d_S3cur3_P@ssw0rd_2026!
```

---

## 📝 Resumen

1. **4 variables en total** (2 nuevas + 2 legacy)
2. **Los valores deben coincidir** (USER=ACCESS_KEY, PASSWORD=SECRET_KEY)
3. **Force Redeploy** después de configurar
4. **Verificar logs** para confirmar que los warnings desaparecieron
