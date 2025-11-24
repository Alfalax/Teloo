# 📱 Bot Conversacional - Escenarios y Respuestas

## 🎯 Descripción General

Este documento describe todos los escenarios conversacionales que maneja el bot de Telegram/WhatsApp, las respuestas predefinidas que envía, y cómo funciona la inteligencia artificial en cada caso.

---

## 🧠 Arquitectura de Decisión

### Rol de la IA (OpenAI GPT-4)
La IA **NO genera las respuestas finales**. Su función es:
- **Detectar intenciones** del usuario (¿qué quiere hacer?)
- **Extraer datos** del mensaje (nombre, teléfono, repuestos, etc.)
- **Clasificar el tipo de mensaje** (pregunta, confirmación, cancelación, etc.)

### Rol del Código
El código Python tiene **respuestas predefinidas** (hardcodeadas) para cada escenario. Una vez que la IA detecta la intención, el código decide qué mensaje enviar.

**Ventajas de este enfoque:**
- ✅ Respuestas rápidas y consistentes
- ✅ Menor costo (menos llamadas a IA)
- ✅ Control total sobre el tono y formato
- ✅ Fácil de modificar y mantener

---

## 📋 Escenarios y Respuestas

### 1️⃣ INICIO DE CONVERSACIÓN

#### Escenario: Usuario envía primer mensaje
**Ejemplos de entrada:**
- "Hola"
- "Necesito repuestos"
- "Buenos días"

**Respuesta del bot:**
```
🤖 ¡Hola! Soy el asistente de TeLOO.

Para ayudarte con tu solicitud de repuestos, necesito:
• Tu nombre y teléfono
• Repuestos que necesitas
• Marca, modelo y año del vehículo
• Tu ciudad

Puedes enviarme un audio o escribir la información.
```

---

### 2️⃣ CREACIÓN DE SOLICITUD

#### Escenario 2.1: Información Incompleta
**Qué pasa:** Usuario envía datos pero faltan campos obligatorios

**Respuesta del bot:**
```
🤔 Para crear tu solicitud necesito la siguiente información:

❌ nombre del cliente
❌ teléfono del cliente
❌ ciudad

📝 Por favor envíame la información que falta.
```

**Variante con datos parciales:**
```
🤔 Para crear tu solicitud necesito la siguiente información:

❌ teléfono del cliente
❌ ciudad

✅ Ya tengo: 2 repuesto(s)
✅ Ya tengo: Vehículo Toyota Corolla

📝 Por favor envíame la información que falta.
```

---

#### Escenario 2.2: Información Completa - Confirmación
**Qué pasa:** Usuario envía todos los datos necesarios

**Respuesta del bot:**
```
✅ Perfecto, actualicé la información:

👤 Cliente: Juan Pérez
📞 Teléfono: 3001234567
📍 Ciudad: Bogotá
🚗 Vehículo: Toyota Corolla 2015

🔧 Repuestos:
• 2x Pastillas de freno delanteras
• 1x Filtro de aceite

¿Ahora sí está todo correcto?
```

---

#### Escenario 2.3: Usuario Confirma Datos
**Entrada del usuario:**
- "Sí"
- "Correcto"
- "Todo bien"
- "Confirmo"

**Respuesta del bot:**
```
✅ ¡Perfecto! Tu solicitud ha sido creada exitosamente.

📋 Solicitud #12345

Pronto recibirás ofertas de nuestros asesores.
Te notificaremos cuando lleguen.
```

---

### 3️⃣ CORRECCIÓN DE DATOS

#### Escenario 3.1: Usuario Corrige un Dato
**Entrada del usuario:**
- "El teléfono es 3009876543"
- "Mi ciudad es Medellín"
- "Me llamo María"

**Respuesta del bot:**
```
✅ Perfecto, actualicé la información:

👤 Cliente: María González
📞 Teléfono: 3009876543
📍 Ciudad: Medellín
🚗 Vehículo: Chevrolet Spark 2018

🔧 Repuestos:
• 4x Llantas 185/65 R15

¿Ahora sí está todo correcto?
```

---

### 4️⃣ CANCELACIÓN

