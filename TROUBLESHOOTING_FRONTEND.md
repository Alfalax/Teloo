# Troubleshooting Frontend - TeLOO V3

## Problema: Páginas de Asesores, Inicio y PQR no funcionan

### Cambios Realizados

1. **Servicio de PQR** (`frontend/admin/src/services/pqr.ts`)
   - ✅ Agregado `baseURL` con `VITE_API_BASE_URL`
   - ✅ Agregados interceptores de autenticación
   - ✅ Agregado manejo de errores 401

2. **Servicio de Analytics** (`frontend/admin/src/services/analytics.ts`)
   - ✅ Corregida variable de entorno a `VITE_ANALYTICS_API_URL`
   - ✅ Apunta correctamente al puerto 8002
   - ✅ Agregado helper `_toISOString()` para convertir fechas a formato ISO
   - ✅ Todos los métodos ahora envían fechas en formato ISO correcto

3. **Hook useDashboard** (`frontend/admin/src/hooks/useDashboard.ts`)
   - ✅ Cambiado formato de fechas de `YYYY-MM-DD` a ISO completo
   - ✅ Usa `toISOString()` en lugar de `format()`

4. **Frontend reiniciado**
   - ✅ Proceso detenido y reiniciado para cargar nuevas configuraciones

### Problema Resuelto: Error 422 (Unprocessable Entity)

**Causa**: El backend de analytics esperaba fechas en formato ISO (con hora), pero el frontend enviaba formato `YYYY-MM-DD`

**Solución**: Agregado helper en el servicio de analytics que convierte automáticamente las fechas al formato correcto antes de enviarlas al backend.

### Verificación de Servicios

```bash
# Verificar que todos los servicios estén corriendo
docker ps

# Deberías ver:
# - teloo-core-api (puerto 8000) - HEALTHY
# - teloo-analytics (puerto 8002) - HEALTHY
# - teloo-postgres (puerto 5432) - HEALTHY
# - teloo-redis (puerto 6379) - HEALTHY
```

### Variables de Entorno

Archivo: `frontend/admin/.env`
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ANALYTICS_API_URL=http://localhost:8002
VITE_REALTIME_URL=http://localhost:8003
```

### Pasos para Verificar

1. **Abrir el navegador en modo incógnito** (para evitar cache)
   - Ir a: http://localhost:3000

2. **Iniciar sesión**
   - Usuario: admin@teloo.com
   - Password: (tu contraseña de admin)

3. **Verificar en la consola del navegador** (F12)
   - No debería haber errores de CORS
   - Las peticiones a `/asesores`, `/pqr`, etc. deberían tener status 200
   - Verificar que el header `Authorization: Bearer <token>` esté presente

4. **Verificar Network Tab**
   - Abrir DevTools > Network
   - Navegar a cada página
   - Verificar que las peticiones se hagan a:
     - `http://localhost:8000/asesores/kpis` (Asesores)
     - `http://localhost:8000/pqr/metrics` (PQR)
     - `http://localhost:8002/v1/dashboards/principal` (Dashboard)

### Errores Comunes y Soluciones

#### Error: "Not authenticated"
**Causa**: Token no está siendo enviado o ha expirado
**Solución**:
1. Cerrar sesión y volver a iniciar sesión
2. Verificar que localStorage tenga `access_token`
3. Verificar en Network tab que el header Authorization esté presente

#### Error: "CORS policy"
**Causa**: El backend no permite peticiones desde el frontend
**Solución**:
1. Verificar que el backend tenga configurado CORS para `http://localhost:3000`
2. Reiniciar el contenedor de core-api:
   ```bash
   docker restart teloo-core-api
   ```

#### Error: "Failed to fetch" o "Network Error"
**Causa**: El servicio no está corriendo o no es accesible
**Solución**:
1. Verificar que el servicio esté corriendo: `docker ps`
2. Verificar logs del servicio: `docker logs teloo-core-api`
3. Verificar que el puerto esté accesible: `curl http://localhost:8000/health`

