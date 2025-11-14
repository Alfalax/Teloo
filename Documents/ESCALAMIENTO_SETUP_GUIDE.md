# Guía de Configuración del Sistema de Escalamiento

## 🎯 Objetivo

Habilitar el sistema de escalamiento y clasificación automática de asesores en 5 niveles basado en 4 variables: proximidad, actividad, desempeño y confianza.

## 📦 Archivos Generados

### 1. Archivo Excel de Asesores
- **Ubicación**: `data/asesores_250_ficticios.xlsx`
- **Contenido**: 250 asesores ficticios distribuidos en ciudades de Colombia
- **Formato**: Listo para importar desde el dashboard administrativo

### 2. Scripts de Generación
- **generate_asesores_excel.py**: Genera el archivo Excel
- **generate_historical_data_sql.py**: Genera datos históricos después de importar

### 3. Documentación
- **data/README_ASESORES.md**: Guía completa de importación y uso

## 🚀 Proceso de Configuración

### Fase 1: Importar Asesores (5 minutos)

1. **Abrir Dashboard Admin**
   ```
   URL: http://localhost:5173
   Usuario: admin@teloo.com
   Password: [tu contraseña de admin]
   ```

2. **Ir a Sección Asesores**
   - Clic en "Asesores" en el menú lateral

3. **Importar Excel**
   - Clic en "Importar desde Excel"
   - Seleccionar: `data/asesores_250_ficticios.xlsx`
   - Esperar 1-2 minutos
   - Verificar: 250 asesores importados exitosamente

### Fase 2: Generar Datos Históricos (2 minutos)

```bash
python scripts/generate_historical_data_sql.py
```

**Resultado esperado:**
```
✅ Datos históricos generados:
   • Historial respuestas: ~3,000 registros
   • Ofertas históricas: ~7,500 registros
   • Auditorías: ~125 registros
```

### Fase 3: Completar Código de Escalamiento (30 minutos)

**Archivos a modificar:**
- `services/core-api/services/escalamiento_service.py`
- `services/core-api/services/solicitudes_service.py`

**Tareas pendientes:**
1. Completar función `verificar_cierre_anticipado()`
2. Agregar fallbacks para métricas sin datos
3. Integrar escalamiento al crear solicitud
4. Crear endpoint manual de ejecución

### Fase 4: Probar el Sistema (10 minutos)

1. **Crear Solicitud de Prueba**
   - Dashboard Admin → Nueva Solicitud
   - Llenar datos del cliente
   - Agregar repuestos
   - Guardar

2. **Verificar Escalamiento Automático**
   - El sistema debe ejecutar escalamiento al crear la solicitud
   - Verificar en logs que se calcularon puntajes
   - Verificar que asesores fueron clasificados en niveles

3. **Probar Dashboard Asesor**
   - Login como asesor: `asesor001@teloo.com` / `Teloo2024!`
   - Verificar que ve la solicitud
   - Hacer una oferta de prueba

## 📊 Datos Generados

### Asesores (250 total)

**Distribución Geográfica:**
- 60% en ciudades principales (Bogotá, Medellín, Cali, Barranquilla, Cartagena)
- 40% en ciudades secundarias (Bucaramanga, Pereira, Manizales, etc.)

**Credenciales:**
- Emails: `asesor001@teloo.com` hasta `asesor250@teloo.com`
- Password: `Teloo2024!` (todos)

### Datos Históricos

**Variable Actividad (Historial de Respuestas):**
- 5-20 respuestas por asesor
- Últimos 30 días
- 70% tasa de respuesta promedio

**Variable Desempeño (Ofertas Históricas):**
- 10-50 ofertas por asesor
- Últimos 6 meses
- 30% tasa de adjudicación
- Montos: $100K - $5M

**Variable Confianza (Auditorías):**
- 50% de asesores con auditoría
- Puntajes: 2.5 - 5.0
- Vigencia: 30 días

## 🎯 Resultado Esperado

### Clasificación en 5 Niveles

Después de ejecutar el escalamiento, los asesores se distribuirán aproximadamente así:

- **Nivel 1** (Top 10%): ~25 asesores
  - Puntaje más alto
  - Notificación: WhatsApp
  - Timeout: 30 minutos

