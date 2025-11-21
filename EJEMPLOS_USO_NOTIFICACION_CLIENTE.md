# 📚 Ejemplos de Uso: Notificación al Cliente

## 🎯 Casos de Uso Comunes

### 1. Notificar Cliente Manualmente

```python
from services.notificacion_cliente_service import NotificacionClienteService
import redis.asyncio as redis

# Conectar a Redis
redis_client = redis.from_url("redis://localhost:6379")

# Notificar cliente
resultado = await NotificacionClienteService.notificar_ofertas_ganadoras(
    solicitud_id="uuid-de-la-solicitud",
    redis_client=redis_client
)

if resultado['success']:
    print(f"✅ Cliente notificado: {resultado['codigo_solicitud']}")
    print(f"   Teléfono: {resultado['cliente_telefono']}")
    print(f"   Métricas: {resultado['metricas']}")
else:
    print(f"❌ Error: {resultado['error']}")
```

### 2. Generar PDF de Ofertas

```python
from services.pdf_generator_service import PDFGeneratorService

# Generar PDF
pdf_buffer = await PDFGeneratorService.generar_pdf_ofertas_ganadoras(
    solicitud_id="uuid-de-la-solicitud"
)

# Guardar PDF
with open("propuesta_cliente.pdf", "wb") as f:
    f.write(pdf_buffer.getvalue())

print("✅ PDF generado: propuesta_cliente.pdf")
```

### 3. Calcular Métricas de Ofertas

```python
from services.pdf_generator_service import PDFGeneratorService

# Calcular métricas
metricas = await PDFGeneratorService.calcular_metricas_ofertas(
    solicitud_id="uuid-de-la-solicitud"
)

print(f"📊 Métricas:")
print(f"   Asesores contactados: {metricas['asesores_contactados']}")
print(f"   Ahorro obtenido: ${metricas['ahorro_obtenido']:,.0f}")
print(f"   Porcentaje ahorro: {metricas['porcentaje_ahorro']:.1f}%")
print(f"   Monto total: ${metricas['monto_total']:,.0f}")
```

### 4. Procesar Respuesta del Cliente

```python
from services.respuesta_cliente_service import RespuestaClienteService

# Procesar respuesta
resultado = await RespuestaClienteService.procesar_respuesta(
    solicitud_id="uuid-de-la-solicitud",
    respuesta_texto="acepto 1,3",
    usar_nlp=True
)

if resultado['success']:
    print(f"✅ Respuesta procesada: {resultado['tipo_respuesta']}")
    print(f"   Mensaje: {resultado['mensaje']}")
    if resultado.get('repuestos_aceptados'):
        print(f"   Aceptados: {resultado['repuestos_aceptados']}")
    if resultado.get('repuestos_rechazados'):
        print(f"   Rechazados: {resultado['repuestos_rechazados']}")
else:
    print(f"❌ Error: {resultado['error']}")
```

### 5. Enviar Recordatorio

```python
from services.notificacion_cliente_service import NotificacionClienteService
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost:6379")

# Enviar recordatorio intermedio
resultado = await NotificacionClienteService.enviar_recordatorio(
    solicitud_id="uuid-de-la-solicitud",
    tipo_recordatorio='intermedio',  # o 'final'
    redis_client=redis_client
)

if resultado['success']:
    print(f"✅ Recordatorio enviado: {resultado['tipo_recordatorio']}")
else:
    print(f"❌ Error: {resultado['error']}")
```

## 🔌 Uso del Endpoint REST

### Endpoint: POST /v1/solicitudes/{solicitud_id}/respuesta-cliente

#### Ejemplo 1: Aceptar Todas las Ofertas

```bash
curl -X POST http://localhost:8000/v1/solicitudes/123e4567-e89b-12d3-a456-426614174000/respuesta-cliente \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-service-api-key" \
  -d '{
    "respuesta_texto": "acepto",
    "usar_nlp": true
  }'
```

**Response:**
```json
{
  "success": true,
  "solicitud_id": "123e4567-e89b-12d3-a456-426614174000",
  "tipo_respuesta": "aceptacion_total",
  "mensaje": "Todas las ofertas han sido aceptadas. Los asesores te contactarán pronto.",
  "repuestos_aceptados": null,
  "repuestos_rechazados": null
}
```

#### Ejemplo 2: Rechazar Todas las Ofertas

```bash
curl -X POST http://localhost:8000/v1/solicitudes/123e4567-e89b-12d3-a456-426614174000/respuesta-cliente \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-service-api-key" \
  -d '{
    "respuesta_texto": "rechazo",
    "usar_nlp": true
  }'
```

**Response:**
```json
{
  "success": true,
  "solicitud_id": "123e4567-e89b-12d3-a456-426614174000",
  "tipo_respuesta": "rechazo_total",
  "mensaje": "Todas las ofertas han sido rechazadas. Gracias por usar TeLOO.",
  "repuestos_aceptados": null,
  "repuestos_rechazados": null
}
```

