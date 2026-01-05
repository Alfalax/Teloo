# ✅ Warnings Corregidos - TeLOO V3

## Fecha: 2026-01-05

### 🔧 Cambios Realizados

#### 1. MinIO Deprecation Warning
**Problema:** MinIO mostraba warning sobre variables deprecadas
```
WARNING: MINIO_ACCESS_KEY and MINIO_SECRET_KEY are deprecated.
Please use MINIO_ROOT_USER and MINIO_ROOT_PASSWORD
```

**Solución:**
- ✅ Actualizado `docker-compose.prod.yml` para usar `MINIO_ROOT_USER` y `MINIO_ROOT_PASSWORD`
- ✅ Actualizado `.env.production` con las nuevas variables (manteniendo compatibilidad)
- ✅ Servicios `core-api` y `files` actualizados para usar las nuevas variables

**Archivos modificados:**
- `docker-compose.prod.yml` (líneas de MinIO y servicios)
- `.env.production` (sección MinIO)

---

#### 2. Core API - Error municipio_id en Clientes
**Problema:** Error al crear clientes de prueba sin municipio_id
```
⚠️ Error creating sample data: null value in column "municipio_id" 
of relation "clientes" violates not-null constraint
```

**Solución:**
- ✅ Actualizado `services/core-api/init_data.py`
- ✅ Agregada lógica para obtener o crear municipios (Bogotá, Medellín, Cali)
- ✅ Clientes de prueba ahora incluyen `municipio_id` válido

**Archivos modificados:**
- `services/core-api/init_data.py` (función `create_sample_data`)

---

### 🚀 Aplicar los Cambios

Para aplicar estos cambios en producción:

```bash
# 1. Reconstruir y reiniciar solo el servicio core-api
docker-compose -f docker-compose.prod.yml up -d --build --no-deps core-api

# 2. Verificar logs
docker logs teloo-core-api --tail 50

# 3. Verificar que MinIO ya no muestre el warning
docker logs teloo-minio --tail 20
```

### ✅ Resultado Esperado

Después de aplicar los cambios:
- ✅ MinIO no mostrará más el warning de variables deprecadas
- ✅ Core API creará clientes de prueba sin errores
- ✅ Todos los servicios funcionarán normalmente

### 📝 Notas

- Los cambios son **backward compatible** - las variables antiguas siguen funcionando
- No se requiere reiniciar toda la stack, solo `core-api`
- Los datos existentes no se ven afectados
