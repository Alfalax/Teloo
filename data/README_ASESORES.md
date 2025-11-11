# Importación de 250 Asesores Ficticios

## 📋 Descripción

Este directorio contiene el archivo Excel con 250 asesores ficticios para probar el sistema de escalamiento y clasificación de asesores.

## 📁 Archivo Generado

- **asesores_250_ficticios.xlsx**: Archivo Excel con 250 asesores distribuidos en ciudades principales y secundarias de Colombia

## 📊 Estructura del Archivo

### Columnas Incluidas

| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| **nombre** | Nombre del asesor | Juan |
| **apellido** | Apellido del asesor | García |
| **email** | Email único | asesor001@teloo.com |
| **telefono** | Teléfono con formato | +573001234001 |
| **ciudad** | Ciudad del punto de venta | Bogotá |
| **departamento** | Departamento | Bogotá D.C. |
| **punto_venta** | Nombre del negocio | Repuestos García |
| **direccion_punto_venta** | Dirección física | Calle 45 #23-67 |
| **password** | Contraseña inicial | Teloo2024! |

### Distribución Geográfica

**Ciudades Principales (60% - 150 asesores):**
- Bogotá
- Medellín
- Cali
- Barranquilla
- Cartagena

**Ciudades Secundarias (40% - 100 asesores):**
- Bucaramanga
- Pereira
- Manizales
- Ibagué
- Cúcuta
- Villavicencio
- Pasto
- Santa Marta
- Montería
- Neiva

## 🚀 Cómo Importar

### Paso 1: Acceder al Dashboard Administrativo

1. Abre el navegador y ve a: `http://localhost:5173`
2. Inicia sesión como administrador
3. Ve a la sección **"Asesores"** en el menú lateral

### Paso 2: Importar el Archivo

1. Haz clic en el botón **"Importar desde Excel"**
2. En el diálogo que aparece, haz clic en **"Elegir archivo"**
3. Selecciona el archivo: `asesores_250_ficticios.xlsx`
4. Haz clic en **"Importar"**
5. Espera a que el proceso termine (puede tomar 1-2 minutos)

### Paso 3: Verificar la Importación

- El sistema mostrará un resumen:
  - Total procesados: 250
  - Exitosos: 250
  - Errores: 0

- Verás los 250 asesores en la tabla de asesores

### Paso 4: Generar Datos Históricos

Después de importar los asesores, ejecuta el script para generar datos históricos:

```bash
python scripts/generate_historical_data_sql.py
```

Este script generará:
- **Historial de respuestas**: 1,250 - 5,000 registros
- **Ofertas históricas**: 2,500 - 12,500 registros
- **Auditorías de confianza**: ~125 registros

## 🔑 Credenciales de Acceso

Todos los asesores tienen las mismas credenciales:

- **Emails**: `asesor001@teloo.com` hasta `asesor250@teloo.com`
- **Contraseña**: `Teloo2024!`

### Ejemplos de Login

```
Email: asesor001@teloo.com
Password: Teloo2024!

Email: asesor050@teloo.com
Password: Teloo2024!

Email: asesor250@teloo.com
Password: Teloo2024!
```

## 🎯 Propósito

Estos datos ficticios permiten:

1. **Probar el escalamiento automático**
   - Crear solicitudes y ver cómo se clasifican los asesores en 5 niveles
   - Verificar el cálculo de puntajes (proximidad, actividad, desempeño, confianza)

2. **Probar el dashboard de asesores**
   - Ver métricas reales en los reportes
   - Analizar distribución geográfica
   - Revisar KPIs de desempeño

3. **Probar el flujo completo**
   - Admin crea solicitud → Escalamiento automático
   - Asesores ven solicitudes en su nivel
   - Asesores hacen ofertas
   - Sistema evalúa y adjudica

## 📈 Datos Históricos Generados

### Historial de Respuestas (Variable Actividad)
- 5-20 respuestas por asesor en últimos 30 días
- 70% de tasa de respuesta promedio
- Tiempos de respuesta: 5 min - 2 horas

### Ofertas Históricas (Variable Desempeño)
- 10-50 ofertas por asesor en últimos 6 meses
- 30% de tasa de adjudicación
- 80% de aceptación por cliente
- 90% de entregas exitosas
- Montos: $100,000 - $5,000,000

### Auditorías de Confianza (Variable Confianza)
- 50% de asesores con auditoría reciente
- Puntajes: 2.5 - 5.0
- Vigencia: 30 días

## 🔧 Regenerar el Archivo

Si necesitas regenerar el archivo Excel:

```bash
python scripts/generate_asesores_excel.py
```

Esto creará un nuevo archivo con 250 asesores diferentes.

## ⚠️ Notas Importantes

1. **No usar en producción**: Estos son datos ficticios solo para desarrollo y pruebas
2. **Emails únicos**: Cada asesor tiene un email único para evitar conflictos
3. **Contraseña compartida**: Todos usan la misma contraseña para facilitar las pruebas
4. **Datos realistas**: Nombres, ciudades y direcciones son realistas pero ficticios

## 🐛 Solución de Problemas

### Error: "Email ya existe"
- Limpia la base de datos antes de importar
- O usa el script para generar un nuevo archivo con emails diferentes

### Error: "Ciudad no encontrada"
- Verifica que la tabla `municipio` tenga datos de DIVIPOLA
- Ejecuta: `python services/core-api/scripts/import_divipola.py`

### Importación muy lenta
- Es normal, 250 asesores pueden tomar 1-2 minutos
- El sistema hashea cada contraseña individualmente

## 📞 Soporte

Si encuentras problemas:
1. Verifica que Docker esté corriendo
2. Verifica que la base de datos esté activa
3. Revisa los logs del backend
4. Contacta al equipo de desarrollo
