# Dashboard Embudo Operativo - Especificación Técnica

## Objetivo
Monitoreo del flujo operacional desde solicitud hasta aceptación

## KPIs Implementados (11)

### 1. Tasa de Entrada de Solicitudes
**Métrica:** Número de nuevas solicitudes creadas por hora, día y semana
**Query SQL:**
```sql
-- Por hora
SELECT 
    DATE_TRUNC('hour', created_at) as periodo,
    COUNT(*) as solicitudes
FROM solicitudes
WHERE created_at BETWEEN $1 AND $2
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY periodo;

-- Por día
SELECT 
    DATE(created_at) as periodo,
    COUNT(*) as solicitudes
FROM solicitudes
WHERE created_at BETWEEN $1 AND $2
GROUP BY DATE(created_at)
ORDER BY periodo;

-- Por semana
SELECT 
    DATE_TRUNC('week', created_at) as periodo,
    COUNT(*) as solicitudes
FROM solicitudes
WHERE created_at BETWEEN $1 AND $2
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY periodo;
```

### 2. Conversión ABIERTA → EN_EVALUACION
**Métrica:** % de solicitudes que reciben al menos una oferta
**Query SQL:**
```sql
SELECT 
    COUNT(DISTINCT s.id) as total_abiertas,
    COUNT(DISTINCT CASE WHEN o.id IS NOT NULL THEN s.id END) as con_ofertas,
    ROUND(
        CAST(COUNT(DISTINCT CASE WHEN o.id IS NOT NULL THEN s.id END) AS FLOAT) / 
        NULLIF(COUNT(DISTINCT s.id), 0) * 100, 
        2
    ) as tasa_conversion
FROM solicitudes s
LEFT JOIN ofertas o ON s.id = o.solicitud_id
WHERE s.created_at BETWEEN $1 AND $2
```

### 3. Conversión EN_EVALUACION → ADJUDICADA
**Métrica:** % de solicitudes con ofertas que resultan en ganador
**Query SQL:**
```sql
SELECT 
    COUNT(DISTINCT s.id) as total_en_evaluacion,
    COUNT(DISTINCT CASE WHEN s.estado = 'ADJUDICADA' THEN s.id END) as adjudicadas,
    ROUND(
        CAST(COUNT(DISTINCT CASE WHEN s.estado = 'ADJUDICADA' THEN s.id END) AS FLOAT) / 
        NULLIF(COUNT(DISTINCT s.id), 0) * 100, 
        2
    ) as tasa_conversion
FROM solicitudes s
WHERE EXISTS (SELECT 1 FROM ofertas o WHERE o.solicitud_id = s.id)
AND s.created_at BETWEEN $1 AND $2
```

### 4. Conversión ADJUDICADA → ACEPTADA
**Métrica:** % de ofertas ganadoras aceptadas por el cliente
**Query SQL:**
```sql
SELECT 
    COUNT(*) as total_adjudicadas,
    COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END) as aceptadas,
    ROUND(
        CAST(COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END) AS FLOAT) / 
        NULLIF(COUNT(*), 0) * 100, 
        2
    ) as tasa_conversion
FROM solicitudes
WHERE estado IN ('ADJUDICADA', 'ACEPTADA')
AND created_at BETWEEN $1 AND $2
```

### 5. Tasa de Conversión General
**Métrica:** (Solicitudes ACEPTADA / Total Solicitudes) × 100
**Query SQL:**
```sql
SELECT 
    COUNT(*) as total_solicitudes,
    COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END) as aceptadas,
    ROUND(
        CAST(COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END) AS FLOAT) / 
        NULLIF(COUNT(*), 0) * 100, 
        2
    ) as tasa_conversion_general
FROM solicitudes
WHERE created_at BETWEEN $1 AND $2
```

### 6. Tiempo hasta Primera Oferta (TTFO)
**Métrica:** Mediana del tiempo desde creación hasta primera oferta
**Query SQL:**
```sql
WITH tiempos AS (
    SELECT 
        s.id,
        EXTRACT(EPOCH FROM (MIN(o.created_at) - s.created_at))/3600 as horas_hasta_primera_oferta
    FROM solicitudes s
    JOIN ofertas o ON s.id = o.solicitud_id
    WHERE s.created_at BETWEEN $1 AND $2
    GROUP BY s.id, s.created_at
)
SELECT 
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY horas_hasta_primera_oferta) as mediana_horas,
    AVG(horas_hasta_primera_oferta) as promedio_horas,
    MIN(horas_hasta_primera_oferta) as min_horas,
    MAX(horas_hasta_primera_oferta) as max_horas
FROM tiempos
```

### 7. Tiempo hasta Adjudicación (TTA)
**Métrica:** Mediana del tiempo desde creación hasta ADJUDICADA
**Query SQL:**
```sql
WITH tiempos AS (
    SELECT 
        id,
        EXTRACT(EPOCH FROM (updated_at - created_at))/3600 as horas_hasta_adjudicacion
    FROM solicitudes
    WHERE estado = 'ADJUDICADA'
    AND created_at BETWEEN $1 AND $2
)
SELECT 
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY horas_hasta_adjudicacion) as mediana_horas,
    AVG(horas_hasta_adjudicacion) as promedio_horas,
    MIN(horas_hasta_adjudicacion) as min_horas,
    MAX(horas_hasta_adjudicacion) as max_horas
FROM tiempos
```

