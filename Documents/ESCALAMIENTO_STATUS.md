# Estado de Implementación del Sistema de Escalamiento

## ✅ COMPLETADO

### 1. Datos Base
- ✅ 250 asesores ficticios importados
- ✅ Distribuidos en ciudades principales y secundarias
- ✅ Todos con credenciales funcionales (Teloo2024!)
- ✅ Visibles en dashboard administrativo

### 2. Configuración
- ✅ Parámetro `puntaje_defecto_asesores_nuevos` agregado a BD (valor: 50)
- ✅ Campo `confianza` existe en modelo Asesor (default: 3.0, rango: 1.0-5.0)

### 3. Backend - Importación
- ✅ Fix en `asesores_service.py` para leer teléfonos como string
- ✅ Validación de formato de teléfono funcionando

## ⏳ PENDIENTE (Para próxima sesión)

### 1. Frontend - Formulario de Asesores
**Archivo**: `frontend/admin/src/components/asesores/AsesorForm.tsx`

Agregar campo confianza:
```tsx
// Después del campo direccion_punto_venta, agregar:
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
    value={formData.confianza || 3.0}
    onChange={(e) => handleInputChange('confianza', parseFloat(e.target.value) || 3.0)}
    disabled={loadingData || isLoading}
  />
  {errors.confianza && (
    <p className="text-sm text-destructive">{errors.confianza}</p>
  )}
</div>
```

Actualizar formData state:
```tsx
const [formData, setFormData] = useState<AsesorCreate>({
  // ... campos existentes
  confianza: 3.0,
});
```

Actualizar useEffect para asesor:
```tsx
if (asesor) {
  setFormData({
    // ... campos existentes
    confianza: asesor.confianza || 3.0,
  });
}
```

Agregar validación:
```tsx
if (formData.confianza < 1.0 || formData.confianza > 5.0) {
  newErrors.confianza = 'La calificación debe estar entre 1.0 y 5.0';
}
```

### 2. Frontend - Tipos TypeScript
**Archivo**: `frontend/admin/src/types/asesores.ts`

```typescript
export interface AsesorCreate {
  // ... campos existentes
  confianza?: number;
}

export interface AsesorUpdate {
  // ... campos existentes
  confianza?: number;
}

export interface Asesor {
  // ... campos existentes
  confianza: number;
}
```

### 3. Backend - Servicio de Asesores
**Archivo**: `services/core-api/services/asesores_service.py`

En `create_asesor` agregar:
```python
confianza = data.get('confianza', 3.0)
asesor = await Asesor.create(
    # ... campos existentes
    confianza=Decimal(str(confianza))
)
```

En `update_asesor` agregar:
```python
if 'confianza' in data:
    asesor.confianza = Decimal(str(data['confianza']))
```

### 4. Backend - Lógica de Escalamiento
**Archivo**: `services/core-api/services/escalamiento_service.py`

Implementar funciones con fallbacks:
- `_calcular_actividad_con_fallback()`
- `_calcular_desempeno_con_fallback()`
- `_tiene_historial_actividad()`
- `_tiene_historial_desempeno()`

Actualizar `calcular_puntaje_asesor()` para usar:
```python
# Confianza desde campo actual del asesor
puntaje_confianza = float(asesor.confianza) * 20  # Escala 1-5 a 0-100
```

### 5. Backend - Integración Automática
**Archivo**: `services/core-api/services/solicitudes_service.py`

En `create_solicitud`, después de guardar:
```python
if solicitud.estado == EstadoSolicitud.ABIERTA:
    from services.escalamiento_service import EscalamientoService
    escalamiento_service = EscalamientoService()
    await escalamiento_service.ejecutar_escalamiento(solicitud.id)
```

## 🎯 Resultado Esperado

Cuando esté completo:
1. Admin puede editar calificación de confianza de cada asesor
2. Asesores nuevos empiezan con puntaje 50 para actividad/desempeño
3. Confianza se toma del campo actual (editable)
4. Al crear solicitud, escalamiento se ejecuta automáticamente
5. Asesores se clasifican en 5 niveles
6. Sistema listo para producción

## 📝 Notas

- El campo `confianza` ya existe en BD con default 3.0
- El parámetro `puntaje_defecto_asesores_nuevos` ya está en BD con valor 50
- Solo falta conectar el frontend y completar la lógica de escalamiento
- Los 250 asesores ya están listos para probar