#### Ejemplo 3: Aceptación Parcial

```bash
curl -X POST http://localhost:8000/v1/solicitudes/123e4567-e89b-12d3-a456-426614174000/respuesta-cliente \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-service-api-key" \
  -d '{
    "respuesta_texto": "acepto 1,3,5",
    "usar_nlp": true
  }'
```

**Response:**
```json
{
  "success": true,
  "solicitud_id": "123e4567-e89b-12d3-a456-426614174000",
  "tipo_respuesta": "aceptacion_parcial",
  "mensaje": "Has aceptado 3 repuesto(s). Los asesores te contactarán pronto.",
  "repuestos_aceptados": [
    "Pastillas de freno delanteras",
    "Filtro de aceite",
    "Bujías"
  ],
  "repuestos_rechazados": [
    "Filtro de aire",
    "Líquido de frenos"
  ]
}
```

#### Ejemplo 4: Rechazo Parcial

```bash
curl -X POST http://localhost:8000/v1/solicitudes/123e4567-e89b-12d3-a456-426614174000/respuesta-cliente \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-service-api-key" \
  -d '{
    "respuesta_texto": "rechazo 2",
    "usar_nlp": true
  }'
```

**Response:**
```json
{
  "success": true,
  "solicitud_id": "123e4567-e89b-12d3-a456-426614174000",
  "tipo_respuesta": "aceptacion_parcial",
  "mensaje": "Has aceptado 4 repuesto(s). Los asesores te contactarán pronto.",
  "repuestos_aceptados": [
    "Pastillas de freno delanteras",
    "Filtro de aceite",
    "Bujías",
    "Líquido de frenos"
  ],
  "repuestos_rechazados": [
    "Filtro de aire"
  ]
}
```

## 🔍 Detección de Intención - Ejemplos

### Respuestas que Detectan "Aceptar Todo"

```python
respuestas_aceptar_todo = [
    "acepto",
    "acepto todo",
    "acepto todas",
    "si",
    "ok",
    "vale",
    "me sirve",
    "perfecto",
    "aceptar todo"
]

for respuesta in respuestas_aceptar_todo:
    intencion = await RespuestaClienteService._detectar_intencion_simple(
        respuesta, solicitud
    )
    assert intencion['tipo'] == 'aceptar_todo'
```

### Respuestas que Detectan "Rechazar Todo"

```python
respuestas_rechazar_todo = [
    "rechazo",
    "rechazo todo",
    "no",
    "no me sirve",
    "ninguno",
    "nada",
    "rechazar todo"
]

for respuesta in respuestas_rechazar_todo:
    intencion = await RespuestaClienteService._detectar_intencion_simple(
        respuesta, solicitud
    )
    assert intencion['tipo'] == 'rechazar_todo'
```

### Respuestas que Detectan "Aceptación Parcial"

```python
respuestas_aceptar_parcial = [
    "acepto 1",
    "acepto 1,3",
    "acepto 1 y 3",
    "acepto 1, 3 y 5",
    "si al 1 y 3",
    "me sirve el 1 y el 3"
]

for respuesta in respuestas_aceptar_parcial:
    intencion = await RespuestaClienteService._detectar_intencion_simple(
        respuesta, solicitud
    )
    assert intencion['tipo'] == 'aceptar_parcial'
    assert len(intencion['repuestos_aceptados']) > 0
```

## 📊 Consultas SQL Útiles

### Ver Solicitudes Pendientes de Notificación

```sql
SELECT 
    id,
    codigo_solicitud,
    estado,
    fecha_evaluacion,
    fecha_notificacion_cliente
FROM solicitudes
WHERE estado = 'EVALUADA'
  AND fecha_evaluacion IS NOT NULL
  AND fecha_notificacion_cliente IS NULL
ORDER BY fecha_evaluacion DESC;
```

### Ver Solicitudes Esperando Respuesta

```sql
SELECT 
    s.id,
    s.codigo_solicitud,
    c.usuario.nombre_completo as cliente,
    c.usuario.telefono,
    s.fecha_notificacion_cliente,
    EXTRACT(EPOCH FROM (NOW() - s.fecha_notificacion_cliente))/3600 as horas_transcurridas
FROM solicitudes s
JOIN clientes c ON s.cliente_id = c.id
WHERE s.estado = 'EVALUADA'
  AND s.fecha_notificacion_cliente IS NOT NULL
  AND s.fecha_respuesta_cliente IS NULL
ORDER BY s.fecha_notificacion_cliente ASC;
```

### Ver Respuestas de Clientes