#### Página carga pero no muestra datos
**Causa**: El backend no tiene datos iniciales
**Solución**:
1. Verificar que el backend haya inicializado datos:
   ```bash
   docker logs teloo-core-api | grep "initialize"
   ```
2. Si no hay datos, reiniciar el contenedor para que ejecute la inicialización

### Comandos Útiles

```bash
# Ver logs del core-api
docker logs -f teloo-core-api

# Ver logs del analytics
docker logs -f teloo-analytics

# Reiniciar todos los servicios
docker-compose restart

# Limpiar cache del navegador y reiniciar frontend
# En el directorio frontend/admin:
npm run dev
```

### Verificación Final

Si todo está configurado correctamente, deberías poder:
1. ✅ Iniciar sesión sin errores
2. ✅ Ver el Dashboard con métricas
3. ✅ Ver la página de Asesores con KPIs y tabla
4. ✅ Ver la página de PQR con métricas
5. ✅ Ver la página de Reportes con gráficos
6. ✅ Ver la página de Configuración (solo admin)

### Próximos Pasos si Aún No Funciona

1. Compartir los errores específicos de la consola del navegador
2. Compartir los logs del backend: `docker logs teloo-core-api --tail 50`
3. Verificar que el usuario tenga los permisos correctos en la base de datos


## Problema 7: PQR Service - AttributeError telefono

**Error:**
```
AttributeError: 'Cliente' object has no attribute 'telefono'
```

**Causa:**
El modelo Cliente no tiene un campo `telefono` directo. El teléfono está en `cliente.usuario.telefono`.

**Solución:**
Actualizar todas las referencias en `pqr_service.py`:
- `pqr.cliente.telefono` → `pqr.cliente.usuario.telefono`
- También en filtros de búsqueda: `Q(cliente__telefono__icontains=search)` → `Q(cliente__usuario__telefono__icontains=search)`

**Archivos modificados:**
- `services/core-api/services/pqr_service.py` (4 cambios)

**Estado:** ✅ Resuelto - Core-API reiniciado exitosamente


## Problema 8: Asesores KPIs Endpoint - Missing .all() call

**Error:**
```
GET /asesores/kpis 500 Internal Server Error
GET /asesores/ciudades 500 Internal Server Error  
GET /asesores/departamentos 500 Internal Server Error
```

**Causa:**
En el endpoint de KPIs, la línea `asesores_activos = await Asesor.filter(estado=EstadoAsesor.ACTIVO)` no incluía `.all()` para ejecutar la query. Esto causaba que al intentar iterar sobre el resultado, fallara porque era un QuerySet no ejecutado.

**Solución:**
Agregar `.all()` al final del filter:
```python
asesores_activos = await Asesor.filter(estado=EstadoAsesor.ACTIVO).all()
```

**Archivos modificados:**
- `services/core-api/routers/asesores.py` (línea 437)

**Estado:** ✅ Resuelto - Backend reiniciado automáticamente con hot-reload


## Problema 9: Asesores Router - Route Conflict

**Error:**
```
GET /asesores/kpis -> Error: invalid input syntax for type uuid: "kpis"
```

**Causa:**
El endpoint dinámico `/{asesor_id}` estaba definido antes que los endpoints específicos como `/kpis`, `/ciudades`, `/departamentos`. FastAPI procesa las rutas en orden, por lo que "kpis" estaba siendo capturado como un `asesor_id`.

**Solución:**
Mover el endpoint `/{asesor_id}` al final del archivo, después de todos los endpoints con rutas específicas. En FastAPI, las rutas más específicas deben definirse antes que las rutas con parámetros dinámicos.

**Archivos modificados:**
- `services/core-api/routers/asesores.py` (endpoint movido de línea 155 al final del archivo)

**Estado:** ✅ Resuelto - Todos los endpoints funcionando correctamente

**Endpoints verificados:**
- ✅ GET /asesores/kpis - 200 OK
- ✅ GET /asesores/ciudades - 200 OK  
- ✅ GET /asesores/departamentos - 200 OK


## Problema 10: PQR Metrics - Tortoise ORM aggregate() not supported