#### Escenario 4.1: Usuario Cancela Completamente
**Entrada del usuario:**
- "Ya no quiero"
- "No voy a hacer solicitud"
- "Déjalo"
- "Olvídalo"
- "Cancela todo"

**Respuesta del bot:**
```
✅ Entendido, he cancelado todo.

Si cambias de opinión y necesitas repuestos, solo escríbeme. ¡Estoy aquí para ayudarte!
```

**Qué hace el sistema:**
- Borra el borrador de Redis
- Limpia las acciones pendientes
- NO crea ninguna solicitud en la base de datos

---

### 5️⃣ PREGUNTAS DEL USUARIO

#### Escenario 5.1: Usuario Hace una Pregunta
**Entrada del usuario:**
- "¿Cuánto tiempo tarda?"
- "¿Cómo funciona?"
- "¿Puedo cambiar algo después?"

**Respuesta del bot:**
```
💬 [Respuesta generada por IA a la pregunta específica]

📋 Resumen actual:
👤 Cliente: Juan Pérez
📞 Teléfono: 3001234567
📍 Ciudad: Bogotá

🚗 Vehículo: Toyota Corolla 2015

🔧 Repuestos:
• 2x Pastillas de freno

¿Está todo correcto o necesitas ajustar algo?
```

**Nota:** En este caso, la IA SÍ genera la respuesta a la pregunta específica, pero el formato del mensaje es predefinido.

---

### 6️⃣ COMANDOS ESPECIALES

#### Comando: /reiniciar o /cancelar
**Respuesta del bot:**
```
🔄 Conversación reiniciada.

Envíame la información de tu solicitud:
• Puedes enviar un audio
• O un mensaje de texto con:
  - Tu nombre y teléfono
  - Repuestos que necesitas
  - Marca, modelo y año del vehículo
  - Tu ciudad
```

---

#### Comando: /ayuda o /help
**Respuesta del bot:**
```
🤖 *Comandos disponibles:*

📝 *Para crear solicitud:*
• Envía un audio con tu información
• O escribe los datos directamente

🔄 *Comandos útiles:*
• /reiniciar - Empezar de nuevo
• /cancelar - Cancelar solicitud actual
• /ayuda - Ver este mensaje

💡 *Tip:* Puedes hablar naturalmente, no necesitas comandos específicos.
```

---

### 7️⃣ RESPUESTA A OFERTAS

#### Escenario 7.1: Usuario Recibe Ofertas y Responde
**Contexto:** El usuario ya tiene una solicitud creada y recibió ofertas de asesores

**Entrada del usuario:**
- "Acepto la primera"
- "Me interesa la oferta de Juan"
- "No me convence ninguna"

**Respuesta del bot:**
```
✅ Perfecto, he registrado tu respuesta.

El asesor será notificado y se pondrá en contacto contigo pronto.

¡Gracias por usar TeLOO!
```

---

### 8️⃣ PROCESAMIENTO DE ARCHIVOS

#### Escenario 8.1: Usuario Envía Excel con Repuestos
**Qué pasa:** Usuario adjunta un archivo Excel con lista de repuestos

**Respuesta del bot (si es exitoso):**
```
📊 Excel procesado correctamente.

Encontré 15 repuestos en tu archivo:
• Pastillas de freno (cantidad: 2)
• Filtro de aceite (cantidad: 1)
• Bujías (cantidad: 4)
[... hasta 7 items, luego muestra solo total]

Ahora necesito:
❌ tu nombre
❌ tu teléfono
❌ marca y modelo del vehículo
❌ tu ciudad
```

**Respuesta del bot (si falla):**
```
❌ No pude procesar el archivo Excel.

Por favor verifica que:
• El archivo tenga columnas "nombre" y "cantidad"
• Los datos estén en la primera hoja
• El formato sea .xlsx o .xls

O puedes escribir los repuestos directamente.
```

---

#### Escenario 8.2: Usuario Envía Audio
**Qué pasa:** El sistema transcribe el audio con Whisper AI y procesa el texto

**Respuesta del bot:**
```
🎤 Audio recibido y procesado.

[Luego continúa con el flujo normal según lo que dijo en el audio]
```

---

