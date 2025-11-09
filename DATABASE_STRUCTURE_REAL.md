# Estructura Real de la Base de Datos TeLOO V3

**Base de Datos:** `teloo_v3` (PostgreSQL)  
**Schema:** `public`  
**Total de Tablas:** 26

## Resumen de Tablas por Módulo

### 1. MÓDULO DE USUARIOS Y ACTORES (3 tablas)

| Tabla | Columnas | Registros | Descripción |
|-------|----------|-----------|-------------|
| **usuarios** | 11 | 13 | Usuarios base del sistema (email, password_hash, nombre, apellido, telefono, rol, estado, ultimo_login) |
| **clientes** | 10 | 6 | Clientes que solicitan repuestos |
| **asesores** | 16 | 6 | Asesores/proveedores que ofrecen repuestos |

**Relaciones:**
- `clientes.usuario_id` → `usuarios.id`
- `asesores.usuario_id` → `usuarios.id`

---

### 2. MÓDULO DE SOLICITUDES Y REPUESTOS (2 tablas)

| Tabla | Columnas | Registros | Descripción |
|-------|----------|-----------|-------------|
| **solicitudes** | 16 | 2 | Solicitudes de repuestos (estado, nivel_actual, ciudad_origen, ofertas_minimas_deseadas, timeout_horas) |
| **repuestos_solicitados** | 14 | 6 | Detalles de repuestos solicitados por solicitud |

**Relaciones:**
- `solicitudes.cliente_id` → `clientes.id`
- `repuestos_solicitados.solicitud_id` → `solicitudes.id`

---

### 3. MÓDULO DE OFERTAS Y EVALUACIÓN (4 tablas)

| Tabla | Columnas | Registros | Descripción |
|-------|----------|-----------|-------------|
| **ofertas** | 16 | 0 | Ofertas de asesores para solicitudes |
| **ofertas_detalle** | 17 | 0 | Detalle de cada oferta por repuesto |
| **adjudicaciones_repuesto** | 14 | 0 | Adjudicación de repuestos a ofertas ganadoras |
| **evaluaciones** | 17 | 0 | Registro de evaluaciones completas |

**Relaciones:**
- `ofertas.solicitud_id` → `solicitudes.id`
- `ofertas.asesor_id` → `asesores.id`
- `ofertas_detalle.oferta_id` → `ofertas.id`
- `ofertas_detalle.repuesto_solicitado_id` → `repuestos_solicitados.id`
- `adjudicaciones_repuesto.solicitud_id` → `solicitudes.id`
- `adjudicaciones_repuesto.oferta_id` → `ofertas.id`
- `adjudicaciones_repuesto.repuesto_solicitado_id` → `repuestos_solicitados.id`
- `adjudicaciones_repuesto.oferta_detalle_id` → `ofertas_detalle.id`
- `evaluaciones.solicitud_id` → `solicitudes.id`

---

### 4. MÓDULO GEOGRÁFICO Y ESCALAMIENTO (3 tablas)

| Tabla | Columnas | Registros | Descripción |
|-------|----------|-----------|-------------|
| **areas_metropolitanas** | 8 | ? | Áreas metropolitanas de Colombia |
| **hubs_logisticos** | 7 | ? | Asignación de hubs logísticos por municipio |
| **evaluaciones_asesores_temp** | 19 | ? | Evaluación temporal de asesores para escalamiento |

**Relaciones:**
- `evaluaciones_asesores_temp.solicitud_id` → `solicitudes.id`
- `evaluaciones_asesores_temp.asesor_id` → `asesores.id`

---

### 5. MÓDULO DE ANALYTICS E HISTÓRICOS (7 tablas)

| Tabla | Columnas | Registros | Descripción |
|-------|----------|-----------|-------------|
| **historial_respuestas_ofertas** | 11 | ? | Historial de respuestas para actividad reciente |
| **ofertas_historicas** | 15 | ? | Historial de ofertas para desempeño histórico |
| **auditorias_tiendas** | 11 | ? | Auditorías de asesores para nivel de confianza |
| **eventos_sistema** | 8 | ? | Eventos del sistema para analytics |
| **metricas_calculadas** | 11 | ? | Cache de métricas calculadas |
| **transacciones** | 13 | ? | Transacciones financieras |
| **sesiones_usuarios** | 13 | ? | Sesiones de usuario para analytics de uso |

**Relaciones:**
- `historial_respuestas_ofertas.asesor_id` → `asesores.id`
- `historial_respuestas_ofertas.solicitud_id` → `solicitudes.id`
- `ofertas_historicas.asesor_id` → `asesores.id`
- `ofertas_historicas.solicitud_id` → `solicitudes.id`
- `auditorias_tiendas.asesor_id` → `asesores.id`
- `auditorias_tiendas.auditor_id` → `usuarios.id`
- `transacciones.solicitud_id` → `solicitudes.id`
- `transacciones.asesor_id` → `asesores.id`
- `sesiones_usuarios.usuario_id` → `usuarios.id`

---

### 6. MÓDULO DE SOPORTE Y CONFIGURACIÓN (5 tablas)

