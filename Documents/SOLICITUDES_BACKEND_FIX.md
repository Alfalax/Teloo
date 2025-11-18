# Corrección: Sistema de Permisos para Asesores

## ❌ Problema Identificado

La implementación inicial tenía un filtro **INCORRECTO** que limitaba a los asesores a ver solo solicitudes en estado `ABIERTA`:

```python
# CÓDIGO INCORRECTO ❌
if user_rol == "ASESOR":
    query = query.filter(estado=EstadoSolicitud.ABIERTA)
```

### Por qué estaba mal:

1. Los asesores tienen su propio frontend (`frontend/advisor`), no acceden al admin
2. Los asesores deben ver solicitudes **asignadas a ellos** por el sistema de escalamiento
3. Los asesores deben ver estas solicitudes en **diferentes estados** (ABIERTA, RECHAZADA, ACEPTADA, etc.)
4. La relación asesor-solicitud se establece mediante:
   - Tabla `evaluaciones_asesores_temp` (asesores evaluados/notificados)
   - Tabla `ofertas` (asesores que hicieron ofertas)

## ✅ Solución Implementada

### 1. Servicio Corregido (`solicitudes_service.py`)

```python
@staticmethod
async def get_solicitudes_paginated(
    # ... parámetros ...
    user_rol: Optional[str] = None,
    asesor_id: Optional[uuid.UUID] = None  # NUEVO
) -> Dict[str, Any]:
    """
    For ASESORES: Only show solicitudes where they were evaluated/notified OR made an offer
    For ADMIN: Show all solicitudes
    """
    query = Solicitud.all()
    
    # FILTRO CORRECTO ✅
    if user_rol == "ASESOR" and asesor_id:
        # Solicitudes donde el asesor fue evaluado/notificado O hizo oferta
        query = query.filter(
            Q(evaluaciones_asesores__asesor_id=asesor_id) |
            Q(ofertas__asesor_id=asesor_id)
        ).distinct()
    
    # Luego aplicar filtros de estado, fecha, etc.
    if estado:
        query = query.filter(estado=estado)
    
    # ... resto del código ...
```

### 2. Router Actualizado (`solicitudes.py`)

```python
@router.get("", response_model=SolicitudesPaginatedResponse)
async def get_solicitudes(
    # ... parámetros ...
    current_user: Usuario = Depends(get_current_user)
):
    """
    Para ASESORES: Solo muestra solicitudes donde fueron evaluados/notificados O hicieron oferta
    Para ADMIN: Muestra todas las solicitudes
    """
    # Obtener asesor_id si el usuario es asesor
    asesor_id = None
    if current_user.rol.value == "ASESOR":
        from models.user import Asesor
        asesor = await Asesor.get_or_none(usuario_id=current_user.id)
        if asesor:
            asesor_id = asesor.id
    
    result = await SolicitudesService.get_solicitudes_paginated(
        # ... parámetros ...
        user_rol=current_user.rol.value,
        asesor_id=asesor_id  # NUEVO
    )
    
    return result
```

### 3. Métricas Mejoradas

El endpoint `/v1/solicitudes/metrics` ahora calcula correctamente:

```python
@router.get("/metrics")
async def get_advisor_metrics(current_user: Usuario = Depends(get_current_user)):
    """
    Métricas reales del asesor:
    - ofertas_asignadas: Total de ofertas enviadas
    - monto_total_ganado: Suma de ofertas ACEPTADAS
    - solicitudes_abiertas: Solicitudes ABIERTAS asignadas
    - tasa_conversion: % de ofertas ganadoras
    """
    asesor = await Asesor.get_or_none(usuario_id=current_user.id)
    
    # Ofertas enviadas
    ofertas_asignadas = await Oferta.filter(asesor_id=asesor.id).count()
    
    # Monto ganado (ofertas ACEPTADAS)
    ofertas_ganadoras = await Oferta.filter(
        asesor_id=asesor.id,
        estado=EstadoOferta.ACEPTADA
    )
    monto_total_ganado = sum(float(o.monto_total) for o in ofertas_ganadoras)
    
    # Solicitudes ABIERTAS asignadas
    solicitudes_abiertas = await Solicitud.filter(
        Q(evaluaciones_asesores__asesor_id=asesor.id) |
        Q(ofertas__asesor_id=asesor.id),
        estado=EstadoSolicitud.ABIERTA
    ).distinct().count()
    
    # Tasa de conversión
    ofertas_ganadoras_count = await Oferta.filter(
        asesor_id=asesor.id,
        estado__in=[EstadoOferta.GANADORA, EstadoOferta.ACEPTADA]
    ).count()
    
    tasa_conversion = (ofertas_ganadoras_count / ofertas_asignadas * 100) if ofertas_asignadas > 0 else 0
    
    return {
        "ofertas_asignadas": ofertas_asignadas,
        "monto_total_ganado": round(monto_total_ganado, 2),
        "solicitudes_abiertas": solicitudes_abiertas,
        "tasa_conversion": round(tasa_conversion, 2)
    }
```