### 9️⃣ MANEJO DE REPUESTOS

#### Escenario 9.1: Lista Corta de Repuestos (≤7 items)
**Formato de visualización:**
```
🔧 Repuestos:
• 2x Pastillas de freno delanteras
• 1x Filtro de aceite
• 4x Bujías NGK
```

---

#### Escenario 9.2: Lista Larga de Repuestos (>7 items)
**Formato de visualización:**
```
🔧 Repuestos: 15 items en total
```

**Razón:** Evitar mensajes muy largos que sean difíciles de leer

---

### 🔟 ERRORES Y CASOS ESPECIALES

#### Escenario 10.1: Error de Conexión con API
**Respuesta del bot:**
```
❌ Lo siento, hubo un error procesando tu solicitud.

Por favor intenta de nuevo en un momento.
Si el problema persiste, contacta a soporte.
```

---

#### Escenario 10.2: Ciudad No Encontrada
**Qué pasa:** El usuario menciona una ciudad que no está en la base de datos

**Respuesta del bot:**
```
⚠️ No encontré la ciudad "[nombre ciudad]" en nuestro sistema.

¿Podrías verificar el nombre? 

Ciudades disponibles: Bogotá, Medellín, Cali, Barranquilla, Cartagena...
```

---

## 🎭 Intenciones que Detecta la IA

La IA de OpenAI clasifica cada mensaje en una de estas intenciones:

| Intención | Descripción | Ejemplo |
|-----------|-------------|---------|
| `create_request` | Usuario quiere crear solicitud | "Necesito pastillas de freno" |
| `cancel` | Usuario quiere cancelar todo | "Ya no quiero", "Olvídalo" |
| `confirm` | Usuario confirma datos | "Sí", "Correcto", "Todo bien" |
| `correct_data` | Usuario corrige un dato | "El teléfono es 3001234567" |
| `query` | Usuario hace pregunta | "¿Cuánto tarda?" |
| `respond_offers` | Usuario responde a ofertas | "Acepto la primera" |
| `reject` | Usuario rechaza todo | "No, todo mal", "Empecemos de nuevo" |

---

## 🔄 Flujo Completo de Conversación

### Ejemplo de Conversación Exitosa

```
👤 Usuario: "Hola, necesito repuestos"

🤖 Bot: "🤖 ¡Hola! Soy el asistente de TeLOO..."

👤 Usuario: [Envía audio: "Necesito pastillas de freno para Toyota Corolla 2015, 
           soy Juan Pérez, mi teléfono es 3001234567, estoy en Bogotá"]

🤖 Bot: "✅ Perfecto, actualicé la información:
        👤 Cliente: Juan Pérez
        📞 Teléfono: 3001234567
        📍 Ciudad: Bogotá
        🚗 Vehículo: Toyota Corolla 2015
        🔧 Repuestos:
        • 2x Pastillas de freno delanteras
        ¿Ahora sí está todo correcto?"

👤 Usuario: "Sí"

🤖 Bot: "✅ ¡Perfecto! Tu solicitud ha sido creada exitosamente.
        📋 Solicitud #12345
        Pronto recibirás ofertas de nuestros asesores."
```

---

### Ejemplo de Conversación con Corrección

```
👤 Usuario: "Necesito llantas para Chevrolet Spark 2018"

🤖 Bot: "🤔 Para crear tu solicitud necesito:
        ❌ nombre del cliente
        ❌ teléfono del cliente
        ❌ ciudad
        ✅ Ya tengo: 1 repuesto(s)
        ✅ Ya tengo: Vehículo Chevrolet Spark"

👤 Usuario: "Juan Pérez, 3001234567, Medellín"

🤖 Bot: "✅ Perfecto, actualicé la información:
        👤 Cliente: Juan Pérez
        📞 Teléfono: 3001234567
        📍 Ciudad: Medellín
        🚗 Vehículo: Chevrolet Spark 2018
        🔧 Repuestos:
        • 4x Llantas
        ¿Ahora sí está todo correcto?"

👤 Usuario: "El teléfono es 3009876543"

🤖 Bot: "✅ Perfecto, actualicé la información:
        👤 Cliente: Juan Pérez
        📞 Teléfono: 3009876543
        [... resto de datos ...]
        ¿Ahora sí está todo correcto?"

👤 Usuario: "Sí"

🤖 Bot: "✅ ¡Perfecto! Tu solicitud ha sido creada..."
```

