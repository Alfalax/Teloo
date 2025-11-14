# 📝 Cómo Cambiar los Rangos de Parámetros Configurables

## 🎯 Resumen
Los rangos de validación (min, max, default, unit, description) ahora son **configurables** y se almacenan en la base de datos. Puedes cambiarlos sin redesplegar el código.

---

## 📍 Opción 1: Desde la Base de Datos (SQL)

### Conectarse a la base de datos:
```bash
docker exec -it teloo-postgres psql -U teloo_user -d teloo_v3
```

### Ver los metadatos actuales:
```sql
SELECT 
    clave, 
    metadata_json->'min' as min_val,
    metadata_json->'max' as max_val,
    metadata_json->'default' as default_val,
    metadata_json->'unit' as unit
FROM parametros_config 
WHERE metadata_json IS NOT NULL
ORDER BY clave;
```

### Cambiar un rango específico:

**Ejemplo 1: Cambiar el rango de "ofertas_minimas_deseadas" de 1-10 a 1-20:**
```sql
UPDATE parametros_config
SET metadata_json = jsonb_set(
    metadata_json,
    '{max}',
    '20'
)
WHERE clave = 'ofertas_minimas_deseadas';
```

**Ejemplo 2: Cambiar el valor por defecto:**
```sql
UPDATE parametros_config
SET metadata_json = jsonb_set(
    metadata_json,
    '{default}',
    '5'
)
WHERE clave = 'ofertas_minimas_deseadas';
```

**Ejemplo 3: Cambiar múltiples valores a la vez:**
```sql
UPDATE parametros_config
SET metadata_json = jsonb_set(
    jsonb_set(
        jsonb_set(
            metadata_json,
            '{min}',
            '2'
        ),
        '{max}',
        '15'
    ),
    '{default}',
    '3'
)
WHERE clave = 'ofertas_minimas_deseadas';
```

**Ejemplo 4: Cambiar la descripción:**
```sql
UPDATE parametros_config
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Nueva descripción del parámetro"'
)
WHERE clave = 'ofertas_minimas_deseadas';
```

---

## 📍 Opción 2: Desde el Frontend (Interfaz de Administración)

### Ubicación en el Frontend:
1. **Navega a:** `http://localhost:3000/configuracion`
2. **Sección:** "Parámetros Generales"
3. **Componente:** `ParametrosGeneralesForm.tsx`

### Cómo funciona:
- El formulario **lee automáticamente** los metadatos desde el backend
- Los campos de entrada se generan **dinámicamente** con los rangos configurados
- Los rangos (min/max) se aplican automáticamente a los inputs

### Código relevante:
```typescript
// frontend/admin/src/components/configuracion/ParametrosGeneralesForm.tsx

// Los parámetros se generan dinámicamente desde metadata
const parametros = Object.entries(metadata)
  .filter(([key, meta]) => {
    // Solo incluir parámetros que tienen min/max
    return meta && typeof meta === 'object' && ('min' in meta || 'max' in meta);
  })
  .map(([key, meta]) => ({
    key,
    label: formatLabel(key),
    description: meta.description || '',
    type: 'number' as const,
    min: meta.min ?? 0,        // ← Rango mínimo desde DB
    max: meta.max ?? 100,      // ← Rango máximo desde DB
    step: (meta.min !== undefined && meta.min < 1) ? 0.1 : 1,
    default: meta.default ?? 0,
    unit: meta.unit || ''
  }));
```

---

## 🔄 Flujo de Actualización

