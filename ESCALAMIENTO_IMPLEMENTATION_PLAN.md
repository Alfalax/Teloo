# Plan de Implementación del Sistema de Escalamiento

## Estado Actual
✅ 250 asesores importados exitosamente  
✅ Campo `confianza` existe en modelo Asesor (default: 3.0, rango: 1.0-5.0)  
✅ Asesores visibles en dashboard admin

## Pendiente de Implementar

### 1. Agregar Campo Confianza al Formulario de Asesores

**Archivo**: `frontend/admin/src/components/asesores/AsesorForm.tsx`

**Cambios**:
- Agregar `confianza` al estado `formData` (default: 3.0)
- Agregar input numérico después del campo `direccion_punto_venta`
- Validación: rango 1.0 - 5.0
- Mostrar en creación y edición

**Código a agregar**:
```tsx
// En formData state
confianza: 3.0,

// En el formulario (después de direccion_punto_venta)
<div className="space-y-2">
  <Label htmlFor="confianza">
    Calificación de Confianza *
    <span className="text-xs text-muted-foreground ml-2">(1.0 - 5.0)</span>
  </Label>
  <Input
    id="confianza"
    type="number"
    step="0.1"
    min="1.0"
    max="5.0"
    value={formData.confianza}
    onChange={(e) => handleInputChange('confianza', parseFloat(e.target.value) || 3.0)}
    disabled={loadingData || isLoading}
  />
  {errors.confianza && (
    <p className="text-sm text-destructive">{errors.confianza}</p>
  )}
</div>

// En validateForm
if (formData.confianza < 1.0 || formData.confianza > 5.0) {
  newErrors.confianza = 'La calificación debe estar entre 1.0 y 5.0';
}
```

### 2. Actualizar Tipos TypeScript

**Archivo**: `frontend/admin/src/types/asesores.ts`

**Agregar**:
```typescript
export interface AsesorCreate {
  // ... campos existentes
  confianza?: number;
}

export interface AsesorUpdate {
  // ... campos existentes
  confianza?: number;
}
```

### 3. Actualizar Backend - Servicio de Asesores

**Archivo**: `services/core-api/services/asesores_service.py`

**En `create_asesor`**: Agregar manejo de `confianza`
**En `update_asesor`**: Agregar manejo de `confianza`

### 4. Agregar Parámetro Configurable

**Archivo**: `scripts/add_puntaje_defecto_param.sql`

```sql
-- Agregar parámetro para puntaje por defecto de asesores nuevos
INSERT INTO parametros_configuracion (clave, valor, tipo_dato, descripcion, categoria)
VALUES (
  'puntaje_defecto_asesores_nuevos',
  '50',
  'integer',
  'Puntaje por defecto (0-100) para actividad y desempeño de asesores sin historial',
  'escalamiento'
) ON CONFLICT (clave) DO NOTHING;
```

### 5. Implementar Lógica de Escalamiento con Fallbacks

**Archivo**: `services/core-api/services/escalamiento_service.py`

**Función**: `calcular_puntaje_asesor()`

```python
async def calcular_puntaje_asesor(
    self,
    asesor: Asesor,
    solicitud: Solicitud,
    config: ParametrosEscalamiento
) -> Dict[str, float]:
    """
    Calcula puntajes de las 4 variables con fallbacks
    """
    
    # 1. PROXIMIDAD (40%) - Siempre calculada
    puntaje_proximidad = await self._calcular_proximidad(asesor, solicitud)
    
    # 2. ACTIVIDAD (25%) - Histórico o default
    puntaje_actividad = await self._calcular_actividad_con_fallback(asesor, config)
    
    # 3. DESEMPEÑO (25%) - Histórico o default
    puntaje_desempeno = await self._calcular_desempeno_con_fallback(asesor, config)
    
    # 4. CONFIANZA (10%) - Campo actual del asesor
    puntaje_confianza = float(asesor.confianza) * 20  # Escala 1-5 a 0-100
    
    # Calcular puntaje total ponderado
    puntaje_total = (
        puntaje_proximidad * config.peso_proximidad +
        puntaje_actividad * config.peso_actividad +
        puntaje_desempeno * config.peso_desempeno +
        puntaje_confianza * config.peso_confianza
    )
    
    return {
        "proximidad": puntaje_proximidad,
        "actividad": puntaje_actividad,
        "desempeno": puntaje_desempeno,
        "confianza": puntaje_confianza,
        "total": puntaje_total,
        "usa_fallback_actividad": not await self._tiene_historial_actividad(asesor),
        "usa_fallback_desempeno": not await self._tiene_historial_desempeno(asesor)
    }

async def _calcular_actividad_con_fallback(
    self,
    asesor: Asesor,
    config: ParametrosEscalamiento
) -> float:
    """Calcula actividad con fallback a puntaje por defecto"""
    if await self._tiene_historial_actividad(asesor):
        return await self._calcular_actividad_desde_historial(asesor)
    else:
        # Usar puntaje por defecto configurable
        return float(config.puntaje_defecto_asesores_nuevos)

async def _calcular_desempeno_con_fallback(
    self,
    asesor: Asesor,
    config: ParametrosEscalamiento
) -> float:
    """Calcula desempeño con fallback a puntaje por defecto"""
    if await self._tiene_historial_desempeno(asesor):
        return await self._calcular_desempeno_desde_historial(asesor)
    else:
        # Usar puntaje por defecto configurable
        return float(config.puntaje_defecto_asesores_nuevos)

async def _tiene_historial_actividad(self, asesor: Asesor) -> bool:
    """Verifica si el asesor tiene historial de respuestas"""
    count = await HistorialRespuestaOferta.filter(asesor_id=asesor.id).count()
    return count > 0

async def _tiene_historial_desempeno(self, asesor: Asesor) -> bool:
    """Verifica si el asesor tiene historial de ofertas"""
    count = await OfertaHistorica.filter(asesor_id=asesor.id).count()
    return count > 0
```

