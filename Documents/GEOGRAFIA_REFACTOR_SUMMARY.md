# Refactorización de Tablas Geográficas - Resumen

## Cambios Realizados

### 1. Base de Datos (scripts/init-db.sql)

**ANTES:**
```sql
CREATE TABLE areas_metropolitanas (
    id UUID PRIMARY KEY,
    area_metropolitana VARCHAR(255),
    ciudad_nucleo VARCHAR(255),
    municipio_norm VARCHAR(255),
    ...
);

CREATE TABLE hubs_logisticos (
    id UUID PRIMARY KEY,
    municipio_norm VARCHAR(255),
    hub_asignado_norm VARCHAR(255),
    ...
);
```

**DESPUÉS:**
```sql
CREATE TABLE municipios (
    id UUID PRIMARY KEY,
    codigo_dane VARCHAR(10) UNIQUE,
    municipio VARCHAR(100),
    municipio_norm VARCHAR(100),
    departamento VARCHAR(100),
    area_metropolitana VARCHAR(100),  -- NULL si no aplica
    hub_logistico VARCHAR(100),
    ...
);
```

**Índices actualizados:**
- `idx_municipios_norm` - Búsqueda por nombre normalizado
- `idx_municipios_departamento` - Filtro por departamento
- `idx_municipios_area_metropolitana` - Filtro por área metropolitana
- `idx_municipios_hub` - Filtro por hub logístico
- `idx_municipios_codigo_dane` - Búsqueda por código DANE

---

### 2. Modelo Python (models/geografia.py)

**ANTES:**
- Clase `AreaMetropolitana` (eliminada)
- Clase `HubLogistico` (eliminada)

**DESPUÉS:**
- Clase `Municipio` (nueva, unificada)

**Métodos principales:**
```python
# Métodos estáticos
Municipio.normalizar_ciudad(ciudad: str) -> str
Municipio.get_by_ciudad(ciudad: str) -> Municipio

# Métodos de clase
Municipio.get_municipios_area_metropolitana(ciudad: str) -> list
Municipio.get_municipios_hub(ciudad: str) -> list
Municipio.get_hub_ciudad(ciudad: str) -> str
```

---

### 3. Servicio de Geografía (services/geografia_service.py)

**ANTES:**
- `importar_areas_metropolitanas_excel()` - Importar áreas metropolitanas
- `importar_hubs_logisticos_excel()` - Importar hubs logísticos
- Dos archivos Excel separados

**DESPUÉS:**
- `importar_divipola_excel()` - Importar desde un solo archivo
- `validar_integridad_geografica()` - Validación unificada
- `get_estadisticas_geograficas()` - Estadísticas consolidadas
- `buscar_municipios()` - Búsqueda con filtros múltiples

---

### 4. Archivos Nuevos Creados

#### scripts/migrate_geografia_tabla_unica.sql
Script de migración SQL para:
- Crear nueva tabla `municipios`
- Migrar datos existentes de tablas antiguas
- Crear índices
- Eliminar tablas antiguas (comentado por seguridad)

#### services/core-api/scripts/import_divipola.py
Script Python para importar datos desde Excel:
- Lee archivo `DIVIPOLA_Municipios.xlsx`
- Valida y normaliza datos
- Inserta en base de datos
- Muestra estadísticas de importación

---

## Ventajas del Cambio

### Performance
- ✅ **1 query vs 3-4 queries** para obtener info geográfica
- ✅ **Menos JOINs** en consultas
- ✅ **Índices optimizados** para búsquedas frecuentes

### Simplicidad
- ✅ **1 modelo vs 2 modelos** Python
- ✅ **1 tabla vs 2 tablas** SQL
- ✅ **Código más limpio** y mantenible

### Mantenimiento
- ✅ **Importación directa** desde Excel DIVIPOLA
- ✅ **Sin duplicación** de datos
- ✅ **Actualización más fácil** de datos geográficos

---

## Migración de Datos

### Paso 1: Ejecutar migración SQL
```bash
docker exec -i teloo-postgres psql -U teloo_user -d teloo_v3 < scripts/migrate_geografia_tabla_unica.sql
```

### Paso 2: Importar datos DIVIPOLA
```bash
cd services/core-api
python scripts/import_divipola.py
```

