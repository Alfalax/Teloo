# Análisis de KPIs: Impacto de Adjudicaciones Mixtas

## 🎯 RESUMEN EJECUTIVO

Con la implementación de **adjudicaciones mixtas** (un asesor puede ganar algunos repuestos de una solicitud, pero no todos), los KPIs actuales que están basados en **solicitudes completas** deben cambiar a **repuestos individuales**.

### Cambio de Paradigma

**❌ ANTES (Incorrecto):**
- Tasa de conversión = Solicitudes ganadas / Solicitudes ofertadas
- Ejemplo: Laura ofertó en 1 solicitud y "ganó" 1 → 100% conversión

**✅ AHORA (Correcto):**
- Tasa de conversión = Repuestos ganados / Repuestos ofertados  
- Ejemplo: Laura ofertó 3 repuestos y ganó 2 → 66.67% conversión

---

## 📊 ANÁLISIS DETALLADO POR COMPONENTE

### 1. DASHBOARD DEL ASESOR (Frontend)
**Archivo:** `frontend/advisor/src/pages/DashboardPage.tsx`

#### KPIs Actuales (INCORRECTOS):
```typescript
interface AsesorKPIs {
  ofertas_asignadas: number;        // ❌ Cuenta solicitudes
  monto_total_ganado: number;       // ✅ OK (ya suma repuestos)
  solicitudes_abiertas: number;     // ⚠️  Ambiguo
  tasa_conversion: number;          // ❌ Basada en solicitudes
}
```

#### KPIs Corregidos (CORRECTOS):
```typescript
interface AsesorKPIs {
  repuestos_ofertados: number;           // ✅ Total de repuestos en ofertas
  repuestos_ganados: number;             // ✅ Repuestos con estado GANADORA
  monto_total_ganado: number;            // ✅ OK (suma de repuestos ganados)
  solicitudes_con_ofertas: number;       // ✅ Solicitudes donde participó
  tasa_conversion_repuestos: number;     // ✅ (repuestos_ganados / repuestos_ofertados) * 100
  tasa_conversion_monto: number;         // ✅ (monto_ganado / monto_ofertado) * 100
  cobertura_promedio: number;            // ✅ % promedio de cobertura en ofertas
}
```

#### Cambios Necesarios:
1. **Tarjeta "Ofertas Asignadas"** → **"Repuestos Ofertados"**
   - Descripción: "Total de repuestos en tus ofertas"
   
2. **Nueva Tarjeta "Repuestos Ganados"**
   - Valor: Número de repuestos con estado GANADORA
   - Descripción: "Repuestos adjudicados a ti"

3. **Tarjeta "Tasa de Conversión"**
   - Fórmula actual: `solicitudes_ganadas / solicitudes_ofertadas`
   - Fórmula correcta: `repuestos_ganados / repuestos_ofertados`

4. **Nueva Tarjeta "Efectividad en Monto"**
   - Fórmula: `monto_ganado / monto_ofertado * 100`
   - Descripción: "% del valor ofertado que ganaste"

---

### 2. TARJETAS DE SOLICITUDES (Frontend)

#### A. SolicitudesGanadas.tsx
**Archivo:** `frontend/advisor/src/components/solicitudes/SolicitudesGanadas.tsx`

**Problemas Actuales:**
- Muestra solicitud como "ganada" si tiene al menos 1 repuesto ganador
- No indica cuántos repuestos ganó de cuántos ofertó
- El total de la oferta incluye todos los repuestos, no solo los ganados

**Cambios Necesarios:**
```typescript
// Agregar indicador de adjudicación parcial
{oferta && (
  <div className="pt-2 border-t space-y-2">
    <div className="flex justify-between items-center">
      <span className="text-sm font-medium">Repuestos ganados:</span>
      <span className="text-lg font-bold text-primary">
        {oferta.detalles.filter(d => d.estado === 'GANADORA').length} / {oferta.detalles.length}
      </span>
    </div>
    
    {/* Mostrar solo el monto de repuestos ganados */}
    <div className="flex justify-between items-center">
      <span className="text-sm font-medium">Monto ganado:</span>
      <span className="text-lg font-bold text-primary">
        {formatCurrency(
          oferta.detalles
            .filter(d => d.estado === 'GANADORA')
            .reduce((sum, d) => sum + d.precio_unitario * d.cantidad, 0)
        )}
      </span>
    </div>
    
    {/* Badge de adjudicación */}
    {oferta.detalles.filter(d => d.estado === 'GANADORA').length < oferta.detalles.length && (
      <Badge variant="warning">Adjudicación Parcial</Badge>
    )}
  </div>
)}
```

#### B. SolicitudesCerradas.tsx
**Archivo:** `frontend/advisor/src/components/solicitudes/SolicitudesCerradas.tsx`

