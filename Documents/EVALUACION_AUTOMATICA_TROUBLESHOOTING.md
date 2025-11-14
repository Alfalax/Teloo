# Troubleshooting: Evaluación Automática

## Problemas Comunes y Soluciones

### 1. La evaluación no se ejecuta automáticamente

**Síntomas:**
- Solicitud tiene 2+ ofertas pero sigue en estado ABIERTA
- No aparecen logs de evaluación

**Causas posibles:**

#### A. El scheduler no está corriendo
```bash
# Verificar logs del contenedor
docker logs teloo-core-api | grep -i scheduler

# Debería mostrar:
# "Scheduler service started successfully"
# "Scheduled jobs configured"
```

**Solución:**
```bash
# Reiniciar el contenedor
docker restart teloo-core-api

# Verificar que inicie correctamente
docker logs teloo-core-api -f
```

#### B. El job no está programado
```bash
# Verificar endpoint de health
curl http://localhost:8000/health

# Debería incluir scheduler_status con el job:
# "verificar_timeouts_escalamiento"
```

**Solución:**
- Verificar que `scheduler_service.py` tenga el job configurado
- Verificar que `main.py` inicialice el scheduler

#### C. La solicitud no cumple las condiciones
```sql
-- Verificar estado de la solicitud
SELECT 
    id,
    estado,
    nivel_actual,
    fecha_escalamiento,
    ofertas_minimas_deseadas,
    (SELECT COUNT(*) FROM ofertas WHERE solicitud_id = solicitudes.id AND estado = 'ENVIADA') as ofertas_count
FROM solicitudes
WHERE id = 'SOLICITUD_ID';
```

**Condiciones requeridas:**
- Estado = 'ABIERTA'
- fecha_escalamiento IS NOT NULL
- ofertas_count >= ofertas_minimas_deseadas O nivel_actual = 5

### 2. La evaluación falla con error

**Síntomas:**
- Logs muestran "❌ Error en evaluación automática"
- Solicitud queda en estado EVALUADA pero sin adjudicaciones

**Diagnóstico:**
```bash
# Ver logs completos del error
docker logs teloo-core-api | grep -A 20 "Error en evaluación automática"
```

**Causas comunes:**

#### A. Ofertas sin detalles
```sql
-- Verificar que las ofertas tengan detalles
SELECT 
    o.id,
    o.codigo_oferta,
    COUNT(od.id) as detalles_count
FROM ofertas o
LEFT JOIN ofertas_detalles od ON o.id = od.oferta_id
WHERE o.solicitud_id = 'SOLICITUD_ID'
GROUP BY o.id;
```

**Solución:**
- Asegurar que cada oferta tenga al menos un detalle
- Verificar que los detalles estén vinculados a repuestos solicitados

#### B. Configuración de pesos inválida
```sql
-- Verificar configuración de pesos
SELECT * FROM parametros_configuracion
WHERE clave = 'pesos_evaluacion_ofertas';
```

**Solución:**
- Los pesos deben sumar 1.0 (precio + tiempo + garantía = 1.0)
- Valores típicos: {"precio": 0.5, "tiempo_entrega": 0.35, "garantia": 0.15}

#### C. Error de cobertura mínima
```sql
-- Verificar configuración de cobertura
SELECT * FROM parametros_configuracion
WHERE clave = 'parametros_generales';
```

**Solución:**
- cobertura_minima_pct debe estar entre 0 y 100
- Valor típico: 50 (50%)

### 3. El evento no se publica a Redis

**Síntomas:**
- Evaluación exitosa pero Agent IA no notifica al cliente
- No aparece log "📢 Evento de evaluación publicado"

**Diagnóstico:**
```bash
# Verificar conexión a Redis
docker exec -it teloo-redis redis-cli PING
# Debería responder: PONG

# Verificar que el scheduler tenga cliente Redis
docker logs teloo-core-api | grep -i "redis"
```

**Solución:**

#### A. Redis no está disponible
```bash
# Verificar que Redis esté corriendo
docker ps | grep redis

# Reiniciar Redis si es necesario
docker restart teloo-redis
```

#### B. Cliente Redis no inicializado
```python
# Verificar en scheduler_service.py que se inicialice:
await scheduler_service.initialize(redis_url)
```

#### C. Suscripción al canal incorrecta
```bash
# En Agent IA, verificar suscripción al canal correcto
# Canal: evaluacion.completada_automatica
```

### 4. Evaluación se ejecuta pero no adjudica repuestos

**Síntomas:**
- Log muestra "✅ Evaluación automática exitosa: 0/4 adjudicados"
- Solicitud en estado EVALUADA pero sin adjudicaciones