```sql
SELECT 
    s.codigo_solicitud,
    s.cliente_acepto,
    s.respuesta_cliente_texto,
    s.fecha_respuesta_cliente,
    COUNT(o.id) FILTER (WHERE o.estado = 'ACEPTADA') as ofertas_aceptadas,
    COUNT(o.id) FILTER (WHERE o.estado = 'RECHAZADA') as ofertas_rechazadas
FROM solicitudes s
LEFT JOIN ofertas o ON s.id = o.solicitud_id
WHERE s.fecha_respuesta_cliente IS NOT NULL
GROUP BY s.id
ORDER BY s.fecha_respuesta_cliente DESC;
```

### Ver Métricas de Conversión

```sql
SELECT 
    COUNT(*) as total_notificaciones,
    COUNT(*) FILTER (WHERE fecha_respuesta_cliente IS NOT NULL) as con_respuesta,
    COUNT(*) FILTER (WHERE cliente_acepto = true) as aceptadas,
    COUNT(*) FILTER (WHERE cliente_acepto = false) as rechazadas,
    COUNT(*) FILTER (WHERE fecha_respuesta_cliente IS NULL 
                     AND NOW() - fecha_notificacion_cliente > INTERVAL '24 hours') as timeout,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fecha_respuesta_cliente IS NOT NULL) / COUNT(*), 2) as tasa_respuesta,
    ROUND(100.0 * COUNT(*) FILTER (WHERE cliente_acepto = true) / COUNT(*), 2) as tasa_aceptacion
FROM solicitudes
WHERE fecha_notificacion_cliente IS NOT NULL;
```

## 🧪 Testing en Desarrollo

### Test Completo del Flujo

```python
import asyncio
from tortoise import Tortoise

async def test_flujo_completo():
    # Initialize DB
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password_2024@localhost:5432/teloo_db",
        modules={"models": ["models.solicitud", "models.oferta", "models.user"]}
    )
    
    try:
        # 1. Buscar solicitud evaluada
        solicitud = await Solicitud.filter(estado=EstadoSolicitud.EVALUADA).first()
        
        # 2. Generar PDF
        pdf = await PDFGeneratorService.generar_pdf_ofertas_ganadoras(str(solicitud.id))
        print(f"✅ PDF generado: {len(pdf.getvalue())} bytes")
        
        # 3. Calcular métricas
        metricas = await PDFGeneratorService.calcular_metricas_ofertas(str(solicitud.id))
        print(f"✅ Métricas: {metricas}")
        
        # 4. Simular respuesta
        resultado = await RespuestaClienteService.procesar_respuesta(
            solicitud_id=str(solicitud.id),
            respuesta_texto="acepto 1,3",
            usar_nlp=False
        )
        print(f"✅ Respuesta procesada: {resultado}")
        
    finally:
        await Tortoise.close_connections()

# Ejecutar
asyncio.run(test_flujo_completo())
```

## 🔧 Configuración Avanzada

### Personalizar Timeout

```python
from services.configuracion_service import ConfiguracionService

# Actualizar timeout
await ConfiguracionService.update_config(
    'parametros_generales',
    {'timeout_ofertas_horas': 48}  # 48 horas en lugar de 20
)
```

### Personalizar Mensaje

```python
# Editar en: services/notificacion_cliente_service.py
# Método: _generar_mensaje_cliente()

mensaje = f"""
🎉 ¡Excelentes noticias!

Hemos encontrado las mejores ofertas para tus repuestos.

📊 Resultados:
• {metricas['asesores_contactados']} asesores contactados
• Ahorro: ${metricas['ahorro_obtenido']:,.0f} ({metricas['porcentaje_ahorro']:.0f}%)

💰 Total: ${metricas['monto_total']:,.0f}

Responde "acepto" para confirmar o "rechazo" para declinar.
"""
```

## 📱 Integración con Agent IA

### Consumir Evento de Notificación

```python
import redis.asyncio as redis
import json

async def consumir_eventos():
    redis_client = redis.from_url("redis://localhost:6379")
    pubsub = redis_client.pubsub()
    
    # Suscribirse a eventos
    await pubsub.subscribe('cliente.notificar_ofertas_ganadoras')
    
    async for message in pubsub.listen():
        if message['type'] == 'message':
            evento = json.loads(message['data'])
            
            # Procesar evento
            print(f"📨 Evento recibido: {evento['tipo_evento']}")
            print(f"   Cliente: {evento['cliente_nombre']}")
            print(f"   Teléfono: {evento['cliente_telefono']}")
            print(f"   Mensaje: {evento['mensaje']}")
            
            # Enviar por WhatsApp
            await enviar_whatsapp(
                telefono=evento['cliente_telefono'],
                mensaje=evento['mensaje'],
                pdf_filename=evento['pdf_filename']
            )

# Ejecutar
asyncio.run(consumir_eventos())
```

---

**Más ejemplos en:** `test_notificacion_cliente_flow.py`  
**Documentación completa:** `IMPLEMENTACION_NOTIFICACION_CLIENTE.md`
