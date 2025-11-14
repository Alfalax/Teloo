# Implementación Backend - Módulo de Solicitudes

## Resumen
Se ha completado la implementación de los endpoints del backend para el módulo de Solicitudes, conectando con el frontend ya existente.

## Archivos Creados/Modificados

### 1. Servicio de Solicitudes
**Archivo:** `services/core-api/services/solicitudes_service.py`

Métodos implementados:
- `get_solicitudes_paginated()` - Obtener solicitudes paginadas con filtros
- `get_solicitud_by_id()` - Obtener detalle de una solicitud específica
- `create_solicitud()` - Crear nueva solicitud con cliente y repuestos
- `get_stats()` - Obtener estadísticas por estado

### 2. Router de Solicitudes
**Archivo:** `services/core-api/routers/solicitudes.py`

Endpoints implementados:
- `GET /v1/solicitudes` - Listar solicitudes con paginación y filtros
- `GET /v1/solicitudes/stats` - Obtener estadísticas
- `POST /v1/solicitudes` - Crear nueva solicitud
- `GET /v1/solicitudes/{id}` - Obtener detalle de solicitud

### 3. Frontend Service
**Archivo:** `frontend/admin/src/services/solicitudes.ts`

Actualizado para conectar con los endpoints reales del backend.

## Características Implementadas

### Paginación y Filtros
- Paginación con `page` y `page_size`
- Filtro por estado (ABIERTA, EVALUADA, ACEPTADA, etc.)
- Búsqueda por nombre, teléfono o ciudad
- Filtro por rango de fechas
- Filtro por ciudad y departamento
- **Filtro inteligente para asesores**: Solo ven solicitudes donde fueron evaluados/notificados (tabla `evaluaciones_asesores_temp`) O donde hicieron oferta (tabla `ofertas`), en cualquier estado

### Creación de Solicitudes
- Validación de geografía (ciudad y departamento)
- Creación automática de Usuario y Cliente si no existen
- Normalización de números telefónicos al formato colombiano (+57)
- Creación de múltiples repuestos asociados
- Validación de años de vehículos (1980-2025)

### Estadísticas
- Total de solicitudes
- Solicitudes abiertas
- Solicitudes evaluadas
- Solicitudes aceptadas
- Solicitudes rechazadas/expiradas/cerradas

## Modelos de Datos

### Request Models
```python
ClienteInput:
  - nombre: str
  - telefono: str
  - email: Optional[str]

RepuestoSolicitadoInput:
  - nombre: str
  - codigo: Optional[str]
  - descripcion: Optional[str]
  - cantidad: int (>= 1)
  - marca_vehiculo: str
  - linea_vehiculo: str
  - anio_vehiculo: int (1980-2025)
  - observaciones: Optional[str]
  - es_urgente: bool

CreateSolicitudRequest:
  - cliente: ClienteInput
  - ciudad_origen: str
  - departamento_origen: str
  - repuestos: List[RepuestoSolicitadoInput]
```

### Response Models
```python
SolicitudResponse:
  - id: str
  - cliente_id: str
  - cliente_nombre: str
  - cliente_telefono: str
  - estado: str
  - nivel_actual: int
  - ciudad_origen: str
  - departamento_origen: str
  - ofertas_minimas_deseadas: int
  - timeout_horas: int
  - fecha_creacion: str
  - fecha_escalamiento: Optional[str]
  - fecha_evaluacion: Optional[str]
  - fecha_expiracion: Optional[str]
  - total_repuestos: int
  - monto_total_adjudicado: float
  - repuestos_solicitados: List[RepuestoSolicitadoResponse]

SolicitudesPaginatedResponse:
  - items: List[SolicitudResponse]
  - total: int
  - page: int
  - page_size: int
  - total_pages: int

SolicitudesStatsResponse:
  - total: int
  - abiertas: int
  - evaluadas: int
  - aceptadas: int
  - rechazadas_expiradas: int
```

## Relaciones de Base de Datos

La implementación maneja correctamente las relaciones:
- `Solicitud` → `Cliente` (ForeignKey)
- `Cliente` → `Usuario` (OneToOne)
- `Solicitud` → `RepuestoSolicitado` (OneToMany)

## Validaciones Implementadas

1. **Geografía**: Validación de ciudad y departamento usando `GeografiaService`
2. **Teléfono**: Normalización automática al formato colombiano (+57XXXXXXXXXX)
3. **Año de vehículo**: Rango válido entre 1980 y 2025
4. **Cantidad de repuestos**: Mínimo 1
5. **Campos requeridos**: Validación de campos obligatorios

## Testing

Se creó un script de prueba: `services/core-api/test_solicitudes_endpoints.py`

Para ejecutar:
```bash
cd services/core-api
python test_solicitudes_endpoints.py
```

Pruebas incluidas:
- ✓ Obtener estadísticas
- ✓ Listar solicitudes paginadas
- ✓ Crear nueva solicitud
- ✓ Obtener solicitud por ID

## Próximos Pasos

### Integración Completa
1. Iniciar el backend: `docker-compose up core-api`
2. Iniciar el frontend: `cd frontend/admin && npm run dev`
3. Probar el flujo completo desde la UI

