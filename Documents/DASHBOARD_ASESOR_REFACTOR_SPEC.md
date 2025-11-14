# Dashboard Asesor - Especificación de Refactor

## 🎯 Objetivo
Reorganizar el dashboard del asesor para mostrar todas las solicitudes en una sola vista con filtros, eliminando las pestañas actuales.

## 📋 Flujo de Estados

### Estados de Solicitud (desde perspectiva del asesor):
1. **ABIERTA** → Solicitud asignada, asesor aún no envía oferta
2. **ENVIADA** → Asesor envió su oferta (oferta en estado ENVIADA)
3. **GANADORA** → Ganó al menos 1 repuesto (oferta en estado GANADORA)
4. **NO_SELECCIONADA** → No ganó ningún repuesto (oferta en estado NO_SELECCIONADA)
5. **ACEPTADA** → Cliente aceptó (solo para ganadoras)
6. **RECHAZADA** → Cliente rechazó (solo para ganadoras)
7. **EXPIRADA** → Expiró sin respuesta del cliente (solo para ganadoras)

### Reglas de Visualización:
- ✅ Mostrar: Solicitudes donde el asesor envió oferta
- ❌ NO mostrar: Solicitudes asignadas donde el asesor NO envió oferta y ya se cerraron/evaluaron

## 🎨 Diseño de UI

### Estructura:
```
┌─────────────────────────────────────────────────────────────┐
│ Dashboard                                                    │
│ Gestiona tus ofertas y solicitudes                          │
├─────────────────────────────────────────────────────────────┤
│ [KPI Cards]                                                  │
├─────────────────────────────────────────────────────────────┤
│ Mis Solicitudes                                              │
│                                                              │
│ [Todas] [Activas] [Finalizadas]    [Lista/Tarjetas] [Carga]│
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Tarjetas de solicitudes ordenadas por prioridad]       │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Filtros:
- **Todas**: Muestra todas las solicitudes
- **Activas**: ABIERTA + ENVIADA
- **Finalizadas**: GANADORA + NO_SELECCIONADA + ACEPTADA + RECHAZADA + EXPIRADA

### Ordenamiento (prioridad):
1. ABIERTA (primero - más urgente)
2. ENVIADA
3. GANADORA
4. NO_SELECCIONADA
5. ACEPTADA
6. RECHAZADA
7. EXPIRADA (último)

### Toggle Vista:
- 🔲 Lista (tabla compacta)
- 🎴 Tarjetas (vista actual)

## 🔧 Cambios Técnicos

### Backend:
✅ **Ya implementado:**
- Actualización de estados de ofertas a GANADORA/NO_SELECCIONADA después de evaluación

### Frontend:

#### 1. Actualizar tipos (solicitudes.ts):
```typescript
export type EstadoOfertaAsesor = 
  | 'ABIERTA'      // No ha enviado oferta
  | 'ENVIADA'      // Oferta enviada
  | 'GANADORA'     // Ganó repuestos
  | 'NO_SELECCIONADA' // No ganó
  | 'ACEPTADA'     // Cliente aceptó
  | 'RECHAZADA'    // Cliente rechazó
  | 'EXPIRADA';    // Expiró

export interface SolicitudConOferta {
  // ... campos existentes
  estado_oferta_asesor: EstadoOfertaAsesor;
  repuestos_ganados?: number;
  repuestos_totales?: number;
}
```

#### 2. Nuevo componente: SolicitudesUnificadas.tsx
- Reemplaza: SolicitudesAbiertas, SolicitudesCerradas, SolicitudesGanadas
- Incluye:
  - Filtros (Todas/Activas/Finalizadas)
  - Toggle Lista/Tarjetas
  - Botón Carga Masiva
  - Ordenamiento automático por prioridad
  - Badges de estado con colores

#### 3. Actualizar DashboardPage.tsx:
- Eliminar Tabs
- Usar SolicitudesUnificadas
- Mantener modales existentes

#### 4. Badges de Estado (colores):
- ABIERTA: `bg-blue-100 text-blue-800` (Azul - acción requerida)
- ENVIADA: `bg-yellow-100 text-yellow-800` (Amarillo - en espera)
- GANADORA: `bg-green-100 text-green-800` (Verde - éxito)
- NO_SELECCIONADA: `bg-gray-100 text-gray-800` (Gris - neutral)
- ACEPTADA: `bg-emerald-100 text-emerald-800` (Verde esmeralda - completado)
- RECHAZADA: `bg-red-100 text-red-800` (Rojo - rechazado)
- EXPIRADA: `bg-orange-100 text-orange-800` (Naranja - expirado)

## 📝 Notas de Implementación

1. **Endpoint Backend**: Necesita devolver `estado_oferta_asesor` calculado
2. **Filtrado**: Se hace en frontend para mejor UX
3. **Ordenamiento**: Usar función de prioridad numérica
4. **Responsive**: Mantener diseño responsive actual
5. **Performance**: Considerar paginación si hay muchas solicitudes

## ✅ Checklist de Implementación

### Backend:
- [x] Actualizar estados de ofertas en evaluación

### Frontend:
- [ ] Actualizar tipos en solicitudes.ts
- [ ] Crear componente SolicitudesUnificadas
- [ ] Actualizar DashboardPage
- [ ] Crear función de ordenamiento por prioridad
- [ ] Implementar filtros
- [ ] Actualizar badges de estado
- [ ] Probar flujo completo

## 🧪 Casos de Prueba

1. **Solicitud ABIERTA**: Debe aparecer primero, botón "Hacer Oferta"
2. **Solicitud ENVIADA**: Debe aparecer después de abiertas, botón "Ver Oferta"
3. **Solicitud GANADORA**: Badge verde, mostrar "Ganaste X de Y repuestos"
4. **Solicitud NO_SELECCIONADA**: Badge gris, mensaje "No seleccionada"
5. **Filtro Activas**: Solo ABIERTA + ENVIADA
6. **Filtro Finalizadas**: Solo estados finales
7. **Ordenamiento**: Verificar orden correcto
8. **Toggle Vista**: Cambiar entre lista y tarjetas

---

**Fecha**: 2025-11-13
**Rama**: feature/frontend-indicadores-estados
