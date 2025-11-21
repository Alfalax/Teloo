# Implementación: Notificación al Cliente Post-Evaluación

## 📋 Resumen

Se implementó el flujo completo de notificación al cliente después de que el sistema evalúa las ofertas ganadoras, incluyendo generación de PDF profesional, envío de mensaje personalizado, detección de respuestas con NLP y manejo de aceptación/rechazo parcial.

## 🎯 Componentes Implementados

### 1. **PDF Generator Service** (`services/core-api/services/pdf_generator_service.py`)

Genera documentos PDF profesionales con las ofertas ganadoras.

**Características:**
- Tabla con ofertas ganadoras (repuesto, asesor, precio, entrega, garantía)
- Información del cliente y vehículo
- Cálculo de métricas (asesores contactados, ahorro obtenido)
- Diseño profesional con colores corporativos
- Formato optimizado para WhatsApp/Telegram

**Funciones principales:**
```python
generar_pdf_ofertas_ganadoras(solicitud_id) -> BytesIO
calcular_metricas_ofertas(solicitud_id) -> Dict[str, Any]
```

### 2. **Notificación Cliente Service** (`services/core-api/services/notificacion_cliente_service.py`)

Gestiona el envío de notificaciones al cliente.

**Características:**
- Genera PDF con ofertas ganadoras
- Crea mensaje personalizado con métricas
- Publica evento a Redis para Agent IA
- Envía recordatorios (intermedio y final)
- Maneja timeout automático

**Mensaje personalizado incluye:**
```
📋 Solicitaste nuestra ayuda para encontrar las mejores ofertas y en TeLOO lo hemos conseguido.

📊 Resultados:
• Contactamos X asesores de repuestos
• Ahorro obtenido: $X,XXX (XX%)

📎 [Adjunto: Propuesta_SOL-XXX.pdf]

Revisa el detalle de cada oferta y dinos qué piensas.

💰 Total: $XX,XXX
⏰ Tienes 24 horas para responder
```

**Funciones principales:**
```python
notificar_ofertas_ganadoras(solicitud_id, redis_client) -> Dict[str, Any]
enviar_recordatorio(solicitud_id, tipo_recordatorio, redis_client) -> Dict[str, Any]
```

### 3. **Respuesta Cliente Service** (`services/core-api/services/respuesta_cliente_service.py`)

Procesa las respuestas del cliente usando detección de intención.

**Características:**
- Detección de intención simple (regex patterns)
- Soporte para NLP con GPT-4 (preparado para integración)
- Aceptación/rechazo total
- Aceptación/rechazo parcial por repuesto
- Actualización automática de estados de ofertas
- Registro de eventos

**Intenciones soportadas:**
- `"acepto"` → Aceptar todas las ofertas
- `"rechazo"` → Rechazar todas
- `"acepto 1,3,5"` → Aceptar repuestos específicos
- `"rechazo 2"` → Rechazar repuestos específicos

**Funciones principales:**
```python
procesar_respuesta(solicitud_id, respuesta_texto, usar_nlp) -> Dict[str, Any]
```

### 4. **Endpoint de Respuesta** (`services/core-api/routers/solicitudes.py`)

Endpoint REST para recibir respuestas del cliente.

```http
POST /v1/solicitudes/{solicitud_id}/respuesta-cliente
Authorization: X-API-Key: {service_api_key}

{
  "respuesta_texto": "acepto 1,3",
  "usar_nlp": true
}
```

**Response:**
```json
{
  "success": true,
  "solicitud_id": "uuid",
  "tipo_respuesta": "aceptacion_parcial",
  "mensaje": "Has aceptado 2 repuesto(s). Los asesores te contactarán pronto.",
  "repuestos_aceptados": ["Pastillas de freno", "Filtro de aceite"],
  "repuestos_rechazados": ["Bujías"]
}
```

### 5. **Jobs Programados** (`services/core-api/jobs/scheduled_jobs.py`)

Dos nuevos jobs para automatización:

#### Job 1: `notificar_clientes_ofertas_ganadoras()`
- **Frecuencia:** Cada 5 minutos
- **Función:** Busca solicitudes EVALUADAS sin notificar y envía PDF + mensaje
- **Trigger:** Después de evaluación automática

#### Job 2: `enviar_recordatorios_cliente()`
- **Frecuencia:** Cada hora
- **Función:** Envía recordatorios y maneja timeouts
- **Recordatorios:**
  - Intermedio: 12 horas después de notificación
  - Final: 23 horas después de notificación
  - Timeout: 24 horas → Auto-rechazo

### 6. **Modelo de Datos** (`services/core-api/models/solicitud.py`)

Nuevos campos agregados al modelo `Solicitud`:

```python
# Timestamps
fecha_notificacion_cliente = DatetimeField(null=True)
fecha_respuesta_cliente = DatetimeField(null=True)

# Response tracking
cliente_acepto = BooleanField(null=True)  # True=accepted, False=rejected, None=no response
respuesta_cliente_texto = TextField(null=True)
```

## 🔄 Flujo Completo

```
1. Sistema evalúa ofertas
   ↓
2. Job detecta solicitud EVALUADA sin notificar
   ↓
3. Genera PDF con ofertas ganadoras
   ↓
4. Calcula métricas (asesores, ahorro)
   ↓
5. Genera mensaje personalizado
   ↓
6. Publica evento a Redis → Agent IA
   ↓
7. Agent IA envía PDF + mensaje por WhatsApp/Telegram
   ↓
8. Cliente responde (acepto/rechazo)
   ↓
9. Agent IA llama endpoint /respuesta-cliente
   ↓
10. Sistema detecta intención y procesa
    ↓
11. Actualiza estados de ofertas (ACEPTADA/RECHAZADA)
    ↓
12. Registra eventos para analytics
    ↓
13. Notifica asesores ganadores
```