**Error:**
```
AttributeError: 'QuerySet' object has no attribute 'aggregate'
GET /pqr/metrics 500 Internal Server Error
```

**Causa:**
Tortoise ORM no soporta los métodos `aggregate()` y `group_by()` de la misma manera que Django ORM. El código estaba intentando usar:
- `.aggregate(avg_time=Avg('tiempo_resolucion_horas'))`
- `.group_by('tipo').annotate(count=Count('id'))`

**Solución:**
Reescribir las queries para calcular las métricas manualmente:
1. **Tiempo promedio**: Obtener todos los registros con `.all()` y calcular el promedio en Python
2. **Distribución por tipo/prioridad**: Iterar sobre todos los registros y contar manualmente

**Archivos modificados:**
- `services/core-api/services/pqr_service.py` (método `get_pqr_metrics`)
- Eliminados imports no utilizados: `Count`, `Avg`

**Estado:** ✅ Resuelto - Endpoint funcionando correctamente

**Endpoint verificado:**
- ✅ GET /pqr/metrics - 200 OK


---

## Resumen Final de Correcciones

**Sesión actual - 10 problemas resueltos:**

1. ✅ **PQR Service** - Configuración de baseURL y autenticación
2. ✅ **Analytics Service** - Formato de fechas ISO
3. ✅ **SelectItem** - Valores vacíos corregidos a "all"
4. ✅ **Auth Endpoints** - Conversión UUID a string
5. ✅ **Asesores Endpoints** - Queries ORM simplificadas
6. ✅ **AsesoresFilters** - Loop infinito corregido
7. ✅ **PQR Service** - Campo telefono corregido (cliente.usuario.telefono)
8. ✅ **Asesores KPIs** - Missing .all() call agregado
9. ✅ **Asesores Router** - Route conflict resuelto (orden de rutas)
10. ✅ **PQR Metrics** - Tortoise ORM aggregate() reemplazado con cálculo manual

**Estado del sistema:**
- ✅ Backend (core-api): Funcionando correctamente en puerto 8000
- ✅ Backend (analytics): Funcionando correctamente en puerto 8002
- ✅ Backend (agent-ia): Funcionando correctamente en puerto 8001
- ✅ Frontend: Servidor de desarrollo activo en puerto 3000
- ✅ Base de datos: PostgreSQL funcionando correctamente

**Endpoints verificados:**
- ✅ GET /asesores/kpis - 200 OK
- ✅ GET /asesores/ciudades - 200 OK
- ✅ GET /asesores/departamentos - 200 OK
- ✅ GET /pqr/metrics - 200 OK

**Próximos pasos recomendados:**
1. Recargar la aplicación frontend para ver todos los cambios aplicados
2. Verificar que no haya más errores en la consola del navegador
3. Probar la funcionalidad completa de cada módulo (Asesores, PQR, Dashboard)


## Problema 11: PQR Metrics - Decimal serialization issue

**Error:**
```
TypeError: metrics?.tiempo_promedio_resolucion_horas?.toFixed is not a function
```

**Causa:**
El schema Pydantic `PQRMetrics` estaba definido con tipo `Decimal` para los campos numéricos, lo que causaba que se serializaran como strings en JSON ("0.0" en lugar de 0.0). JavaScript no puede usar `.toFixed()` en strings.

**Solución:**
1. Cambiar el tipo en el schema de `Decimal` a `float`:
   - `tiempo_promedio_resolucion_horas: float`
   - `tasa_resolucion_24h: float`
2. Convertir explícitamente a `float()` en el servicio al crear el objeto PQRMetrics

**Archivos modificados:**
- `services/core-api/schemas/pqr.py` (PQRMetrics model)
- `services/core-api/services/pqr_service.py` (conversión a float)

**Estado:** ✅ Resuelto - Valores numéricos serializados correctamente

**Verificación:**
- ✅ GET /pqr/metrics - 200 OK
- ✅ tiempo_promedio_resolucion_horas: 0.0 (número, no string)
- ✅ tasa_resolucion_24h: 0.0 (número, no string)
