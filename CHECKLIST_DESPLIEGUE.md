# ✅ Checklist de Despliegue: Notificación al Cliente

## 📋 Pre-Despliegue

### Verificación de Código
- [x] Todos los servicios implementados
- [x] Endpoint REST creado
- [x] Jobs programados configurados
- [x] Modelo de datos actualizado
- [x] Tests creados y pasando

### Verificación de Documentación
- [x] Guía técnica completa
- [x] Diagramas de flujo
- [x] Ejemplos de uso
- [x] Guía de instalación
- [x] Troubleshooting

### Verificación de Scripts
- [x] Migración de BD lista
- [x] Script de verificación listo
- [x] Tests automatizados listos
- [x] Requirements definidos

---

## 🚀 Despliegue (5 minutos)

### Paso 1: Instalar Dependencias
```bash
cd services/core-api
pip install reportlab==4.0.7
```
- [ ] Ejecutado
- [ ] Sin errores
- [ ] Verificado con `pip list | grep reportlab`

### Paso 2: Aplicar Migración de Base de Datos
```bash
psql -U teloo_user -d teloo_db -f scripts/add_client_response_fields.sql
```
- [ ] Ejecutado
- [ ] Sin errores
- [ ] Verificado con query de validación

**Query de verificación:**
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'solicitudes' 
AND column_name IN (
    'fecha_notificacion_cliente',
    'fecha_respuesta_cliente',
    'cliente_acepto',
    'respuesta_cliente_texto'
);
```
- [ ] 4 columnas retornadas

### Paso 3: Verificar Setup
```bash
python verify_notificacion_cliente_setup.py
```
- [ ] Ejecutado
- [ ] 6/6 checks passed
- [ ] Sin errores

### Paso 4: Reiniciar Servicios
```bash
docker-compose restart core-api
```
- [ ] Ejecutado
- [ ] Servicio reiniciado correctamente
- [ ] Sin errores en logs

**Verificar logs:**
```bash
docker-compose logs core-api | grep "Scheduled jobs configured"
```
- [ ] Mensaje encontrado
- [ ] Jobs 5 y 6 listados

### Paso 5: Ejecutar Tests
```bash
python test_notificacion_cliente_flow.py
```
- [ ] Ejecutado
- [ ] 5/5 tests passed
- [ ] PDF generado correctamente

---

## 🔍 Post-Despliegue

### Verificación de Servicios

#### 1. Verificar Endpoint
```bash
curl http://localhost:8000/docs
```
- [ ] Endpoint visible: `POST /v1/solicitudes/{solicitud_id}/respuesta-cliente`
- [ ] Documentación correcta

#### 2. Verificar Jobs Programados
```bash
docker-compose logs core-api | grep -E "(Job 5|Job 6)"
```
- [ ] Job 5 configurado (notificar_clientes_ofertas_ganadoras)
- [ ] Job 6 configurado (enviar_recordatorios_cliente)

#### 3. Verificar Base de Datos
```sql
-- Verificar campos
\d solicitudes

-- Verificar índice
\di idx_solicitudes_pending_response

-- Verificar parámetro
SELECT * FROM parametros_configuracion 
WHERE clave = 'timeout_respuesta_cliente_horas';
```
- [ ] Campos agregados
- [ ] Índice creado
- [ ] Parámetro configurado

#### 4. Verificar Redis
```bash
docker-compose ps redis
```
- [ ] Redis corriendo
- [ ] Sin errores

---

## 🧪 Prueba Manual

### Escenario 1: Notificación Automática

1. **Crear solicitud de prueba**
   - [ ] Solicitud creada
   - [ ] Estado: ABIERTA

2. **Esperar evaluación automática**
   - [ ] Ofertas recibidas
   - [ ] Evaluación ejecutada
   - [ ] Estado: EVALUADA

3. **Verificar notificación**
   ```bash
   docker-compose logs -f core-api | grep "Cliente notificado"
   ```
   - [ ] Notificación enviada
   - [ ] PDF generado
   - [ ] Evento publicado a Redis

### Escenario 2: Respuesta del Cliente

1. **Simular respuesta de aceptación**
   ```bash
   curl -X POST http://localhost:8000/v1/solicitudes/{id}/respuesta-cliente \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key" \
     -d '{"respuesta_texto": "acepto", "usar_nlp": true}'
   ```
   - [ ] Request exitoso (200)
   - [ ] Response correcta
   - [ ] Estados actualizados

2. **Verificar en base de datos**
   ```sql
   SELECT 
       codigo_solicitud,
       cliente_acepto,
       respuesta_cliente_texto,
       fecha_respuesta_cliente
   FROM solicitudes
   WHERE id = '{id}';
   ```
   - [ ] cliente_acepto = true
   - [ ] respuesta_cliente_texto guardada
   - [ ] fecha_respuesta_cliente registrada

3. **Verificar estados de ofertas**
   ```sql
   SELECT estado, COUNT(*) 
   FROM ofertas 
   WHERE solicitud_id = '{id}' 
   GROUP BY estado;
   ```
   - [ ] Ofertas en estado ACEPTADA

### Escenario 3: Recordatorios

1. **Simular solicitud con 12h de antigüedad**
   ```sql
   UPDATE solicitudes 
   SET fecha_notificacion_cliente = NOW() - INTERVAL '12 hours'
   WHERE id = '{id}';
   ```
   - [ ] Actualizado

2. **Esperar ejecución del job (cada hora)**
   ```bash
   docker-compose logs -f core-api | grep "Recordatorio intermedio"
   ```
   - [ ] Recordatorio enviado

### Escenario 4: Timeout

1. **Simular solicitud con 24h de antigüedad**
   ```sql
   UPDATE solicitudes 
   SET fecha_notificacion_cliente = NOW() - INTERVAL '24 hours'
   WHERE id = '{id}';
   ```
   - [ ] Actualizado

2. **Esperar ejecución del job**
   ```bash
   docker-compose logs -f core-api | grep "Timeout alcanzado"
   ```
   - [ ] Timeout detectado
   - [ ] Ofertas auto-rechazadas
   - [ ] Solicitud cerrada

---

## 📊 Monitoreo Continuo

### Métricas a Monitorear (Primera Semana)

#### Día 1-3
- [ ] Tasa de notificación exitosa (objetivo: >95%)
- [ ] Errores en generación de PDF (objetivo: 0)
- [ ] Tiempo de respuesta del endpoint (objetivo: <500ms)

#### Día 4-7
- [ ] Tasa de respuesta de clientes (baseline)
- [ ] Tasa de aceptación vs rechazo (baseline)
- [ ] Tasa de timeout (objetivo: <20%)

### Logs a Revisar Diariamente

```bash
# Notificaciones enviadas
docker-compose logs core-api | grep "Cliente notificado" | wc -l

