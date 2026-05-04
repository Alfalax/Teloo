"""
Centralized prompts and bot message constants.

All LLM system prompts and user-facing error/info messages live here
so they can be updated in one place without hunting through processor files.
"""

# ---------------------------------------------------------------------------
# LLM System Prompts
# ---------------------------------------------------------------------------

INTENT_SYSTEM_PROMPT = """Analiza el mensaje del usuario y determina su intención. Responde SOLO con un JSON válido.

DATOS ACTUALES:
{draft_context}

ÚLTIMO REPUESTO AGREGADO:
{last_repuesto}

ÚLTIMO MENSAJE DEL BOT:
{last_bot_message}

CONTEXTO: Si el usuario menciona cantidades ("las 2", "son 3") después de una pregunta sobre cantidades,
actualiza la cantidad del ÚLTIMO REPUESTO AGREGADO.

FORMATO DE RESPUESTA:
{{
  "intent": "confirm" | "reject" | "correct" | "question",
  "answer": "respuesta a la pregunta (solo si intent es question)",
  "updated_data": {{
    "cliente": {{"nombre": "...", "telefono": "...", "ciudad": "..."}},
    "vehiculo": {{"marca": "...", "linea": "...", "anio": "..."}},
    "repuestos": [{{"nombre": "...", "cantidad": 1}}]
  }}
}}

INTENCIONES:
- "confirm": Usuario confirma que todo está bien SIN mencionar cambios.
  Ejemplos: "sí", "ok", "perfecto", "todo bien", "correcto", "así está", "confirmar", "adelante",
            "aprobado", "listo", "dale", "de acuerdo", "excelente", "genial", "bien", "muy bien"
  NO ES CONFIRMACIÓN: "serían las 2" (menciona cantidad), "sí, pero..." (tiene corrección)

- "reject": Usuario rechaza TODO y quiere empezar de nuevo (SOLO rechazos totales y explícitos).
  Ejemplos: "no, todo mal", "empecemos de nuevo", "borra todo", "cancela todo"
  NO ES RECHAZO: "no" (solo), "no, es la izquierda" (es corrección)

- "question": Usuario hace una pregunta o pide aclaración.
  Ejemplos: "¿las pastillas vienen 1 o el par?", "¿cuánto demora?", "¿puedo agregar más?"
  Responde la pregunta en "answer" y mantén los datos sin cambios.

- "correct": Usuario quiere corregir o agregar algo específico.
  Ejemplos: "el teléfono es 3006515619", "agrega pastillas traseras", "el año es 2019"

REGLAS:
1. Si el mensaje tiene "?" o palabras como "viene", "vienen", "puedo", "cómo", "cuánto" → "question"
2. Si menciona números/cantidades → "correct", NO "confirm"
3. Si dice "no" pero está corrigiendo algo → "correct", NO "reject"
4. Solo usa "reject" si quiere borrar TODO y empezar de nuevo
5. Para "correct": copia TODOS los datos actuales a updated_data y modifica solo los mencionados
6. Si dice "agregar" o "también necesito", AGREGA el repuesto a la lista existente"""


EXTRACTION_SYSTEM_PROMPT = """Extrae información del mensaje y responde SOLO con JSON válido (sin markdown):
{
  "repuestos": [{"nombre": "kit de arrastre", "cantidad": 1}],
  "vehiculo": {"marca": "", "linea": "", "anio": ""},
  "cliente": {"telefono": "", "nombre": "", "ciudad": ""}
}

REGLAS CRÍTICAS:
- Extrae SOLO la información que el usuario menciona explícitamente
- NO inventes ni asumas datos que no están en el mensaje
- Si el usuario NO menciona marca/modelo/año del vehículo, dejá esos campos vacíos ""
- Si el usuario NO menciona nombre/teléfono/ciudad, dejá esos campos vacíos ""
- Extrae TODOS los repuestos mencionados
- TELÉFONO: Los números colombianos tienen 10 dígitos y empiezan con 3.
  Si ves números separados, únelos (ej: "300 65 15 619" → "3006515619")
- Respondé SOLO el JSON, sin texto adicional

EJEMPLOS:
Mensaje: "necesito kit de arrastre y filtro de aire"
→ {"repuestos": [...], "vehiculo": {"marca": "", "linea": "", "anio": ""}, "cliente": {"telefono": "", "nombre": "", "ciudad": ""}}

Mensaje: "para una Yamaha FZ 2.0 del 2018"
→ {"repuestos": [], "vehiculo": {"marca": "Yamaha", "linea": "FZ 2.0", "anio": "2018"}, "cliente": {"telefono": "", "nombre": "", "ciudad": ""}}"""


# ---------------------------------------------------------------------------
# User-facing messages (canonical — use these instead of inline strings)
# ---------------------------------------------------------------------------

ERR_TECHNICAL = "Lo siento, hubo un problema técnico. Por favor intentá de nuevo en unos minutos."
ERR_PROCESS_MSG = "❌ Error al procesar tu mensaje. Por favor intentá de nuevo en unos momentos."
ERR_AUDIO_TRANSCRIPTION = "🎤 Recibí tu audio pero no pude transcribirlo. ¿Podés escribirme el mensaje?"
ERR_CITY_UNAVAILABLE = "📍 Lo sentimos, actualmente no tenemos cobertura en {city}. Puedes consultar las ciudades disponibles."

MSG_WELCOME = (
    "👋 ¡Hola! Soy el asistente de *TeLOO*.\n\n"
    "Te ayudo a conseguir los mejores repuestos para tu vehículo al mejor precio.\n\n"
    "Para crear tu solicitud, contame:\n"
    "🔧 ¿Qué repuestos necesitás?\n"
    "🚗 Marca, modelo y año de tu vehículo\n"
    "📍 Tu ciudad\n"
    "👤 Tu nombre y teléfono\n\n"
    "Podés enviarme un *mensaje de voz* o texto. ¡Como prefieras! 😊"
)

MSG_WELCOME_TELEGRAM = MSG_WELCOME + "\n\n💡 Tip: si en algún momento querés empezar de nuevo, escribí /reiniciar"

MSG_CANCELLED = "✅ Entendido, he cancelado todo.\n\nSi cambias de opinión y necesitas repuestos, solo escríbeme. ¡Estoy aquí para ayudarte!"

MSG_RESTARTED = (
    "🔄 Conversación reiniciada.\n\n"
    "Envíame la información de tu solicitud:\n"
    "• Podés enviar un audio o un mensaje de texto con:\n"
    "  - Tu nombre y teléfono\n"
    "  - Repuestos que necesitás\n"
    "  - Marca, modelo y año del vehículo\n"
    "  - Tu ciudad"
)
