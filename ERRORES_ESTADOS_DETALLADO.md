# Errores de Estados - Detalle Exacto

## ❌ BACKEND - 1 Archivo con Error

### `services/core-api/models/enums.py`

**Líneas 27-33:**
```python
class EstadoSolicitud(str, Enum):
    """Estados de solicitud"""
    ABIERTA = "ABIERTA"
    EVALUADA = "EVALUADA"
    ACEPTADA = "ACEPTADA"          # ❌ ELIMINAR
    RECHAZADA = "RECHAZADA"        # ❌ ELIMINAR
    EXPIRADA = "EXPIRADA"          # ❌ ELIMINAR
    CERRADA_SIN_OFERTAS = "CERRADA_SIN_OFERTAS"
```

**Problema:** Define 6 estados cuando solo debería definir 3.

**Impacto:** 
- Pydantic acepta estos estados en validación
- Puede causar confusión en desarrollo
- Los servicios NO los usan (están bien), pero el enum base está mal

---

## ❌ FRONTEND - 3 Archivos con Errores

### 1. `frontend/advisor/src/types/solicitud.ts`

**Línea 5:**
```typescript
estado: 'ABIERTA' | 'EVALUADA' | 'ACEPTADA' | 'RECHAZADA' | 'EXPIRADA' | 'CERRADA_SIN_OFERTAS';
//                              ❌ ELIMINAR  ❌ ELIMINAR  ❌ ELIMINAR
```

**Problema:** Define estados que el backend nunca enviará.

---

### 2. `frontend/advisor/src/components/solicitudes/SolicitudesUnificadas.tsx`

**Líneas 42-45 - Función `determinarEstadoOfertaAsesor`:**
```typescript
if (solicitud.estado === 'ACEPTADA') return 'ACEPTADA';      // ❌ ELIMINAR
if (solicitud.estado === 'RECHAZADA') return 'RECHAZADA';    // ❌ ELIMINAR
if (solicitud.estado === 'EXPIRADA') return 'EXPIRADA';      // ❌ ELIMINAR
if (solicitud.estado === 'CERRADA_SIN_OFERTAS') return 'EXPIRADA';  // ✅ MANTENER
```

**Problema:** Verifica estados que nunca llegarán del backend.

**Líneas 137-139 - Filtro de solicitudes:**
```typescript
if (!solicitud.mi_oferta && 
    ['EVALUADA', 'ACEPTADA', 'RECHAZADA', 'EXPIRADA', 'CERRADA_SIN_OFERTAS'].includes(solicitud.estado)) {
    //           ❌ ELIMINAR ❌ ELIMINAR ❌ ELIMINAR
    return false;
}
```

**Problema:** Filtra por estados que nunca existirán.

---

### 3. `frontend/admin/src/types/solicitudes.ts`

**Líneas 7-12:**
```typescript
export type EstadoSolicitud =
  | "ABIERTA"
  | "EVALUADA"
  | "ACEPTADA"              // ❌ ELIMINAR
  | "RECHAZADA"             // ❌ ELIMINAR
  | "EXPIRADA"              // ❌ ELIMINAR
  | "CERRADA_SIN_OFERTAS";
```

**Problema:** Define estados que el backend nunca enviará.

---

## ✅ CORRECCIONES NECESARIAS

### Backend (1 archivo)

**`services/core-api/models/enums.py`:**
```python
class EstadoSolicitud(str, Enum):
    """Estados de solicitud"""
    ABIERTA = "ABIERTA"
    EVALUADA = "EVALUADA"
    CERRADA_SIN_OFERTAS = "CERRADA_SIN_OFERTAS"
```

### Frontend Advisor (2 archivos)

**`frontend/advisor/src/types/solicitud.ts`:**
```typescript
estado: 'ABIERTA' | 'EVALUADA' | 'CERRADA_SIN_OFERTAS';
```

**`frontend/advisor/src/components/solicitudes/SolicitudesUnificadas.tsx`:**

Líneas 42-45:
```typescript
// ELIMINAR estas 3 líneas:
// if (solicitud.estado === 'ACEPTADA') return 'ACEPTADA';
// if (solicitud.estado === 'RECHAZADA') return 'RECHAZADA';
// if (solicitud.estado === 'EXPIRADA') return 'EXPIRADA';

// MANTENER:
if (solicitud.estado === 'CERRADA_SIN_OFERTAS') return 'EXPIRADA';
```

Líneas 137-139:
```typescript
if (!solicitud.mi_oferta && 
    ['EVALUADA', 'CERRADA_SIN_OFERTAS'].includes(solicitud.estado)) {
    return false;
}
```

### Frontend Admin (1 archivo)

**`frontend/admin/src/types/solicitudes.ts`:**
```typescript
export type EstadoSolicitud =
  | "ABIERTA"
  | "EVALUADA"
  | "CERRADA_SIN_OFERTAS";
```

---

## 📊 RESUMEN

| Componente | Archivos con Error | Líneas Afectadas |
|------------|-------------------|------------------|
| **Backend** | 1 | ~7 líneas |
| **Frontend Advisor** | 2 | ~10 líneas |
| **Frontend Admin** | 1 | ~6 líneas |
| **TOTAL** | **4 archivos** | **~23 líneas** |

---

## ⚠️ POR QUÉ ES IMPORTANTE CORREGIR

1. **Consistencia:** Frontend y backend deben tener el mismo contrato
2. **Bugs potenciales:** Lógica que verifica estados inexistentes nunca se ejecutará
3. **Confusión:** Desarrolladores pueden usar estados incorrectos
4. **TypeScript:** Los tipos incorrectos no alertan de errores reales
5. **Mantenibilidad:** Código más limpio y fácil de entender

---

## ✅ ESTADOS FINALES CORRECTOS

### Solicitud (3 estados)
1. `ABIERTA` - Recibiendo ofertas
2. `EVALUADA` - Ofertas evaluadas y adjudicadas
3. `CERRADA_SIN_OFERTAS` - Sin ofertas válidas

### Oferta (6 estados)
1. `ENVIADA` - Oferta enviada
2. `GANADORA` - Ganó repuestos
3. `NO_SELECCIONADA` - No ganó
4. `EXPIRADA` - Expiró por timeout
5. `RECHAZADA` - Cliente rechazó
6. `ACEPTADA` - Cliente aceptó
