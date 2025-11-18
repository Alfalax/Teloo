# Mejora en la Lógica de Cobertura de Ofertas

## Problema Identificado

La lógica anterior era demasiado restrictiva cuando múltiples asesores ofertaban el mismo repuesto con cobertura < 50%.

### Caso problemático (Solicitud 611c3f18):
- 5 repuestos solicitados
- 2 asesores ofertan el mismo repuesto (Pastillas de freno)
- Ambos con 20% de cobertura (1 de 5 repuestos)
- **Resultado anterior:** Solicitud cerrada sin ofertas (CERRADA_SIN_OFERTAS)
- **Problema:** El cliente no recibió ninguna oferta a pesar de haber 2 disponibles

## Solución Implementada

### Cambio en `services/core-api/services/evaluacion_service.py`

**ANTES:**
```python
# Si solo hay una oferta (único oferente), adjudicar por excepción
if len(ofertas_excepcion) == 1:
    ofertas_con_repuesto = ofertas_excepcion
else:
    return {'success': False, ...}  # Rechazar si hay múltiples ofertas
```

**DESPUÉS:**
```python
# Si hay ofertas disponibles (1 o más), evaluarlas por puntaje
if len(ofertas_excepcion) > 0:
    ofertas_con_repuesto = ofertas_excepcion
    if len(ofertas_excepcion) == 1:
        # Log: único oferente
    else:
        # Log: múltiples ofertas compitiendo
else:
    return {'success': False, ...}  # Solo rechazar si NO hay ofertas
```

## Nueva Lógica de Evaluación

### Nivel 1: Ofertas con cobertura >= 50%
- **Prioridad absoluta**
- Compiten solo entre ellas por puntaje
- Protege a asesores con alta cobertura

### Nivel 2: Si no hay ofertas con >= 50%
- **Evaluar todas las ofertas disponibles** (1 o más)
- Seleccionar la mejor por puntaje
- Ya no se rechaza por tener múltiples competidores

### Nivel 3: Sin ofertas
- Solo se cierra sin ofertas si realmente no hay ninguna

## Beneficios

1. **Más ofertas para el cliente:** Casos que antes se cerraban sin ofertas ahora se adjudican
2. **Competencia justa:** Múltiples asesores pueden competir incluso con baja cobertura
3. **Protección de cobertura alta:** Se mantiene la prioridad para ofertas >= 50%
4. **Mejor experiencia:** El cliente siempre recibe la mejor oferta disponible

## Casos de Uso

### Caso 1: Múltiples ofertas con baja cobertura (MEJORADO)
- Solicitud: 5 repuestos
- Asesor A: 20% (1 repuesto: Pastillas) - $100,000
- Asesor B: 20% (1 repuesto: Pastillas) - $90,000
- **Resultado:** Se adjudica a Asesor B por mejor precio

### Caso 2: Único oferente con baja cobertura (SIN CAMBIO)
- Solicitud: 5 repuestos
- Asesor A: 20% (1 repuesto único)
- **Resultado:** Se adjudica a Asesor A (único oferente)

### Caso 3: Ofertas con alta cobertura (SIN CAMBIO)
- Solicitud: 5 repuestos
- Asesor A: 80% (4 repuestos)
- Asesor B: 20% (1 repuesto)
- **Resultado:** Asesor A tiene prioridad en sus repuestos

## Motivos de Adjudicación

Se agregó un nuevo motivo para mayor claridad:

- `mejor_puntaje_con_cobertura`: Ganó con cobertura >= 50%
- `unica_oferta_disponible`: Único oferente (cualquier cobertura)
- `mejor_puntaje_sin_cobertura_suficiente`: **NUEVO** - Ganó entre múltiples ofertas < 50%

## Impacto

- **Archivos modificados:** 1 (`evaluacion_service.py`)
- **Líneas cambiadas:** ~15
- **Riesgo:** Bajo
- **Compatibilidad:** Total (no afecta casos existentes)
