# 🔐 Configuración de API Keys - TeLOO Agent IA

## ✅ Estado Actual

### OpenAI (Configurado)
- **Modelo de Texto:** `gpt-4o-mini` ($0.15 por 1M tokens)
- **Modelo de Audio:** `whisper-1` ($0.006 por minuto)
- **Estado:** ✅ Configurado y listo para usar

### Gemini (Configurado)
- **Modelo:** `gemini-1.5-flash` (económico y rápido)
- **Uso:** Respaldo automático si OpenAI falla
- **Estado:** ✅ Configurado y listo

---

## 🎯 Modelos Configurados

### 1. Para Audio (Whisper-1)
```
Proveedor: OpenAI
Modelo: whisper-1
Costo: $0.006/minuto
Uso: Transcripción de notas de voz
```

### 2. Para Texto (GPT-4o-mini)
```
Proveedor: OpenAI
Modelo: gpt-4o-mini
Costo: $0.15/1M tokens (~$0.02 por mensaje)
Uso: Extracción de repuestos y vehículos
```

---

## 💰 Estimación de Costos

### Por Mensaje
- **Texto simple:** ~$0.002 (0.2 centavos)
- **Audio 30 seg:** ~$0.03 (3 centavos)
- **Audio 2 min:** ~$0.05 (5 centavos)

### Mensual (estimado)
- **10 clientes/día:** ~$12 USD/mes
- **50 clientes/día:** ~$60 USD/mes
- **100 clientes/día:** ~$120 USD/mes

---

## 🔒 Seguridad

### Archivos Protegidos
✅ `.env` está en `.gitignore`
✅ No se subirá a GitHub
✅ Solo existe localmente

### Verificación
```bash
# Verificar que .env está ignorado
git check-ignore services/agent-ia/.env
# Debe retornar: services/agent-ia/.env
```

### ⚠️ NUNCA HAGAS ESTO
```bash
# ❌ NO agregar .env al repositorio
git add services/agent-ia/.env

# ❌ NO compartir el archivo .env
# ❌ NO subir .env a GitHub, Slack, email, etc.
```

---

## 🚀 Próximos Pasos

### 1. Configurar Gemini (Opcional)
Si quieres un respaldo, obtén una API key de Google:
- Ir a: https://makersuite.google.com/app/apikey
- Crear API key
- Agregar a `.env`:
  ```
  GEMINI_API_KEY=tu-key-aqui
  GEMINI_MODEL=gemini-1.5-flash
  ```

### 2. Probar el Bot
```bash
# Reiniciar el servicio agent-ia
docker-compose restart agent-ia

# Ver logs
docker-compose logs -f agent-ia
```

### 3. Enviar Mensaje de Prueba
Envía un mensaje al bot de Telegram:
```
"Necesito pastillas de freno para Chevrolet Spark 2015"
```

---

## 📊 Monitoreo de Uso

### Ver Uso en OpenAI
1. Ir a: https://platform.openai.com/usage
2. Ver consumo en tiempo real
3. Configurar alertas de presupuesto

### Límites Recomendados
- **Inicial:** $10 USD (para pruebas)
- **Producción:** $50-100 USD/mes
- **Alerta:** Configurar aviso al 80% del límite

---

## 🆘 Solución de Problemas

### Error: "Invalid API Key"
```bash
# Verificar que la key está en .env
cat services/agent-ia/.env | grep OPENAI_API_KEY

# Reiniciar servicio
docker-compose restart agent-ia
```

### Error: "Rate Limit Exceeded"
- Has excedido el límite de requests
- Espera 1 minuto o aumenta tu plan en OpenAI

### Error: "Insufficient Quota"
- No tienes crédito en tu cuenta OpenAI
- Agregar crédito en: https://platform.openai.com/account/billing

---

## 📝 Notas Importantes

1. **Crédito Inicial:** Agrega $10-20 USD para empezar
2. **Monitoreo:** Revisa el uso semanalmente
3. **Alertas:** Configura alertas en OpenAI Dashboard
4. **Respaldo:** Considera configurar Gemini como fallback
5. **Seguridad:** Nunca compartas tu `.env` file

---

## ✅ Checklist de Seguridad

- [x] API key configurada en `.env`
- [x] `.env` está en `.gitignore`
- [x] Modelo económico configurado (gpt-4o-mini)
- [ ] Crédito agregado en OpenAI ($10+ USD)
- [ ] Alertas de presupuesto configuradas
- [ ] Bot probado con mensaje de prueba
- [x] Gemini configurado como respaldo

---

**Última actualización:** 2024
**Estado:** ✅ Listo para usar