| Tabla | Columnas | Registros | Descripción |
|-------|----------|-----------|-------------|
| **pqrs** | 13 | ? | Peticiones, Quejas y Reclamos |
| **notificaciones** | 11 | ? | Notificaciones del sistema |
| **logs_auditoria** | 11 | ? | Logs de auditoría para trazabilidad |
| **parametros_config** | 7 | ? | Parámetros de configuración del sistema |
| **alertas_metricas** | 9 | ? | Alertas de métricas |

**Relaciones:**
- `pqrs.cliente_id` → `clientes.id`
- `pqrs.respondido_por_id` → `usuarios.id`
- `notificaciones.usuario_id` → `usuarios.id`
- `logs_auditoria.actor_id` → `usuarios.id`
- `parametros_config.modificado_por_id` → `usuarios.id`

---

### 7. MÓDULO DE ALERTAS (2 tablas)

| Tabla | Columnas | Registros | Descripción |
|-------|----------|-----------|-------------|
| **alertas_metricas** | 9 | ? | Definición de alertas de métricas |
| **historial_alertas** | 7 | ? | Historial de alertas disparadas |
| **eventos_metricas** | 6 | ? | Eventos relacionados con métricas |

**Relaciones:**
- `historial_alertas.alerta_id` → `alertas_metricas.id`

---

## Estructura de Tabla USUARIOS (Ejemplo Detallado)

```sql
CREATE TABLE usuarios (
    id                UUID PRIMARY KEY,
    created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    email             VARCHAR(255) NOT NULL UNIQUE,
    password_hash     VARCHAR(255) NOT NULL,
    nombre            VARCHAR(100) NOT NULL,
    apellido          VARCHAR(100) NOT NULL,
    telefono          VARCHAR(15) NOT NULL,
    rol               VARCHAR(7) NOT NULL DEFAULT 'CLIENT',
    estado            VARCHAR(10) NOT NULL DEFAULT 'ACTIVO',
    ultimo_login      TIMESTAMP WITH TIME ZONE
);
```

**Roles disponibles:** ADMIN, ADVISOR, ANALYST, SUPPORT, CLIENT  
**Estados disponibles:** ACTIVO, INACTIVO, SUSPENDIDO, BLOQUEADO

---

## Estructura de Tabla SOLICITUDES (Ejemplo Detallado)

```sql
CREATE TABLE solicitudes (
    id                       UUID PRIMARY KEY,
    created_at               TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at               TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cliente_id               UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    estado                   VARCHAR(19) NOT NULL DEFAULT 'ABIERTA',
    nivel_actual             INTEGER NOT NULL DEFAULT 1,
    ciudad_origen            VARCHAR(100) NOT NULL,
    departamento_origen      VARCHAR(100) NOT NULL,
    ofertas_minimas_deseadas INTEGER NOT NULL DEFAULT 2,
    timeout_horas            INTEGER NOT NULL DEFAULT 20,
    fecha_escalamiento       TIMESTAMP WITH TIME ZONE,
    fecha_evaluacion         TIMESTAMP WITH TIME ZONE,
    fecha_expiracion         TIMESTAMP WITH TIME ZONE,
    metadata_json            JSONB NOT NULL,
    total_repuestos          INTEGER NOT NULL DEFAULT 0,
    monto_total_adjudicado   NUMERIC(15,2) NOT NULL DEFAULT 0
);
```

**Estados disponibles:** ABIERTA, EVALUADA, ACEPTADA, RECHAZADA, EXPIRADA, CERRADA_SIN_OFERTAS

---

## Datos Actuales en la Base de Datos

| Tabla | Registros |
|-------|-----------|
| usuarios | 13 |
| clientes | 6 |
| asesores | 6 |
| solicitudes | 2 |
| repuestos_solicitados | 6 |
| ofertas | 0 |
| ofertas_detalle | 0 |
| adjudicaciones_repuesto | 0 |
| evaluaciones | 0 |

---

## Observaciones Importantes

1. **No hay ENUMs nativos de PostgreSQL**: Los estados se manejan como VARCHAR con validaciones a nivel de aplicación
2. **No hay vistas materializadas**: Aunque el script SQL las define, no están creadas en la BD actual
3. **Schema público**: Todas las tablas están en el schema `public`, no en `teloo` como sugiere el script
4. **Datos de prueba**: Hay 13 usuarios, 6 clientes, 6 asesores y 2 solicitudes con 6 repuestos
5. **Sin ofertas**: No hay ofertas, evaluaciones ni adjudicaciones todavía
6. **Tablas de alertas**: Existen tablas adicionales para el sistema de alertas que no estaban en los modelos Python

---

## Relaciones Principales (Foreign Keys)

Total de relaciones: **30 foreign keys**

Las relaciones más importantes:
- Usuarios → Clientes/Asesores (1:1)
- Clientes → Solicitudes (1:N)
- Solicitudes → Repuestos Solicitados (1:N)
- Solicitudes → Ofertas (1:N)
- Asesores → Ofertas (1:N)
- Ofertas → Ofertas Detalle (1:N)
- Repuestos Solicitados → Ofertas Detalle (1:N)
- Ofertas Detalle → Adjudicaciones (1:1)

---

**Fecha de análisis:** 2025-11-08  
**Base de datos:** teloo_v3 en Docker (contenedor: teloo-postgres)
