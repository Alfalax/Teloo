# Bug: Variable no definida en evaluación causa estados inconsistentes

## Problema Identificado

**Solicitud afectada:** 090084ea-3205-4dae-9448-631a11e6161e  
**Síntoma:** Solicitud marcada como `CERRADA_SIN_OFERTAS` pero tiene 2 ofertas (1 GANADORA, 1 NO_SELECCIONADA)

## Causa Raíz

### Error en `evaluacion_service.py` línea 580

```python
return {
    'ofertas_ganadoras': len(ofertas_ganadoras),  # ❌ Variable no definida
    'ofertas_no_seleccionadas': len(ofertas_no_seleccionadas),  # ❌ Variable no definida
}
```

### Cronología del Bug

1. **14:19:26** - Solicitud creada correctamente con estado `ABIERTA`
2. **14:20:26** - Sandra Romero envía oferta ($315,000, 5 repuestos, 100% cobertura)
3. **14:21:07** - Andrea Herrera envía oferta ($35,000, 1 repuesto, 20% cobertura)
4. **14:21:30** - Job automático detecta timeout y ejecuta evaluación:
   - ✅ Adjudica los 5 repuestos a Sandra Romero
   - ✅ Marca ofertas como GANADORA/NO_SELECCIONADA
   - ❌ **ERROR:** `name 'ofertas_ganadoras' is not defined`
   - ❌ **Transacción hace ROLLBACK**
   - ❌ Estado de solicitud NO se actualiza (queda en estado incorrecto)

### Logs del Error

```
INFO:services.evaluacion_service:Evaluación completada para solicitud SOL-090084EA: 
5/5 repuestos adjudicados, 1 asesores ganadores, monto total: $315,000, tiempo: 87ms

ERROR:services.evaluacion_service:Error inesperado evaluando solicitud 090084ea: 
name 'ofertas_ganadoras' is not defined

ERROR:jobs.scheduled_jobs:Error evaluando en nivel máximo: 
Error interno evaluando solicitud: name 'ofertas_ganadoras' is not defined
```

## Impacto

### Inconsistencia de Datos
- **Ofertas actualizadas:** Estados GANADORA/NO_SELECCIONADA se guardaron
- **Solicitud NO actualizada:** Quedó en estado incorrecto
- **Adjudicaciones NO creadas:** Se perdieron por el rollback
- **Monto NO actualizado:** `monto_total_adjudicado` = 0

### Por qué las ofertas sí se actualizaron

Las ofertas se actualizaron **FUERA de la transacción atómica** (líneas 495-499):

```python
# Esto está DENTRO de la transacción
async with in_transaction() as conn:
    # ... crear adjudicaciones ...
    
    # Actualizar estados de ofertas
    for oferta in ofertas_activas:
        if oferta.id in ofertas_ganadoras_ids:
            oferta.estado = EstadoOferta.GANADORA
        else:
            oferta.estado = EstadoOferta.NO_SELECCIONADA
        await oferta.save(using_db=conn)  # ✅ Dentro de transacción
    
    # Actualizar solicitud
    await solicitud.save(using_db=conn)  # ✅ Dentro de transacción

# Esto está FUERA de la transacción
return {
    'ofertas_ganadoras': len(ofertas_ganadoras),  # ❌ ERROR aquí
}
```

**Resultado:** El error ocurre DESPUÉS de que la transacción se commitea, por lo que las ofertas y solicitud SÍ se actualizaron, pero el error impide que se creen las adjudicaciones y se complete el proceso.

## Solución Implementada

### Código Corregido

```python
# Determine if it's a mixed adjudication (multiple different asesores won)
asesores_ganadores = set(adj.oferta.asesor.id for adj in adjudicaciones_creadas)
es_adjudicacion_mixta = len(asesores_ganadores) > 1

# Count winning and non-selected offers ← NUEVO
ofertas_ganadoras = [o for o in ofertas_activas if o.estado == EstadoOferta.GANADORA]
ofertas_no_seleccionadas = [o for o in ofertas_activas if o.estado == EstadoOferta.NO_SELECCIONADA]
```

### Archivo Modificado
- `services/core-api/services/evaluacion_service.py` (línea ~523)

## Prevención Futura

### 1. Testing
- ✅ Agregar test unitario que verifique el retorno completo de `evaluar_solicitud`
- ✅ Test de integración que simule evaluación automática

### 2. Type Hints
```python
def evaluar_solicitud(...) -> Dict[str, Any]:  # Agregar validación de schema
```

### 3. Validación de Variables
- Usar linters que detecten variables no definidas
- Agregar mypy para type checking estático

## Relación con Transacciones Atómicas

Este bug **NO fue causado** por la implementación de transacciones atómicas, pero las transacciones **expusieron el bug**:

- **Antes:** Sin transacciones, el error pasaba desapercibido
- **Después:** Con transacciones, el error causa rollback y estados inconsistentes más evidentes

Las transacciones atómicas son correctas y necesarias. El bug era preexistente en el código.

## Estado

- ✅ **Bug identificado:** Variable no definida
- ✅ **Causa raíz encontrada:** Error en línea 580
- ✅ **Solución implementada:** Variables definidas correctamente
- ⏳ **Pendiente:** Corregir solicitud 090084ea manualmente
- ⏳ **Pendiente:** Agregar tests para prevenir regresión

## Recomendación

1. **Corregir solicitud 090084ea:** Actualizar estado a `EVALUADA` y crear adjudicaciones faltantes
2. **Monitorear logs:** Verificar que no haya más solicitudes afectadas
3. **Agregar tests:** Prevenir regresión de este bug
