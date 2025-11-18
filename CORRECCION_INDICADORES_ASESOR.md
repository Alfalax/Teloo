# Corrección de Indicadores del Dashboard del Asesor

## 📊 Indicadores a Corregir

### 1. Ofertas Asignadas → **Repuestos Asignados**
**ANTES:**
- Contaba número de ofertas enviadas por el asesor
- No consideraba período de tiempo

**DESPUÉS:**
- Cuenta la cantidad total de **repuestos** en TODAS las solicitudes que le han sido **asignadas**
- Solo del **mes actual**
- Fuente: `repuestos_solicitados` de solicitudes en `evaluaciones_asesores_temp`
- **NO importa si ganó o no**, cuenta todos los repuestos de solicitudes asignadas

**Query:**
```sql
SELECT SUM(rs.cantidad)
FROM solicitudes s
JOIN evaluaciones_asesores_temp e ON e.solicitud_id = s.id
JOIN repuestos_solicitados rs ON rs.solicitud_id = s.id
WHERE e.asesor_id = :asesor_id
  AND s.created_at >= :inicio_mes
```

---

### 2. Monto Total Ganado
**ANTES:**
- Sumaba montos de ofertas ACEPTADAS
- No consideraba período de tiempo

**DESPUÉS:**
- Suma total de los montos que los **clientes han aceptado**
- Solo ofertas **ganadoras** que el asesor ganó
- Solo del **mes actual**
- Fuente: `adjudicaciones_repuesto` con estado ACEPTADA

**Query:**
```sql
SELECT SUM(ar.precio_adjudicado * ar.cantidad_adjudicada)
FROM adjudicaciones_repuesto ar
JOIN ofertas o ON ar.oferta_id = o.id
WHERE o.asesor_id = :asesor_id
  AND o.estado = 'ACEPTADA'
  AND EXTRACT(MONTH FROM ar.created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
  AND EXTRACT(YEAR FROM ar.created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
```

---

### 3. Solicitudes Abiertas → **Pendientes por Oferta**
**ANTES:**
- Contaba solicitudes ABIERTAS asignadas al asesor
- No consideraba si ya había ofertado

**DESPUÉS:**
- Cuenta solicitudes **pendientes por ofertar** que le fueron asignadas
- Solo del **mes actual**
- Criterio: Solicitudes ABIERTAS donde:
  - El asesor está en `evaluaciones_asesores_temp`
  - El asesor NO tiene oferta enviada aún
  - `solicitud.nivel_actual >= evaluacion.nivel_entrega`

**Query:**
```sql
SELECT COUNT(DISTINCT s.id)
FROM solicitudes s
JOIN evaluaciones_asesores_temp e ON e.solicitud_id = s.id
WHERE e.asesor_id = :asesor_id
  AND s.estado = 'ABIERTA'
  AND s.nivel_actual >= e.nivel_entrega
  AND NOT EXISTS (
    SELECT 1 FROM ofertas o 
    WHERE o.solicitud_id = s.id 
    AND o.asesor_id = :asesor_id
  )
  AND EXTRACT(MONTH FROM s.created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
  AND EXTRACT(YEAR FROM s.created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
```

---

### 4. Tasa de Conversión
**ANTES:**
- Porcentaje de ofertas ganadoras vs ofertas enviadas (cantidad)

**DESPUÉS:**
- Relación en porcentaje entre:
  - **Numerador:** Suma del monto total de lo que el cliente aceptó
  - **Denominador:** Suma del monto total de todo lo que ofertamos
- Solo del **mes actual**
- Fórmula: `(monto_aceptado / monto_ofertado) * 100`

**Query:**
```sql
-- Monto ofertado (todas las ofertas del mes)
SELECT SUM(o.monto_total) as monto_ofertado
FROM ofertas o
WHERE o.asesor_id = :asesor_id
  AND EXTRACT(MONTH FROM o.created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
  AND EXTRACT(YEAR FROM o.created_at) = EXTRACT(YEAR FROM CURRENT_DATE)

-- Monto aceptado (ofertas ACEPTADAS del mes)
SELECT SUM(o.monto_total) as monto_aceptado
FROM ofertas o
WHERE o.asesor_id = :asesor_id
  AND o.estado = 'ACEPTADA'
  AND EXTRACT(MONTH FROM o.created_at) = EXTRACT(MONTH FROM CURRENT_DATE)
  AND EXTRACT(YEAR FROM o.created_at) = EXTRACT(YEAR FROM CURRENT_DATE)

-- Tasa de conversión
tasa_conversion = (monto_aceptado / monto_ofertado) * 100
```

---

## 🔄 Cambios en el Frontend

### Tipos (frontend/advisor/src/types/kpi.ts)
```typescript
export interface AsesorKPIs {
  repuestos_adjudicados: number;  // Antes: ofertas_asignadas
  monto_total_ganado: number;
  pendientes_por_oferta: number;  // Antes: solicitudes_abiertas
  tasa_conversion: number;
}
```

### Labels en KPIDashboard
- "Ofertas Asignadas" → "Repuestos Adjudicados"
- "Solicitudes Abiertas" → "Pendientes por Oferta"

---

## 📝 Archivos a Modificar

1. **Backend:**
   - `services/core-api/routers/solicitudes.py` - Endpoint `/metrics`

2. **Frontend:**
   - `frontend/advisor/src/types/kpi.ts` - Tipos
   - `frontend/advisor/src/components/dashboard/KPIDashboard.tsx` - Labels
   - `frontend/advisor/src/pages/DashboardPage.tsx` - Estado inicial

---

## ✅ Validación

Después de los cambios, verificar:
1. Los indicadores muestran valores del mes actual
2. "Repuestos Adjudicados" cuenta repuestos, no ofertas
3. "Pendientes por Oferta" excluye solicitudes ya ofertadas
4. "Tasa de Conversión" usa montos, no cantidades
5. Todos los indicadores se actualizan correctamente