**Cambios Necesarios:**
- Mostrar cuántos repuestos ofertó vs cuántos ganó otro asesor
- Indicar si perdió todos o solo algunos repuestos

```typescript
{solicitud.mi_oferta && (
  <div className="pt-2 border-t">
    <p className="text-sm font-medium mb-1">Tu oferta:</p>
    <div className="text-sm text-muted-foreground space-y-1">
      <div>Repuestos ofertados: {solicitud.mi_oferta.detalles.length}</div>
      <div>Repuestos ganados: {solicitud.mi_oferta.detalles.filter(d => d.estado === 'GANADORA').length}</div>
      <div>Monto ofertado: {formatCurrency(totalOferta)}</div>
      {solicitud.mi_oferta.detalles.some(d => d.estado === 'GANADORA') && (
        <Badge variant="success">Ganaste algunos repuestos</Badge>
      )}
    </div>
  </div>
)}
```

---

### 3. ANALYTICS SERVICE (Backend)

#### A. Dashboard Principal
**Archivo:** `services/analytics/app/routers/dashboards.py`

**KPIs Afectados:**

1. **`ofertas_totales_asignadas`** → **`repuestos_ofertados_totales`**
   ```python
   # Query actual (INCORRECTA)
   SELECT COUNT(*) as total FROM ofertas WHERE created_at BETWEEN $1 AND $2
   
   # Query correcta
   SELECT COUNT(*) as total 
   FROM oferta_detalles od
   JOIN ofertas o ON od.oferta_id = o.id
   WHERE o.created_at BETWEEN $1 AND $2
   ```

2. **`tasa_conversion`** → **`tasa_conversion_repuestos`**
   ```python
   # Query actual (INCORRECTA)
   SELECT 
       COUNT(*) as total_solicitudes,
       COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END) as aceptadas,
       (COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END)::float / COUNT(*)) * 100 as tasa
   FROM solicitudes
   
   # Query correcta
   SELECT 
       COUNT(*) as total_repuestos,
       COUNT(CASE WHEN od.estado = 'GANADORA' THEN 1 END) as ganados,
       (COUNT(CASE WHEN od.estado = 'GANADORA' THEN 1 END)::float / COUNT(*)) * 100 as tasa
   FROM oferta_detalles od
   JOIN ofertas o ON od.oferta_id = o.id
   WHERE o.created_at BETWEEN $1 AND $2
   ```

#### B. Metrics Calculator
**Archivo:** `services/analytics/app/services/metrics_calculator.py`

**Métodos a Modificar:**

1. **`_calcular_tasa_conversion()`**
   - Cambiar de solicitudes a repuestos
   - Considerar `oferta_detalles.estado = 'GANADORA'`

2. **`_calcular_ofertas_totales()`** → **`_calcular_repuestos_ofertados()`**
   ```python
   async def _calcular_repuestos_ofertados(self, fecha_inicio, fecha_fin):
       query = """
       SELECT 
           COUNT(*) as total_repuestos,
           COUNT(DISTINCT o.solicitud_id) as solicitudes_participadas,
           COUNT(DISTINCT o.asesor_id) as asesores_participantes
       FROM oferta_detalles od
       JOIN ofertas o ON od.oferta_id = o.id
       WHERE o.created_at BETWEEN $1 AND $2
       """
       result = await self._execute_query(query, [fecha_inicio, fecha_fin])
       return result[0] if result else {"total_repuestos": 0}
   ```

3. **`_calcular_valor_promedio_transaccion()`**
   - Ya está correcto (suma repuestos individuales)
   - ✅ No requiere cambios

---

### 4. EMBUDO OPERATIVO

**Archivo:** `services/analytics/EMBUDO_OPERATIVO_SPEC.md`

#### KPIs Afectados:

1. **KPI 2: Conversión ABIERTA → EN_EVALUACION**
   - Actual: % de solicitudes con al menos una oferta
   - Correcto: % de repuestos que recibieron al menos una oferta
   
2. **KPI 3: Conversión EN_EVALUACION → ADJUDICADA**
   - Actual: % de solicitudes adjudicadas
   - Correcto: % de repuestos adjudicados

3. **KPI 4: Conversión ADJUDICADA → ACEPTADA**
   - Actual: % de solicitudes aceptadas
   - Correcto: % de repuestos aceptados por el cliente

4. **KPI 5: Conversión General**
   - Actual: Solicitudes ACEPTADA / Total solicitudes
   - Correcto: Repuestos ACEPTADOS / Total repuestos solicitados

**Queries Corregidas:**

