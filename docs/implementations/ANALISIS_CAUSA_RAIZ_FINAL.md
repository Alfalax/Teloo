# ANÁLISIS CAUSA RAÍZ - Solicitud 91269925

## DATOS CONFIRMADOS

**Solicitud 91269925:**
- Estado final: EVALUADA
- Nivel final: 4 (NO llegó a nivel 5)
- Fecha escalamiento: 2025-11-14 17:12:58
- Fecha evaluación: 2025-11-14 17:15:34 (2.6 minutos después)
- Ofertas recibidas: 1
- Ofertas completas (100%): 0
- Ofertas mínimas deseadas: 2
- Repuestos totales: 5
- Repuestos cubiertos por oferta: 3 (60%)

## FLUJO DEL CÓDIGO

El job se ejecuta cada minuto. Cuando detecta timeout (2 min):

### 1. Primera verificación (línea 439):
```python
if ofertas_completas >= solicitud.ofertas_minimas_deseadas:
    # EVALUAR
```
**Resultado:** 0 >= 2 = FALSO → NO evalúa aquí

### 2. Segunda verificación (línea 485):
```python
if solicitud.nivel_actual >= NIVEL_MAXIMO:  # 4 >= 5
    # Ya está en nivel máximo
```
**Resultado:** 4 >= 5 = FALSO → NO entra aquí

### 3. Debería escalar (línea 567):
```python
siguiente_nivel = solicitud.nivel_actual + 1  # 5
# Escalar a nivel 5
```

## PREGUNTA CRÍTICA

¿Por qué se evaluó en nivel 4 si ninguna de las condiciones de evaluación se cumplió?

## HIPÓTESIS A VERIFICAR

1. ¿Hay otro código que evalúa solicitudes fuera del job?
2. ¿Se llamó manualmente el endpoint de evaluación?
3. ¿Hay un error en cómo se cuentan las ofertas completas?
4. ¿El job se ejecutó dos veces y en la segunda ejecución ya estaba evaluada?

## SIGUIENTE PASO

Necesito revisar los logs EXACTOS del momento en que se evaluó la solicitud para ver qué condición se cumplió realmente.
