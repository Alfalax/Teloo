# 🚀 Inicio Rápido: Telegram Bot

## ✅ Token Configurado

Tu bot está listo con el token: `8120912225:AAE1UsQxAfYTTMfrknLMB9Yn9TOZA6uuTZk`

---

## 📋 Pasos para Iniciar

### **Paso 1: Copiar archivo de configuración**

```bash
# Navegar al directorio
cd services/agent-ia

# Copiar el archivo de prueba
copy .env.test .env
```

### **Paso 2: Iniciar servicios básicos**

```bash
# Volver a la raíz
cd ../..

# Iniciar solo los servicios necesarios
docker-compose up -d postgres redis
```

### **Paso 3: Verificar que Redis esté corriendo**

```bash
docker-compose ps redis
```

Deberías ver:
```
NAME          STATUS
teloo-redis   Up X minutes (healthy)
```

### **Paso 4: Iniciar el bot**

**Opción A: Sin Docker (Recomendado para pruebas)**

```bash
cd services/agent-ia

# Instalar dependencias (solo la primera vez)
pip install python-telegram-bot httpx pydantic pydantic-settings

# Iniciar bot
python start_polling.py
```

**Opción B: Con Docker**

```bash
# Construir e iniciar
docker-compose up -d agent-ia

# Ver logs
docker-compose logs -f agent-ia
```

---

## 🎯 Probar el Bot

1. **Busca tu bot en Telegram**
   - Abre Telegram
   - Busca el nombre de tu bot (el que configuraste con BotFather)
   - O busca por username (ej: `@tu_bot_username`)

2. **Envía un mensaje de prueba**
   ```
   Hola
   ```

3. **El bot debería responder**
   - Si no tienes API keys configuradas, responderá con un mensaje básico
   - Si tienes API keys, procesará el mensaje completo

---

## 📊 Logs que Verás

```
============================================================
🤖 TeLOO V3 - Telegram Bot (Long Polling Mode)
============================================================

📝 Instrucciones:
   1. Asegúrate de tener TELEGRAM_BOT_TOKEN en .env
   2. Envía mensajes a tu bot en Telegram
   3. Presiona Ctrl+C para detener

============================================================

INFO - TelegramPollingService initialized
INFO - 🚀 Starting Telegram Long Polling...
INFO - Bot Token: 8120912225...
INFO - ✅ Bot connected: @tu_bot_username
INFO -    Name: Tu Bot Name
INFO - 📡 Polling loop started. Waiting for messages...

# Cuando envíes un mensaje:
INFO - 📨 Received 1 update(s)
INFO - 💬 Text from @tu_usuario: Hola
INFO - Processing text message...
INFO - ✅ Message sent to 123456789
```

---

## 🔧 Modo de Prueba (Sin API Keys)

Si no tienes API keys todavía, el bot funcionará en modo básico:

- ✅ Recibe mensajes
- ✅ Responde con mensajes simples
- ❌ No procesa audio (necesita OpenAI/Whisper)
- ❌ No extrae entidades (necesita Deepseek/OpenAI)

**Para funcionalidad completa, necesitas agregar al menos:**
- `OPENAI_API_KEY` (para audio y texto)

---

## 🎯 Agregar API Keys

Cuando tengas las API keys, edita el archivo `.env`:

```bash
# Abrir con notepad
notepad services/agent-ia/.env

# Agregar las keys:
OPENAI_API_KEY=sk-proj-tu-key-aqui
DEEPSEEK_API_KEY=sk-tu-key-aqui

# Guardar y reiniciar el bot
```

---

## 🐛 Troubleshooting

### Error: "TELEGRAM_BOT_TOKEN not configured"
```bash
# Verificar que el archivo .env existe
dir services\agent-ia\.env

# Si no existe, copiar desde .env.test
copy services\agent-ia\.env.test services\agent-ia\.env
```

### Error: "Connection refused" (Redis)
```bash
# Iniciar Redis
docker-compose up -d redis

# Verificar que esté corriendo
docker-compose ps redis
```

### El bot no responde
```bash
# 1. Verificar que el polling esté corriendo
# 2. Verificar logs para errores
# 3. Verificar que el token sea correcto

# Probar el token manualmente:
curl "https://api.telegram.org/bot8120912225:AAE1UsQxAfYTTMfrknLMB9Yn9TOZA6uuTZk/getMe"
```

---

## ✅ Checklist

- [ ] Copiaste `.env.test` a `.env`
- [ ] Iniciaste Redis (`docker-compose up -d redis`)
- [ ] Ejecutaste `python start_polling.py`
- [ ] Ves el mensaje "Polling loop started"
- [ ] Buscaste tu bot en Telegram
- [ ] Enviaste un mensaje de prueba

---

## 🎉 ¡Listo!

Tu bot está configurado y listo para recibir mensajes. 

**Próximos pasos:**
1. Prueba enviando mensajes de texto
2. Agrega API keys para funcionalidad completa
3. Prueba con audio cuando tengas OpenAI configurado

¿Necesitas ayuda? Revisa los logs para ver qué está pasando.