- **Nivel 2** (Siguiente 15%): ~38 asesores
  - Puntaje alto
  - Notificación: WhatsApp
  - Timeout: 45 minutos

- **Nivel 3** (Siguiente 25%): ~63 asesores
  - Puntaje medio-alto
  - Notificación: Push
  - Timeout: 60 minutos

- **Nivel 4** (Siguiente 25%): ~63 asesores
  - Puntaje medio-bajo
  - Notificación: Push
  - Timeout: 90 minutos

- **Nivel 5** (Último 25%): ~61 asesores
  - Puntaje más bajo
  - Notificación: Push
  - Timeout: 120 minutos

### Cálculo de Puntajes

Cada asesor tendrá un puntaje calculado con:

```
Puntaje Total = (Proximidad × 40%) + (Actividad × 25%) + (Desempeño × 25%) + (Confianza × 10%)
```

**Ejemplo:**
```
Asesor en Bogotá para solicitud en Bogotá:
- Proximidad: 100 (misma ciudad)
- Actividad: 85 (85% respuesta)
- Desempeño: 75 (75% éxito)
- Confianza: 90 (4.5/5.0)

Puntaje = (100×0.4) + (85×0.25) + (75×0.25) + (90×0.1) = 89
Nivel asignado: 1 o 2
```

## 🔧 Comandos Útiles

### Regenerar Archivo Excel
```bash
python scripts/generate_asesores_excel.py
```

### Regenerar Datos Históricos
```bash
python scripts/generate_historical_data_sql.py
```

### Verificar Asesores en BD
```sql
SELECT COUNT(*) FROM asesor WHERE estado = 'ACTIVO';
```

### Verificar Datos Históricos
```sql
SELECT COUNT(*) FROM historial_respuesta_oferta;
SELECT COUNT(*) FROM oferta_historica;
SELECT COUNT(*) FROM auditoria_tienda;
```

### Limpiar Datos de Prueba
```sql
-- Eliminar asesores ficticios
DELETE FROM asesor WHERE usuario_id IN (
    SELECT id FROM usuario WHERE email LIKE 'asesor%@teloo.com'
);

-- Eliminar datos históricos
DELETE FROM historial_respuesta_oferta;
DELETE FROM oferta_historica;
DELETE FROM auditoria_tienda;
```

## 📈 Métricas en Dashboards

Con estos datos, los dashboards mostrarán:

### Dashboard Principal
- Total asesores: 250
- Asesores activos: 250
- Distribución geográfica realista
- Métricas de actividad

### Dashboard Asesores
- Ranking por desempeño
- Tasa de respuesta individual
- Ofertas ganadas/perdidas
- Puntaje de confianza

### Reportes
- Embudo operativo con datos
- Análisis de conversión
- Tendencias temporales
- KPIs calculados

## ⚠️ Notas Importantes

1. **Solo para desarrollo**: Estos son datos ficticios
2. **No usar en producción**: Limpiar antes de deploy
3. **Contraseñas compartidas**: Cambiar en producción
4. **Datos realistas**: Pero completamente ficticios

## 🐛 Solución de Problemas

### Importación falla
- Verificar que Docker esté corriendo
- Verificar conexión a base de datos
- Revisar logs del backend

### Datos históricos no se generan
- Verificar que los asesores estén importados
- Verificar conexión a PostgreSQL
- Revisar permisos de usuario de BD

### Escalamiento no funciona
- Verificar que existan datos históricos
- Revisar logs del servicio de escalamiento
- Verificar configuración de pesos y umbrales

## 📞 Próximos Pasos

1. ✅ Importar asesores desde Excel
2. ✅ Generar datos históricos
3. ⏳ Completar código de escalamiento
4. ⏳ Integrar con creación de solicitudes
5. ⏳ Probar flujo completo
6. ⏳ Ajustar pesos y umbrales según resultados
7. ⏳ Implementar notificaciones (opcional)

## 🎉 Beneficios

Con este setup tendrás:

- ✅ 250 asesores para pruebas realistas
- ✅ Datos históricos para métricas
- ✅ Distribución geográfica real
- ✅ Escalamiento automático funcional
- ✅ Dashboards con datos reales
- ✅ Flujo completo de solicitud → oferta → adjudicación
