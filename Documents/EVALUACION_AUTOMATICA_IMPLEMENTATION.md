# Implementación de Evaluación Automática de Ofertas

## Resumen

Se ha implementado el sistema de evaluación automática de ofertas que se ejecuta cuando se cumplen las condiciones definidas en los requirements del sistema.

## Cambios Implementados

### 1. Modificación de `services/core-api/jobs/scheduled_jobs.py`

#### Función agregada: `_publicar_evento_evaluacion_completada()`

Nueva función helper que publica eventos a Redis cuando se completa una evaluación automática:

```python
async def _publicar_evento_evaluacion_completada(
    solicitud,
    resultado_evaluacion: Dict[str, Any],
    redis_client: redis.Redis
):
```

**Propósito:** Notificar al Agent IA que debe contactar al cliente con los resultados de la evaluación.

**Evento publicado:** `evaluacion.completada_automatica`

**Datos del evento:**
- `solicitud_id`: ID de la solicitud evaluada
- `cliente_telefono`: Teléfono del cliente para notificación
- `cliente_nombre`: Nombre completo del cliente
- `repuestos_adjudicados`: Cantidad de repuestos con ganador
- `repuestos_totales`: Total de repuestos solicitados
- `monto_total`: Monto total adjudicado
- `es_adjudicacion_mixta`: Si hay múltiples asesores ganadores
- `asesores_ganadores`: Cantidad de asesores que ganaron
- `adjudicaciones`: Detalle completo de adjudicaciones

#### Modificación: `verificar_timeouts_escalamiento()`

Se agregó evaluación automática en dos escenarios:

**Escenario 1: Cierre anticipado (ofertas mínimas alcanzadas)**

```python
if ofertas_count >= solicitud.ofertas_minimas_deseadas:
    # EJECUTAR EVALUACIÓN AUTOMÁTICA
    resultado_eval = await EvaluacionService.evaluar_solicitud(str(solicitud.id))
    
    if resultado_eval['success']:
        # Publicar evento para notificar al cliente
        await _publicar_evento_evaluacion_completada(solicitud, resultado_eval, redis_client)
```

**Comportamiento:**
- ✅ Cuando una solicitud alcanza el número mínimo de ofertas deseadas (ej: 2 ofertas)
- ✅ Se ejecuta automáticamente la evaluación
- ✅ Se calculan puntajes y se adjudican ganadores
- ✅ Se publica evento a Redis para notificación al cliente
- ✅ Estado cambia a `EVALUADA`

**Escenario 2: Nivel máximo alcanzado**

```python
if solicitud.nivel_actual >= NIVEL_MAXIMO:
    if ofertas_count > 0:
        # EJECUTAR EVALUACIÓN AUTOMÁTICA con ofertas disponibles
        resultado_eval = await EvaluacionService.evaluar_solicitud(str(solicitud.id))
        
        if resultado_eval['success'] and resultado_eval['repuestos_adjudicados'] > 0:
            # Publicar evento
            await _publicar_evento_evaluacion_completada(solicitud, resultado_eval, redis_client)
        else:
            # Sin adjudicaciones, cerrar sin ofertas
            solicitud.estado = EstadoSolicitud.CERRADA_SIN_OFERTAS
    else:
        # Sin ofertas, cerrar sin ofertas
        solicitud.estado = EstadoSolicitud.CERRADA_SIN_OFERTAS
```

**Comportamiento:**
- ✅ Cuando una solicitud llega al nivel 5 (máximo)
- ✅ Si tiene ofertas, se evalúa automáticamente
- ✅ Si la evaluación es exitosa, se notifica al cliente
- ✅ Si no hay adjudicaciones o no hay ofertas, estado cambia a `CERRADA_SIN_OFERTAS`

#### Import agregado

```python
import json  # Para serializar eventos a Redis
```

## Flujo Completo del Sistema

```
┌─────────────────────────────────────────────────────────┐
│  1. Cliente envía solicitud por WhatsApp                │
│     → Agent IA crea solicitud en Core API               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  2. Escalamiento automático (primera oleada)            │
│     → Notifica asesores Nivel 1                         │
│     → Inicia timer de 15 minutos                        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  3. Asesores envían ofertas                             │
│     → Ofertas se registran en estado ENVIADA            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  4. Job verifica cada minuto (scheduled_jobs.py)        │
│     ✅ ¿Tiene 2+ ofertas? → EVALÚA AUTOMÁTICAMENTE      │
│     ⏰ ¿Pasaron 15 min? → Escala a Nivel 2              │
│     ❌ ¿Nivel 5 sin ofertas? → Cierra sin ofertas       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  5. Evaluación automática (evaluacion_service.py)       │
│     → Calcula puntajes: precio(50%) + tiempo(35%) +     │
│       garantía(15%)                                      │
│     → Aplica regla de cobertura mínima 50%              │
│     → Aplica lógica de cascada si es necesario          │
│     → Crea adjudicaciones por repuesto                  │
│     → Cambia estado a EVALUADA                          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  6. Publicación de evento a Redis                       │
│     → evaluacion.completada_automatica                  │
│     → Incluye datos completos de adjudicaciones         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  7. Agent IA recibe evento y notifica cliente           │
│     → Envía resumen de ofertas por WhatsApp            │
│     → Cliente puede aceptar/rechazar                    │
└─────────────────────────────────────────────────────────┘
```

