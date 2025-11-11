# Diagnóstico del Sistema de Escalamiento

## Fecha: 2025-11-11

## Problema Reportado
El sistema está asignando solicitudes a TODOS los asesores (256) en lugar de filtrar geográficamente primero.

## Análisis Realizado

### 1. Errores Encontrados

#### Error 1: Variable `logger` no definida (RESUELTO ✅)
- **Ubicación**: `services/solicitudes_service.py` línea 248
- **Problema**: Se estaba redefiniendo `logger` localmente dentro de un bloque condicional
- **Solución**: Eliminada la redefinición local, usar el logger global

#### Error 2: Ciudades duplicadas (RESUELTO ✅)
- **Problema**: Hay municipios con el mismo nombre en diferentes departamentos (ej: CALDAS en Antioquia y Boyacá)
- **Solución**: Buscar municipio por `municipio_norm` Y `departamento`

#### Error 3: Coroutine sin await (RESUELTO ✅)
- **Ubicación**: `services/escalamiento_service.py` línea 777
- **Problema**: `await ParametroConfig.get_valor().get()` - llamando `.get()` en una coroutine
- **Solución**: Separar en dos líneas con await primero

#### Error 4: Inclusión de municipios con `area_metropolitana = 'NO'` (RESUELTO ✅)
- **Problema**: El filtro `area_metropolitana__isnull=False` incluía municipios con valor 'NO'
- **Solución**: Agregar filtro `area_metropolitana__not='NO'`

#### Error 5: Import incorrecto (PENDIENTE ❌)
- **Ubicación**: `services/escalamiento_service.py` función `aplicar_fallbacks_metricas`
- **Problema**: `from models.configuracion import ParametroConfig` - el módulo no existe
- **Solución Aplicada**: Eliminar el import local (ya está importado al inicio desde `models.analytics`)
- **Estado**: El error persiste en los logs más recientes

### 2. Logs de la Última Solicitud (COPACABANA)

```
Solicitud ID: 3e5377fc-8c36-42c4-bbb1-318563f3caf3
Ciudad: COPACABANA, ANTIOQUIA
Asesores evaluados: 160
Nivel asignado: Todos en nivel 5
Error: "No module named 'models.configuracion'" (repetido para cada asesor)
```

### 3. Datos Geográficos Verificados

**COPACABANA, ANTIOQUIA**:
- Área metropolitana: SI
- Hub logístico: MEDELLÍN

**VILLAVICENCIO, META**:
- Área metropolitana: NO
- Hub logístico: BOGOTÁ D.C.

**Conclusión**: Villavicencio NO debería estar en los 160 asesores seleccionados para COPACABANA.

### 4. Reglas Geográficas (Según Design.md)

El sistema debe seleccionar asesores en 3 grupos:

1. **Misma ciudad**: Asesores de COPACABANA
2. **Áreas metropolitanas nacionales**: Asesores de TODAS las ciudades que SÍ están en áreas metropolitanas (excluyendo 'NO')
3. **Hub logístico**: Asesores del hub MEDELLÍN (118 municipios)

## Estado Actual

### Fixes Aplicados
1. ✅ Logger fix
2. ✅ Búsqueda por ciudad Y departamento
3. ✅ Await en ParametroConfig
4. ✅ Exclusión de area_metropolitana='NO'
5. ❌ Import de ParametroConfig (persiste el error)

### Problema Pendiente

El error `No module named 'models.configuracion'` indica que el último reinicio NO tomó el fix correctamente. Esto está causando que:
- Todos los cálculos de métricas fallen
- Todos los asesores sean clasificados en nivel 5 (fallback)
- No se puedan ver los logs de selección geográfica

## Próximos Pasos

1. **Verificar que el fix del import esté aplicado correctamente**
2. **Reiniciar el servicio para tomar los cambios**
3. **Crear una NUEVA solicitud para probar**
4. **Verificar los logs que muestren**:
   - "Total asesores activos en BD: 256"
   - "Característica 1 - Misma ciudad"
   - "Característica 2 - Áreas metropolitanas"
   - "Característica 3 - Hub logístico"
   - "Total asesores elegibles (sin duplicados): X" (debe ser < 256)

## Comando para Verificar

```bash
# Ver logs del escalamiento
docker logs teloo-core-api --tail 200 | grep -E "Iniciando escalamiento|Total asesores|Característica|elegibles"

# Ver última solicitud
docker exec teloo-postgres psql -U teloo_user -d teloo_v3 -c "SELECT id, ciudad_origen, created_at FROM solicitudes ORDER BY created_at DESC LIMIT 1;"

# Ver evaluaciones de la última solicitud
docker exec teloo-postgres psql -U teloo_user -d teloo_v3 -c "SELECT COUNT(*) FROM evaluaciones_asesores_temp WHERE solicitud_id = '<ID>';"
```
