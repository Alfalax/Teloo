# 🚨 Coolify No Tomó los Cambios - Solución

## Problema
Los logs muestran que Coolify sigue usando el código antiguo:
- ❌ MinIO warning sigue apareciendo
- ❌ Error de municipio_id sigue apareciendo

## ✅ Solución: Force Redeploy en Coolify

### Pasos en la UI de Coolify:

1. **Ve a tu proyecto TeLOO en Coolify**

2. **Selecciona el servicio "core-api"**

3. **Force Redeploy:**
   - Click en el botón "⚙️ Settings" o "Actions"
   - Busca la opción "Force Rebuild" o "Force Redeploy"
   - Marca la opción "Clear Build Cache" si está disponible
   - Click en "Deploy" o "Redeploy"

4. **Monitorea los logs en tiempo real:**
   - Ve a la pestaña "Logs"
   - Deberías ver el proceso de build y deploy
   - Verifica que diga "Cloning from branch: develop"

### Verificación del Deploy:

Después del redeploy, los logs deberían mostrar:

```
✅ Sin warning de MinIO:
MinIO Object Storage Server
(sin "WARNING: MINIO_ACCESS_KEY and MINIO_SECRET_KEY are deprecated")

✅ Sin error de municipio_id:
"Default data initialized"
"Core API service started successfully"
(sin "⚠️ Error creating sample data")
```

---

## 🔍 Si el Problema Persiste

### Opción 1: Verificar Variables de Entorno en Coolify

En Coolify, ve a Environment Variables y asegúrate de tener:

```bash
# Variables MinIO (NUEVAS - requeridas)
MINIO_ROOT_USER=tu_usuario_minio
MINIO_ROOT_PASSWORD=tu_password_minio

# Variables MinIO (LEGACY - para compatibilidad)
MINIO_ACCESS_KEY=tu_usuario_minio
MINIO_SECRET_KEY=tu_password_minio
```

### Opción 2: Verificar que Coolify esté en la rama correcta

1. En Coolify, ve a Settings del proyecto
2. Verifica que esté configurado para usar la rama "develop"
3. Si está en "main", cámbialo a "develop" o haz merge a main

### Opción 3: Trigger Manual desde Git

```bash
# Hacer un commit vacío para forzar el trigger
git commit --allow-empty -m "chore: trigger Coolify redeploy"
git push origin develop
```

Luego en Coolify, click en "Deploy" manualmente.

---

## 📝 Notas

- Coolify a veces cachea el código y no detecta cambios
- "Force Rebuild" limpia el cache y hace pull fresco del repo
- Las variables de entorno se configuran en la UI de Coolify, no en .env