---

### Ejemplo de Conversación con Cancelación

```
👤 Usuario: "Necesito repuestos"

🤖 Bot: "🤖 ¡Hola! Soy el asistente de TeLOO..."

👤 Usuario: "Pastillas de freno para Toyota"

🤖 Bot: "🤔 Para crear tu solicitud necesito:
        ❌ nombre del cliente
        ❌ teléfono del cliente
        ❌ año del vehículo
        ❌ ciudad"

👤 Usuario: "Ya no quiero hacer ninguna solicitud"

🤖 Bot: "✅ Entendido, he cancelado todo.
        Si cambias de opinión y necesitas repuestos, 
        solo escríbeme. ¡Estoy aquí para ayudarte!"
```

---

## 📊 Datos que Extrae la IA

De cada mensaje, la IA intenta extraer:

### Datos del Cliente
- **Nombre completo**
- **Teléfono** (10 dígitos)
- **Ciudad**

### Datos del Vehículo
- **Marca** (Toyota, Chevrolet, Mazda, etc.)
- **Modelo/Línea** (Corolla, Spark, etc.)
- **Año** (2015, 2018, etc.)

### Datos de Repuestos
- **Nombre del repuesto**
- **Cantidad** (default: 1)
- **Descripción adicional** (opcional)

---

## 🎨 Emojis Utilizados

El bot usa emojis consistentes para mejorar la experiencia:

| Emoji | Significado |
|-------|-------------|
| 🤖 | Bot/Sistema |
| ✅ | Éxito/Confirmación |
| ❌ | Error/Falta información |
| 🤔 | Pensando/Necesita datos |
| 👤 | Cliente/Usuario |
| 📞 | Teléfono |
| 📍 | Ubicación/Ciudad |
| 🚗 | Vehículo |
| 🔧 | Repuestos |
| 📋 | Solicitud/Resumen |
| 💬 | Pregunta/Respuesta |
| 🔄 | Reiniciar |
| 📊 | Excel/Archivo |
| 🎤 | Audio |
| ⚠️ | Advertencia |
| 💡 | Tip/Consejo |

---

## 🔧 Cómo Modificar Respuestas

Para cambiar cualquier mensaje del bot:

1. **Ubicar el archivo:** `services/agent-ia/app/services/telegram_message_processor.py`
2. **Buscar el mensaje** que quieres cambiar
3. **Editar el texto** manteniendo el formato
4. **Reiniciar el servicio** para aplicar cambios

**Ejemplo:**
```python
# Antes
cancel_msg = "✅ Entendido, he cancelado todo.\n\n"
cancel_msg += "Si cambias de opinión..."

# Después (más formal)
cancel_msg = "✅ Su solicitud ha sido cancelada.\n\n"
cancel_msg += "Si desea crear una nueva solicitud..."
```

---

## 📝 Notas Importantes

1. **Contexto Conversacional:** El bot mantiene el contexto de la conversación en Redis por 24 horas
2. **Límite de Repuestos:** Muestra máximo 7 repuestos en detalle, luego solo el total
3. **Transcripción de Audio:** Usa Whisper AI de OpenAI (muy preciso)
4. **Procesamiento de Excel:** Busca columnas "nombre" y "cantidad"
5. **Normalización de Ciudades:** Ignora tildes y mayúsculas para búsqueda
6. **Timeout de Respuesta:** Si el usuario no responde en 24h, se borra el borrador

---

## 🚀 Próximas Mejoras Sugeridas

- [ ] Agregar soporte para imágenes de repuestos
- [ ] Permitir editar solicitudes ya creadas
- [ ] Agregar historial de solicitudes del usuario
- [ ] Notificaciones proactivas cuando lleguen ofertas
- [ ] Soporte multiidioma (inglés, portugués)
- [ ] Integración con catálogo de repuestos para autocompletar

---

**Última actualización:** 21 de Noviembre de 2025
**Versión del documento:** 1.0