## ⏰ Sistema de Recordatorios

```
Hora 0: Notificación inicial con PDF
   ↓
Hora 12: Recordatorio intermedio
   "⏰ Recordatorio: Tienes ofertas pendientes..."
   ↓
Hora 23: Recordatorio final
   "⚠️ ÚLTIMA HORA para responder..."
   ↓
Hora 24: Timeout automático
   - Auto-rechazo de todas las ofertas
   - Notificación al cliente
   - Cierre de solicitud
```

## 📊 Métricas Calculadas

El sistema calcula automáticamente:

1. **Asesores contactados:** Número único de asesores que presentaron ofertas
2. **Ahorro obtenido:** Diferencia entre precio máximo y precio ganador por repuesto
3. **Porcentaje de ahorro:** (Ahorro / Precio original) * 100
4. **Monto total:** Suma de precios adjudicados

## 🗄️ Migración de Base de Datos

Script SQL: `scripts/add_client_response_fields.sql`

```sql
ALTER TABLE solicitudes ADD COLUMN fecha_notificacion_cliente TIMESTAMP NULL;
ALTER TABLE solicitudes ADD COLUMN fecha_respuesta_cliente TIMESTAMP NULL;
ALTER TABLE solicitudes ADD COLUMN cliente_acepto BOOLEAN NULL;
ALTER TABLE solicitudes ADD COLUMN respuesta_cliente_texto TEXT NULL;

-- Índice para consultas eficientes
CREATE INDEX idx_solicitudes_pending_response 
ON solicitudes(estado, fecha_notificacion_cliente, fecha_respuesta_cliente)
WHERE fecha_notificacion_cliente IS NOT NULL 
  AND fecha_respuesta_cliente IS NULL;
```

## 🧪 Testing

Script de prueba: `test_notificacion_cliente_flow.py`

**Tests incluidos:**
1. ✅ Generación de PDF
2. ✅ Cálculo de métricas
3. ✅ Generación de mensaje
4. ✅ Detección de intención
5. ✅ Procesamiento de respuestas (dry run)

**Ejecutar tests:**
```bash
python test_notificacion_cliente_flow.py
```

## 📝 Configuración

Parámetro agregado a `parametros_generales`:

```json
{
  "timeout_ofertas_horas": 20
}
```

**Nota:** Se reutiliza el parámetro existente `timeout_ofertas_horas` del dashboard administrativo en lugar de crear uno nuevo.

Configurable desde el dashboard administrativo.

## 🔗 Integración con Agent IA

El sistema publica eventos a Redis que Agent IA consume:

### Evento 1: Notificación de ofertas
```json
{
  "tipo_evento": "cliente.notificar_ofertas_ganadoras",
  "solicitud_id": "uuid",
  "codigo_solicitud": "SOL-ABC123",
  "cliente_telefono": "+57304888XXXX",
  "cliente_nombre": "Fernando Hernández",
  "mensaje": "...",
  "pdf_filename": "Propuesta_SOL-ABC123.pdf",
  "metricas": {...},
  "timeout_horas": 24
}
```

### Evento 2: Recordatorio
```json
{
  "tipo_evento": "cliente.recordatorio_ofertas",
  "solicitud_id": "uuid",
  "tipo_recordatorio": "intermedio|final",
  "mensaje": "..."
}
```

### Evento 3: Timeout
```json
{
  "tipo_evento": "cliente.timeout_respuesta",
  "solicitud_id": "uuid",
  "mensaje": "El tiempo para responder ha expirado..."
}
```

## 🚀 Despliegue

### 1. Aplicar migración
```bash
psql -U teloo_user -d teloo_db -f scripts/add_client_response_fields.sql
```

### 2. Reiniciar servicios
```bash
docker-compose restart core-api
```

### 3. Verificar jobs programados
Los jobs se ejecutan automáticamente según el scheduler configurado en `scheduler_service.py`.

### 4. Monitorear logs
```bash
docker-compose logs -f core-api | grep -E "(notificar|recordatorio|respuesta)"
```

## 📈 Próximos Pasos

1. **Integración NLP avanzada:** Conectar con GPT-4 para detección de intención más robusta
2. **Dashboard de métricas:** Visualizar tasas de aceptación/rechazo
3. **A/B Testing:** Probar diferentes formatos de mensaje
4. **Personalización:** Mensajes adaptados por segmento de cliente
5. **Multi-idioma:** Soporte para inglés y otros idiomas

## 🐛 Troubleshooting

### PDF no se genera
- Verificar que `reportlab` esté instalado: `pip install reportlab`
- Verificar que la solicitud tenga adjudicaciones

### Cliente no recibe notificación
- Verificar que Redis esté corriendo
- Verificar logs de Agent IA
- Verificar que el teléfono del cliente sea válido

### Respuesta no se procesa
- Verificar que el endpoint esté protegido con API key
- Verificar formato del request
- Verificar logs de detección de intención

## 📚 Referencias

- **ReportLab Documentation:** https://www.reportlab.com/docs/reportlab-userguide.pdf
- **Tortoise ORM:** https://tortoise.github.io/
- **FastAPI:** https://fastapi.tiangolo.com/

---

**Implementado por:** Kiro AI Assistant  
**Fecha:** 20 de Noviembre, 2025  
**Versión:** 1.0.0
