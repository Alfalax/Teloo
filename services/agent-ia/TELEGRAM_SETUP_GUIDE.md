# 🤖 Guía de Configuración de Telegram Bot

Esta guía te ayudará a configurar un bot de Telegram para probar el servicio Agent IA sin necesidad de configurar WhatsApp Business API.

---

## 📋 Requisitos Previos

- Cuenta de Telegram (descarga la app si no la tienes)
- Acceso a internet
- 5 minutos de tu tiempo ⏱️

---

## 🚀 Paso 1: Crear el Bot con BotFather

1. **Abre Telegram** y busca `@BotFather`
2. **Inicia conversación** con `/start`
3. **Crea un nuevo bot** con el comando:
   ```
   /newbot
   ```
4. **Elige un nombre** para tu bot (ej: "TeLOO Repuestos Bot")
5. **Elige un username** (debe terminar en "bot", ej: "teloo_repuestos_bot")
6. **Guarda el token** que te da BotFather (se ve así):
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

---

## ⚙️ Paso 2: Configurar el Servicio

### Opción A: Usando archivo .env

1. Crea un archivo `.env` en `services/agent-ia/`:
   ```bash
   cd services/agent-ia
   cp .env.example .env
   ```

2. Edita el archivo `.env` y agrega tu token:
   ```bash
   # Telegram Configuration
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_ENABLED=true
   
   # Redis (necesario)
   REDIS_URL=redis://localhost:6379
   
   # Core API (necesario)
   CORE_API_URL=http://localhost:8000
   
   # Al menos un proveedor LLM (recomendado: Deepseek por bajo costo)
   DEEPSEEK_API_KEY=tu_deepseek_api_key
   
   # O usa Ollama local (gratis)
   LOCAL_LLM_ENABLED=true
   LOCAL_LLM_URL=http://localhost:11434
   ```

### Opción B: Variables de entorno directas

```bash
export TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_ENABLED=true
export REDIS_URL="redis://localhost:6379"
export CORE_API_URL="http://localhost:8000"
export DEEPSEEK_API_KEY="tu_deepseek_api_key"
```

---

## 🏃 Paso 3: Iniciar los Servicios

### 1. Iniciar Redis (si no está corriendo)

```bash
# Con Docker
docker run -d -p 6379:6379 redis:latest

# O con instalación local
redis-server
```

### 2. Iniciar Core API (si no está corriendo)

```bash
cd services/core-api
python main.py
```

### 3. Iniciar Agent IA

```bash
cd services/agent-ia

# Instalar dependencias (primera vez)
pip install -r requirements.txt

# Iniciar servicio
python main.py
```

El servicio debería iniciar en `http://localhost:8001`

---

## 🔗 Paso 4: Configurar el Webhook

### Opción A: Usando ngrok (para testing local)

1. **Instala ngrok** (si no lo tienes):
   ```bash
   # Windows (con Chocolatey)
   choco install ngrok
   
   # Mac (con Homebrew)
   brew install ngrok
   
   # O descarga de https://ngrok.com/download
   ```

2. **Inicia ngrok** para exponer tu servicio local:
   ```bash
   ngrok http 8001
   ```

3. **Copia la URL HTTPS** que te da ngrok (ej: `https://abc123.ngrok.io`)

4. **Configura el webhook** usando curl o Postman:
   ```bash
   curl -X POST "http://localhost:8001/v1/telegram/set-webhook?webhook_url=https://abc123.ngrok.io/v1/telegram/webhook"
   ```

   O abre en tu navegador:
   ```
   http://localhost:8001/v1/telegram/set-webhook?webhook_url=https://abc123.ngrok.io/v1/telegram/webhook
   ```

### Opción B: Usando servidor público

Si tienes un servidor con dominio público:

```bash
curl -X POST "http://localhost:8001/v1/telegram/set-webhook?webhook_url=https://tudominio.com/v1/telegram/webhook"
```

---

## ✅ Paso 5: Probar el Bot