**Diagnóstico:**
```sql
-- Ver detalles de la evaluación
SELECT * FROM evaluaciones
WHERE solicitud_id = 'SOLICITUD_ID'
ORDER BY created_at DESC
LIMIT 1;

-- Ver ofertas y sus coberturas
SELECT 
    o.id,
    o.codigo_oferta,
    COUNT(DISTINCT od.repuesto_solicitado_id) as repuestos_cubiertos,
    (SELECT COUNT(*) FROM repuestos_solicitados WHERE solicitud_id = o.solicitud_id) as total_repuestos,
    (COUNT(DISTINCT od.repuesto_solicitado_id) * 100.0 / 
     (SELECT COUNT(*) FROM repuestos_solicitados WHERE solicitud_id = o.solicitud_id)) as cobertura_pct
FROM ofertas o
JOIN ofertas_detalles od ON o.id = od.oferta_id
WHERE o.solicitud_id = 'SOLICITUD_ID'
GROUP BY o.id;
```

**Causas comunes:**

#### A. Ninguna oferta cumple cobertura mínima
- Todas las ofertas tienen cobertura < 50%
- No hay oferta única (excepción)

**Solución:**
- Reducir cobertura_minima_pct temporalmente
- O esperar más ofertas con mejor cobertura

#### B. Ofertas con precios fuera de rango
```sql
-- Verificar precios de ofertas
SELECT 
    od.repuesto_solicitado_id,
    od.precio_unitario,
    od.tiempo_entrega_dias,
    od.garantia_meses
FROM ofertas_detalles od
JOIN ofertas o ON od.oferta_id = o.id
WHERE o.solicitud_id = 'SOLICITUD_ID';
```

**Solución:**
- Verificar que precios estén entre 1,000 y 50,000,000 COP
- Verificar que garantía esté entre 1 y 60 meses
- Verificar que tiempo de entrega esté entre 0 y 90 días

### 5. Job se ejecuta muy lento

**Síntomas:**
- Job tarda más de 1 minuto en completar
- Logs muestran warnings de "misfire"

**Diagnóstico:**
```bash
# Ver tiempo de ejecución del job
docker logs teloo-core-api | grep "Job escalamiento completado"
```

**Solución:**

#### A. Muchas solicitudes abiertas
```sql
-- Contar solicitudes abiertas
SELECT COUNT(*) FROM solicitudes
WHERE estado = 'ABIERTA' AND fecha_escalamiento IS NOT NULL;
```

**Optimización:**
- Agregar índices en la tabla solicitudes:
```sql
CREATE INDEX IF NOT EXISTS idx_solicitudes_estado_fecha 
ON solicitudes(estado, fecha_escalamiento);
```

#### B. Evaluaciones muy lentas
- Reducir timeout de evaluación en configuración
- Optimizar queries de evaluación

### 6. Verificación de Salud del Sistema

**Script de verificación completo:**

```bash
#!/bin/bash

echo "=== Verificación de Evaluación Automática ==="

echo -e "\n1. Verificar scheduler..."
curl -s http://localhost:8000/health | jq '.scheduler_status'

echo -e "\n2. Verificar Redis..."
docker exec teloo-redis redis-cli PING

echo -e "\n3. Verificar solicitudes pendientes..."
docker exec teloo-postgres psql -U teloo_user -d teloo_db -c "
SELECT 
    COUNT(*) FILTER (WHERE estado = 'ABIERTA') as abiertas,
    COUNT(*) FILTER (WHERE estado = 'EVALUADA') as evaluadas,
    COUNT(*) FILTER (WHERE estado = 'CERRADA_SIN_OFERTAS') as cerradas
FROM solicitudes;"

echo -e "\n4. Verificar últimas evaluaciones..."
docker exec teloo-postgres psql -U teloo_user -d teloo_db -c "
SELECT 
    id,
    fecha_evaluacion,
    total_repuestos_adjudicados,
    monto_total_adjudicado
FROM evaluaciones
ORDER BY created_at DESC
LIMIT 5;"

echo -e "\n5. Verificar logs recientes..."
docker logs teloo-core-api --tail 50 | grep -E "(Evaluación|evaluacion|EVALUA)"

echo -e "\n=== Verificación completada ==="
```

## Logs Importantes

### Logs Normales (Exitosos)

```
🔍 Verificando timeouts de escalamiento...
⚙️ Tiempos configurados por nivel: {1: 15, 2: 20, 3: 25, 4: 30, 5: 35}
📋 Encontradas 5 solicitudes abiertas con escalamiento
✅ Ofertas mínimas alcanzadas: 2 >= 2
✅ Evaluación automática exitosa: 3/4 adjudicados
📢 Evento de evaluación publicado para solicitud abc123
📊 Resumen: 0 escaladas, 1 cerradas
```

### Logs de Error (Requieren Atención)

```
❌ Error en evaluación automática: [error details]
❌ Error publicando evento de evaluación: [error details]
❌ Evaluación automática falló: [error message]
```

### Logs de Advertencia (Informativos)

```
⚠️ No hay asesores en Nivel 5
⚠️ Evaluación sin adjudicaciones, cerrando sin ofertas
❌ Sin ofertas en nivel máximo, cerrando solicitud
```

## Contacto y Soporte

Si el problema persiste después de seguir esta guía:

1. Recopilar logs completos: `docker logs teloo-core-api > logs.txt`
2. Exportar estado de solicitud problemática (SQL queries arriba)
3. Verificar configuración del sistema
4. Revisar el código en `services/core-api/jobs/scheduled_jobs.py`