### 8. Tiempo hasta Decisión del Cliente (TTCD)
**Métrica:** Mediana del tiempo desde adjudicación hasta decisión
**Query SQL:**
```sql
-- Nota: Requiere timestamp de cuando se notifica al cliente
-- Por ahora usamos updated_at como proxy
WITH tiempos AS (
    SELECT 
        id,
        EXTRACT(EPOCH FROM (updated_at - created_at))/3600 as horas_decision
    FROM solicitudes
    WHERE estado IN ('ACEPTADA', 'RECHAZADA')
    AND created_at BETWEEN $1 AND $2
)
SELECT 
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY horas_decision) as mediana_horas,
    AVG(horas_decision) as promedio_horas
FROM tiempos
```

### 9. Tasa de Llenado de Solicitudes
**Métrica:** 100% - % CERRADA_SIN_OFERTAS
**Query SQL:**
```sql
SELECT 
    COUNT(*) as total_solicitudes,
    COUNT(CASE WHEN estado = 'CERRADA_SIN_OFERTAS' THEN 1 END) as sin_ofertas,
    ROUND(
        (1 - CAST(COUNT(CASE WHEN estado = 'CERRADA_SIN_OFERTAS' THEN 1 END) AS FLOAT) / 
        NULLIF(COUNT(*), 0)) * 100, 
        2
    ) as tasa_llenado
FROM solicitudes
WHERE created_at BETWEEN $1 AND $2
```

### 10. Tasa de Escalamiento
**Métrica:** % solicitudes que escalan más allá del Nivel 1
**Query SQL:**
```sql
-- Usando tabla evaluacion_asesores_temp
SELECT 
    COUNT(DISTINCT solicitud_id) as total_solicitudes,
    COUNT(DISTINCT CASE WHEN nivel_entrega > 1 THEN solicitud_id END) as escaladas,
    ROUND(
        CAST(COUNT(DISTINCT CASE WHEN nivel_entrega > 1 THEN solicitud_id END) AS FLOAT) / 
        NULLIF(COUNT(DISTINCT solicitud_id), 0) * 100, 
        2
    ) as tasa_escalamiento
FROM evaluacion_asesores_temp eat
JOIN solicitudes s ON eat.solicitud_id = s.id
WHERE s.created_at BETWEEN $1 AND $2
```

### 11. Tasa de Fallo por Nivel
**Métrica:** % solicitudes sin ofertas por nivel específico
**Query SQL:**
```sql
WITH solicitudes_por_nivel AS (
    SELECT 
        nivel_entrega,
        COUNT(DISTINCT solicitud_id) as total_asignadas,
        COUNT(DISTINCT CASE 
            WHEN NOT EXISTS (
                SELECT 1 FROM ofertas o 
                WHERE o.solicitud_id = eat.solicitud_id 
                AND o.asesor_id = eat.asesor_id
            ) THEN solicitud_id 
        END) as sin_ofertas
    FROM evaluacion_asesores_temp eat
    JOIN solicitudes s ON eat.solicitud_id = s.id
    WHERE s.created_at BETWEEN $1 AND $2
    GROUP BY nivel_entrega
)
SELECT 
    nivel_entrega,
    total_asignadas,
    sin_ofertas,
    ROUND(
        CAST(sin_ofertas AS FLOAT) / NULLIF(total_asignadas, 0) * 100, 
        2
    ) as tasa_fallo
FROM solicitudes_por_nivel
ORDER BY nivel_entrega
```

## Estructura de Respuesta

```json
{
  "dashboard": "embudo_operativo",
  "periodo": {
    "inicio": "2025-01-01T00:00:00Z",
    "fin": "2025-01-31T23:59:59Z"
  },
  "metricas": {
    "tasa_entrada": {
      "por_hora": [...],
      "por_dia": [...],
      "por_semana": [...]
    },
    "conversiones": {
      "abierta_a_evaluacion": 75.5,
      "evaluacion_a_adjudicada": 45.2,
      "adjudicada_a_aceptada": 85.0,
      "conversion_general": 28.9
    },
    "tiempos": {
      "ttfo_mediana_horas": 2.5,
      "ttfo_promedio_horas": 3.2,
      "tta_mediana_horas": 24.0,
      "tta_promedio_horas": 28.5,
      "ttcd_mediana_horas": 4.0,
      "ttcd_promedio_horas": 6.5
    },
    "fallos": {
      "tasa_llenado": 92.5,
      "tasa_escalamiento": 35.0,
      "fallo_por_nivel": {
        "1": 15.0,
        "2": 25.0,
        "3": 35.0,
        "4": 45.0,
        "5": 55.0
      }
    }
  },
  "generado_en": "2025-01-31T10:00:00Z"
}
```

## Notas de Implementación

1. **Cache:** TTL de 15 minutos para métricas del embudo
2. **Performance:** Usar índices en `created_at`, `estado`, `solicitud_id`
3. **Validación:** Verificar que fechas sean válidas y período no exceda 90 días
4. **Fallback:** Retornar 0s en caso de error, no fallar el endpoint