# Errores
docker-compose logs core-api | grep "ERROR.*notificacion" | wc -l

# Respuestas procesadas
docker-compose logs core-api | grep "Intención detectada" | wc -l

# Timeouts
docker-compose logs core-api | grep "Timeout alcanzado" | wc -l
```

- [ ] Día 1 revisado
- [ ] Día 2 revisado
- [ ] Día 3 revisado
- [ ] Día 4 revisado
- [ ] Día 5 revisado
- [ ] Día 6 revisado
- [ ] Día 7 revisado

---

## 🐛 Troubleshooting

### Problema: PDF no se genera

**Síntomas:**
- Error: "No module named 'reportlab'"

**Solución:**
```bash
pip install reportlab==4.0.7
```
- [ ] Resuelto

### Problema: Endpoint no responde

**Síntomas:**
- 404 Not Found

**Solución:**
```bash
# Verificar que el servicio está corriendo
docker-compose ps core-api

# Reiniciar si es necesario
docker-compose restart core-api
```
- [ ] Resuelto

### Problema: Jobs no se ejecutan

**Síntomas:**
- No hay logs de jobs

**Solución:**
```bash
# Verificar scheduler
docker-compose logs core-api | grep "Scheduler started"

# Reiniciar servicio
docker-compose restart core-api
```
- [ ] Resuelto

### Problema: Redis no conecta

**Síntomas:**
- Error: "Connection refused"

**Solución:**
```bash
# Verificar Redis
docker-compose ps redis

# Iniciar Redis
docker-compose up -d redis
```
- [ ] Resuelto

---

## ✅ Firma de Aceptación

### Desarrollador
- [ ] Código implementado y testeado
- [ ] Documentación completa
- [ ] Tests pasando

**Firma:** _________________ **Fecha:** _________

### DevOps
- [ ] Migración aplicada
- [ ] Servicios desplegados
- [ ] Monitoreo configurado

**Firma:** _________________ **Fecha:** _________

### Product Manager
- [ ] Funcionalidad verificada
- [ ] Métricas definidas
- [ ] Aceptación final

**Firma:** _________________ **Fecha:** _________

---

## 📈 Métricas de Éxito (Primera Semana)

| Métrica | Objetivo | Real | Estado |
|---------|----------|------|--------|
| Tasa de notificación exitosa | >95% | __% | ⏳ |
| Tiempo de respuesta endpoint | <500ms | __ms | ⏳ |
| Tasa de respuesta clientes | >50% | __% | ⏳ |
| Tasa de aceptación | >60% | __% | ⏳ |
| Tasa de timeout | <20% | __% | ⏳ |
| Errores en producción | 0 | __ | ⏳ |

---

## 🎉 Despliegue Completado

- [ ] Todos los checks pasados
- [ ] Pruebas manuales exitosas
- [ ] Monitoreo configurado
- [ ] Equipo notificado
- [ ] Documentación compartida

**Fecha de despliegue:** _________________

**Responsable:** _________________

**Estado final:** ⏳ PENDIENTE / ✅ COMPLETADO

---

**Versión:** 1.0.0  
**Última actualización:** 20 de Noviembre, 2025