### 6. Integrar Escalamiento al Crear Solicitud

**Archivo**: `services/core-api/services/solicitudes_service.py`

**En `create_solicitud`**:
```python
# Después de crear la solicitud
if solicitud.estado == EstadoSolicitud.ABIERTA:
    # Ejecutar escalamiento automáticamente
    from services.escalamiento_service import EscalamientoService
    escalamiento_service = EscalamientoService()
    await escalamiento_service.ejecutar_escalamiento(solicitud.id)
```

## Orden de Implementación

1. ✅ Importar 250 asesores (COMPLETADO)
2. ✅ Agregar campo confianza al formulario (COMPLETADO)
3. ✅ Agregar parámetros configurables (COMPLETADO)
4. ✅ Implementar lógica de escalamiento con fallbacks (COMPLETADO)
5. ✅ Integrar escalamiento automático (COMPLETADO)
6. ⏳ **Probar flujo completo** (SIGUIENTE)

## Estado Actual - TODO IMPLEMENTADO ✅

### ✅ Lo que está funcionando:

1. **256 asesores activos** en BD (250 importados + 6 existentes)
2. **Campo confianza editable** en formulario de asesores (frontend + backend)
3. **Fallbacks configurables** desde BD:
   - `fallback_actividad_asesores_nuevos` = 3.0
   - `fallback_desempeno_asesores_nuevos` = 3.0
   - Editables desde: Admin → Configuración → Parámetros Generales
4. **Lógica de escalamiento** con fallbacks implementada
5. **Integración automática** al crear solicitud

### 📍 Dónde configurar los fallbacks:

**Dashboard Admin**:
1. Login → Configuración
2. Tab: "Parámetros del Sistema"
3. Buscar: "Fallback Actividad" y "Fallback Desempeño"
4. Rango: 1.0 - 5.0 puntos
5. Por defecto: 3.0 (neutral)

## 🎯 Próximo Paso: PROBAR FLUJO COMPLETO

### Prueba 1: Crear Solicitud y Verificar Escalamiento

**Pasos**:
1. Login como admin en dashboard
2. Ir a Solicitudes → Nueva Solicitud
3. Llenar datos del cliente y repuestos
4. Guardar solicitud
5. **Verificar**: El escalamiento se ejecuta automáticamente
6. **Verificar en BD**: 
   ```sql
   SELECT COUNT(*) FROM evaluaciones_asesores_temp 
   WHERE solicitud_id = '<id_solicitud>';
   ```

### Prueba 2: Verificar que Asesores Ven la Solicitud

**Pasos**:
1. Login como asesor en dashboard advisor
2. Ir a Solicitudes Abiertas
3. **Verificar**: Aparece la solicitud creada
4. **Verificar**: Puede hacer oferta

### Prueba 3: Verificar Fallbacks en Acción

**Pasos**:
1. Crear solicitud en Bogotá
2. **Verificar en logs**: Asesores sin historial usan fallback 3.0
3. **Verificar**: Asesores de Bogotá tienen mejor nivel que otros

## Resultado Esperado Final

- ✅ Asesores nuevos empiezan con puntaje 3.0 (configurable) para actividad/desempeño
- ✅ Confianza se toma del campo actual del asesor (editable por admin)
- ✅ A medida que participan, acumulan historial real
- ✅ Sistema listo para producción desde día 1
- ⏳ Flujo completo probado y funcionando