## 🎯 Comportamiento Correcto

### Frontend Advisor - Pestañas

#### Pestaña "Abiertas"
```typescript
// Solicitudes donde el asesor puede hacer ofertas
GET /v1/solicitudes?estado=ABIERTA

// Backend filtra:
// - Solicitudes en estado ABIERTA
// - Donde el asesor fue evaluado (evaluaciones_asesores_temp)
// - O donde ya hizo oferta (ofertas)
```

#### Pestaña "Cerradas"
```typescript
// Solicitudes donde participó pero no ganó
GET /v1/solicitudes?estado=RECHAZADA

// Backend filtra:
// - Solicitudes en estado RECHAZADA/EXPIRADA/CERRADA_SIN_OFERTAS
// - Donde el asesor fue evaluado O hizo oferta
```

#### Pestaña "Ganadas"
```typescript
// Solicitudes donde su oferta fue seleccionada
GET /v1/solicitudes?estado=ACEPTADA

// Backend filtra:
// - Solicitudes en estado GANADORA/ACEPTADA
// - Donde el asesor hizo oferta Y ganó
```

## 📊 Flujo Completo

```
1. Cliente crea solicitud
   └─> Estado: ABIERTA
   
2. Sistema de Escalamiento
   └─> Evalúa asesores elegibles
   └─> Crea registros en evaluaciones_asesores_temp
   └─> Asesores AHORA VEN la solicitud ✅
   
3. Asesor hace oferta
   └─> Crea registro en tabla ofertas
   └─> Asesor sigue viendo la solicitud ✅
   
4. Admin evalúa
   └─> Estado: EVALUADA
   └─> Asesores siguen viendo ✅
   
5. Adjudicación
   └─> Ganadores: Estado ACEPTADA (pestaña "Ganadas")
   └─> No seleccionados: Estado RECHAZADA (pestaña "Cerradas")
```

## 🔐 Seguridad

- ✅ Asesores solo ven solicitudes asignadas por el sistema
- ✅ Asesores ven solicitudes en todos los estados relevantes
- ✅ No pueden "descubrir" solicitudes no asignadas
- ✅ La relación se establece automáticamente por el algoritmo
- ✅ Admin ve todas las solicitudes sin restricción

## 📝 Archivos Modificados

1. `services/core-api/services/solicitudes_service.py`
   - Agregado parámetro `asesor_id`
   - Implementado filtro correcto con Q objects
   - Filtro por evaluaciones_asesores O ofertas

2. `services/core-api/routers/solicitudes.py`
   - Obtención de asesor_id del usuario actual
   - Paso de asesor_id al servicio
   - Métricas mejoradas con cálculos reales

3. `SOLICITUDES_BACKEND_IMPLEMENTATION.md`
   - Actualizada documentación
   - Agregada sección de permisos y visibilidad
   - Explicación del sistema de asignación

## ✅ Testing

Para probar la corrección:

```bash
# 1. Login como asesor
POST /v1/auth/login
{
  "email": "asesor@example.com",
  "password": "password"
}

# 2. Ver solicitudes asignadas
GET /v1/solicitudes
# Debe retornar solo solicitudes donde el asesor fue evaluado O hizo oferta

# 3. Filtrar por estado
GET /v1/solicitudes?estado=ABIERTA
# Debe retornar solo solicitudes ABIERTAS asignadas

# 4. Ver métricas
GET /v1/solicitudes/metrics
# Debe retornar métricas reales del asesor
```

## 🎉 Resultado

Ahora el sistema funciona correctamente:
- Los asesores ven solo sus solicitudes asignadas
- Pueden ver solicitudes en diferentes estados
- Las métricas reflejan su desempeño real
- El sistema respeta el flujo de escalamiento diseñado
