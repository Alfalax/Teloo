# Resumen de Corrección: Sistema de Configuración

**Fecha:** 2025-11-11  
**Estado:** ✅ COMPLETADO Y VERIFICADO

---

## Problema Original

Los cambios en la configuración no se guardaban ni persistían correctamente. Al cambiar de pestaña o recargar la página, los valores volvían a los anteriores.

---

## Causas Identificadas

1. **Duplicación de registros en BD**: Había parámetros con nombres diferentes para los mismos valores
2. **Cache del navegador**: Las peticiones GET estaban siendo cacheadas
3. **Falta de re-render**: Al cambiar de pestaña no se recargaba la configuración
4. **Metadata incompleto**: 8 parámetros no tenían metadata y no aparecían en el frontend
5. **Lectura incorrecta**: El backend no leía correctamente `parametros_generales` desde registros individuales

---

## Soluciones Implementadas

### 1. Eliminación de Duplicados
```sql
-- Eliminados registros duplicados:
DELETE FROM parametros_config WHERE clave IN (
    'cobertura_minima_pct',           -- duplicado de cobertura_minima_porcentaje
    'timeout_evaluacion_seg',         -- duplicado de timeout_evaluacion_segundos
    'periodo_actividad_dias',         -- duplicado de periodo_actividad_reciente_dias
    'periodo_desempeno_meses',        -- duplicado de periodo_desempeno_historico_meses
    'canales_notificacion',           -- duplicado de canales_por_nivel
    'parametros_generales'            -- JSON grande eliminado, ahora usa registros individuales
);
```

### 2. Evitar Cache del Navegador
**Archivo:** `frontend/admin/src/services/configuracion.ts`
```typescript
// Agregado timestamp único a peticiones GET
async getConfiguracion(): Promise<ConfiguracionConMetadata> {
  const response = await apiClient.get(`/admin/configuracion?_t=${Date.now()}`, {
    headers: {
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    }
  });
  return response.data;
}
```

### 3. Recarga Automática al Cambiar Pestañas
**Archivo:** `frontend/admin/src/components/configuracion/ConfiguracionSistema.tsx`
```typescript
// Agregado useEffect que recarga al cambiar pestaña
useEffect(() => {
  loadConfiguracion();
}, [activeCategory, loadConfiguracion]);
```

### 4. Forzar Re-render con Key Única
**Archivo:** `frontend/admin/src/components/configuracion/ConfiguracionSistema.tsx`
```typescript
const renderComponent = (categoria: any, configuracion: any) => {
  const Component = categoria.component;
  const data = configuracion[categoria.key];
  const dataKey = JSON.stringify(data); // Key única basada en datos
  
  return (
    <Component 
      key={dataKey}  // Fuerza re-render cuando datos cambian
      data={data} 
      categoria={categoria.key}
    />
  );
};
```

### 5. Lectura Correcta de Parámetros Individuales
**Archivo:** `services/core-api/services/configuracion_service.py`
```python
# Backend ahora construye parametros_generales desde registros individuales
if categoria == 'parametros_generales':
    parametros = {}
    default_params = ConfiguracionService.DEFAULT_CONFIG.get('parametros_generales', {})
    for key in default_params.keys():
        valor = await ParametroConfig.get_valor(key, default_params.get(key))
        parametros[key] = valor
    return parametros
```

### 6. Metadata Completo para Todos los Parámetros
**Archivo:** `scripts/add_missing_metadata.sql`
```sql
-- Agregado metadata para 8 parámetros faltantes:
-- cobertura_minima_porcentaje, confianza_minima_operar,
-- notificacion_expiracion_horas_antes, periodo_actividad_reciente_dias,
-- periodo_desempeno_historico_meses, puntaje_defecto_asesores_nuevos,
-- timeout_evaluacion_segundos, timeout_ofertas_horas
```

### 7. Delay Antes de Recargar
**Archivo:** `frontend/admin/src/hooks/useConfiguracion.ts`
```typescript
const updateConfiguracion = useCallback(async (categoria, valores) => {
  const result = await configuracionService.updateConfiguracion(categoria, valores);
  
  // Delay de 100ms para asegurar que BD se actualice
  await new Promise(resolve => setTimeout(resolve, 100));
  
  await loadConfiguracion();
  return result;
}, [loadConfiguracion]);
```

