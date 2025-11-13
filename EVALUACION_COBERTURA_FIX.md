# 🔧 Fix: Algoritmo de Evaluación con Cobertura Mínima

## Problema Identificado

El algoritmo de evaluación tenía un **bug crítico** en la lógica de cobertura que impedía las adjudicaciones mixtas:

### Comportamiento Incorrecto (ANTES)
1. Para cada repuesto, filtraba ofertas que lo incluían
2. Luego calculaba la cobertura de cada oferta
3. **Resultado**: Solo evaluaba ofertas completas (100% cobertura)

**Ejemplo Real:**
- Solicitud: sensor 1 + Sensor 2
- Laura: 100% cobertura (ambos) → ✅ Evaluada
- José: 50% cobertura (solo Sensor 2) → ❌ NO evaluada
- Miguel: 50% cobertura (solo sensor 1) → ❌ NO evaluada
- Sandra: 50% cobertura (solo sensor 1) → ❌ NO evaluada

**Resultado**: Laura ganó TODO con $220,000

---

## Solución Implementada

### Comportamiento Correcto (DESPUÉS)

**Algoritmo en 5 pasos:**

1. **Filtrar por cobertura a nivel de oferta completa**
   - Calcular cobertura de cada oferta: `(repuestos_cubiertos / total_repuestos) * 100`
   - Filtrar ofertas con cobertura ≥ 50%

2. **Filtrar ofertas que tienen el repuesto específico**
   - De las ofertas que pasaron el filtro de cobertura
   - Seleccionar solo las que incluyen el repuesto a evaluar

3. **Aplicar excepción de único oferente**
   - Si no hay ofertas con cobertura suficiente
   - Pero hay UN SOLO oferente para ese repuesto
   - Adjudicar por excepción (sin importar cobertura)

4. **Evaluar con fórmula de puntaje**
   ```
   Puntaje_Final = (Puntaje_Precio × peso_precio) + 
                   (Puntaje_Tiempo × peso_tiempo) + 
                   (Puntaje_Garantía × peso_garantía)
   ```
   
   Donde cada componente se normaliza 0-1:
   - **Precio**: `(precio_max - precio_oferta) / (precio_max - precio_min)` (menor es mejor)
   - **Tiempo**: `(tiempo_max - tiempo_oferta) / (tiempo_max - tiempo_min)` (menor es mejor)
   - **Garantía**: `(garantia_oferta - garantia_min) / (garantia_max - garantia_min)` (mayor es mejor)

5. **Adjudicar al mejor puntaje**
   - El repuesto se adjudica al asesor con mayor puntaje final
   - Permite adjudicaciones mixtas (diferentes asesores por repuesto)

---

## Ejemplo con Datos Reales

### Solicitud 95b71481
**Repuestos solicitados:**
- sensor 1: 2 unidades
- Sensor 2: 1 unidad

**Ofertas recibidas:**

| Asesor | sensor 1 | Sensor 2 | Cobertura | Pasa Filtro |
|--------|----------|----------|-----------|-------------|
| Laura Pérez | $80,000 (2u) | $60,000 (1u) | 100% (2/2) | ✅ SÍ |
| José Moreno | - | $50,000 (1u) | 50% (1/2) | ✅ SÍ |
| Miguel Jiménez | $40,000 (2u) | - | 50% (1/2) | ✅ SÍ |
| Sandra Romero | $50,000 (2u) | - | 50% (1/2) | ✅ SÍ |

### Evaluación Esperada

**sensor 1** (Laura, Miguel, Sandra califican):
- Miguel: $40,000 → **Mejor precio** → Probablemente gane
- Sandra: $50,000 → Segundo mejor
- Laura: $80,000 → Más caro

**Sensor 2** (Laura, José califican):
- José: $50,000 → **Mejor precio** → Probablemente gane
- Laura: $60,000 → Más caro

### Resultado Esperado
- **sensor 1** → Miguel Jiménez: $80,000 (2 × $40,000)
- **Sensor 2** → José Moreno: $50,000 (1 × $50,000)
- **Total**: $130,000 (ahorro de $90,000 vs $220,000 actual)

---

## Cambios en el Código

### Archivo Modificado
`services/core-api/services/evaluacion_service.py`

### Función Corregida
`evaluar_repuesto_con_cobertura()`

### Cambios Clave

**ANTES:**
```python
# Filtraba por repuesto PRIMERO
ofertas_con_repuesto = []
for oferta in ofertas_disponibles:
    detalle = await OfertaDetalle.get_or_none(
        oferta=oferta,
        repuesto_solicitado=repuesto  # ← Filtro incorrecto
    )
    if detalle:
        ofertas_con_repuesto.append((oferta, detalle))

# Luego calculaba cobertura (ya filtrado)
for oferta, detalle in ofertas_con_repuesto:
    repuestos_cubiertos = await OfertaDetalle.filter(oferta=oferta).count()
    cobertura_pct = (repuestos_cubiertos / total_repuestos_solicitud) * 100
```

**DESPUÉS:**
```python
# Calcula cobertura PRIMERO (todas las ofertas)
ofertas_con_cobertura_suficiente = []
for oferta in ofertas_disponibles:
    repuestos_cubiertos = await OfertaDetalle.filter(oferta=oferta).count()
    cobertura_pct = (repuestos_cubiertos / total_repuestos_solicitud) * 100
    
    if cobertura_pct >= cobertura_minima_pct:
        ofertas_con_cobertura_suficiente.append({
            'oferta': oferta,
            'cobertura_pct': cobertura_pct
        })

# Luego filtra por repuesto (solo las que pasaron cobertura)
ofertas_con_repuesto = []
for oferta_data in ofertas_con_cobertura_suficiente:
    detalle = await OfertaDetalle.get_or_none(
        oferta=oferta_data['oferta'],
        repuesto_solicitado=repuesto
    )
    if detalle:
        ofertas_con_repuesto.append({
            'oferta': oferta_data['oferta'],
            'detalle': detalle,
            'cobertura_pct': oferta_data['cobertura_pct']
        })
```

---

## Próximos Pasos

1. ✅ Código corregido
2. ⏳ Reiniciar servicio core-api
3. ⏳ Crear nueva solicitud de prueba
4. ⏳ Verificar adjudicaciones mixtas
5. ⏳ Validar cálculos de puntaje

---

## Notas Importantes

- La cobertura mínima está configurada en 50%
- Las ofertas con cobertura ≥ 50% participan en la evaluación
- Las ofertas con cobertura < 50% solo participan si son el único oferente
- El sistema ahora permite adjudicaciones mixtas (múltiples asesores ganadores)
- Cada repuesto se evalúa independientemente con la fórmula completa

---

**Fecha**: 2025-11-13  
**Archivo**: `services/core-api/services/evaluacion_service.py`  
**Función**: `evaluar_repuesto_con_cobertura()`
