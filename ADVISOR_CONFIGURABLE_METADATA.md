# Metadatos Configurables en Frontend Advisor

## 📋 Resumen

Se implementó el sistema de metadatos configurables en el frontend advisor para eliminar valores hardcodeados y permitir que los rangos de validación se obtengan dinámicamente desde el backend.

## ✅ Cambios Implementados

### 1. **Nuevos Archivos Creados**

#### `frontend/advisor/src/services/configuracion.ts`
- Servicio para obtener parámetros de configuración desde el backend
- Métodos para obtener parámetros por clave
- Soporte para valores por defecto (fallback)

#### `frontend/advisor/src/hooks/useConfiguracion.ts`
- Hook personalizado para usar configuración en componentes
- Carga automática de parámetros
- Métodos helper para acceder a valores y metadatos

### 2. **Componentes Actualizados**

#### `OfertaIndividualModal.tsx`
**Antes (Hardcodeado):**
```typescript
// Valores fijos en el código
precio: 1000 - 50000000
garantía: 1 - 60 meses
tiempo: 0 - 90 días
```

**Después (Configurable):**
```typescript
// Valores obtenidos desde backend
const precioMin = precioMeta?.min ?? 1000;
const precioMax = precioMeta?.max ?? 50000000;
const garantiaMin = garantiaMeta?.min ?? 1;
const garantiaMax = garantiaMeta?.max ?? 60;
const tiempoMin = tiempoMeta?.min ?? 0;
const tiempoMax = tiempoMeta?.max ?? 90;
```

#### `CargaMasivaModal.tsx`
- Misma implementación que OfertaIndividualModal
- Validaciones dinámicas en procesamiento de Excel
- Mensajes de error con rangos configurables

## 🔧 Parámetros Configurables

Los siguientes parámetros se obtienen desde `parametros_configuracion`:

| Clave | Descripción | Uso |
|-------|-------------|-----|
| `precio_minimo_oferta` | Precio mínimo permitido | Validación de precios |
| `precio_maximo_oferta` | Precio máximo permitido | Validación de precios |
| `garantia_minima_meses` | Garantía mínima en meses | Validación de garantía |
| `garantia_maxima_meses` | Garantía máxima en meses | Validación de garantía |
| `tiempo_entrega_minimo_dias` | Tiempo mínimo de entrega | Validación de tiempo |
| `tiempo_entrega_maximo_dias` | Tiempo máximo de entrega | Validación de tiempo |

## 📊 Beneficios

1. **Centralización**: Los rangos se configuran una sola vez en el backend
2. **Consistencia**: Admin y Advisor usan los mismos valores
3. **Flexibilidad**: Cambios sin necesidad de redeployar frontend
4. **Mantenibilidad**: Código más limpio y fácil de mantener
5. **Fallback**: Valores por defecto si falla la carga

## 🔄 Flujo de Datos

```
Backend (parametros_configuracion)
    ↓
API Endpoint (/configuracion/parametros)
    ↓
configuracionService.getParametros()
    ↓
useConfiguracion() hook
    ↓
Componentes (OfertaIndividualModal, CargaMasivaModal)
    ↓
Validaciones dinámicas
```

## 🧪 Testing

Para probar los cambios:

1. Modificar valores en la tabla `parametros_configuracion`
2. Recargar el frontend advisor
3. Verificar que los nuevos rangos se apliquen en:
   - Placeholders de inputs
   - Validaciones de formulario
   - Mensajes de error
   - Procesamiento de Excel

## 📝 Ejemplo de Uso

```typescript
// En cualquier componente
import { useConfiguracion } from '@/hooks/useConfiguracion';

function MiComponente() {
  const { getValor, getMetadata } = useConfiguracion([
    'precio_minimo_oferta',
    'precio_maximo_oferta'
  ]);

  const precioMin = getMetadata('precio_minimo_oferta')?.min ?? 1000;
  const precioMax = getMetadata('precio_maximo_oferta')?.max ?? 50000000;

  // Usar precioMin y precioMax en validaciones
}
```

## 🚀 Próximos Pasos

- [ ] Agregar más parámetros configurables según necesidad
- [ ] Implementar cache de configuración
- [ ] Agregar tests unitarios para el hook
- [ ] Documentar nuevos parámetros en el admin

## 📌 Notas

- Los valores por defecto (fallback) aseguran que el sistema funcione incluso si falla la carga de configuración
- El hook `useConfiguracion` puede recibir un array de claves específicas para optimizar la carga
- Los metadatos incluyen `min`, `max`, `step`, `unit`, `help_text`, etc.

---

**Fecha**: 2025-11-10  
**Rama**: `feature/advisor-frontend-improvements`  
**Estado**: ✅ Completado