## Manejo de Errores

El sistema implementa manejo robusto de errores:

1. **Error en evaluación:** Se registra el error pero no falla el job completo
2. **Error publicando evento:** Se registra pero no afecta la evaluación
3. **Solicitud sin ofertas:** Se cierra con estado `CERRADA_SIN_OFERTAS`
4. **Evaluación sin adjudicaciones:** Se cierra con estado `CERRADA_SIN_OFERTAS`

## Logs y Monitoreo

El sistema genera logs detallados en cada paso:

```
✅ Ofertas mínimas alcanzadas: 2 >= 2
✅ Evaluación automática exitosa: 3/4 adjudicados
📢 Evento de evaluación publicado para solicitud abc123
```

```
❌ Nivel máximo alcanzado para solicitud xyz789
📊 Evaluando solicitud en nivel máximo con 1 ofertas
✅ Evaluación en nivel máximo: 2 repuestos adjudicados
```

## Configuración

El sistema usa la configuración existente:

- **Ofertas mínimas:** `solicitud.ofertas_minimas_deseadas` (default: 2)
- **Nivel máximo:** 5 (constante)
- **Tiempos por nivel:** Configurables en `tiempos_espera_nivel`
- **Pesos de evaluación:** Configurables en `pesos_evaluacion_ofertas`
- **Cobertura mínima:** Configurable en `parametros_generales.cobertura_minima_pct`

## Próximos Pasos

1. ✅ **FASE 1 COMPLETADA:** Evaluación automática integrada en job de timeouts
2. ⏳ **FASE 2 PENDIENTE:** Agent IA debe suscribirse al evento `evaluacion.completada_automatica`
3. ⏳ **FASE 3 PENDIENTE:** Implementar notificaciones al cliente vía WhatsApp

## Testing

### Script de Prueba Automatizado

Se ha creado `test_evaluacion_automatica.py` con tres modos de prueba:

```bash
# Test completo
python test_evaluacion_automatica.py --test all

# Test de cierre anticipado
python test_evaluacion_automatica.py --test cierre

# Test de nivel máximo
python test_evaluacion_automatica.py --test nivel_max
```

### Prueba Manual

Para probar el sistema manualmente:

1. **Crear una solicitud con 2 repuestos:**
   ```bash
   # Usar el frontend admin o API directamente
   POST /api/solicitudes
   ```

2. **Asesores envían ofertas:**
   ```bash
   # Usar el frontend advisor o API
   POST /api/ofertas
   ```

3. **Esperar 1 minuto:**
   - El job `verificar_timeouts_escalamiento` se ejecuta cada minuto
   - Verificar logs del contenedor `teloo-core-api`

4. **Verificar evaluación:**
   ```bash
   # Ver logs
   docker logs teloo-core-api -f
   
   # Buscar mensajes como:
   # ✅ Ofertas mínimas alcanzadas: 2 >= 2
   # ✅ Evaluación automática exitosa: 3/4 adjudicados
   # 📢 Evento de evaluación publicado
   ```

5. **Verificar evento en Redis:**
   ```bash
   # Conectar a Redis
   docker exec -it teloo-redis redis-cli
   
   # Suscribirse al canal
   SUBSCRIBE evaluacion.completada_automatica
   ```

### Verificación de Estado

```sql
-- Ver solicitudes evaluadas recientemente
SELECT id, estado, nivel_actual, fecha_evaluacion, monto_total_adjudicado
FROM solicitudes
WHERE estado = 'EVALUADA'
ORDER BY fecha_evaluacion DESC
LIMIT 10;

-- Ver adjudicaciones de una solicitud
SELECT 
    r.nombre as repuesto,
    u.nombre_completo as asesor_ganador,
    a.precio_adjudicado,
    a.puntaje_obtenido,
    a.motivo_adjudicacion
FROM adjudicaciones_repuestos a
JOIN repuestos_solicitados r ON a.repuesto_solicitado_id = r.id
JOIN ofertas o ON a.oferta_id = o.id
JOIN asesores ase ON o.asesor_id = ase.id
JOIN usuarios u ON ase.usuario_id = u.id
WHERE a.solicitud_id = 'SOLICITUD_ID_AQUI';
```

## Cumplimiento de Requirements

Este cambio implementa el **Requirement 5** del spec:

> **Requirement 5:** Como sistema automatizado, quiero evaluar las ofertas recibidas de manera objetiva y transparente, para seleccionar las mejores opciones por cada repuesto individual.

**Acceptance Criteria cumplidos:**
- ✅ AC1: Evaluación automática se activa cuando corresponde
- ✅ AC2: Puntajes calculados con fórmula configurada
- ✅ AC3: Regla de cobertura ≥50% aplicada
- ✅ AC4: Lógica de cascada implementada
- ✅ AC5: Adjudicación por excepción para oferta única

## Archivos Modificados

- `services/core-api/jobs/scheduled_jobs.py` - Evaluación automática integrada

## Fecha de Implementación

12 de Noviembre de 2025