### Funcionalidades Pendientes
- Implementar parsing real de Excel para repuestos
- Agregar endpoint para actualizar estado de solicitud
- Agregar endpoint para eliminar solicitud
- Implementar filtros avanzados adicionales
- Agregar exportación a Excel de solicitudes

### Mejoras Sugeridas
- Agregar caché para estadísticas
- Implementar búsqueda full-text
- Agregar índices de base de datos para mejorar performance
- Implementar rate limiting para creación de solicitudes
- Agregar validación de duplicados (misma solicitud en corto tiempo)

## Notas Técnicas

### Manejo de Clientes
El sistema crea automáticamente un Usuario y Cliente cuando se crea una solicitud con un teléfono nuevo. Esto permite que el sistema funcione sin requerir registro previo del cliente.

### Formato de Teléfono
Los números telefónicos se normalizan automáticamente al formato colombiano (+57XXXXXXXXXX). Si el número no tiene el prefijo, se agrega automáticamente.

### Permisos
Los asesores solo pueden ver solicitudes en estado ABIERTA. Los administradores pueden ver todas las solicitudes.

### Performance
- Se usa `prefetch_related` para optimizar queries con relaciones
- La paginación limita los resultados a un máximo de 100 items por página
- Los filtros se aplican a nivel de base de datos para mejor performance


## 🔐 Sistema de Permisos y Visibilidad

### Diferencia entre Admin y Asesor

El sistema tiene **dos frontends separados** con diferentes niveles de acceso:

#### Frontend Admin (`frontend/admin`)
- **Usuarios**: ADMIN, SUPERADMIN
- **Acceso**: Todas las solicitudes del sistema
- **Funcionalidades**: 
  - Ver todas las solicitudes en cualquier estado
  - Crear nuevas solicitudes
  - Gestionar asesores
  - Ver reportes y analytics
  - Configurar el sistema

#### Frontend Advisor (`frontend/advisor`)
- **Usuarios**: ASESOR
- **Acceso**: Solo solicitudes asignadas
- **Funcionalidades**:
  - Ver solicitudes donde fueron notificados por el sistema de escalamiento
  - Ver solicitudes donde ya hicieron ofertas
  - Hacer ofertas individuales o masivas
  - Ver sus métricas personales

### Cómo Funciona la Asignación de Solicitudes a Asesores

1. **Cliente crea solicitud** (vía WhatsApp o Admin)
   - Estado: ABIERTA
   - Sistema ejecuta algoritmo de escalamiento

2. **Sistema de Escalamiento evalúa asesores**
   - Calcula puntaje basado en: proximidad (40%), actividad (25%), desempeño (20%), confianza (15%)
   - Clasifica asesores en niveles 1-5
   - Crea registros en tabla `evaluaciones_asesores_temp`
   - **Estos asesores ahora "ven" la solicitud**

3. **Notificación por oleadas**
   - Nivel 1: Mejores asesores (WhatsApp)
   - Nivel 2-5: Escalamiento progresivo si no hay suficientes ofertas

4. **Asesor hace oferta**
   - Se crea registro en tabla `ofertas`
   - Asesor sigue viendo la solicitud en diferentes estados

5. **Admin evalúa ofertas**
   - Estado: EVALUADA
   - Asesores siguen viendo la solicitud

6. **Adjudicación**
   - Ganadores: Estado GANADORA/ACEPTADA (pestaña "Ganadas")
   - No seleccionados: Estado RECHAZADA (pestaña "Cerradas")

### Consulta SQL Simplificada

```sql
-- Para ASESORES: Solo solicitudes donde participaron
SELECT DISTINCT s.*
FROM solicitudes s
LEFT JOIN evaluaciones_asesores_temp eat ON s.id = eat.solicitud_id
LEFT JOIN ofertas o ON s.id = o.solicitud_id
WHERE (eat.asesor_id = :asesor_id OR o.asesor_id = :asesor_id)
  AND s.estado = :estado_filtro  -- Opcional

-- Para ADMIN: Todas las solicitudes
SELECT s.*
FROM solicitudes s
WHERE s.estado = :estado_filtro  -- Opcional
```

### Pestañas del Frontend Advisor

```typescript
// Abiertas: Solicitudes donde puede ofertar
estado = 'ABIERTA' 
+ (evaluado O ya ofertó)

// Cerradas: Solicitudes donde participó pero no ganó
estado IN ('RECHAZADA', 'EXPIRADA', 'CERRADA_SIN_OFERTAS')
+ (evaluado O ya ofertó)

// Ganadas: Solicitudes donde su oferta fue seleccionada
estado IN ('GANADORA', 'ACEPTADA')
+ (ofertó Y ganó)
```

### Métricas del Asesor

El endpoint `/v1/solicitudes/metrics` calcula:

1. **ofertas_asignadas**: Total de ofertas enviadas por el asesor
2. **monto_total_ganado**: Suma de montos de ofertas ACEPTADAS
3. **solicitudes_abiertas**: Solicitudes ABIERTAS donde fue evaluado/notificado
4. **tasa_conversion**: (Ofertas ganadoras / Ofertas enviadas) * 100

### Seguridad

- Los asesores **NUNCA** ven solicitudes de otros asesores
- Los asesores **SOLO** ven solicitudes donde el sistema los evaluó como elegibles
- La relación se establece automáticamente por el algoritmo de escalamiento
- No hay forma de que un asesor "descubra" solicitudes no asignadas
