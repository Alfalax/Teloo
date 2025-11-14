# Eliminación del campo `nivel_actual` de la tabla `asesores`

**Fecha:** 2025-11-14  
**Tipo:** Refactorización / Limpieza de código

## 📋 Resumen

Se eliminó el campo `nivel_actual` de la tabla `asesores` porque era **redundante y no se usaba en ningún proceso crítico** del sistema.

## 🔍 Análisis Previo

### ❌ NO SE USABA EN:
1. **Escalamiento de solicitudes** - Usa `evaluaciones_asesores_temp.nivel_entrega`
2. **Evaluación de ofertas** - Usa `evaluaciones_asesores_temp`
3. **Filtros de solicitudes** - Usa `evaluaciones_asesores_temp`
4. **Cálculo de puntajes** - Se calcula dinámicamente

### ✅ SOLO SE USABA PARA:
1. **Display en frontend** - Mostrar en tabla de asesores
2. **Respuestas de API** - Información de referencia
3. **Logs de debug** - Información no crítica

## 🎯 Confusión Identificada

Existían **DOS campos diferentes** con nombres similares:
- `asesor.nivel_actual` (tabla `asesores`) - **REDUNDANTE** ❌
- `solicitud.nivel_actual` (tabla `solicitudes`) - **CRÍTICO** ✅

El campo en `solicitudes` SÍ es crítico porque:
- Controla el escalamiento de solicitudes (niveles 1-5)
- Determina qué asesores ven cada solicitud
- Se usa en el filtro: `solicitud.nivel_actual >= evaluacion.nivel_entrega`

## 📝 Cambios Realizados

### 1. Backend

#### Modelo (`services/core-api/models/user.py`)
```python
# ANTES
nivel_actual = fields.IntField(default=3)  # 1-5

# DESPUÉS
# Campo eliminado
```

#### Routers (`services/core-api/routers/asesores.py`)
```python
# ANTES
"nivel_actual": asesor.nivel_actual,

# DESPUÉS
# Línea eliminada de todas las respuestas
```

#### Services (`services/core-api/services/asesores_service.py`)
```python
# ANTES
'nivel_actual': asesor.nivel_actual,

# DESPUÉS
# Línea eliminada
```

### 2. Frontend

#### Tipos (`frontend/admin/src/types/asesores.ts`)
```typescript
// ANTES
export interface Asesor {
  nivel_actual: number;
  // ...
}

// DESPUÉS
export interface Asesor {
  // Campo eliminado
  // ...
}
```

#### Tabla (`frontend/admin/src/components/asesores/AsesoresTable.tsx`)
```tsx
{/* ANTES */}
<TableHead>Nivel</TableHead>
{/* ... */}
<TableCell>
  <span>{asesor.nivel_actual}</span>
</TableCell>

{/* DESPUÉS */}
{/* Columna eliminada */}
```

### 3. Base de Datos

#### Script de migración (`scripts/remove_nivel_actual_from_asesores.sql`)
```sql
ALTER TABLE asesores DROP COLUMN nivel_actual;
```

## 🚀 Aplicar Migración

```bash
# Ejecutar migración en la base de datos
psql -U postgres -d teloo_v3 -f scripts/remove_nivel_actual_from_asesores.sql
```

## ✅ Verificación

Después de aplicar los cambios:

1. **Backend funciona correctamente** - El escalamiento usa `evaluaciones_asesores_temp`
2. **Frontend muestra asesores sin errores** - Columna "Nivel" eliminada
3. **APIs responden sin el campo** - `nivel_actual` ya no aparece en respuestas
4. **Base de datos limpia** - Columna eliminada de tabla `asesores`

## 📊 Impacto

### ✅ Beneficios
- **Código más limpio** - Elimina campo redundante
- **Menos confusión** - Solo existe `solicitud.nivel_actual` (el importante)
- **Mantenibilidad** - Menos campos que mantener sincronizados
- **Claridad** - El nivel se calcula dinámicamente por solicitud

### ⚠️ Sin Impacto Negativo
- **No afecta escalamiento** - Usa `evaluaciones_asesores_temp`
- **No afecta evaluación** - Usa cálculos dinámicos
- **No afecta filtros** - Usa `solicitud.nivel_actual`
- **No afecta funcionalidad** - Era solo display

## 🔄 Alternativas Consideradas

1. **Mantenerlo como referencia** - Descartado: no aporta valor
2. **Renombrarlo a `nivel_base`** - Descartado: sigue siendo redundante
3. **Eliminarlo** - ✅ **SELECCIONADO**: Limpia el código sin impacto

## 📚 Documentación Relacionada

- `FIX_BUG_ESCALAMIENTO.md` - Corrección del bug de escalamiento
- `ANALISIS_CAUSA_RAIZ_FINAL.md` - Análisis completo del sistema
- `services/core-api/services/escalamiento_service.py` - Lógica de escalamiento real

## 🎓 Lecciones Aprendidas

1. **Nombres similares causan confusión** - `asesor.nivel_actual` vs `solicitud.nivel_actual`
2. **Campos redundantes deben eliminarse** - No mantener datos duplicados
3. **Calcular dinámicamente es mejor** - Evita desincronización
4. **Documentar decisiones** - Facilita mantenimiento futuro

---

**Conclusión:** El campo `nivel_actual` en la tabla `asesores` era completamente redundante. Su eliminación limpia el código sin afectar ninguna funcionalidad crítica del sistema.
