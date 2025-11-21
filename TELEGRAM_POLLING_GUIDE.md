# 🤖 Guía: Telegram Long Polling (Pruebas Locales)

## ✅ Ventajas de Long Polling

- ✅ **No necesitas VPS**
- ✅ **No necesitas dominio**
- ✅ **No necesitas HTTPS**
- ✅ **No necesitas IP pública**
- ✅ **Funciona desde tu máquina local**
- ✅ **Perfecto para desarrollo y pruebas**

---

## 🚀 Pasos para Probar

### **Paso 1: Crear Bot con BotFather**

1. Abre Telegram y busca [@BotFather](https://t.me/botfather)
2. Envía `/newbot`
3. Sigue las instrucciones:
   ```
   BotFather: Alright, a new bot. How are we going to call it?
   Tú: TeLOO Repuestos Bot
   
   BotFather: Good. Now let's choose a username for your bot.
   Tú: teloo_repuestos_bot
   
   BotFather: Done! Your token is: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
4. **Copia el token** (lo necesitarás en el siguiente paso)

---

### **Paso 2: Configurar Variables de Entorno**

Edita el archivo `.env` en `services/agent-ia/`:

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ENABLED=true

# API Keys (necesarias para procesamiento)
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...

# Core API
CORE_API_URL=http://core-api:8000

# Redis
REDIS_URL=redis://redis:6379
```

---

### **Paso 3: Iniciar Servicios Docker**

```bash
# Desde la raíz del proyecto
docker-compose up -d postgres redis core-api

# Verificar que estén corriendo
docker-compose ps
```

---

### **Paso 4: Iniciar el Bot en Modo Polling**

**Opción A: Dentro del contenedor Docker**

```bash
# Entrar al contenedor
docker-compose exec agent-ia bash

# Iniciar polling
python start_polling.py
```

**Opción B: Directamente en tu máquina (sin Docker)**

```bash
# Navegar al directorio
cd services/agent-ia

# Instalar dependencias (si no lo has hecho)
pip install -r requirements.txt

# Iniciar polling
python start_polling.py
```

---

### **Paso 5: Probar el Bot**

Abre Telegram y busca tu bot (ej: `@teloo_repuestos_bot`)

#### **Prueba 1: Mensaje de Texto**
```
Tú: Hola, necesito pastillas de freno para Chevrolet Spark 2015
Bot: [Procesando mensaje...]
```

#### **Prueba 2: Nota de Voz**
```
Grabar audio: "Necesito discos de freno delanteros para Mazda 3 del 2018"
Bot: [Transcribiendo y procesando...]
```

#### **Prueba 3: Imagen**
```
Enviar foto de un repuesto con código visible
Bot: [Analizando imagen...]
```

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

2024-11-19 20:00:00 - INFO - TelegramPollingService initialized
2024-11-19 20:00:00 - INFO - 🚀 Starting Telegram Long Polling...
2024-11-19 20:00:01 - INFO - ✅ Bot connected: @teloo_repuestos_bot
2024-11-19 20:00:01 - INFO -    Name: TeLOO Repuestos Bot
2024-11-19 20:00:01 - INFO - 📡 Polling loop started. Waiting for messages...

# Cuando envías un mensaje:
2024-11-19 20:01:15 - INFO - 📨 Received 1 update(s)
2024-11-19 20:01:15 - INFO - 💬 Text from @tu_usuario: Necesito pastillas de freno...
2024-11-19 20:01:16 - INFO - Processing text message...
2024-11-19 20:01:17 - INFO - ✅ Message sent to 123456789
```

---

## 🔧 Comandos Útiles

### Detener el Bot
```bash
# Presionar Ctrl+C en la terminal donde corre el bot
```

### Ver Logs en Tiempo Real
```bash
# Si corre en Docker
docker-compose logs -f agent-ia

# Si corre localmente
# Los logs aparecen directamente en la terminal
```

### Reiniciar el Bot
```bash
# Detener (Ctrl+C) y volver a ejecutar
python start_polling.py
```

---

## 🐛 Troubleshooting

### Error: "TELEGRAM_BOT_TOKEN not configured"
```bash
# Verificar que el token esté en .env
cat services/agent-ia/.env | grep TELEGRAM_BOT_TOKEN

# Si no está, agregarlo:
echo "TELEGRAM_BOT_TOKEN=tu-token-aqui" >> services/agent-ia/.env
```

### Error: "Failed to get bot info"
```bash
# Verificar que el token sea correcto
curl "https://api.telegram.org/bot<TU_TOKEN>/getMe"

# Debe retornar información del bot
```

### El bot no responde
```bash
# 1. Verificar que el polling esté corriendo
# 2. Verificar logs para ver si recibe mensajes
# 3. Verificar que Redis y Core API estén corriendo
docker-compose ps

# 4. Verificar API keys en .env
cat services/agent-ia/.env | grep API_KEY
```

---

## 📈 Próximos Pasos

Una vez que funcione en local con Long Polling:

1. **Probar todos los tipos de mensajes** (texto, audio, imágenes)
2. **Verificar que se crean solicitudes** en la base de datos
3. **Ajustar prompts** según los resultados
4. **Cuando esté listo para producción** → Migrar a Webhook en VPS

---

## 🎯 Comparación: Desarrollo vs Producción

| Aspecto | Desarrollo (Polling) | Producción (Webhook) |
|---------|---------------------|---------------------|
| **Setup** | 5 minutos | 2-3 horas |
| **Costo** | $0 | ~$10/mes |
| **Escalabilidad** | Baja | Alta |
| **Latencia** | ~1-2 seg | <500ms |
| **Ideal para** | Pruebas, desarrollo | Usuarios reales |

---

## ✅ Checklist

Antes de iniciar el polling:

- [ ] Creaste el bot con BotFather
- [ ] Copiaste el token
- [ ] Configuraste TELEGRAM_BOT_TOKEN en .env
- [ ] Configuraste las API keys (OpenAI, Deepseek)
- [ ] Iniciaste Docker (postgres, redis, core-api)
- [ ] Ejecutaste `python start_polling.py`
- [ ] Ves el mensaje "Polling loop started"

---

## 🎉 ¡Listo!

Ahora puedes probar tu bot desde tu máquina local sin necesidad de VPS, dominio o configuraciones complejas.

Cuando estés listo para producción, simplemente:
1. Sube a un VPS
2. Cambia de polling a webhook
3. Configura HTTPS con Nginx

¡Pero para pruebas, Long Polling es perfecto! 🚀
