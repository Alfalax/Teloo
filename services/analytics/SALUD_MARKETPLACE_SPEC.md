# Dashboard Salud del Marketplace - Especificación Técnica

## Objetivo
Medir el equilibrio, la liquidez y la competitividad del ecosistema de TeLo

## KPIs Implementados (5)

### 1. Ratio Oferta/Demanda
**Métrica:** (Número de Asesores Activos / Número de Solicitudes Diarias)
**Query SQL:**
```sql
WITH asesores_activos AS (
    SELECT COUNT(DISTINCT a.id) as total_asesores
    FROM asesores a
    JOIN usuarios u ON a.usuario_id = u.id
    WHERE u.estado = 'ACTIVO' 
    AND a.estado = 'ACTIVO'
),
solicitudes_diarias AS (
    SELECT COUNT(*) / NULLIF(DATE_PART('day', $2::timestamp - $1::timestamp), 0) as promedio_diario
    FROM solicitudes
    WHERE created_at BETWEEN $1 AND $2
)
SELECT 
    aa.total_asesores,
    sd.promedio_diario,
    CASE 
        WHEN sd.promedio_diario > 0 THEN 
            ROUND(CAST(aa.total_asesores AS FLOAT) / sd.promedio_diario, 2)
        ELSE 0 
    END as ratio
FROM asesores_activos aa, solicitudes_diarias sd
```

### 2. Densidad de Ofertas
**Métrica:** Número promedio de ofertas por solicitud que fue llenada
**Query SQL:**
```sql
WITH solicitudes_con_ofertas AS (
    SELECT 
        s.id,
        COUNT(o.id) as num_ofertas
    FROM solicitudes s
    JOIN ofertas o ON s.id = o.solicitud_id
    WHERE s.created_at BETWEEN $1 AND $2
    GROUP BY s.id
)
SELECT 
    COUNT(*) as solicitudes_llenadas,
    SUM(num_ofertas) as total_ofertas,
    ROUND(AVG(num_ofertas), 2) as densidad_promedio,
    MIN(num_ofertas) as min_ofertas,
    MAX(num_ofertas) as max_ofertas
FROM solicitudes_con_ofertas
```

### 3. Tasa de Participación de Asesores
**Métrica:** % de asesores habilitados que enviaron al menos una oferta en el período
**Query SQL:**
```sql
WITH asesores_habilitados AS (
    SELECT COUNT(DISTINCT a.id) as total
    FROM asesores a
    JOIN usuarios u ON a.usuario_id = u.id
    WHERE u.estado = 'ACTIVO' 
    AND a.estado = 'ACTIVO'
),
asesores_con_ofertas AS (
    SELECT COUNT(DISTINCT o.asesor_id) as total
    FROM ofertas o
    WHERE o.created_at BETWEEN $1 AND $2
)
SELECT 
    ah.total as total_habilitados,
    aco.total as total_participantes,
    CASE 
        WHEN ah.total > 0 THEN 
            ROUND(CAST(aco.total AS FLOAT) / ah.total * 100, 2)
        ELSE 0 
    END as tasa_participacion
FROM asesores_habilitados ah, asesores_con_ofertas aco
```

### 4. Tasa de Adjudicación del Asesor Promedio
**Métrica:** Para un asesor típico, % de ofertas que resultan ADJUDICADA
**Query SQL:**
```sql
WITH ofertas_por_asesor AS (
    SELECT 
        o.asesor_id,
        COUNT(*) as total_ofertas,
        COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras
    FROM ofertas o
    WHERE o.created_at BETWEEN $1 AND $2
    GROUP BY o.asesor_id
),
tasas_individuales AS (
    SELECT 
        CASE 
            WHEN total_ofertas > 0 THEN 
                CAST(ofertas_ganadoras AS FLOAT) / total_ofertas * 100
            ELSE 0 
        END as tasa_individual
    FROM ofertas_por_asesor
)
SELECT 
    COUNT(*) as asesores_con_ofertas,
    ROUND(AVG(tasa_individual), 2) as tasa_adjudicacion_promedio,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tasa_individual), 2) as mediana,
    ROUND(MIN(tasa_individual), 2) as min_tasa,
    ROUND(MAX(tasa_individual), 2) as max_tasa
FROM tasas_individuales
```

