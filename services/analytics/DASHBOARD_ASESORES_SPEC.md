# Dashboard Análisis de Asesores - Especificación Técnica

## Objetivo
Análisis detallado del desempeño y comportamiento de los asesores en la plataforma

## KPIs Implementados (13)

### 1. Total de Asesores Activos
**Métrica:** Número de asesores que enviaron al menos una oferta en el período
**Query SQL:**
```sql
SELECT COUNT(DISTINCT asesor_id) as total_asesores_activos
FROM ofertas
WHERE created_at BETWEEN $1 AND $2
```

### 2. Tasa de Respuesta Promedio
**Métrica:** % de solicitudes a las que respondieron vs solicitudes asignadas
**Query SQL:**
```sql
WITH asignaciones AS (
    SELECT 
        asesor_id,
        COUNT(DISTINCT solicitud_id) as solicitudes_asignadas
    FROM solicitudes_asesores
    WHERE created_at BETWEEN $1 AND $2
    GROUP BY asesor_id
),
respuestas AS (
    SELECT 
        asesor_id,
        COUNT(DISTINCT solicitud_id) as solicitudes_respondidas
    FROM ofertas
    WHERE created_at BETWEEN $1 AND $2
    GROUP BY asesor_id
)
SELECT 
    COUNT(DISTINCT a.asesor_id) as total_asesores,
    AVG(CASE 
        WHEN a.solicitudes_asignadas > 0 THEN 
            (COALESCE(r.solicitudes_respondidas, 0)::FLOAT / a.solicitudes_asignadas * 100)
        ELSE 0 
    END) as tasa_respuesta_promedio
FROM asignaciones a
LEFT JOIN respuestas r ON a.asesor_id = r.asesor_id
```

### 3. Tiempo de Respuesta Promedio (TTFO por Asesor)
**Métrica:** Tiempo promedio desde asignación hasta primera oferta
**Query SQL:**
```sql
WITH tiempos_respuesta AS (
    SELECT 
        o.asesor_id,
        EXTRACT(EPOCH FROM (o.created_at - sa.created_at)) / 60 as minutos
    FROM ofertas o
    JOIN solicitudes_asesores sa ON o.solicitud_id = sa.solicitud_id 
        AND o.asesor_id = sa.asesor_id
    WHERE o.created_at BETWEEN $1 AND $2
    AND sa.created_at < o.created_at
)
SELECT 
    COUNT(DISTINCT asesor_id) as asesores_con_respuestas,
    ROUND(AVG(minutos), 2) as tiempo_promedio_minutos,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY minutos), 2) as mediana_minutos,
    ROUND(MIN(minutos), 2) as min_minutos,
    ROUND(MAX(minutos), 2) as max_minutos
FROM tiempos_respuesta
```

### 4. Ofertas por Asesor (Promedio)
**Métrica:** Número promedio de ofertas enviadas por asesor activo
**Query SQL:**
```sql
WITH ofertas_por_asesor AS (
    SELECT 
        asesor_id,
        COUNT(*) as total_ofertas
    FROM ofertas
    WHERE created_at BETWEEN $1 AND $2
    GROUP BY asesor_id
)
SELECT 
    COUNT(*) as total_asesores,
    ROUND(AVG(total_ofertas), 2) as ofertas_promedio,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_ofertas), 2) as mediana,
    MIN(total_ofertas) as min_ofertas,
    MAX(total_ofertas) as max_ofertas
FROM ofertas_por_asesor
```

### 5. Tasa de Adjudicación por Asesor
**Métrica:** % de ofertas que resultaron ganadoras por asesor
**Query SQL:**
```sql
WITH estadisticas_asesor AS (
    SELECT 
        asesor_id,
        COUNT(*) as total_ofertas,
        COUNT(CASE WHEN estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                ROUND(COUNT(CASE WHEN estado = 'GANADORA' THEN 1 END)::FLOAT / COUNT(*) * 100, 2)
            ELSE 0 
        END as tasa_adjudicacion
    FROM ofertas
    WHERE created_at BETWEEN $1 AND $2
    GROUP BY asesor_id
)
SELECT 
    COUNT(*) as total_asesores,
    ROUND(AVG(tasa_adjudicacion), 2) as tasa_promedio,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tasa_adjudicacion), 2) as mediana,
    ROUND(MIN(tasa_adjudicacion), 2) as min_tasa,
    ROUND(MAX(tasa_adjudicacion), 2) as max_tasa
FROM estadisticas_asesor
```

### 6. Ranking Top 10 Asesores
**Métrica:** Top 10 asesores por número de ofertas ganadoras
**Query SQL:**
```sql
SELECT 
    a.id,
    a.nombre_comercial,
    a.ciudad,
    COUNT(o.id) as ofertas_ganadoras,
    ROUND(AVG(ev.puntaje_total), 2) as puntaje_promedio,
    ROUND(COUNT(o.id)::FLOAT / (
        SELECT COUNT(*) FROM ofertas o2 
        WHERE o2.asesor_id = a.id 
        AND o2.created_at BETWEEN $1 AND $2
    ) * 100, 2) as tasa_adjudicacion
FROM asesores a
JOIN ofertas o ON a.id = o.asesor_id
LEFT JOIN evaluaciones ev ON o.id = ev.oferta_id
WHERE o.estado = 'GANADORA'
AND o.created_at BETWEEN $1 AND $2
GROUP BY a.id, a.nombre_comercial, a.ciudad
ORDER BY ofertas_ganadoras DESC, puntaje_promedio DESC
LIMIT 10
```

