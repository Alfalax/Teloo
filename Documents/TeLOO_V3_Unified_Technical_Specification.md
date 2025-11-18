# TeLOO V3 - Especificación Técnica Unificada
**Versión:** 3.0 Consolidada  
**Fecha:** 2025-01-11  
**Estado:** Documento de Referencia para Desarrollo  

## 🎯 Objetivo del Documento
Esta especificación unifica todos los documentos de TeLOO V3 en una sola referencia técnica completa. El sistema de orden de entrega de solicitudes a asesores utiliza **exclusivamente** la formulación del documento `Sistema_Orden_Entrega_Asesores_TeLOO.md`, reemplazando cualquier otra formulación encontrada en documentos previos.

---

## 📋 Índice
1. [Visión General del Sistema](#1-visión-general)
2. [Arquitectura y Stack Tecnológico](#2-arquitectura-y-stack)
3. [Modelo de Datos](#3-modelo-de-datos)
4. [Sistema de Orden de Entrega (Autoritativo)](#4-sistema-de-orden-de-entrega)
5. [Procesos de Negocio](#5-procesos-de-negocio)
6. [Sistema de Evaluación de Ofertas](#6-sistema-de-evaluación-de-ofertas)
7. [APIs y Contratos](#7-apis-y-contratos)
8. [Eventos del Sistema](#8-eventos-del-sistema)
9. [Interfaz de Usuario](#9-interfaz-de-usuario)
10. [Seguridad y Autenticación](#10-seguridad-y-autenticación)
11. [Observabilidad y Monitoreo](#11-observabilidad-y-monitoreo)
12. [Consideraciones de Rendimiento](#12-consideraciones-de-rendimiento)
13. [Manejo de Errores](#13-manejo-de-errores)
14. [Testing y QA](#14-testing-y-qa)
15. [Deployment y DevOps](#15-deployment-y-devops)

---

## 1. Visión General

### 1.1 Descripción del Sistema
TeLOO V3 es un **marketplace inteligente de repuestos automotrices** que actúa como intermediario automatizado entre clientes que necesitan repuestos y asesores/proveedores que los venden.

### 1.2 Innovación Clave
El sistema utiliza un **algoritmo de escalamiento automático por niveles geográficos** que:
- Optimiza la búsqueda priorizando asesores cercanos y de alta calidad
- Expande automáticamente la búsqueda si no hay cobertura local
- Evalúa ofertas mediante algoritmos transparentes y configurables
- Elimina el sesgo humano en la selección de proveedores

### 1.3 Componentes Principales

#### 🤖 Agente IA (WhatsApp Interface)
- Recibe solicitudes vía WhatsApp en múltiples formatos (texto, audio, Excel)
- Procesa información usando NLP para extraer datos estructurados
- Gestiona comunicación bidireccional con clientes
- Presenta ofertas ganadoras y maneja respuestas
- Administra PQR (Peticiones, Quejas y Reclamos)

#### 🏢 TeLOO Core Platform
- **Motor de Escalamiento**: Calcula niveles dinámicos de asesores (1-5) usando el algoritmo autoritativo
- **Distribuidor de Solicitudes**: Asigna solicitudes según algoritmos de proximidad
- **Motor de Evaluación**: Evalúa ofertas automáticamente con criterios configurables
- **Gestor de Estados**: Controla transiciones de solicitudes y ofertas
- **Sistema de Notificaciones**: Push notifications + fallback WhatsApp

#### 📊 Analytics Service (Microservicio Independiente)
- Captura eventos en tiempo real del Core Platform
- Procesa métricas de negocio sin Machine Learning (Fase 1)
- Genera dashboards con métricas básicas
- Proporciona alertas automáticas por umbrales simples

---

## 2. Arquitectura y Stack Tecnológico

### 2.1 Microservicios (MVP)

| Servicio | Responsabilidad | Tecnología | Público |
|----------|------------------|------------|---------|
| core-api | Solicitudes, ofertas, escalamiento, evaluación, adjudicación | FastAPI (Py 3.11), Tortoise ORM, Redis, PostgreSQL | No |
| agent-ia | Webhook WhatsApp, NLP ligero, normalización | FastAPI, modelo local u OpenAI opcional, Redis | **Sí** |
| analytics | Dashboards, ETL, caché | FastAPI, Pandas, Redis, PostgreSQL (replica) | No |
| realtime-gateway | WebSockets admin/asesor | FastAPI + Socket.IO, Redis adapter | **Sí** |
| files | Adjuntos (Excel), antivirus, firma, MinIO | FastAPI, MinIO (S3 local), clamd | No |
| admin-frontend | Backoffice | React + Vite + Tailwind + shadcn/ui | **Sí** |
| advisor-frontend | Panel asesor | React + Vite + Tailwind + shadcn/ui | **Sí** |

### 2.2 Infraestructura Compartida

| Componente | Tecnología | Uso |
|------------|------------|-----|
| DB | PostgreSQL | Datos transaccionales |
| Cache/Colas/Locks | Redis | Pub/Sub, RQ/Celery, locks distribuidos |
| Storage | MinIO (S3 local) | Archivos |
| Proxy | NGINX/Traefik | TLS, rutas |
| Observabilidad | Prometheus, Grafana, Loki, Sentry (self-hosted) | Métricas, logs, errores |
| CI/CD | GitHub Actions | Build/test/deploy |

### 2.3 Comunicación y Contratos
- **REST/JSON** (OpenAPI versionado)
- **Redis pub/sub** (eventos con JSON Schema)
- **WebSockets** (Redis adapter)

### 2.4 Compatibilidad Futura con Core Java
- Congelar **contratos REST + eventos**
- Migración paralela `core-java` (Spring Boot/Quarkus) con **canary release**
- Dominio desacoplado (hexagonal, puertos/adaptadores)

---

## 3. Modelo de Datos

### 3.1 Tablas Principales

```sql
-- Usuarios del sistema
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hash_password VARCHAR(255) NOT NULL,
    rol VARCHAR(50) NOT NULL CHECK (rol IN ('ADMIN', 'ADVISOR', 'ANALYST', 'SUPPORT', 'CLIENT')),
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO', 'SUSPENDIDO')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Asesores/Proveedores
CREATE TABLE asesores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id),
    ciudad_id INTEGER NOT NULL,
    confianza DECIMAL(3,2) DEFAULT 3.0 CHECK (confianza >= 1.0 AND confianza <= 5.0),
    inventario_30d DECIMAL(5,2) DEFAULT 0.0,
    t_resp_30d_min INTEGER DEFAULT 0,
    nivel_actual SMALLINT DEFAULT 3 CHECK (nivel_actual >= 1 AND nivel_actual <= 5),
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO', 'SUSPENDIDO')),
    actividad_reciente_pct DECIMAL(5,2) DEFAULT 0.0,
    desempeno_historico_pct DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Clientes
CREATE TABLE clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    ciudad_id INTEGER NOT NULL,
    direccion VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Solicitudes
CREATE TABLE solicitudes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    estado VARCHAR(50) NOT NULL DEFAULT 'ABIERTA',
    nivel_actual SMALLINT DEFAULT 1 CHECK (nivel_actual >= 1 AND nivel_actual <= 5),
    ciudad_origen VARCHAR(255) NOT NULL,
    departamento_origen VARCHAR(255) NOT NULL,
    metadata_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Repuestos solicitados
CREATE TABLE repuestos_solicitados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solicitud_id UUID NOT NULL REFERENCES solicitudes(id),
    nombre VARCHAR(255) NOT NULL,
    codigo VARCHAR(100),
    marca_vehiculo VARCHAR(100),
    linea_vehiculo VARCHAR(100),
    anio_vehiculo SMALLINT,
    cantidad INTEGER NOT NULL DEFAULT 1,
    observaciones TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ofertas
CREATE TABLE ofertas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solicitud_id UUID NOT NULL REFERENCES solicitudes(id),
    asesor_id UUID NOT NULL REFERENCES asesores(id),
    tiempo_entrega_dias SMALLINT NOT NULL CHECK (tiempo_entrega_dias >= 0 AND tiempo_entrega_dias <= 90),
    observaciones TEXT,
    estado VARCHAR(50) NOT NULL DEFAULT 'ENVIADA',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Detalle de ofertas
CREATE TABLE ofertas_detalle (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    oferta_id UUID NOT NULL REFERENCES ofertas(id),
    repuesto_solicitado_id UUID NOT NULL REFERENCES repuestos_solicitados(id),
    precio_unitario DECIMAL(10,2) NOT NULL CHECK (precio_unitario >= 1000 AND precio_unitario <= 50000000),
    cantidad INTEGER NOT NULL DEFAULT 1,
    garantia_meses SMALLINT NOT NULL CHECK (garantia_meses >= 1 AND garantia_meses <= 60),
    tiempo_entrega_dias SMALLINT NOT NULL CHECK (tiempo_entrega_dias >= 0 AND tiempo_entrega_dias <= 90),
    origen VARCHAR(20) DEFAULT 'FORM' CHECK (origen IN ('FORM', 'EXCEL')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Adjudicaciones por repuesto (nuevo sistema)
CREATE TABLE adjudicaciones_repuesto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solicitud_id UUID NOT NULL REFERENCES solicitudes(id),
    oferta_id UUID NOT NULL REFERENCES ofertas(id),
    repuesto_solicitado_id UUID NOT NULL REFERENCES repuestos_solicitados(id),
    puntaje_obtenido DECIMAL(3,2) NOT NULL,
    precio_adjudicado DECIMAL(10,2) NOT NULL,
    tiempo_entrega_adjudicado SMALLINT NOT NULL,
    garantia_adjudicada SMALLINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(solicitud_id, repuesto_solicitado_id)
);

-- Evaluaciones
CREATE TABLE evaluaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solicitud_id UUID NOT NULL REFERENCES solicitudes(id),
    parametros_json JSONB NOT NULL,
    resultado_json JSONB NOT NULL,
    duracion_ms INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ciudades
CREATE TABLE ciudades (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    departamento VARCHAR(255) NOT NULL,
    tipo_ciudad VARCHAR(50) NOT NULL CHECK (tipo_ciudad IN ('PRINCIPAL', 'SECUNDARIA', 'TERCIARIA', 'OTRA')),
    lat DECIMAL(10,8),
    lon DECIMAL(11,8)
);

-- Parámetros de configuración
CREATE TABLE parametros_config (
    clave VARCHAR(100) PRIMARY KEY,
    valor_json JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Logs de auditoría
CREATE TABLE logs_auditoria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NOT NULL REFERENCES usuarios(id),
    accion VARCHAR(100) NOT NULL,
    entidad VARCHAR(100) NOT NULL,
    entidad_id UUID,
    diff_json JSONB,
    ts TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PQR
CREATE TABLE pqr (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('PETICION', 'QUEJA', 'RECLAMO')),
    prioridad VARCHAR(50) NOT NULL CHECK (prioridad IN ('BAJA', 'MEDIA', 'ALTA', 'CRITICA')),
    estado VARCHAR(50) NOT NULL DEFAULT 'ABIERTA',
    resumen VARCHAR(255) NOT NULL,
    detalle TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3.2 Tablas de Soporte para Sistema de Orden de Entrega

```sql
-- Áreas Metropolitanas TeLOO
CREATE TABLE areas_metropolitanas_teloo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    area_metropolitana VARCHAR(255) NOT NULL,
    ciudad_nucleo VARCHAR(255) NOT NULL,
    municipio_norm VARCHAR(255) NOT NULL,
    UNIQUE(municipio_norm)
);

-- Asignación de Hubs
CREATE TABLE asignacion_hubs_200km (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    municipio_norm VARCHAR(255) NOT NULL,
    hub_asignado_norm VARCHAR(255) NOT NULL,
    UNIQUE(municipio_norm)
);

-- Evaluación temporal de asesores
CREATE TABLE evaluacion_asesores_temp (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solicitud_id UUID NOT NULL REFERENCES solicitudes(id),
    asesor_id UUID NOT NULL REFERENCES asesores(id),
    proximidad DECIMAL(3,2) NOT NULL,
    actividad_reciente_5 DECIMAL(3,2) NOT NULL,
    desempeno_historico_5 DECIMAL(3,2) NOT NULL,
    nivel_confianza DECIMAL(3,2) NOT NULL,
    puntaje_total DECIMAL(4,3) NOT NULL,
    nivel_entrega SMALLINT NOT NULL,
    canal VARCHAR(50) NOT NULL,
    tiempo_espera_min INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 4. Sistema de Orden de Entrega (Autoritativo)

### 4.1 Fórmula de Puntaje (Configurable)

```
puntaje_total = (proximidad × W1) + (actividad_reciente_5 × W2) + 
                (desempeño_histórico_5 × W3) + (nivel_confianza × W4)
```

**Pesos por defecto (configurables):**
- `W1 = peso_proximidad = 0.40` (40%)
- `W2 = peso_actividad = 0.25` (25%)
- `W3 = peso_desempeño = 0.20` (20%)
- `W4 = peso_confianza = 0.15` (15%)

**Rango de variables:** 1.0 a 5.0

### 4.2 Normalización de Variables

```
actividad_reciente_5 = 1 + 4 × (actividad_reciente_pct / 100)
desempeño_histórico_5 = 1 + 4 × (desempeño_histórico_pct / 100)
```

**Tratamiento de faltantes:**
- Si `actividad_reciente_pct` o `desempeño_histórico_pct` son nulos → usar **0** (→ 1.0)
- Si `nivel_confianza` nulo → usar **3.0**
- Si `proximidad` no calculable → usar **3.0**

### 4.3 Cálculo de Proximidad

**Valores de proximidad (configurables):**
- `prox_misma_ciudad = 5.0`
- `prox_AM_mismo_hub = 4.0`
- `prox_mismo_hub = 3.5`
- `prox_OTRA_AM_fuera_hub = 3.0`

**Algoritmo de proximidad:**
```pseudo
INPUT: ciudad_origen, depto_origen, asesor.ciudad, asesor.depto

# Normalización robusta
c0 = NORMALIZA(ciudad_origen); d0 = NORMALIZA(depto_origen)
cA = NORMALIZA(asesor.ciudad); dA = NORMALIZA(asesor.depto)

# Conjuntos de pertenencia
AM_ciudad_origen = MUNICIPIOS_DE_LA_MISMA_AM(c0)
HUB_ciudad_origen = MUNICIPIOS_DEL_MISMO_HUB(c0)
AM_asesor = MUNICIPIOS_DE_LA_MISMA_AM(cA)
HUB_asesor = MUNICIPIOS_DEL_MISMO_HUB(cA)

# Reglas (primera que cumple aplica)
IF cA == c0:
    proximidad = prox_misma_ciudad
ELSE IF (cA ∈ AM_ciudad_origen) AND (cA ∈ HUB_ciudad_origen):
    proximidad = prox_AM_mismo_hub
ELSE IF (cA ∈ HUB_ciudad_origen):
    proximidad = prox_mismo_hub
ELSE IF (AM_asesor ≠ ∅) AND (cA ∉ AM_ciudad_origen):
    proximidad = prox_OTRA_AM_fuera_hub
ELSE:
    proximidad = prox_OTRA_AM_fuera_hub

RETURN proximidad
```

### 4.4 Variables Adicionales

#### Actividad Reciente
- **Período:** 30 días (configurable)
- **Fórmula:** `actividad_reciente_% = (respuestas / enviadas) × 100`
- **Fuente:** `Historial_Respuestas_Ofertas`

#### Desempeño Histórico
- **Período:** 6 meses (configurable)
- **Submétricas:**
  - `tasa_adjudicación = (adjudicadas / enviadas) × 100`
  - `tasa_cumplimiento = (cumplidas / adjudicadas) × 100`
  - `eficiencia_respuesta = max(0, 1 - (t_promedio / tiempo_max)) × 100`
- **Fórmula:** `desempeño_% = 0.5×tasa_adjudicación + 0.3×tasa_cumplimiento + 0.2×eficiencia_respuesta`

#### Nivel de Confianza
- **Fuente:** `Auditoria_Tiendas` (servicio externo)
- **Rango:** 1-5 (1=Crítica, 5=Excelente)
- **Mínimo para operar:** 2.0 (configurable)

### 4.5 Niveles de Entrega

| Nivel | Rango de Puntaje | Canal | Tiempo Espera | Objetivo |
|-------|------------------|--------|---------------|----------|
| 1 | ≥ 4.5 | WhatsApp | 15 min | Prioridad máxima |
| 2 | 4.0 - 4.49 | WhatsApp | 20 min | Alta prioridad |
| 3 | 3.5 - 3.99 | Push | 25 min | Media |
| 4 | 3.0 - 3.49 | Push | 30 min | Respaldo |
| 5 | < 3.0 | N/A | 0 min | Reserva (sin envío) |

**Parámetros configurables:**
- `ofertas_minimas_deseadas = 2` (default)
- `tamano_oleada_max = 0` (0 = ilimitado)

### 4.6 Proceso de Escalamiento

```mermaid
flowchart TD
    A[Solicitud Creada] --> B[Asignar a Nivel 1]
    B --> C[Esperar tiempo nivel]
    C --> D{¿Ofertas mínimas?}
    D -->|0 ofertas| E[Escalar a Nivel 2]
    D -->|1 oferta| F[Escalar 1 nivel más]
    D -->|2+ ofertas| G[Proceder a Evaluación]
    F --> H[Esperar tiempo siguiente nivel]
    H --> I{¿2ª oferta?}
    I -->|Sí| G
    I -->|No| J[Evaluar con 1 oferta]
    E --> K[Repetir hasta Nivel 5]
    K --> L{¿Ofertas en N5?}
    L -->|Sí| G
    L -->|No| M[CERRADA_SIN_OFERTAS]
```

### 4.7 Reglas de Desempate

1. **Mayor nivel_confianza** (si `prioridad_confianza=true`)
2. **Mayor actividad_reciente_5** (si `prioridad_actividad=true`)
3. **Menor tiempo de respuesta reciente** (si disponible)
4. **Aleatorio estable** (seed por `solicitud_id`)

---

## 5. Procesos de Negocio

### 5.1 Flujo Completo del Proceso

#### FASE 1: Iniciación de Solicitud

**Información requerida:**
- **Repuestos:** Nombre específico o lista múltiple (soporta Excel)
- **Vehículo:** Marca, línea, año modelo
- **Cliente:** Nombre, teléfono, ciudad, dirección

**Procesamiento por Agente IA:**
```mermaid
graph LR
    A[Mensaje WhatsApp] --> B[Agente IA NLP]
    B --> C[Extracción Datos]
    C --> D[Validación]
    D --> E{¿Completos?}
    E -->|No| F[Solicitar Aclaraciones]
    E -->|Sí| G[Estructurar JSON]
    F --> B
    G --> H[Enviar a Core API]
```

**Validaciones automáticas:**
- Teléfono: Formato colombiano +57XXXXXXXXXX
- Ciudad: Debe existir en catálogo
- Año vehículo: Rango 1980-2025
- Nombre: 2-100 caracteres, solo letras y espacios

#### FASE 2: Escalamiento Inteligente

**El sistema calcula niveles dinámicos para cada solicitud:**
1. Recálculo completo de todos los asesores
2. Asignación a niveles 1-5 según puntaje
3. Ejecución por oleadas con tiempos configurables
4. Cierre anticipado al alcanzar 2 ofertas mínimas

#### FASE 3: Proceso de Ofertas

**Notificación a asesores:**
```
🔔 Nueva Solicitud Disponible
📋 Pastillas de freno Toyota Corolla 2015
📍 Bogotá, Cundinamarca
⏰ Tiempo restante: 28 minutos
💰 Haz tu oferta ahora
```

**Campos obligatorios de oferta:**
```json
{
  "oferta": {
    "repuestos": [
      {
        "repuesto_solicitud_id": "123",
        "precio_unitario": 85000,
        "cantidad": 1,
        "garantia_meses": 6
      }
    ],
    "tiempo_entrega_dias": 2,
    "observaciones": "Pastillas originales Toyota"
  }
}
```

**Ofertas parciales:**
- ✅ **Permitidas y fomentadas**
- No es obligatorio ofertar todos los repuestos
- Pueden existir múltiples ganadores
- Prioridad por cobertura, luego por puntaje

#### FASE 4: Evaluación Automática de Ofertas

**Trigger de evaluación:**
- Se cumple tiempo del nivel actual
- Se reciben 2+ ofertas
- Administrador fuerza evaluación

**Algoritmo de evaluación por repuesto:**
```
Puntaje_Final = (Puntaje_Precio × 0.50) + 
                (Puntaje_Tiempo × 0.35) + 
                (Puntaje_Garantía × 0.15)
```

**Regla de adjudicación:**
- **Cobertura mínima:** 50% de los repuestos
- **Adjudicación por cascada:** Si la mejor no cumple 50%, sigue con la siguiente
- **Excepción:** Si es la única oferta para un repuesto, se adjudica sin importar cobertura

#### FASE 5: Comunicación de Resultados

**Para oferta única:**
```
🎉 ¡Tenemos una oferta para tu solicitud!
📋 Solicitud: Pastillas de freno Toyota Corolla 2015
💰 Precio: $78,000
⏰ Tiempo: 1 día
🛡️ Garantía: 3 meses
🏪 Proveedor: AutoPartes Medellín

¿Aceptas? Responde SÍ o NO
```

**Para oferta mixta:**
```
🎉 ¡Oferta mixta disponible!
📋 8 repuestos para Toyota Corolla 2015
👥 2 asesores especializados
📦 7 de 8 repuestos disponibles
💰 Total: $245,000
⏰ Máximo: 2 días

¿Aceptas? Responde SÍ, NO o DETALLES
```

#### FASE 6: Estados Finales

- **ACEPTADA:** Cliente aceptó, comunicación directa establecida
- **RECHAZADA:** Cliente rechazó la oferta
- **EXPIRADA:** Cliente no respondió en tiempo límite (20h default)
- **CERRADA_SIN_OFERTAS:** No se encontraron oferentes

---

## 6. Sistema de Evaluación de Ofertas

### 6.1 Estados Simplificados

| Estado | Descripción | Visible Para | Acciones |
|--------|-------------|---------------|----------|
| ENVIADA | Oferta enviada, esperando evaluación | Asesor | Modificar (si está en tiempo) |
| GANADORA | Gana al menos un repuesto | Asesor, Cliente | Aceptar/Rechazar (Cliente) |
| NO_SELECCIONADA | No gana ningún repuesto | Asesor | Ver detalles |
| EXPIRADA | Cliente no responde en 20h | Asesor, Cliente | Solo consulta |
| RECHAZADA | Cliente rechaza oferta | Asesor, Cliente | Solo consulta |
| ACEPTADA | Cliente acepta oferta | Asesor, Cliente | Procesar pedido |

### 6.2 Algoritmo de Evaluación

```mermaid
flowchart TD
    A[Solicitud con N repuestos] --> B[Para cada repuesto]
    B --> C[Evaluar todas las ofertas disponibles]
    C --> D[Aplicar fórmula de puntuación]
    D --> E[Ordenar por puntaje descendente]
    E --> F[Tomar primera oferta]
    F --> G{¿Cobertura ≥50%?}
    G -->|Sí| H[Adjudicar repuesto]
    G -->|No| I{¿Es única oferta?}
    I -->|Sí| J[Adjudicar por excepción]
    I -->|No| K[No adjudicar]
    H --> L[Continuar con siguiente]
    J --> L
    K --> L
    L --> M{¿Quedan repuestos?}
    M -->|Sí| B
    M -->|No| N[Generar resultado final]
```

### 6.3 Cálculo de Puntajes

**Puntaje de Precio:**
```
mejor_precio = MIN(todos_los_precios_ofertas)
diferencia_porcentual = ((precio_oferta - mejor_precio) / mejor_precio) × 100

Puntaje_Precio = CASE
  WHEN diferencia_porcentual ≤ 5% THEN 5
  WHEN diferencia_porcentual ≤ 8% THEN 3
  ELSE 1
END
```

**Puntaje de Tiempo:**
```
Puntaje_Tiempo = CASE
  WHEN dias_entrega ≤ 0 THEN 5  -- Mismo día
  WHEN dias_entrega ≤ 3 THEN 3
  ELSE 1
END
```

**Puntaje de Garantía:**
```
Puntaje_Garantia = CASE
  WHEN meses_garantia > 3 THEN 5
  WHEN meses_garantia ≥ 1 THEN 3
  ELSE 1
END
```

### 6.4 Parámetros Configurables

| Parámetro | Valor Default | Descripción |
|-----------|---------------|-------------|
| PESO_PRECIO | 50% | Importancia del precio |
| PESO_TIEMPO | 35% | Importancia del tiempo de entrega |
| PESO_GARANTIA | 15% | Importancia de la garantía |
| COBERTURA_MINIMA | 50% | % mínimo de cobertura para adjudicar |
| TIMEOUT_RESPUESTA_CLIENTE | 20h | Tiempo límite para respuesta |
| TIMEOUT_EVALUACION | 5min | Tiempo máximo para evaluación |

---

## 7. APIs y Contratos

### 7.1 Core API Endpoints

#### Autenticación
```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "asesor@example.com",
  "password": "secure_password"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

#### Solicitudes
```http
POST /v1/solicitudes
Authorization: Bearer {token}
Content-Type: application/json

{
  "cliente": {
    "nombre": "Juan Pérez",
    "telefono": "+573001234567",
    "ciudad_id": 1,
    "direccion": "Calle 123 #45-67"
  },
  "repuestos": [
    {
      "nombre": "Pastillas de freno delanteras",
      "codigo": "BP001",
      "marca_vehiculo": "Toyota",
      "linea_vehiculo": "Corolla",
      "anio_vehiculo": 2015,
      "cantidad": 1,
      "observaciones": "Originales preferiblemente"
    }
  ]
}
```

#### Ofertas
```http
POST /v1/ofertas
Authorization: Bearer {token}
Content-Type: application/json

{
  "solicitud_id": "550e8400-e29b-41d4-a716-446655440000",
  "tiempo_entrega_dias": 2,
  "observaciones": "Productos originales Toyota",
  "repuestos": [
    {
      "repuesto_solicitado_id": "660e8400-e29b-41d4-a716-446655440000",
      "precio_unitario": 85000,
      "cantidad": 1,
      "garantia_meses": 6
    }
  ]
}
```

#### Evaluación
```http
POST /v1/evaluaciones/{solicitud_id}/run
Authorization: Bearer {token}

Response:
{
  "solicitud_id": "550e8400-e29b-41d4-a716-446655440000",
  "estado": "EVALUADA",
  "adjudicaciones": [
    {
      "repuesto_id": "660e8400-e29b-41d4-a716-446655440000",
      "oferta_id": "770e8400-e29b-41d4-a716-446655440000",
      "asesor_id": "880e8400-e29b-41d4-a716-446655440000",
      "precio_adjudicado": 78000,
      "tiempo_entrega_adjudicado": 1,
      "garantia_adjudicada": 3,
      "puntaje_obtenido": 4.5
    }
  ]
}
```

### 7.2 Agent IA Endpoints

```http
POST /v1/webhooks/whatsapp
Content-Type: application/json

{
  "message": {
    "from": "573001234567",
    "text": "Hola, necesito pastillas de freno para Toyota Corolla 2015",
    "timestamp": "2025-01-11T10:30:00Z"
  }
}
```

### 7.3 Analytics Endpoints

```http
GET /v1/dashboards/funnel
GET /v1/dashboards/market-health
GET /v1/dashboards/finance
GET /v1/dashboards/advisors
```

---

## 8. Eventos del Sistema

### 8.1 Eventos Redis Pub/Sub

| Canal | Descripción | Payload Ejemplo |
|-------|-------------|-----------------|
| `solicitud.created` | Nueva solicitud creada | `{ solicitud_id, nivel_inicial, ciudad }` |
| `solicitud.escalated` | Solicitud escalada de nivel | `{ solicitud_id, nuevo_nivel }` |
| `oferta.created` | Nueva oferta registrada | `{ solicitud_id, oferta_id, asesor_id }` |
| `evaluacion.completed` | Evaluación finalizada | `{ solicitud_id, adjudicaciones, ts }` |
| `cliente.accepted` | Cliente aceptó oferta | `{ solicitud_id, adjudicaciones, ts }` |
| `cliente.rejected` | Cliente rechazó oferta | `{ solicitud_id }` |
| `timeout.triggered` | Timeout de nivel alcanzado | `{ solicitud_id, tipo, nivel }` |
| `asesor.level.recalculated` | Nivel de asesor recalculado | `{ asesor_id, nivel_calculado, fecha }` |
| `oferta.bulk_uploaded` | Oferta masiva cargada | `{ solicitud_id, asesor_id, n_detalles, ts }` |
| `oferta.bulk_error` | Error en carga masiva | `{ solicitud_id, asesor_id, errores }` |

### 8.2 WebSocket Events

```javascript
// Cliente se conecta
ws.emit('join', { user_id: 'asesor_123', role: 'advisor' });

// Nuevas ofertas en tiempo real
ws.on('oferta nueva', (data) => {
  console.log('Nueva oferta:', data);
});

// Cambios en solicitudes
ws.on('solicitud actualizada', (data) => {
  console.log('Solicitud actualizada:', data);
});
```

---

## 9. Interfaz de Usuario

### 9.1 Admin Frontend

**Dashboard Principal:**
- Métricas en tiempo real (29 KPIs)
- Gestión de asesores y configuraciones
- Monitoreo de solicitudes y evaluaciones
- Panel de PQR y auditoría

**Configuración de Parámetros:**
```javascript
// Ejemplo de configuración de pesos
const parametros = {
  // Sistema de orden de entrega
  peso_proximidad: 0.40,
  peso_actividad: 0.25,
  peso_desempeno: 0.20,
  peso_confianza: 0.15,
  
  // Umbrales de nivel
  nivel1_min: 4.5,
  nivel2_min: 4.0,
  nivel3_min: 3.5,
  nivel4_min: 3.0,
  
  // Tiempos de espera
  nivel1_tiempo: 15,
  nivel2_tiempo: 20,
  nivel3_tiempo: 25,
  nivel4_tiempo: 30,
  
  // Sistema de evaluación
  peso_precio: 0.50,
  peso_tiempo: 0.35,
  peso_garantia: 0.15,
  cobertura_minima: 0.50
};
```

### 9.2 Advisor Frontend

**Panel de Asesor:**
- Lista de solicitudes disponibles
- Formulario de ofertas (individual y masiva por Excel)
- Historial de ofertas y adjudicaciones
- Notificaciones en tiempo real

**Carga Masiva Excel:**
```javascript
// Descargar template
GET /v1/ofertas/{solicitud_id}/template

// Subir Excel completado
POST /v1/ofertas/upload
Content-Type: multipart/form-data

// Validaciones en frontend
- Archivo .xlsx, < 5MB
- Validación de rangos de precios, garantía, tiempo
- Preview de datos antes de enviar
```

---

## 10. Seguridad y Autenticación

### 10.1 OAuth2 + JWT (Local)
- **Tokens:** Access (15min), Refresh (7d)
- **Algoritmo:** RS256 con JWKS interno
- **RBAC:** Roles por acción: ADMIN, ADVISOR, ANALYST, SUPPORT, CLIENT

### 10.2 Matriz de Permisos

| Acción / Recurso | ADMIN | ADVISOR | ANALYST | SUPPORT | CLIENT |
|-------------------|-------|---------|---------|---------|--------|
| CRUD asesores | ✅ | R | R | R | ❌ |
| Crear ofertas | R | ✅ | ❌ | ❌ | ❌ |
| Ver solicitudes | ✅ | R | R | R | vía WhatsApp |
| Forzar evaluación | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver dashboards | ✅ | R | ✅ | R | ❌ |

### 10.3 Seguridad de Datos
- **TLS end-to-end** (HTTPS/WSS)
- **CORS restringido** por dominio
- **Rate limiting:** 100 req/min/IP
- **Validación estricta** con Pydantic/Pydantic
- **Sanitización de archivos** con ClamAV
- **PII cifrada** en tránsito y reposo

---

## 11. Observabilidad y Monitoreo

### 11.1 SLOs (Service Level Objectives)

| Servicio | Métrica | Objetivo |
|----------|---------|----------|
| core-api | Disponibilidad | ≥ 99.5% |
| core-api | Latencia p95 | < 300ms |
| Evaluación | Tiempo máximo | < 5s |
| Redis | Disponibilidad | ≥ 99.9% |
| Cache | Hit rate | ≥ 80% |

### 11.2 Alertas

| Alerta | Umbral | Tiempo |
|--------|--------|--------|
| Error rate | > 1% | 5 min |
| Latencia p95 | > SLO | 10 min |
| Cola de trabajos | > N pendientes | 5 min |
| Cache hit rate | < 80% | 5 min |
| CPU usage | > 80% | 10 min |
| WebSocket disconnections | > 20% | 5 min |

### 11.3 Stack de Observabilidad
- **Prometheus:** Métricas
- **Grafana:** Dashboards y alertas
- **Loki:** Logs agregados
- **Sentry:** Gestión de errores
- **OpenTelemetry:** Trazas distribuidas

---

## 12. Consideraciones de Rendimiento

### 12.1 Optimizaciones
- **Batch processing** para cálculos de asesores
- **Caching** de AM/HUB por ciudad (TTL 15min)
- **Índices** en campos de búsqueda frecuente
- **Paginación** en listados grandes
- **Connection pooling** en base de datos

### 12.2 Objetivos de Performance

| Operación | Objetivo p95 |
|-----------|--------------|
| GET /v1/solicitudes | < 250ms |
| POST /v1/ofertas | < 300ms |
| Evaluación completa | < 5s |
| WebSocket latency | < 100ms |

### 12.3 Escalabilidad
- **Horizontal:** Microservicios stateless
- **Vertical:** Workers async para procesamiento pesado
- **Cache:** Redis con cluster mode
- **DB:** Replicación read-only para analytics

---

## 13. Manejo de Errores

### 13.1 Códigos de Error Estándar

```json
{
  "type": "https://teloo.app/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "El campo precio_unitario debe estar entre 1000 y 50000000",
  "instance": "/v1/ofertas",
  "timestamp": "2025-01-11T10:30:00Z"
}
```

### 13.2 Casos Edge

**Ciudad fuera de AM y HUB:**
- Asignar `prox_OTRA_AM_fuera_hub`
- Log de advertencia
- Continuar con proceso normal

**Métricas faltantes:**
- Usar valores por defecto (1.0 para actividad/desempeño, 3.0 para confianza)
- Marcar `asesor_incompleto=true`
- Notificar a administrador si es crítico

**Ofertas durante evaluación:**
- Rechazar con estado 409 Conflict
- Mensaje: "Evaluación en progreso"

**Caída de WhatsApp API:**
- Circuit breaker con 3 intentos
- Fallback a cola de mensajes pendientes
- Retry exponencial: 1min, 5min, 15min, 1h

---

## 14. Testing y QA

### 14.1 Estrategia de Testing

| Tipo | Herramienta | Alcance |
|------|-------------|---------|
| Unitarios | pytest | Reglas de negocio, cálculos |
| Integración | testcontainers | DB, Redis, colas |
| Contratos | Pact | APIs REST y eventos |
| E2E | Cypress/Playwright | Flujos completos UI |
| Carga | k6/Locust | 200-500 usuarios concurrentes |

### 14.2 Casos de Prueba Críticos

**Sistema de Orden de Entrega:**
- ✅ Cálculo correcto de proximidad para todas las combinaciones
- ✅ Normalización de variables con valores límite
- ✅ Empates resueltos por reglas de desempate
- ✅ Escalamiento hasta nivel 5 sin ofertas
- ✅ Cierre anticipado con 2 ofertas mínimas

**Evaluación de Ofertas:**
- ✅ Adjudicación con 1 oferta (excepción única)
- ✅ Adjudicación múltiple con cobertura ≥50%
- ✅ Regla de cascada cuando mejor oferta <50%
- ✅ Repuestos sin cubrir cuando ninguna cumple
- ✅ Concurrencia: ofertas durante evaluación

**Carga Masiva Excel:**
- ✅ Archivo válido procesado correctamente
- ✅ Validación de rangos y tipos de datos
- ✅ Archivo de errores generado con detalles
- ✅ Límites de tamaño y formato respetados

---

## 15. Deployment y DevOps

### 15.1 Pipeline CI/CD

```yaml
# Ejemplo de pipeline GitHub Actions
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pytest tests/unit
          pytest tests/integration
          pytest tests/contract
      
  build:
    needs: test
    steps:
      - name: Build Docker images
        run: |
          docker build -t teloo/core-api:${{ github.sha }} .
          docker build -t teloo/agent-ia:${{ github.sha }} .
      
      - name: Security scan
        run: trivy image teloo/core-api:${{ github.sha }}
      
  deploy:
    needs: build
    steps:
      - name: Deploy to staging
        run: |
          kubectl set image deployment/core-api core-api=teloo/core-api:${{ github.sha }}
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Deploy to production
        run: |
          kubectl set image deployment/core-api core-api=teloo/core-api:${{ github.sha }}
```

### 15.2 Entornos

| Entorno | Orquestación | Dominio | Propósito |
|---------|--------------|---------|-----------|
| local | Docker Compose | localhost | Desarrollo individual |
| staging | Docker Swarm | staging.teloo.local | QA/UAT |
| production | Kubernetes | *.teloo.app | Producción alta disponibilidad |

### 15.3 Variables de Configuración

```bash
# Core API
TELOO_CORE_DB_URL=postgresql+asyncpg://user:pass@postgres:5432/teloo
TELOO_CORE_REDIS_URL=redis://redis:6379/0
TELOO_JWT_PRIVATE_KEY_PATH=/secrets/jwt_private.pem
TELOO_JWKS_URL=https://auth.teloo.app/.well-known/jwks.json

# Timeouts
TELOO_TIMEOUT_NIVEL_MIN=30
TELOO_EVAL_TIMEOUT_MS=300000
TELOO_TIMEOUT_RESPUESTA_CLIENTE=20h

# Pesos del sistema
TELOO_PESO_PROXIMIDAD=0.40
TELOO_PESO_ACTIVIDAD=0.25
TELOO_PESO_DESEMPENO=0.20
TELOO_PESO_CONFIANZA=0.15

# Storage
TELOO_MINIO_ENDPOINT=http://minio:9000
TELOO_MINIO_ACCESS_KEY=teloo
TELOO_MINIO_SECRET_KEY=********
```

### 15.4 Backup y Recuperación

| Activo | Frecuencia | Retención | Ubicación |
|--------|------------|-----------|-----------|
| PostgreSQL (dump + WAL) | 6h | 30-90 días | Disco + Remoto |
| MinIO (buckets) | Diario | 30-90 días | NFS/Obj Store |
| Configuración | Diario | 30 días | Git + Backup cifrado |
| Redis (RDB) | 2h | 7 días | Disco rápido |

---

## 📋 Checklist de Implementación

### Fase 0: Infraestructura Base
- [ ] Repositorios y CI/CD configurados
- [ ] Docker Compose para desarrollo local
- [ ] Esqueletos de microservicios
- [ ] Base de datos y migraciones

### Fase 1: Core y Autenticación
- [ ] OAuth2/JWT local implementado
- [ ] RBAC con roles y permisos
- [ ] CRUD de asesores y ciudades
- [ ] WebSocket authentication

### Fase 2: Solicitudes y Escalamiento
- [ ] Creación de solicitudes con validación
- [ ] Algoritmo de orden de entrega (autoritativo)
- [ ] Sistema de niveles y oleadas
- [ ] Eventos Redis pub/sub

### Fase 3: Ofertas y Evaluación
- [ ] Sistema de ofertas con estados simplificados
- [ ] Evaluación por repuesto individual
- [ ] Regla de cascada ≥50% implementada
- [ ] Adjudicaciones y auditoría

### Fase 4: Interfaces y Tiempo Real
- [ ] Admin frontend con dashboards
- [ ] Advisor frontend con notificaciones
- [ ] Carga masiva Excel de ofertas
- [ ] WebSockets para tiempo real

### Fase 5: Analytics y Monitoreo
- [ ] Servicio de analytics con 29 KPIs
- [ ] Dashboards configurables
- [ ] Sistema de alertas
- [ ] Logs centralizados

### Fase 6: Seguridad y Performance
- [ ] Rate limiting y CORS
- [ ] Escaneo de vulnerabilidades
- [ ] Tests de carga con k6
- [ ] Optimización de queries

### Fase 7: Testing Completo
- [ ] Tests unitarios >80% cobertura
- [ ] Tests de integración de APIs
- [ ] Tests E2E de flujos críticos
- [ ] Validación de reglas de negocio

### Fase 8: Documentación y Deployment
- [ ] Documentación API (OpenAPI)
- [ ] Guías de deployment
- [ ] Runbooks de operación
- [ ] Manual de usuario

---

## 🔗 Referencias y Enlaces

### Documentos Fuente
- [Sistema_Orden_Entrega_Asesores_TeLOO.md](./Sistema_Orden_Entrega_Asesores_TeLOO.md) - **Fórmula autoritativa de orden de entrega**
- [Procesos_Negocio_TELOO_V3.md](./Procesos_Negocio_TELOO_V3.md) - Flujos de negocio detallados
- [Especificacion_Simplificacion_Evaluacion_Ofertas_V3.md](./Especificacion_Simplificacion_Evaluacion_Ofertas_V3.md) - Sistema de evaluación simplificado
- [Plan_Tecnico_Implementacion_TELOO_V1.5.md](./Plan_Tecnico_Implementacion_TELOO_V1.5.md) - Arquitectura técnica y stack

### Recursos Técnicos
- [OpenAPI Specification](https://swagger.io/specification/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Commands](https://redis.io/commands)

---

## 📝 Notas Finales

Este documento representa la especificación técnica completa y unificada de TeLOO V3. **El sistema de orden de entrega utiliza exclusivamente la formulación del documento `Sistema_Orden_Entrega_Asesores_TeLOO.md`**, con proximidad (40%), actividad reciente (25%), desempeño histórico (20%) y nivel de confianza (15%).

Cualquier discrepancia con formulaciones anteriores en otros documentos debe resolverse utilizando esta especificación como fuente autoritativa.

**Versión:** 3.0 Consolidada  
**Última actualización:** 2025-01-11  
**Estado:** Listo para desarrollo