```python
async def _calcular_conversion_abierta_evaluacion(self, fecha_inicio, fecha_fin):
    """% de repuestos que recibieron al menos una oferta"""
    query = """
    SELECT 
        COUNT(DISTINCT rs.id) as total_repuestos,
        COUNT(DISTINCT CASE WHEN od.id IS NOT NULL THEN rs.id END) as con_ofertas
    FROM repuestos_solicitados rs
    JOIN solicitudes s ON rs.solicitud_id = s.id
    LEFT JOIN oferta_detalles od ON rs.id = od.repuesto_solicitado_id
    WHERE s.created_at BETWEEN $1 AND $2
    """
    result = await self._execute_query(query, [fecha_inicio, fecha_fin])
    if result and result[0]['total_repuestos'] > 0:
        return round((result[0]['con_ofertas'] / result[0]['total_repuestos']) * 100, 2)
    return 0.0
```

---

### 5. DASHBOARD FINANCIERO

**Archivo:** `services/analytics/app/services/metrics_calculator.py`

#### KPIs Afectados:

**✅ ESTOS YA ESTÁN CORRECTOS:**
- `valor_bruto_ofertado` - Ya suma `oferta_detalles`
- `valor_bruto_adjudicado` - Ya filtra por `estado = 'GANADORA'`
- `valor_bruto_aceptado` - Ya considera repuestos aceptados

**⚠️ VERIFICAR:**
- Asegurar que las queries usan `oferta_detalles` y no `ofertas`
- Confirmar que el estado `GANADORA` está a nivel de detalle

---

### 6. DASHBOARD DE ASESORES

**Archivo:** `services/analytics/DASHBOARD_ASESORES_SPEC.md`

#### KPIs Afectados:

1. **KPI 4: Ofertas por Asesor** → **Repuestos Ofertados por Asesor**
   ```sql
   -- Actual (INCORRECTO)
   SELECT asesor_id, COUNT(*) as total_ofertas
   FROM ofertas
   GROUP BY asesor_id
   
   -- Correcto
   SELECT o.asesor_id, COUNT(od.id) as total_repuestos_ofertados
   FROM ofertas o
   JOIN oferta_detalles od ON o.id = od.oferta_id
   GROUP BY o.asesor_id
   ```

2. **KPI 5: Tasa de Adjudicación por Asesor**
   ```sql
   -- Actual (INCORRECTO)
   SELECT 
       asesor_id,
       COUNT(*) as total_ofertas,
       COUNT(CASE WHEN estado = 'GANADORA' THEN 1 END) as ganadoras
   FROM ofertas
   GROUP BY asesor_id
   
   -- Correcto
   SELECT 
       o.asesor_id,
       COUNT(od.id) as total_repuestos,
       COUNT(CASE WHEN od.estado = 'GANADORA' THEN 1 END) as ganados
   FROM ofertas o
   JOIN oferta_detalles od ON o.id = od.oferta_id
   GROUP BY o.asesor_id
   ```

3. **KPI 6: Ranking Top 10 Asesores**
   - Cambiar de "ofertas ganadoras" a "repuestos ganados"
   - Agregar columna de "tasa de conversión de repuestos"

---

## 📋 RESUMEN DE CAMBIOS NECESARIOS

### Frontend (Advisor)

| Componente | Cambio | Prioridad |
|------------|--------|-----------|
| DashboardPage.tsx | Cambiar KPIs de solicitudes a repuestos | 🔴 ALTA |
| KPIDashboard component | Crear nuevas tarjetas de métricas | 🔴 ALTA |
| SolicitudesGanadas.tsx | Mostrar repuestos ganados vs ofertados | 🔴 ALTA |
| SolicitudesCerradas.tsx | Indicar adjudicaciones parciales | 🟡 MEDIA |
| VerOfertaModal.tsx | Mostrar estado por repuesto | 🟡 MEDIA |

### Backend (Analytics)

| Archivo | Método | Cambio | Prioridad |
|---------|--------|--------|-----------|
| metrics_calculator.py | `_calcular_tasa_conversion()` | Cambiar a repuestos | 🔴 ALTA |
| metrics_calculator.py | `_calcular_ofertas_totales()` | Contar repuestos | 🔴 ALTA |
| metrics_calculator.py | `_calcular_conversion_*()` | Todos los del embudo | 🔴 ALTA |
| metrics_calculator.py | `_calcular_ofertas_por_asesor()` | Cambiar a repuestos | 🟡 MEDIA |
| metrics_calculator.py | `_calcular_tasa_adjudicacion_asesor()` | Basado en repuestos | 🟡 MEDIA |
| dashboards.py | `get_dashboard_principal()` | Actualizar estructura de respuesta | 🔴 ALTA |

### Base de Datos

| Tabla | Campo | Acción | Prioridad |
|-------|-------|--------|-----------|
| oferta_detalles | estado | ✅ Ya existe | - |
| ofertas | estado | ⚠️ Verificar si se usa | 🟡 MEDIA |

---

## 🎯 EJEMPLO PRÁCTICO: CASO LAURA REYES

