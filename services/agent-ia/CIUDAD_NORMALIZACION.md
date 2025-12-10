# Normalización Inteligente de Ciudades

## Problema Resuelto

Los usuarios colombianos suelen mencionar la ciudad junto con el departamento al que pertenece:
- "Bello Antioquia"
- "Medellín Antioquia"
- "Cali Valle"
- "Bogotá Cundinamarca"

Esto causaba errores al buscar el municipio en la base de datos porque se buscaba "BELLO ANTIOQUIA" en lugar de solo "BELLO".

## Solución Implementada

### Función `limpiar_ciudad()`

Ubicación: `services/agent-ia/app/services/solicitud_service.py`

Esta función realiza 3 operaciones:

1. **Normalización básica:**
   - Quita tildes: "Medellín" → "MEDELLIN"
   - Convierte a mayúsculas: "bello" → "BELLO"
   - Elimina espacios extra

2. **Detección de departamentos:**
   - Identifica 33 departamentos de Colombia
   - Busca el departamento al final o al inicio del texto
   - Ejemplos: "BELLO ANTIOQUIA", "ANTIOQUIA BELLO"

3. **Limpieza:**
   - Remueve el departamento detectado
   - Retorna solo el nombre del municipio limpio

### Ejemplos de Transformación

```python
limpiar_ciudad("Bello Antioquia")      # → "BELLO"
limpiar_ciudad("Medellín Antioquia")   # → "MEDELLIN"
limpiar_ciudad("Cali Valle")           # → "CALI"
limpiar_ciudad("Bogotá Cundinamarca")  # → "BOGOTA"
limpiar_ciudad("Barranquilla")         # → "BARRANQUILLA"
```

## Departamentos Soportados

La función reconoce los 33 departamentos de Colombia:

- Antioquia, Valle del Cauca, Valle, Cundinamarca
- Atlántico, Bolívar, Santander, Norte de Santander
- Cauca, Nariño, Tolima, Huila, Meta
- Córdoba, Cesar, Magdalena, Boyacá
- Caldas, Risaralda, Quindío, Chocó, Sucre
- La Guajira, Guajira, Casanare, Arauca
- Putumayo, Caquetá, Vichada, Guainía
- Guaviare, Vaupés, Amazonas

## Integración

### Telegram

```python
# En telegram_message_processor.py
from app.services.solicitud_service import limpiar_ciudad

ciudad_normalizada = limpiar_ciudad(cliente["ciudad"])
# Buscar municipio con ciudad limpia
```

### WhatsApp

```python
# En solicitud_service.py - _prepare_solicitud_data()
ciudad_limpia = limpiar_ciudad(cliente.get("ciudad", ""))

cliente_data = {
    "ciudad": ciudad_limpia,  # Ciudad sin departamento
    ...
}
```

## Logs

La función registra cada limpieza realizada:

```
INFO - Ciudad limpiada: 'Bello Antioquia' -> 'BELLO'
INFO - Ciudad limpiada: 'Medellín Antioquia' -> 'MEDELLIN'
```

Esto ayuda a monitorear y debuggear el comportamiento.

## Beneficios

1. **Mejor UX:** Los usuarios pueden hablar naturalmente
2. **Menos errores:** Reduce fallos por formato de ciudad
3. **Consistencia:** Misma lógica en Telegram y WhatsApp
4. **Mantenible:** Función centralizada y reutilizable
5. **Extensible:** Fácil agregar más departamentos si es necesario

## Testing

Para probar la función:

```python
from app.services.solicitud_service import limpiar_ciudad

# Casos de prueba
assert limpiar_ciudad("Bello Antioquia") == "BELLO"
assert limpiar_ciudad("Medellín Antioquia") == "MEDELLIN"
assert limpiar_ciudad("Cali Valle del Cauca") == "CALI"
assert limpiar_ciudad("Bogotá") == "BOGOTA"
assert limpiar_ciudad("  Barranquilla  ") == "BARRANQUILLA"
```

## Casos Edge

- **Ciudad vacía:** Retorna string vacío
- **Solo departamento:** Retorna el departamento normalizado
- **Múltiples espacios:** Se limpian automáticamente
- **Tildes y caracteres especiales:** Se normalizan correctamente
- **Mayúsculas/minúsculas:** Se unifican a mayúsculas

## Futuras Mejoras

1. Agregar sinónimos de departamentos (ej: "Valle" = "Valle del Cauca")
2. Detectar abreviaciones comunes (ej: "Bog" = "Bogotá")
3. Sugerir correcciones para ciudades mal escritas
4. Cache de ciudades frecuentes para mejor performance
