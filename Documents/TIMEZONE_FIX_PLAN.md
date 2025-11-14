# Plan de Corrección de Timezone

## Problema Actual

La aplicación tiene manejo inconsistente de fechas:
- ❌ Algunos usan `datetime.now()` (hora local del servidor)
- ❌ Algunos usan `datetime.utcnow()` (deprecated en Python 3.12)
- ✅ Algunos usan `datetime.now(timezone.utc)` (correcto)
- ✅ Config DB: `timezone="America/Bogota"`

## Solución

### Backend: Siempre UTC
- Usar `datetime.now(timezone.utc)` en todo el código
- Base de datos almacena en UTC
- Tortoise ORM convierte automáticamente

### Frontend: Mostrar hora local
- Recibir fechas en formato ISO 8601 con UTC
- Convertir a hora local del navegador
- Mostrar en formato legible para Colombia

### Docker: Configurar timezone
- Contenedores con TZ=America/Bogota
- PostgreSQL con timezone UTC

## Archivos a Corregir

### Críticos (afectan funcionalidad)
1. `services/core-api/routers/auth.py` - ultimo_login
2. `services/core-api/services/ofertas_service.py` - fecha_expiracion, updated_at
3. `services/core-api/services/evaluacion_service.py` - fecha_evaluacion
4. `services/core-api/services/pqr_service.py` - fecha_respuesta
5. `services/core-api/services/escalamiento_service.py` - fecha_escalamiento

### Medios (afectan logs/eventos)
6. `services/core-api/services/scheduler_service.py` - executed_at
7. Varios archivos con timestamps en eventos

### Bajos (tests)
8. Archivos de tests con datetime.now()

## Implementación

### Fase 1: Backend crítico (ahora)
- Corregir archivos críticos
- Crear helper function para fechas

### Fase 2: Frontend (ahora)
- Crear utility para formateo de fechas
- Actualizar componentes que muestran fechas

### Fase 3: Docker (después)
- Actualizar docker-compose.yml
- Agregar variables de entorno

### Fase 4: Tests (después)
- Actualizar mocks de tests