```
┌─────────────────────────────────────────────────────────────┐
│  1. Cambias metadata_json en la base de datos              │
│     UPDATE parametros_config SET metadata_json = ...       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Backend lee los nuevos metadatos                        │
│     GET /admin/configuracion                                │
│     → Incluye metadata en la respuesta                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Frontend recibe y aplica los nuevos rangos              │
│     useConfiguracion() → metadata                           │
│     → Inputs se actualizan automáticamente                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Usuario ve los nuevos rangos en el formulario           │
│     ✅ Sin redesplegar código                               │
│     ✅ Cambios inmediatos                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Parámetros Configurables Actuales

| Parámetro | Min | Max | Default | Unit | Descripción |
|-----------|-----|-----|---------|------|-------------|
| `ofertas_minimas_deseadas` | 1 | 10 | 2 | ofertas | Número mínimo de ofertas antes de cierre anticipado |
| `timeout_evaluacion_segundos` | 1 | 30 | 5 | segundos | Tiempo máximo para completar evaluación |
| `vigencia_auditoria_dias` | 1 | 365 | 30 | días | Días de vigencia de auditorías de confianza |
| `periodo_actividad_reciente_dias` | 1 | 90 | 30 | días | Período para calcular actividad reciente |
| `periodo_desempeno_historico_meses` | 1 | 24 | 6 | meses | Período para calcular desempeño histórico |
| `confianza_minima_operar` | 1.0 | 5.0 | 2.0 | puntos | Nivel mínimo de confianza para operar |
| `cobertura_minima_porcentaje` | 0 | 100 | 70 | % | Porcentaje mínimo de cobertura requerido |
| `timeout_ofertas_horas` | 1 | 168 | 24 | horas | Tiempo máximo para recibir ofertas |
| `notificacion_expiracion_horas_antes` | 1 | 48 | 2 | horas | Horas antes de expiración para notificar |

---

## 🧪 Ejemplo Práctico Completo

### Escenario: Cambiar el rango de "Ofertas Mínimas Deseadas"

**Antes:**
- Min: 1
- Max: 10
- Default: 2

**Después:**
- Min: 2
- Max: 20
- Default: 5

**SQL para aplicar el cambio:**
```sql
-- Conectarse a la base de datos
docker exec -it teloo-postgres psql -U teloo_user -d teloo_v3

-- Aplicar el cambio
UPDATE parametros_config
SET metadata_json = '{
  "min": 2,
  "max": 20,
  "default": 5,
  "unit": "ofertas",
  "description": "Número mínimo de ofertas antes de cierre anticipado"
}'::jsonb
WHERE clave = 'ofertas_minimas_deseadas';

-- Verificar el cambio
SELECT clave, metadata_json 
FROM parametros_config 
WHERE clave = 'ofertas_minimas_deseadas';
```

**Resultado en el Frontend:**
1. Refresca la página de configuración
2. El input ahora acepta valores entre 2 y 20
3. El valor por defecto es 5
4. ✅ Sin necesidad de redesplegar

---

## ✅ Ventajas de este Enfoque

1. **Sin Redespliegue:** Cambios inmediatos sin tocar código
2. **Centralizado:** Un solo lugar para todas las validaciones
3. **Auditable:** Todos los cambios quedan registrados en la DB
4. **Sincronizado:** Frontend y backend siempre en sync
5. **Escalable:** Fácil agregar nuevos parámetros

---

## 🔍 Verificar que Funciona

### 1. Verificar en la base de datos:
```sql
SELECT clave, metadata_json FROM parametros_config WHERE clave = 'ofertas_minimas_deseadas';
```

### 2. Verificar en el backend:
```bash
curl http://localhost:8000/admin/configuracion | jq '.metadata.ofertas_minimas_deseadas'
```

### 3. Verificar en el frontend:
- Abre DevTools (F12)
- Ve a la pestaña Network
- Busca la petición a `/admin/configuracion`
- Verifica que `metadata` incluye los nuevos valores

---

## 📞 Soporte

Si tienes problemas:
1. Verifica que el backend esté corriendo: `docker ps`
2. Revisa los logs: `docker logs teloo-core-api`
3. Verifica la conexión a la DB: `docker exec -it teloo-postgres psql -U teloo_user -d teloo_v3`
