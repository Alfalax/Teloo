# ✅ Nuevo Indicador: Tasa de Oferta

**Fecha:** 2025-11-14  
**Tipo:** Nuevo indicador agregado

---

## 📊 Definición

**Tasa de Oferta:** Porcentaje de repuestos ofertados sobre el total de repuestos asignados.

**Fórmula:**
```
Tasa de Oferta = (Repuestos Ofertados / Repuestos Asignados) * 100
```

---

## 🎯 Propósito

Este indicador mide la **capacidad de respuesta** del asesor:
- ✅ **100%:** El asesor ofertó todos los repuestos asignados
- ✅ **>80%:** Buena cobertura de ofertas
- ⚠️ **<50%:** Baja participación en las solicitudes asignadas

---

## 📝 Cálculo

### Repuestos Asignados
Total de repuestos en TODAS las solicitudes asignadas al asesor (mes actual):
```sql
SELECT SUM(rs.cantidad)
FROM solicitudes s
JOIN evaluaciones_asesores_temp e ON e.solicitud_id = s.id
JOIN repuestos_solicitados rs ON rs.solicitud_id = s.id
WHERE e.asesor_id = :asesor_id
  AND s.created_at >= :inicio_mes
```

### Repuestos Ofertados
Total de repuestos que el asesor ofertó (mes actual):
```sql
SELECT SUM(od.cantidad)
FROM ofertas o
JOIN ofertas_detalle od ON od.oferta_id = o.id
WHERE o.asesor_id = :asesor_id
  AND o.created_at >= :inicio_mes
```

### Tasa de Oferta
```python
tasa_oferta = 0.0
if repuestos_asignados > 0:
    tasa_oferta = (repuestos_ofertados / repuestos_asignados) * 100
```

---

## 📋 Ejemplo con Sandra Romero

### Solicitudes Asignadas (mes actual)
1. **Solicitud #c2f30973 (BARBOSA):**
   - Repuestos asignados: 3 (Farola 1 x1, Farola 2 x2)
   - Repuestos ofertados: 1 (Farola 1 x1)

2. **Solicitud #9d9185ab (ALEJANDRÍA):**
   - Repuestos asignados: 2 (Pastillas x2)
   - Repuestos ofertados: 2 (Pastillas x2)

3. **Solicitud #91269925 (ALEJANDRÍA):**
   - Repuestos asignados: 5 (varios)
   - Repuestos ofertados: 5 (todos)

### Cálculo
- **Total Asignados:** 3 + 2 + 5 = 10 repuestos
- **Total Ofertados:** 1 + 2 + 5 = 8 repuestos
- **Tasa de Oferta:** (8 / 10) * 100 = **80%**

---

## 🎨 Visualización en Dashboard

**Tarjeta 5:**
- **Título:** Tasa de Oferta
- **Valor:** 80.0%
- **Icono:** Target (🎯)
- **Color:** Indigo
- **Posición:** Quinta tarjeta (después de Tasa de Conversión)

---

## 📝 Archivos Modificados

### Backend
1. ✅ `services/core-api/routers/solicitudes.py` - Cálculo agregado

### Frontend
2. ✅ `frontend/advisor/src/types/kpi.ts` - Tipo actualizado
3. ✅ `frontend/advisor/src/pages/DashboardPage.tsx` - Estado actualizado
4. ✅ `frontend/advisor/src/services/solicitudes.ts` - Respuesta actualizada
5. ✅ `frontend/advisor/src/components/dashboard/KPIDashboard.tsx` - Tarjeta agregada

---

## 🔍 Interpretación

### Tasa Alta (>80%)
- ✅ El asesor está respondiendo activamente
- ✅ Buena cobertura de las solicitudes asignadas
- ✅ Alta participación en el marketplace

### Tasa Media (50-80%)
- ⚠️ El asesor responde selectivamente
- ⚠️ Puede estar priorizando ciertas solicitudes
- ⚠️ Oportunidad de mejorar cobertura

### Tasa Baja (<50%)
- ❌ Baja participación
- ❌ Muchas solicitudes sin respuesta
- ❌ Posible problema de capacidad o interés

---

## 💡 Diferencia con Tasa de Conversión

| Indicador | Qué Mide | Fórmula |
|-----------|----------|---------|
| **Tasa de Oferta** | Capacidad de respuesta | Repuestos ofertados / Repuestos asignados |
| **Tasa de Conversión** | Efectividad comercial | Monto aceptado / Monto ofertado |

**Ejemplo:**
- Tasa de Oferta 80% = Ofertó 8 de 10 repuestos asignados
- Tasa de Conversión 45% = De lo que ofertó, el cliente aceptó el 45% del monto

---

## ✅ Resultado

El dashboard ahora muestra **5 indicadores** en lugar de 4, proporcionando una visión más completa del desempeño del asesor.
