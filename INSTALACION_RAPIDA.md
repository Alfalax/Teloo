# 🚀 Instalación Rápida: Notificación al Cliente

## ⚡ Pasos de Instalación (5 minutos)

### 1️⃣ Instalar Dependencias

```bash
cd services/core-api
pip install reportlab==4.0.7
```

O usando el archivo de requirements:

```bash
pip install -r requirements_notificacion_cliente.txt
```

### 2️⃣ Aplicar Migración de Base de Datos

```bash
psql -U teloo_user -d teloo_db -f scripts/add_client_response_fields.sql
```

**Esto agregará:**
- 4 nuevos campos a la tabla `solicitudes`
- 1 índice para consultas eficientes
- 1 parámetro de configuración

### 3️⃣ Verificar Instalación

```bash
python verify_notificacion_cliente_setup.py
```

**Resultado esperado:**
```
✅ PASSED: Imports
✅ PASSED: Files
✅ PASSED: Database Migration
✅ PASSED: Configuration
✅ PASSED: Scheduler
✅ PASSED: Endpoint

Total: 6/6 checks passed
🎉 All checks passed! System is ready.
```

### 4️⃣ Reiniciar Servicios

```bash
docker-compose restart core-api
```

O si no usas Docker:

```bash
# Detener el servicio
pkill -f "uvicorn.*core-api"

# Iniciar el servicio
cd services/core-api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5️⃣ Ejecutar Tests (Opcional)

```bash
python test_notificacion_cliente_flow.py
```

## ✅ Verificación Post-Instalación

### Verificar Logs

```bash
# Ver logs del servicio
docker-compose logs -f core-api

# Buscar confirmación de jobs
docker-compose logs core-api | grep "Scheduled jobs configured"
```

**Deberías ver:**
```
INFO: Scheduled jobs configured
INFO: Job 5: notificar_clientes_ofertas_ganadoras
INFO: Job 6: enviar_recordatorios_cliente
```

### Verificar Base de Datos

```bash
psql -U teloo_user -d teloo_db -c "
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'solicitudes' 
AND column_name IN (
    'fecha_notificacion_cliente',
    'fecha_respuesta_cliente',
    'cliente_acepto',
    'respuesta_cliente_texto'
);"
```

**Resultado esperado:**
```
         column_name          |     data_type      
------------------------------+--------------------
 cliente_acepto               | boolean
 fecha_notificacion_cliente   | timestamp
 fecha_respuesta_cliente      | timestamp
 respuesta_cliente_texto      | text
```

### Verificar Endpoint

```bash
curl -X POST http://localhost:8000/docs
```

Buscar el endpoint: `POST /v1/solicitudes/{solicitud_id}/respuesta-cliente`

## 🔧 Troubleshooting

### Error: "No module named 'reportlab'"

**Solución:**
```bash
pip install reportlab==4.0.7
```

### Error: "relation 'solicitudes' does not exist"

**Solución:**
```bash
# Verificar que la base de datos existe
psql -U teloo_user -d teloo_db -c "\dt solicitudes"

# Si no existe, ejecutar migraciones principales primero
```

### Error: "Job not found in scheduler"

**Solución:**
```bash
# Reiniciar el servicio
docker-compose restart core-api

# Verificar logs
docker-compose logs core-api | grep "Scheduled jobs"
```

### Error: "Redis connection refused"

**Solución:**
```bash
# Verificar que Redis está corriendo
docker-compose ps redis

# Si no está corriendo, iniciarlo
docker-compose up -d redis
```

## 📊 Monitoreo Inicial

### Ver Notificaciones Enviadas

```bash
docker-compose logs -f core-api | grep "Cliente notificado"
```

### Ver Recordatorios

```bash
docker-compose logs -f core-api | grep "Recordatorio"
```

### Ver Respuestas Procesadas

```bash
docker-compose logs -f core-api | grep "Intención detectada"
```

## 🎯 Prueba Manual

### 1. Crear una solicitud de prueba
### 2. Esperar evaluación automática
### 3. Verificar que se envía notificación (logs)
### 4. Simular respuesta del cliente:

```bash
curl -X POST http://localhost:8000/v1/solicitudes/{solicitud_id}/respuesta-cliente \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-service-api-key" \
  -d '{
    "respuesta_texto": "acepto",
    "usar_nlp": true
  }'
```

## 📈 Métricas a Monitorear

Después de la instalación, monitorear:

1. **Tasa de notificación exitosa** (debe ser ~100%)
2. **Tiempo promedio de respuesta del cliente**
3. **Tasa de aceptación vs rechazo**
4. **Tasa de timeout** (debe ser baja)

## 🆘 Soporte

Si encuentras problemas:

1. Revisar logs: `docker-compose logs core-api`
2. Verificar setup: `python verify_notificacion_cliente_setup.py`
3. Revisar documentación: `IMPLEMENTACION_NOTIFICACION_CLIENTE.md`
4. Ejecutar tests: `python test_notificacion_cliente_flow.py`

## ✅ Checklist Final

- [ ] Dependencias instaladas (`reportlab`)
- [ ] Migración de BD aplicada
- [ ] Servicios reiniciados
- [ ] Verificación ejecutada (6/6 passed)
- [ ] Logs monitoreados
- [ ] Endpoint verificado
- [ ] Prueba manual exitosa

---

**Tiempo estimado:** 5 minutos  
**Dificultad:** Fácil  
**Prerequisitos:** Python 3.8+, PostgreSQL, Redis