1. **Busca tu bot** en Telegram por el username que elegiste
2. **Inicia conversación** con `/start`
3. **Envía un mensaje** de prueba:
   ```
   Necesito pastillas de freno para Toyota Corolla 2015
   ```

4. **El bot debería responder** procesando tu mensaje con el sistema NLP

---

## 🧪 Ejemplos de Mensajes de Prueba

### Mensaje Simple
```
Necesito pastillas de freno
```

### Mensaje Completo
```
Necesito pastillas de freno delanteras para Toyota Corolla 2015. 
Estoy en Bogotá. Mi nombre es Juan Pérez.
```

### Mensaje con Múltiples Repuestos
```
Necesito:
- Pastillas de freno
- Discos de freno
- Aceite 5W30

Para Chevrolet Aveo 2012
```

### Enviar Imagen
Envía una foto del repuesto que necesitas y el bot la analizará con IA

---

## 📊 Verificar Estado del Bot

### Ver estado del webhook:
```bash
curl http://localhost:8001/v1/telegram/status
```

### Ver logs del servicio:
Los logs aparecerán en la consola donde ejecutaste `python main.py`

---

## 🔧 Comandos Útiles

### Eliminar webhook (para testing local sin ngrok):
```bash
curl -X POST http://localhost:8001/v1/telegram/delete-webhook
```

### Ver información del webhook:
```bash
curl http://localhost:8001/v1/telegram/status
```

### Verificar que el servicio está corriendo:
```bash
curl http://localhost:8001/health
```

---

## 🐛 Troubleshooting

### El bot no responde

1. **Verifica que el servicio está corriendo**:
   ```bash
   curl http://localhost:8001/health
   ```

2. **Verifica el webhook**:
   ```bash
   curl http://localhost:8001/v1/telegram/status
   ```

3. **Revisa los logs** en la consola del servicio

4. **Verifica que ngrok está corriendo** (si lo usas)

### Error "Bot token is invalid"

- Verifica que copiaste correctamente el token de BotFather
- Asegúrate de que no hay espacios al inicio o final del token

### Error "Connection refused"

- Verifica que Redis está corriendo: `redis-cli ping` (debería responder "PONG")
- Verifica que Core API está corriendo: `curl http://localhost:8000/health`

### El bot recibe mensajes pero no procesa

- Verifica que tienes al menos un proveedor LLM configurado (Deepseek, Ollama, etc.)
- Revisa los logs para ver errores específicos

---

## 🎯 Flujo Completo de Testing

1. ✅ Crear bot con BotFather
2. ✅ Configurar token en .env
3. ✅ Iniciar Redis
4. ✅ Iniciar Core API
5. ✅ Iniciar Agent IA
6. ✅ Configurar webhook con ngrok
7. ✅ Enviar mensaje de prueba
8. ✅ Verificar respuesta del bot
9. ✅ Probar flujo completo de solicitud

---

## 📚 Recursos Adicionales

- **Telegram Bot API Docs**: https://core.telegram.org/bots/api
- **BotFather Commands**: https://core.telegram.org/bots#6-botfather
- **ngrok Docs**: https://ngrok.com/docs

---

## 💡 Ventajas de Telegram vs WhatsApp para Testing

| Característica | Telegram | WhatsApp |
|----------------|----------|----------|
| **Setup** | 5 minutos | Días (aprobación Meta) |
| **Costo** | Gratis | Requiere cuenta Business |
| **Webhook** | Simple | Requiere signature validation |
| **Testing Local** | Fácil con ngrok | Requiere HTTPS público |
| **Límites** | Muy generosos | Estrictos |
| **Multimedia** | Soportado | Soportado |

---

## 🚀 Próximos Pasos

Una vez que hayas probado con Telegram y todo funcione correctamente, puedes:

1. Migrar a WhatsApp Business API para producción
2. Configurar múltiples proveedores LLM para mejor performance
3. Ajustar los prompts y respuestas según tus necesidades
4. Implementar métricas y monitoreo

---

**¿Necesitas ayuda?** Revisa los logs del servicio o contacta al equipo de desarrollo.