### 7. Especialización por Tipo de Repuesto
**Métrica:** Distribución de ofertas por categoría de repuesto
**Query SQL:**
```sql
SELECT 
    rs.categoria,
    COUNT(DISTINCT o.asesor_id) as asesores_participantes,
    COUNT(o.id) as total_ofertas,
    COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras,
    ROUND(COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END)::FLOAT / COUNT(o.id) * 100, 2) as tasa_exito
FROM ofertas o
JOIN ofertas_detalle od ON o.id = od.oferta_id
JOIN repuestos_solicitud rs ON od.repuesto_solicitud_id = rs.id
WHERE o.created_at BETWEEN $1 AND $2
GROUP BY rs.categoria
ORDER BY total_ofertas DESC
```

### 8. Distribución Geográfica
**Métrica:** Asesores activos por ciudad
**Query SQL:**
```sql
SELECT 
    a.ciudad,
    COUNT(DISTINCT a.id) as asesores_activos,
    COUNT(o.id) as total_ofertas,
    COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras,
    ROUND(AVG(CASE 
        WHEN o.estado = 'GANADORA' THEN 1.0 
        ELSE 0.0 
    END) * 100, 2) as tasa_adjudicacion
FROM asesores a
JOIN ofertas o ON a.id = o.asesor_id
WHERE o.created_at BETWEEN $1 AND $2
GROUP BY a.ciudad
ORDER BY asesores_activos DESC
LIMIT 20
```

### 9. Nivel de Confianza Promedio
**Métrica:** Puntaje promedio de confianza de asesores activos
**Query SQL:**
```sql
SELECT 
    COUNT(DISTINCT a.id) as total_asesores,
    ROUND(AVG(a.nivel_confianza), 2) as nivel_promedio,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY a.nivel_confianza), 2) as mediana,
    ROUND(MIN(a.nivel_confianza), 2) as min_nivel,
    ROUND(MAX(a.nivel_confianza), 2) as max_nivel
FROM asesores a
WHERE a.id IN (
    SELECT DISTINCT asesor_id 
    FROM ofertas 
    WHERE created_at BETWEEN $1 AND $2
)
```

### 10. Asesores Nuevos
**Métrica:** Asesores que se registraron en el período
**Query SQL:**
```sql
SELECT 
    COUNT(*) as asesores_nuevos,
    COUNT(CASE WHEN estado = 'ACTIVO' THEN 1 END) as activos,
    COUNT(CASE WHEN id IN (
        SELECT DISTINCT asesor_id FROM ofertas 
        WHERE created_at BETWEEN $1 AND $2
    ) THEN 1 END) as con_ofertas
FROM asesores
WHERE created_at BETWEEN $1 AND $2
```

### 11. Tasa de Retención
**Métrica:** % de asesores del período anterior que siguen activos
**Query SQL:**
```sql
WITH periodo_anterior AS (
    SELECT DISTINCT asesor_id
    FROM ofertas
    WHERE created_at BETWEEN $1 - INTERVAL '30 days' AND $1
),
periodo_actual AS (
    SELECT DISTINCT asesor_id
    FROM ofertas
    WHERE created_at BETWEEN $1 AND $2
)
SELECT 
    (SELECT COUNT(*) FROM periodo_anterior) as asesores_periodo_anterior,
    (SELECT COUNT(*) FROM periodo_actual WHERE asesor_id IN (SELECT asesor_id FROM periodo_anterior)) as asesores_retenidos,
    ROUND(
        (SELECT COUNT(*) FROM periodo_actual WHERE asesor_id IN (SELECT asesor_id FROM periodo_anterior))::FLOAT / 
        NULLIF((SELECT COUNT(*) FROM periodo_anterior), 0) * 100, 
        2
    ) as tasa_retencion
```

### 12. Satisfacción del Cliente (por Asesor)
**Métrica:** Calificación promedio de clientes a ofertas ganadoras
**Query SQL:**
```sql
SELECT 
    COUNT(DISTINCT o.asesor_id) as asesores_calificados,
    ROUND(AVG(s.calificacion_asesor), 2) as calificacion_promedio,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.calificacion_asesor), 2) as mediana,
    ROUND(MIN(s.calificacion_asesor), 2) as min_calificacion,
    ROUND(MAX(s.calificacion_asesor), 2) as max_calificacion
FROM ofertas o
JOIN solicitudes s ON o.solicitud_id = s.id
WHERE o.estado = 'GANADORA'
AND s.calificacion_asesor IS NOT NULL
AND o.created_at BETWEEN $1 AND $2
```

