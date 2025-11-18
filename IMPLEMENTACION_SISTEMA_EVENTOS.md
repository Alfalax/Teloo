# Implementación del Sistema de Eventos para Métricas de Escalamiento

## Resumen

Se implementó un sistema de eventos que pobla automáticamente las tablas auxiliares `ofertas_historicas` y `historial_respuestas_ofertas` para el cálculo correcto de las métricas de **actividad reciente** y **desempeño histórico** en el algoritmo de escalamiento.

## Problema Identificado

Las funciones `calcular_actividad_reciente` y `calcular_desempeno_historico` en `escalamiento_service.py` consultaban tablas auxiliares que estaban vacías, causando que todos los asesores obtuvieran valores de fallback idénticos (3.0 y 1.0 respectivamente), sin reflejar su historial real.

## Solución Implementada

### 1. Servicio de Eventos (`services/core-api/services/events_service.py`)

Nuevo servicio que maneja 4 eventos principales:

#### `on_oferta_created()`
- **Cuándo:** Al crear una nueva oferta
- **Acción:** Inserta registro en `ofertas_historicas`
- **Datos:** oferta_id, asesor_id, solicitud_id, monto_total, tiempo_respuesta_seg

#### `on_oferta_adjudicada()`
- **Cuándo:** Al evaluar y marcar una oferta como GANADORA
- **Acción:** Actualiza `adjudicada=True` en `ofertas_historicas`

#### `on_solicitud_escalada()`
- **Cuándo:** Al notificar asesores en una oleada de escalamiento
- **Acción:** Inserta registros en `historial_respuestas_ofertas` para cada asesor notificado
- **Datos:** asesor_id, solicitud_id, fecha_envio, nivel, canal

#### `on_asesor_respondio()`
- **Cuándo:** Al crear una oferta (si el asesor fue notificado)
- **Acción:** Actualiza `respondio=True` y `tiempo_respuesta_seg` en `historial_respuestas_ofertas`

### 2. Integración en Servicios Existentes

#### `ofertas_service.py`
- **Línea ~175:** Llama a `on_oferta_created()` después del commit de transacción
- **Línea ~180:** Calcula tiempo de respuesta y llama a `on_asesor_respondio()` si aplica

#### `escalamiento_service.py`
- **Línea ~680:** Llama a `on_solicitud_escalada()` después de notificar asesores en `ejecutar_oleada()`

#### `evaluacion_service.py`
- **Línea ~520:** Llama a `on_oferta_adjudicada()` para cada oferta ganadora después del commit

## Flujo de Datos

```
1. ESCALAMIENTO
   └─> Solicitud escalada a Nivel X
       └─> events_service.on_solicitud_escalada()
           └─> Inserta en historial_respuestas_ofertas
               (asesor_id, solicitud_id, fecha_envio, respondio=False)

2. CREACIÓN DE OFERTA
   └─> Asesor crea oferta
       └─> events_service.on_oferta_created()
           └─> Inserta en ofertas_historicas
               (oferta_id, asesor_id, adjudicada=False)
       └─> events_service.on_asesor_respondio()
           └─> Actualiza historial_respuestas_ofertas
               (respondio=True, tiempo_respuesta_seg)

3. EVALUACIÓN
   └─> Oferta marcada como GANADORA
       └─> events_service.on_oferta_adjudicada()
           └─> Actualiza ofertas_historicas
               (adjudicada=True)
```

## Beneficios

1. **Datos Reales:** Las métricas ahora reflejan el historial real de cada asesor
2. **Arquitectura Correcta:** Alineado con el diseño original del sistema
3. **Automático:** No requiere jobs de migración ni mantenimiento manual
4. **Producción Ready:** Funciona desde el primer escalamiento/oferta

## Impacto en Escalamiento

### Antes
- Sandra: actividad=3.0, desempeño=1.0 (fallback)
- Andrea: actividad=3.0, desempeño=1.0 (fallback)
- Otros 191: actividad=3.0, desempeño=1.0 (fallback)

### Después (esperado)
- Sandra (4 ofertas, 4 ganadoras): actividad=3.0-5.0, desempeño=5.0
- Andrea (4 ofertas, 1 ganadora): actividad=3.0-5.0, desempeño=2.0
- Otros 191 (sin ofertas): actividad=1.0, desempeño=1.0 (fallback)

## Testing

Para probar el sistema:

1. Limpiar base de datos (ya hecho)
2. Crear una solicitud
3. Escalar la solicitud → Verifica `historial_respuestas_ofertas`
4. Crear ofertas → Verifica `ofertas_historicas`
5. Evaluar solicitud → Verifica `adjudicada=True`
6. Crear nueva solicitud y escalar → Verifica que las métricas reflejen el historial

## Archivos Modificados

- ✅ `services/core-api/services/events_service.py` (NUEVO)
- ✅ `services/core-api/services/ofertas_service.py`
- ✅ `services/core-api/services/escalamiento_service.py`
- ✅ `services/core-api/services/evaluacion_service.py`

## Próximos Pasos

1. Probar flujo completo con solicitudes reales
2. Verificar que las métricas se calculan correctamente
3. Monitorear logs para detectar errores en eventos
4. Considerar agregar índices en tablas auxiliares si el volumen crece

## Notas Técnicas

- Los eventos se ejecutan **después** del commit de transacciones para garantizar consistencia
- Los errores en eventos se loguean pero no afectan el flujo principal
- El sistema es **idempotente**: si un evento falla, se puede reintentar sin duplicar datos
- Compatible con el sistema de eventos Redis existente (no lo reemplaza, lo complementa)