### Situación:
- Solicitud con 3 repuestos (Flasher 1, 2, 3)
- Laura oferta los 3 repuestos
- Sandra oferta 2 repuestos (Flasher 1, 2)
- Resultado: Laura gana 2 (Flasher 2, 3), Sandra gana 1 (Flasher 1)

### KPIs INCORRECTOS (Actuales):
```
Laura:
- Solicitudes ofertadas: 1
- Solicitudes ganadas: 1
- Tasa de conversión: 100% ❌ INCORRECTO

Sandra:
- Solicitudes ofertadas: 1
- Solicitudes ganadas: 1
- Tasa de conversión: 100% ❌ INCORRECTO
```

### KPIs CORRECTOS (Propuestos):
```
Laura:
- Repuestos ofertados: 3
- Repuestos ganados: 2
- Tasa de conversión: 66.67% ✅ CORRECTO
- Monto ofertado: $190,000
- Monto ganado: $160,000
- Efectividad en monto: 84.2%

Sandra:
- Repuestos ofertados: 2
- Repuestos ganados: 1
- Tasa de conversión: 50% ✅ CORRECTO
- Monto ofertado: $230,000
- Monto ganado: $50,000
- Efectividad en monto: 21.7%
```

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### Fase 1: Backend (Analytics) - CRÍTICO
1. Modificar `metrics_calculator.py`:
   - `_calcular_repuestos_ofertados()`
   - `_calcular_repuestos_ganados()`
   - `_calcular_tasa_conversion_repuestos()`
   - Todos los métodos del embudo operativo

2. Actualizar `dashboards.py`:
   - Cambiar estructura de respuesta de KPIs
   - Agregar nuevos endpoints si es necesario

3. Crear tests:
   - Verificar cálculos con adjudicaciones mixtas
   - Casos de prueba con datos reales

### Fase 2: Frontend (Advisor) - CRÍTICO
1. Actualizar tipos TypeScript:
   - Modificar `AsesorKPIs` interface
   - Agregar campos de repuestos

2. Modificar componentes:
   - `DashboardPage.tsx` - Nuevos KPIs
   - `SolicitudesGanadas.tsx` - Indicadores de adjudicación
   - `SolicitudesCerradas.tsx` - Mostrar parciales

3. Crear nuevos componentes si es necesario:
   - `RepuestosGanadosCard.tsx`
   - `TasaConversionRepuestosCard.tsx`

### Fase 3: Validación
1. Probar con datos reales de Laura y Sandra
2. Verificar que los números coincidan con cálculos manuales
3. Ajustar UI/UX según feedback

---

## ⚠️ CONSIDERACIONES IMPORTANTES

1. **Retrocompatibilidad:**
   - Mantener endpoints antiguos temporalmente
   - Agregar parámetro `version=v2` para nuevos cálculos

2. **Performance:**
   - Las queries de repuestos son más pesadas (más JOINs)
   - Considerar índices en `oferta_detalles.estado`
   - Usar cache agresivo (15-30 minutos)

3. **Migración de Datos:**
   - Verificar que todas las ofertas existentes tengan `oferta_detalles`
   - Asegurar que el campo `estado` esté poblado correctamente

4. **Documentación:**
   - Actualizar API docs
   - Crear guía de migración para el equipo
   - Documentar nuevos KPIs en Confluence/Wiki

---

## 📊 MÉTRICAS DE ÉXITO

Sabremos que la implementación es exitosa cuando:

1. ✅ Los KPIs de Laura muestren 66.67% de conversión (no 100%)
2. ✅ El dashboard muestre "2 de 3 repuestos ganados"
3. ✅ El monto ganado refleje solo los repuestos adjudicados
4. ✅ Las tarjetas de solicitudes indiquen adjudicaciones parciales
5. ✅ Los reportes de analytics sean consistentes con la realidad

---

## 🔗 ARCHIVOS A MODIFICAR

### Alta Prioridad (Crítico)
1. `services/analytics/app/services/metrics_calculator.py`
2. `services/analytics/app/routers/dashboards.py`
3. `frontend/advisor/src/pages/DashboardPage.tsx`
4. `frontend/advisor/src/components/solicitudes/SolicitudesGanadas.tsx`
5. `frontend/advisor/src/types/kpi.ts` (crear/modificar)

### Media Prioridad
6. `frontend/advisor/src/components/solicitudes/SolicitudesCerradas.tsx`
7. `services/analytics/EMBUDO_OPERATIVO_SPEC.md` (documentación)
8. `services/analytics/DASHBOARD_ASESORES_SPEC.md` (documentación)

### Baja Prioridad
9. Tests unitarios
10. Documentación de API
11. Guías de usuario

---

**Fecha de Análisis:** 2025-01-13  
**Autor:** Análisis Técnico TeLOO  
**Estado:** Pendiente de Implementación