### 5. Tasa de Aceptación del Cliente
**Métrica:** Del total de ofertas ADJUDICADA, % que son ACEPTADA por el cliente
**Query SQL:**
```sql
WITH ofertas_adjudicadas AS (
    SELECT 
        COUNT(*) as total_adjudicadas,
        COUNT(CASE WHEN s.estado = 'ACEPTADA' THEN 1 END) as aceptadas
    FROM ofertas o
    JOIN solicitudes s ON o.solicitud_id = s.id
    WHERE o.estado = 'GANADORA'
    AND o.created_at BETWEEN $1 AND $2
)
SELECT 
    total_adjudicadas,
    aceptadas,
    CASE 
        WHEN total_adjudicadas > 0 THEN 
            ROUND(CAST(aceptadas AS FLOAT) / total_adjudicadas * 100, 2)
        ELSE 0 
    END as tasa_aceptacion
FROM ofertas_adjudicadas
```

## Estructura de Respuesta

```json
{
  "dashboard": "salud_marketplace",
  "periodo": {
    "inicio": "2025-01-01T00:00:00Z",
    "fin": "2025-01-31T23:59:59Z"
  },
  "metricas": {
    "ratio_oferta_demanda": {
      "asesores_activos": 245,
      "solicitudes_diarias_promedio": 12.5,
      "ratio": 19.6
    },
    "densidad_ofertas": {
      "solicitudes_llenadas": 350,
      "total_ofertas": 1250,
      "densidad_promedio": 3.57,
      "min_ofertas": 1,
      "max_ofertas": 12
    },
    "tasa_participacion_asesores": {
      "total_habilitados": 245,
      "total_participantes": 189,
      "tasa_participacion": 77.14
    },
    "tasa_adjudicacion_promedio": {
      "asesores_con_ofertas": 189,
      "tasa_promedio": 28.5,
      "mediana": 25.0,
      "min_tasa": 0.0,
      "max_tasa": 85.0
    },
    "tasa_aceptacion_cliente": {
      "total_adjudicadas": 120,
      "aceptadas": 102,
      "tasa_aceptacion": 85.0
    }
  },
  "generado_en": "2025-01-31T10:00:00Z"
}
```

## Insights de Negocio

### Ratio Oferta/Demanda
- **Óptimo:** 15-25 asesores por solicitud diaria
- **Bajo (<10):** Riesgo de saturación, poca competencia
- **Alto (>30):** Exceso de oferta, baja utilización de asesores

### Densidad de Ofertas
- **Óptimo:** 3-5 ofertas por solicitud
- **Bajo (<2):** Poca competencia, riesgo de precios altos
- **Alto (>7):** Buena competencia pero puede indicar sobre-notificación

### Tasa de Participación
- **Óptimo:** >70%
- **Medio (50-70%):** Revisar estrategias de engagement
- **Bajo (<50%):** Problema crítico de activación

### Tasa de Adjudicación Promedio
- **Óptimo:** 20-35%
- **Bajo (<15%):** Asesores desmotivados, alta competencia
- **Alto (>40%):** Poca competencia o asignación muy selectiva

### Tasa de Aceptación Cliente
- **Óptimo:** >80%
- **Medio (60-80%):** Revisar algoritmo de evaluación
- **Bajo (<60%):** Desalineación entre algoritmo y preferencias del cliente

## Notas de Implementación

1. **Cache:** TTL de 10 minutos para métricas de salud
2. **Performance:** Queries optimizadas con CTEs
3. **Período recomendado:** Últimos 7 días para métricas de salud
4. **Alertas:** Configurar alertas si ratio < 10 o tasa participación < 50%
