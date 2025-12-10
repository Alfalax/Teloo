# 🔐 Guía de Seguridad - API Keys

## ✅ Configuración Completada

Tu proyecto está configurado de forma segura:

### 1. Archivo `.env` Protegido
- ✅ El archivo `.env` está en `.gitignore`
- ✅ NO se subirá a GitHub automáticamente
- ✅ Contiene tus claves secretas

### 2. Archivo `.env.example` Público
- ✅ Es una plantilla sin claves reales
- ✅ Se puede subir a GitHub sin problemas
- ✅ Ayuda a otros desarrolladores a configurar el proyecto

---

## 🔑 Cómo Agregar tu API Key de OpenAI

### Paso 1: Obtén tu API Key
1. Ve a: https://platform.openai.com/api-keys
2. Inicia sesión o crea una cuenta
3. Haz clic en "Create new secret key"
4. Copia la clave (empieza con `sk-...`)

### Paso 2: Agrega la Clave al Archivo `.env`
1. Abre el archivo: `services/agent-ia/.env`
2. Busca la línea: `OPENAI_API_KEY=TU_API_KEY_AQUI`
3. Reemplaza `TU_API_KEY_AQUI` con tu clave real:
   ```bash
   OPENAI_API_KEY=sk-proj-abc123xyz...
   ```
4. Guarda el archivo

### Paso 3: Verifica que Funcione
```bash
# Reinicia el servicio
docker-compose restart agent-ia

# Verifica los logs
docker-compose logs -f agent-ia
```

---

## 🚨 Reglas de Seguridad IMPORTANTES

### ❌ NUNCA Hagas Esto:
- ❌ NO subas el archivo `.env` a GitHub
- ❌ NO compartas tu API key en chat, email o Slack
- ❌ NO pongas la API key directamente en el código
- ❌ NO hagas commit de archivos con claves reales
- ❌ NO compartas screenshots que muestren tu API key

### ✅ SIEMPRE Haz Esto:
- ✅ Usa variables de entorno (`.env`)
- ✅ Verifica `.gitignore` antes de hacer push
- ✅ Rota (cambia) tus claves si se exponen
- ✅ Usa claves diferentes para desarrollo y producción
- ✅ Revisa los commits antes de hacer push

---

## 🔍 Verificar que tu API Key NO se Subirá

### Antes de hacer `git push`:
```bash
# Ver qué archivos se van a subir
git status

# Verificar que .env NO aparezca en la lista
# Si aparece, DETENTE y revisa tu .gitignore
```

### Verificar .gitignore:
```bash
# Buscar si .env está ignorado
cat .gitignore | grep ".env"

# Deberías ver:
# .env
# .env.local
# .env.development
# .env.production
```

---

## 🛡️ Qué Hacer si Expones tu API Key

### Si accidentalmente subes tu clave a GitHub:

1. **Revoca la clave inmediatamente:**
   - Ve a: https://platform.openai.com/api-keys
   - Elimina la clave expuesta

2. **Crea una nueva clave:**
   - Genera una nueva API key
   - Actualiza tu archivo `.env`

3. **Limpia el historial de Git (si es necesario):**
   ```bash
   # Contacta a tu equipo de DevOps
   # Puede requerir reescribir el historial de Git
   ```

4. **Verifica cargos:**
   - Revisa tu cuenta de OpenAI por uso no autorizado
   - Configura límites de gasto

---

## 💰 Configuración de Costos Actual

### Modelos Configurados:
- **Texto:** `gpt-4o-mini` → $0.15 por 1M tokens (~$0.02 por mensaje)
- **Audio:** `whisper-1` → $0.006 por minuto

### Costos Estimados:
- 100 mensajes de texto: ~$2 USD
- 50 audios de 30 seg: ~$1.50 USD
- Total mensual (uso moderado): $10-20 USD

### Configurar Límites en OpenAI:
1. Ve a: https://platform.openai.com/account/billing/limits
2. Configura un límite mensual (ej: $50 USD)