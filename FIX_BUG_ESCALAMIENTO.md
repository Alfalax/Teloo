# 🐛 FIX: Bug de Evaluación Prematura en Escalamiento

## 📋 RESUMEN DEL BUG

**Solicitud afectada:** 91269925-529b-496e-974d-37c228c06bbd

**Síntoma:** La solicitud se evaluó prematuramente en nivel 4 con solo 1 oferta incompleta (60% cobertura), cuando debería haber escalado a nivel 5.

---

## 🔍 CAUSA RAÍZ

El código tenía **3 problemas** en el archivo `services/core-api/jobs/scheduled_jobs.py`:

### 1. Verificación de asesores en tabla incorrecta (INNECESARIA)
```python
# ❌ CÓDIGO ANTERIOR
asesores_disponibles = await Asesor.filter(
    nivel_actual=siguiente_nivel,  # Busca en tabla asesores
    estado=EstadoUsuario.ACTIVO
).count()
```
- Todos los asesores tienen `nivel_actual=3` en la tabla `asesores`
- Los niveles de escalamiento están en `evaluaciones_asesores_temp`
- Esta verificación siempre retornaba 0 para niveles 4 y 5

### 2. Lógica anidada innecesaria
```python
# ❌ CÓDIGO ANTERIOR
if asesores_disponibles == 0:  # Siempre verdadero
    if siguiente_nivel >= NIVEL_MAXIMO:
        if len(ofertas) > 0:  # ← BUG: Cualquier oferta
            # EVALÚA
```

### 3. Verificación incorrecta de ofertas
```python
# ❌ CÓDIGO ANTERIOR
if len(ofertas) > 0:  # Verifica si hay CUALQUIER oferta
    # EVALÚA con ofertas incompletas
```
- No verificaba si las ofertas eran completas (100% cobertura)
- No verificaba si cumplía el mínimo de ofertas completas requeridas

---

## ✅ SOLUCIÓN IMPLEMENTADA

### Cambio 1: Eliminar verificación de asesores innecesaria
Se eliminó completamente la verificación de asesores en la tabla `asesores` porque:
- Es inútil (siempre retorna 0)
- Los niveles reales están en `evaluaciones_asesores_temp`
- No afecta la lógica de escalamiento

### Cambio 2: Verificar nivel máximo directamente
```python
# ✅ CÓDIGO NUEVO
if siguiente_nivel >= NIVEL_MAXIMO:
    # Verificar ofertas COMPLETAS
    if ofertas_completas >= solicitud.ofertas_minimas_deseadas:
        # EVALUAR
    else:
        # ESCALAR al nivel máximo y esperar timeout
```

### Cambio 3: Verificar ofertas COMPLETAS
```python
# ✅ CÓDIGO NUEVO
if ofertas_completas >= solicitud.ofertas_minimas_deseadas:
    # Solo evalúa si hay suficientes ofertas COMPLETAS
```

---

## 🎯 COMPORTAMIENTO DESPUÉS DEL FIX

### Caso 1: Solicitud en nivel 4 con 1 oferta incompleta
**ANTES (BUG):**
1. Timeout cumplido
2. Busca asesores con nivel_actual=5 → 0
3. siguiente_nivel (5) >= NIVEL_MAXIMO (5) → VERDADERO
4. len(ofertas) > 0 → VERDADERO
5. **EVALÚA** ❌ (incorrecto)

**DESPUÉS (FIX):**
1. Timeout cumplido
2. siguiente_nivel (5) >= NIVEL_MAXIMO (5) → VERDADERO
3. ofertas_completas (0) >= ofertas_minimas_deseadas (2) → FALSO
4. **ESCALA a nivel 5** ✅ (correcto)
5. Espera timeout de nivel 5
6. Si sigue sin ofertas completas → cierra sin ofertas

### Caso 2: Solicitud en nivel 5 con 2 ofertas completas
**ANTES y DESPUÉS (CORRECTO):**
1. Ya está en nivel máximo
2. ofertas_completas (2) >= ofertas_minimas_deseadas (2) → VERDADERO
3. **EVALÚA** ✅ (correcto)

### Caso 3: Solicitud en nivel 5 con 0 ofertas
**ANTES y DESPUÉS (CORRECTO):**
1. Ya está en nivel máximo
2. ofertas_completas (0) >= ofertas_minimas_deseadas (2) → FALSO
3. **CIERRA SIN OFERTAS** ✅ (correcto)

---

## 📝 ARCHIVOS MODIFICADOS

- `services/core-api/jobs/scheduled_jobs.py`
  - Líneas 485-565: Lógica cuando solicitud YA está en nivel máximo
  - Líneas 567-680: Lógica de escalamiento a siguiente nivel

---

## ✅ VALIDACIÓN

Para validar el fix:

1. Crear una solicitud en nivel 3
2. Hacer 1 oferta incompleta (60% cobertura)
3. Esperar timeout (2 minutos)
4. Verificar que escale a nivel 4 (no evalúe)
5. Esperar timeout de nivel 4
6. Verificar que escale a nivel 5 (no evalúe)
7. Esperar timeout de nivel 5
8. Verificar que cierre sin ofertas (no evalúe)

---

## 🎉 RESULTADO

El bug está corregido. Las solicitudes ahora:
- Escalan correctamente hasta el nivel máximo
- Solo evalúan cuando tienen ofertas completas suficientes
- Cierran sin ofertas cuando no cumplen el mínimo en nivel máximo