### 13. Valor Promedio de Oferta por Asesor
**Métrica:** Ticket promedio de ofertas por asesor
**Query SQL:**
```sql
WITH valores_por_asesor AS (
    SELECT 
        o.asesor_id,
        SUM(od.precio_unitario * rs.cantidad) as valor_oferta
    FROM ofertas o
    JOIN ofertas_detalle od ON o.id = od.oferta_id
    JOIN repuestos_solicitud rs ON od.repuesto_solicitud_id = rs.id
    WHERE o.created_at BETWEEN $1 AND $2
    GROUP BY o.asesor_id, o.id
)
SELECT 
    COUNT(DISTINCT asesor_id) as total_asesores,
    ROUND(AVG(valor_oferta), 0) as valor_promedio,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY valor_oferta), 0) as mediana,
    ROUND(MIN(valor_oferta), 0) as min_valor,
    ROUND(MAX(valor_oferta), 0) as max_valor
FROM valores_por_asesor
```

## Estructura de Respuesta

```json
{
  "dashboard": "asesores",
  "periodo": {
    "inicio": "2025-01-01T00:00:00Z",
    "fin": "2025-01-31T23:59:59Z"
  },
  "filtros": {
    "ciudad": null
  },
  "metricas": {
    "total_asesores_activos": 245,
    "tasa_respuesta_promedio": {
      "total_asesores": 245,
      "tasa_promedio": 78.5
    },
    "tiempo_respuesta_promedio": {
      "asesores_con_respuestas": 240,
      "tiempo_promedio_minutos": 25.3,
      "mediana_minutos": 18.5,
      "min_minutos": 2.0,
      "max_minutos": 180.0
    },
    "ofertas_por_asesor": {
      "total_asesores": 245,
      "ofertas_promedio": 12.8,
      "mediana": 10.0,
      "min_ofertas": 1,
      "max_ofertas": 85
    },
    "tasa_adjudicacion_por_asesor": {
      "total_asesores": 245,
      "tasa_promedio": 34.2,
      "mediana": 32.0,
      "min_tasa": 0.0,
      "max_tasa": 85.0
    },
    "ranking_top_10": [
      {
        "id": 123,
        "nombre_comercial": "Repuestos Premium",
        "ciudad": "BOGOTA",
        "ofertas_ganadoras": 45,
        "puntaje_promedio": 4.8,
        "tasa_adjudicacion": 52.3
      }
    ],
    "especializacion_repuestos": [
      {
        "categoria": "Motor",
        "asesores_participantes": 180,
        "total_ofertas": 850,
        "ofertas_ganadoras": 280,
        "tasa_exito": 32.9
      }
    ],
    "distribucion_geografica": [
      {
        "ciudad": "BOGOTA",
        "asesores_activos": 95,
        "total_ofertas": 1250,
        "ofertas_ganadoras": 420,
        "tasa_adjudicacion": 33.6
      }
    ],
    "nivel_confianza_promedio": {
      "total_asesores": 245,
      "nivel_promedio": 4.2,
      "mediana": 4.3,
      "min_nivel": 2.5,
      "max_nivel": 5.0
    },
    "asesores_nuevos": {
      "asesores_nuevos": 28,
      "activos": 25,
      "con_ofertas": 18
    },
    "tasa_retencion": {
      "asesores_periodo_anterior": 230,
      "asesores_retenidos": 212,
      "tasa_retencion": 92.1
    },
    "satisfaccion_cliente": {
      "asesores_calificados": 180,
      "calificacion_promedio": 4.3,
      "mediana": 4.5,
      "min_calificacion": 2.0,
      "max_calificacion": 5.0
    },
    "valor_promedio_oferta": {
      "total_asesores": 245,
      "valor_promedio": 850000,
      "mediana": 750000,
      "min_valor": 50000,
      "max_valor": 5000000
    }
  },
  "generado_en": "2025-01-31T10:00:00Z"
}
```

## Insights de Negocio

### Tasa de Respuesta
- **Óptimo:** >75%
- **Preocupante:** <60%
- **Acción:** Identificar asesores con baja respuesta para capacitación

### Tiempo de Respuesta
- **Óptimo:** <30 minutos
- **Aceptable:** 30-60 minutos
- **Lento:** >60 minutos

### Tasa de Adjudicación
- **Excelente:** >40%
- **Bueno:** 25-40%
- **Bajo:** <25%

### Retención
- **Saludable:** >85%
- **Preocupante:** <75%
- **Crítico:** <60%

## Filtros Disponibles

1. **ciudad:** Filtrar por ciudad específica
2. **categoria_repuesto:** Filtrar por especialización
3. **nivel_confianza_min:** Filtrar por nivel mínimo de confianza

## Notas de Implementación

1. **Performance:** Queries complejas con múltiples JOINs - usar índices
2. **Cache:** TTL de 15 minutos (datos de asesores cambian frecuentemente)
3. **Paginación:** Ranking y distribuciones limitadas a top 10-20
4. **Privacidad:** No exponer datos sensibles de asesores individuales
5. **Validación:** Verificar que asesor_id existe en todas las queries
