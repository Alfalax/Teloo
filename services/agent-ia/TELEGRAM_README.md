# 🤖 Telegram Bot Integration

Integración de Telegram Bot para testing del servicio Agent IA sin necesidad de configurar WhatsApp Business API.

## 🎯 ¿Por qué Telegram?

- ✅ **Setup en 5 minutos** vs días con WhatsApp
- ✅ **Gratis** vs costos de WhatsApp Business
- ✅ **Fácil de probar localmente** con ngrok
- ✅ **Mismo flujo** que WhatsApp (reutiliza toda la lógica)
- ✅ **API simple** sin validaciones complejas

## 🚀 Quick Start

### 1. Crear Bot

Habla con [@BotFather](https://t.me/botfather) en Telegram:

```
/newbot
```

Guarda el token que te da.

### 2. Configurar

Crea `.env` con tu token:

```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ENABLED=true
REDIS_URL=redis://localhost:6379
CORE_API_URL=http://localhost:8000
DEEPSEEK_API_KEY=tu_key  # O usa Ollama local
```

### 3. Iniciar Servicios

```bash
# Terminal 1: Redis
docker run -d -p 6379:6379 redis

# Terminal 2: Core API
cd services/core-api
python main.py

# Terminal 3: Agent IA
cd services/agent-ia
python main.py

# Terminal 4: Procesador de mensajes (opcional, para background processing)
python start_telegram_bot.py
```

### 4. Configurar Webhook

Con ngrok:

```bash
# Terminal 5: ngrok
ngrok http 8001

# Luego configura el webhook
curl -X POST "http://localhost:8001/v1/telegram/set-webhook?webhook_url=https://TU-URL-NGROK.ngrok.io/v1/telegram/webhook"
```

### 5. Probar

Busca tu bot en Telegram y envía:

```
Necesito pastillas de freno para Toyota Corolla 2015
```

## 📁 Archivos Creados

```
services/agent-ia/
├── app/
│   ├── models/
│   │   └── telegram.py                    # Modelos Telegram
│   ├── routers/
│   │   └── telegram.py                    # Endpoints webhook
│   └── services/
│       ├── telegram_service.py            # Cliente Telegram API
│       └── telegram_message_processor.py  # Procesador de mensajes
├── TELEGRAM_SETUP_GUIDE.md               # Guía detallada
├── TELEGRAM_README.md                    # Este archivo
└── start_telegram_bot.py                 # Script de inicio rápido
```

## 🔄 Arquitectura

```
Telegram Bot API
    ↓
Webhook Handler (/v1/telegram/webhook)
    ↓
Message Queue (Redis)
    ↓
Telegram Message Processor
    ↓
[Convierte a formato WhatsApp]
    ↓
NLP Service (existente) ✅
    ↓
LLM Router (existente) ✅
    ↓
Conversation Manager (existente) ✅
    ↓
Solicitud Service (existente) ✅
```

**Solo se agregó la capa de Telegram**, todo lo demás se reutiliza.

## 🎨 Características

### Mensajes Soportados

- ✅ **Texto**: Procesamiento NLP completo
- ✅ **Imágenes**: Análisis con Anthropic Claude Vision
- ✅ **Documentos**: Extracción con OpenAI GPT-4
- ✅ **Audio**: Transcripción con Anthropic Claude

### Funcionalidades

- ✅ **Conversaciones multi-turno**: Mantiene contexto
- ✅ **Preguntas aclaratorias**: Solicita información faltante
- ✅ **Creación de solicitudes**: Integración con Core API
- ✅ **Envío de resultados**: Notifica ofertas al cliente
- ✅ **Rate limiting**: 100 req/min/IP
- ✅ **Formato Markdown**: Mensajes bien formateados

## 📊 Endpoints

### POST /v1/telegram/webhook
Recibe actualizaciones de Telegram

### GET /v1/telegram/status
Estado del bot y webhook

### POST /v1/telegram/set-webhook
Configura URL del webhook

### POST /v1/telegram/delete-webhook
Elimina webhook

## 🧪 Testing

### Mensaje Simple
```
Necesito pastillas de freno
```

### Mensaje Completo
```
Necesito pastillas de freno para Toyota Corolla 2015
Estoy en Bogotá
Mi nombre es Juan Pérez
```

### Con Imagen
Envía foto del repuesto

### Con Múltiples Repuestos
```
Necesito:
- Pastillas de freno
- Discos de freno  
- Aceite 5W30

Para Chevrolet Aveo 2012
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Telegram
TELEGRAM_BOT_TOKEN=tu_token
TELEGRAM_ENABLED=true

# Redis (requerido)
REDIS_URL=redis://localhost:6379

# Core API (requerido)
CORE_API_URL=http://localhost:8000

# LLM Providers (al menos uno)
DEEPSEEK_API_KEY=tu_key          # Recomendado (bajo costo)
OLLAMA_BASE_URL=http://localhost:11434  # O local (gratis)
GEMINI_API_KEY=tu_key            # Opcional
OPENAI_API_KEY=tu_key            # Opcional
ANTHROPIC_API_KEY=tu_key         # Opcional

# Configuración
CONVERSATION_TTL_HOURS=1
RATE_LIMIT_PER_MINUTE=100
LOG_LEVEL=INFO
```

## 📈 Monitoreo

### Ver logs
```bash
# En la terminal donde corre el servicio
tail -f logs/agent-ia.log
```

### Verificar estado
```bash
curl http://localhost:8001/v1/telegram/status
```

### Verificar webhook
```bash
curl http://localhost:8001/v1/telegram/status | jq '.webhook_info'
```

## 🐛 Troubleshooting

### Bot no responde

1. Verifica servicio: `curl http://localhost:8001/health`
2. Verifica webhook: `curl http://localhost:8001/v1/telegram/status`
3. Verifica ngrok: Debe estar corriendo
4. Revisa logs del servicio

### Error "Invalid token"

- Copia correctamente el token de BotFather
- Sin espacios al inicio/final

### Error "Connection refused"

- Redis: `redis-cli ping` → debe responder "PONG"
- Core API: `curl http://localhost:8000/health`

## 🔄 Migración a WhatsApp

Cuando estés listo para producción:

1. Mantén el código de Telegram para testing
2. Configura WhatsApp Business API
3. Ambos pueden coexistir
4. Usa Telegram para desarrollo, WhatsApp para producción

## 📚 Documentación

- [Guía de Setup Completa](./TELEGRAM_SETUP_GUIDE.md)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [BotFather](https://core.telegram.org/bots#6-botfather)

## 💡 Tips

- Usa ngrok para testing local
- Configura múltiples LLMs para mejor performance
- Revisa logs para debugging
- Prueba diferentes tipos de mensajes
- Usa Markdown para formatear respuestas

## 🎉 ¡Listo!

Ahora puedes probar todo el flujo del Agent IA sin configurar WhatsApp. Cuando funcione correctamente, migrar a WhatsApp será trivial.
