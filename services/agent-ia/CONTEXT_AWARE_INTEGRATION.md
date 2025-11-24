# Integración de Sistema Contextual Inteligente

## ✅ Completado
- [x] Creado `context_manager.py` con interpretación GPT-4

## 📋 Pasos de Integración

### 1. Actualizar `telegram_message_processor.py`

Agregar al inicio del archivo:
```python
from app.services.context_manager import get_context_manager
```

### 2. Modificar método `process_message()`

Reemplazar la lógica actual con:

```python
async def process_message(self, message: str, user_id: str, chat_id: str) -> str:
    """Process incoming message with context awareness"""
    try:
        context_mgr = get_context_manager()
        
        # 1. Guardar mensaje del usuario
        await context_mgr.add_message(user_id, "user", message)
        
        # 2. Interpretar con contexto usando GPT-4
        interpretation = await context_mgr.interpret_with_context(user_id, message)
        
        logger.info(f"🎯 Intent: {interpretation['intent']} - {interpretation['action']}")
        
        # 3. Procesar según intención
        response = await self._handle_intent(interpretation, message, user_id, chat_id)
        
        # 4. Guardar respuesta del asistente
        await context_mgr.add_message(user_id, "assistant", response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return "❌ Error procesando mensaje. Por favor intenta de nuevo."
```

### 3. Crear método `_handle_intent()`

```python
async def _handle_intent(self, interpretation: dict, message: str, user_id: str, chat_id: str) -> str:
    """Handle different intents"""
    intent = interpretation['intent']
    context_mgr = get_context_manager()
    
    if intent == "create_request":
        # Procesar creación de solicitud (lógica actual)
        return await self._handle_create_request(message, user_id, chat_id)
    
    elif intent == "correct_data":
        # Corregir dato específico
        field = interpretation['extracted_data'].get('field')
        value = interpretation['extracted_data'].get('value')
        return await self._handle_correct_data(user_id, field, value)
    
    elif intent == "confirm":
        # Confirmar y crear solicitud
        return await self._handle_confirm_request(user_id, chat_id)
    
    elif intent == "respond_offers":
        # Responder a ofertas (llamar a core-api)
        return await self._handle_offer_response(message, user_id)
    
    elif intent == "cancel":
        # Cancelar y limpiar contexto
        await context_mgr.clear_pending_action(user_id)
        return "❌ Operación cancelada. ¿En qué más puedo ayudarte?"
    
    else:  # query
        return "🤔 No entendí bien. ¿Quieres crear una solicitud de repuestos?"
```

### 4. Implementar `_handle_correct_data()`

```python
async def _handle_correct_data(self, user_id: str, field: str, value: str) -> str:
    """Corrige un dato de la solicitud en creación"""
    try:
        context_mgr = get_context_manager()
        pending = await context_mgr.get_pending_actions(user_id)
        
        if not pending or pending.get('type') != 'creating_request':
            return "No hay solicitud en creación para corregir."
        
        # Actualizar el dato
        draft = pending.get('data', {}).get('draft', {})
        
        if field == 'telefono':
            draft['telefono'] = value
        elif field == 'nombre':
            draft['nombre_cliente'] = value
        elif field == 'ciudad':
            draft['ciudad'] = value
        
        # Guardar cambios
        pending['data']['draft'] = draft
        await context_mgr.set_pending_action(user_id, 'creating_request', pending['data'])
        
        # Mostrar resumen actualizado
        return await self._show_draft_summary(draft)
        
    except Exception as e:
        logger.error(f"Error correcting data: {e}")
        return "❌ Error corrigiendo dato"
```

### 5. Actualizar `_show_draft_summary()`

Agregar al final:
```python
# Marcar como pendiente de confirmación
context_mgr = get_context_manager()
await context_mgr.set_pending_action(
    user_id, 
    'creating_request',
    {'draft': draft, 'missing_fields': missing}
)
```

### 6. Actualizar `_handle_offer_response()`

```python
async def _handle_offer_response(self, message: str, user_id: str) -> str:
    """Maneja respuesta a ofertas usando core-api"""
    try:
        context_mgr = get_context_manager()
        pending = await context_mgr.get_pending_actions(user_id)
        
        if not pending or pending.get('type') != 'awaiting_offer_response':
            return "No hay ofertas pendientes de respuesta."
        
        solicitud_id = pending.get('data', {}).get('solicitud_id')
        
        # Llamar a core-api para procesar respuesta
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CORE_API_URL}/v1/solicitudes/{solicitud_id}/respuesta-cliente",
                json={"texto": message, "usar_nlp": True}
            )
            
            if response.status_code == 200:
                # Limpiar acción pendiente
                await context_mgr.clear_pending_action(user_id)
                return "✅ Respuesta procesada correctamente"
            else:
                return "❌ Error procesando respuesta"
                
    except Exception as e:
        logger.error(f"Error handling offer response: {e}")
        return "❌ Error procesando respuesta"
```

### 7. Marcar ofertas como pendientes

Cuando se envía notificación de ofertas, agregar:
```python
context_mgr = get_context_manager()
await context_mgr.set_pending_action(
    user_id,
    'awaiting_offer_response',
    {'solicitud_id': solicitud_id},
    ttl=86400  # 24 horas
)
```

## 🧪 Testing

1. Reiniciar agent-ia:
```bash
docker-compose restart agent-ia
```

2. Probar flujo:
- Enviar audio con solicitud
- Cuando pregunte "¿está correcto?", enviar solo "3006515619"
- Debe reconocer como corrección de teléfono
- Confirmar con "si"

## 📊 Beneficios

- ✅ Conversación natural sin comandos rígidos
- ✅ Entiende contexto automáticamente
- ✅ Maneja ambigüedades inteligentemente
- ✅ Fallback si GPT-4 falla
- ✅ Historial conversacional persistente

## 💰 Costos

- GPT-4o-mini: ~$0.15 por 1M tokens input
- Promedio: ~500 tokens por interpretación
- Costo por mensaje: ~$0.00008 (menos de 1 centavo)