### Paso 3: Verificar importación
```sql
-- Verificar total de municipios
SELECT COUNT(*) FROM municipios;

-- Ver distribución por hub
SELECT hub_logistico, COUNT(*) 
FROM municipios 
GROUP BY hub_logistico;

-- Ver áreas metropolitanas
SELECT area_metropolitana, COUNT(*) 
FROM municipios 
WHERE area_metropolitana IS NOT NULL
GROUP BY area_metropolitana;
```

---

## Estructura del Archivo DIVIPOLA_Municipios.xlsx

### Columnas Requeridas:
- `municipio` - Nombre del municipio
- `departamento` - Departamento
- `hub_logistico` - Hub logístico asignado

### Columnas Opcionales:
- `codigo_dane` - Código DANE del municipio
- `area_metropolitana` - Área metropolitana (NULL si no aplica)

### Ejemplo de Datos:
| codigo_dane | municipio | departamento | area_metropolitana | hub_logistico |
|-------------|-----------|--------------|-------------------|---------------|
| 11001 | Bogotá | Cundinamarca | Área Metropolitana de Bogotá | HUB_CENTRO |
| 05001 | Medellín | Antioquia | Área Metropolitana del Valle de Aburrá | HUB_ANTIOQUIA |
| 76001 | Cali | Valle del Cauca | Área Metropolitana de Cali | HUB_VALLE |

---

## Impacto en el Código Existente

### ✅ Sin Impacto
- Frontend (no usa estas tablas directamente)
- API endpoints públicos (no hay endpoints de geografía)
- Servicios de solicitudes y ofertas (aún no implementados)

### ⚠️ Requiere Actualización
- `services/escalamiento_service.py` - Algoritmo de escalamiento (cuando se implemente)
- Tests de geografía (si existen)

---

## Algoritmo de Escalamiento

El algoritmo de escalamiento usa la proximidad geográfica:

```python
async def calcular_proximidad(ciudad_solicitud: str, ciudad_asesor: str):
    """
    Calcula proximidad entre solicitud y asesor
    """
    # Obtener municipios
    mun_solicitud = await Municipio.get_by_ciudad(ciudad_solicitud)
    mun_asesor = await Municipio.get_by_ciudad(ciudad_asesor)
    
    # 1. Misma ciudad (Proximidad 5.0)
    if mun_solicitud.municipio_norm == mun_asesor.municipio_norm:
        return (5.0, "misma_ciudad")
    
    # 2. Misma área metropolitana (Proximidad 4.0)
    if (mun_solicitud.area_metropolitana and 
        mun_solicitud.area_metropolitana == mun_asesor.area_metropolitana):
        return (4.0, "area_metropolitana")
    
    # 3. Mismo hub logístico (Proximidad 3.5)
    if mun_solicitud.hub_logistico == mun_asesor.hub_logistico:
        return (3.5, "hub_logistico")
    
    # 4. Otros (Proximidad 3.0)
    return (3.0, "otros")
```

---

## Checklist de Implementación

- [x] Actualizar `scripts/init-db.sql`
- [x] Crear script de migración SQL
- [x] Actualizar `models/geografia.py`
- [x] Reescribir `services/geografia_service.py`
- [x] Crear script `import_divipola.py`
- [ ] Ejecutar migración en base de datos
- [ ] Importar datos DIVIPOLA
- [ ] Verificar datos importados
- [ ] Actualizar tests (si existen)
- [ ] Actualizar documentación

---

## Comandos Útiles

### Verificar estructura de tabla
```sql
\d municipios
```

### Contar registros
```sql
SELECT COUNT(*) FROM municipios;
```

### Ver muestra de datos
```sql
SELECT * FROM municipios LIMIT 10;
```

### Buscar municipio específico
```sql
SELECT * FROM municipios WHERE municipio_norm = 'BOGOTA';
```

### Listar hubs
```sql
SELECT DISTINCT hub_logistico, COUNT(*) 
FROM municipios 
GROUP BY hub_logistico 
ORDER BY COUNT(*) DESC;
```

---

**Fecha:** 2025-11-08  
**Rama:** `feature/geografia-tabla-unica`  
**Estado:** ✅ Código actualizado, pendiente migración de datos
