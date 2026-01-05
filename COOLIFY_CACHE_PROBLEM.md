# 🚨 Coolify NO Está Tomando el Código Nuevo

## Problema Confirmado

Los logs muestran que Coolify sigue usando **código viejo en cache**:

```
❌ Error: AutoPartes Ana (código viejo)
✅ Debería ser: Repuestos Ana (código nuevo)

❌ Error: municipio_id null en asesores
✅ Debería: crear municipio y asignarlo
```

## 🔧 Solución: Forzar Limpieza de Cache

### Opción 1: En Coolify UI (MÁS EFECTIVA)

1. **Ve a tu servicio core-api en Coolify**

2. **Stop el servicio:**
   - Click en "Stop" o "Pause"
   - Espera que se detenga completamente

3. **Limpia el cache:**
   - Busca opción "Clear Build Cache" o "Prune"
   - Si no existe, ve al siguiente paso

4. **Elimina el contenedor:**
   - En algunos Coolify, hay opción "Delete Container"
   - Esto fuerza a recrear todo desde cero

5. **Redeploy con Force Rebuild:**
   - Click en "Deploy" o "Redeploy"
   - Marca "Force Rebuild" si está disponible
   - Marca "No Cache" si está disponible

### Opción 2: Trigger desde Git (ALTERNATIVA)

Si Coolify sigue sin tomar el código, haz un commit vacío:

```bash
git commit --allow-empty -m "chore: force Coolify cache clear"
git push origin develop
```

Luego en Coolify, click en "Deploy".

### Opción 3: Cambiar el Dockerfile (NUCLEAR)

Si nada funciona, agrega una línea al Dockerfile para forzar rebuild:

```dockerfile
# En services/core-api/Dockerfile, agrega al inicio:
# Cache bust: 2026-01-05-v2
```

Esto fuerza a Docker a reconstruir desde cero.

---

## 🔍 Verificar que Coolify Tomó el Código Nuevo

Después del redeploy, verifica en los logs:

### ✅ Código NUEVO (correcto):
```
"Repuestos Pedro"  ← Debe decir "Repuestos", no "AutoPartes"
"Repuestos Ana"    ← Debe decir "Repuestos", no "AutoPartes"
"Default data initialized" ← Sin error de municipio_id
```

### ❌ Código VIEJO (incorrecto):
```
"AutoPartes Pedro"  ← Si dice "AutoPartes", es código viejo
"AutoPartes Ana"    ← Si dice "AutoPartes", es código viejo
"⚠️ Error creating sample data: null value in column municipio_id"
```

---

## 📋 Checklist de Verificación

- [ ] Servicio detenido en Coolify
- [ ] Cache limpiado
- [ ] Redeploy con Force Rebuild
- [ ] Logs muestran "Repuestos" (no "AutoPartes")
- [ ] No hay error de municipio_id
- [ ] MinIO sin warning (si configuraste las variables)

---

## 🔐 Variables MinIO (Recordatorio)

Mientras estás en Coolify, verifica que estas variables estén configuradas:

```bash
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=tu_password
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=tu_password
```

Si no están, agrégalas ANTES del redeploy.