---

## Verificación Final

### ✅ No Hay Duplicados
```sql
SELECT clave, COUNT(*) FROM parametros_config 
GROUP BY clave HAVING COUNT(*) > 1;
-- Resultado: 0 rows (sin duplicados)
```

### ✅ Todos los Parámetros Existen
```sql
SELECT COUNT(*) FROM parametros_config 
WHERE clave IN (...18 parámetros...);
-- Resultado: 18 rows
```

### ✅ Todos Tienen Metadata
```sql
SELECT clave FROM parametros_config 
WHERE clave IN (...18 parámetros...) 
AND (metadata_json IS NULL OR metadata_json = '{}');
-- Resultado: 0 rows (todos tienen metadata)
```

### ✅ Consistencia Backend-Frontend
- DEFAULT_CONFIG (backend): 18 parámetros ✓
- ParametrosGenerales (TypeScript): 18 campos ✓
- Base de datos: 18 registros con metadata ✓

---

## Parámetros Configurables (18 Total)

| # | Parámetro | Valor | Min | Max | Unidad |
|---|-----------|-------|-----|-----|--------|
| 1 | ofertas_minimas_deseadas | 2 | 1 | 10 | ofertas |
| 2 | precio_minimo_oferta | 100 | 100 | 10M | COP |
| 3 | precio_maximo_oferta | 13M | 1M | 100M | COP |
| 4 | garantia_minima_meses | 1 | 1 | 12 | meses |
| 5 | garantia_maxima_meses | 12 | 12 | 120 | meses |
| 6 | tiempo_entrega_minimo_dias | 0 | 0 | 30 | días |
| 7 | tiempo_entrega_maximo_dias | 30 | 30 | 180 | días |
| 8 | cobertura_minima_porcentaje | 50 | 0 | 100 | % |
| 9 | timeout_evaluacion_segundos | 5 | 1 | 30 | seg |
| 10 | vigencia_auditoria_dias | 30 | 1 | 365 | días |
| 11 | timeout_ofertas_horas | 20 | 1 | 168 | horas |
| 12 | notificacion_expiracion_horas_antes | 2 | 1 | 24 | horas |
| 13 | confianza_minima_operar | 3 | 1.0 | 5.0 | puntos |
| 14 | periodo_actividad_reciente_dias | 30 | 7 | 90 | días |
| 15 | periodo_desempeno_historico_meses | 1 | 1 | 24 | meses |
| 16 | fallback_actividad_asesores_nuevos | 3 | 1.0 | 5.0 | puntos |
| 17 | fallback_desempeno_asesores_nuevos | 3 | 1.0 | 5.0 | puntos |
| 18 | puntaje_defecto_asesores_nuevos | 50 | 0 | 100 | puntos |

---

## Archivos Modificados

### Backend
- `services/core-api/services/configuracion_service.py` - Lectura de parámetros individuales
- `scripts/add_missing_metadata.sql` - Metadata para parámetros faltantes

### Frontend
- `frontend/admin/src/services/configuracion.ts` - Timestamp y headers anti-cache
- `frontend/admin/src/hooks/useConfiguracion.ts` - Delay antes de recargar
- `frontend/admin/src/components/configuracion/ConfiguracionSistema.tsx` - Recarga al cambiar pestaña + key única
- `frontend/admin/src/types/configuracion.ts` - Tipo con 18 campos

---

## Resultado Final

✅ **Todos los cambios en configuración ahora:**
1. Se guardan correctamente en la BD
2. Persisten al cambiar de pestaña
3. Persisten al recargar la página
4. Aparecen todos los 18 parámetros
5. No hay duplicados ni inconsistencias
6. El sistema funciona sin necesidad de Ctrl+Shift+R

---

## Notas para Producción

- ✅ No hay cambios breaking
- ✅ Migración de BD ejecutada exitosamente
- ✅ Backend reiniciado y funcionando
- ✅ Frontend actualizado y probado
- ✅ Sin duplicados en BD
- ✅ Metadata completo para todos los parámetros

**Estado:** Listo para producción
