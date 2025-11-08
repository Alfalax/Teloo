# Guía de Importación de Repuestos desde Excel

## Descripción

La funcionalidad de importación de repuestos desde Excel permite cargar múltiples repuestos de manera masiva en el formulario de creación de solicitudes.

## Formato del Archivo Excel

### Columnas Soportadas

El sistema acepta las siguientes columnas (no distingue entre mayúsculas/minúsculas):

| Columna | Requerido | Descripción | Ejemplo |
|---------|-----------|-------------|---------|
| **Nombre** | ✅ Sí | Nombre del repuesto | "Pastillas de freno delanteras" |
| **Marca Vehiculo** | ✅ Sí | Marca del vehículo | "Toyota" |
| **Linea** | ❌ No | Línea del vehículo | "Corolla" |
| **Año** | ❌ No | Año del vehículo (1980-2026) | 2015 |
| **Cantidad** | ❌ No | Cantidad solicitada (default: 1) | 2 |
| **Codigo** | ❌ No | Código del repuesto | "BR-001" |
| **Observaciones** | ❌ No | Notas adicionales | "Cerámicas" |
| **Urgente** | ❌ No | "SI" o "NO" | "NO" |

### Variaciones de Nombres de Columnas

El sistema acepta múltiples variaciones de nombres de columnas:

- **Nombre**: `Nombre`, `nombre`
- **Marca Vehiculo**: `Marca Vehiculo`, `Marca Vehículo`, `marca_vehiculo`
- **Linea**: `Linea`, `Línea`, `linea`, `linea_vehiculo`
- **Año**: `Año`, `Anio`, `año`, `anio`, `anio_vehiculo`
- **Cantidad**: `Cantidad`, `cantidad`
- **Codigo**: `Codigo`, `Código`, `codigo`
- **Observaciones**: `Observaciones`, `observaciones`
- **Urgente**: `Urgente`, `urgente`, `es_urgente`

## Ejemplo de Archivo Excel

```
| Nombre                        | Marca Vehiculo | Linea   | Año  | Cantidad | Codigo | Observaciones  | Urgente |
|-------------------------------|----------------|---------|------|----------|--------|----------------|---------|
| Pastillas de freno delanteras | Toyota         | Corolla | 2015 | 2        | BR-001 | Cerámicas      | NO      |
| Filtro de aceite              | Honda          | Civic   | 2018 | 1        | FO-123 | Original       | SI      |
| Amortiguadores traseros       | Chevrolet      | Spark   | 2020 | 2        |        | Par completo   | NO      |
```

## Cómo Usar

### 1. Descargar Template

1. En el formulario de creación de solicitudes, ve al paso "Repuestos Solicitados"
2. Haz clic en la pestaña "Excel"
3. Haz clic en el botón "Descargar Template Excel"
4. Se descargará un archivo `template-repuestos.xlsx` con ejemplos

### 2. Llenar el Template

1. Abre el archivo descargado en Excel, Google Sheets o LibreOffice
2. Llena las filas con los datos de tus repuestos
3. Asegúrate de incluir al menos las columnas requeridas: **Nombre** y **Marca Vehiculo**
4. Guarda el archivo

### 3. Importar el Archivo

1. En la pestaña "Excel", haz clic en "Elegir archivo"
2. Selecciona tu archivo Excel (.xlsx o .xls)
3. El sistema procesará el archivo automáticamente
4. Si hay errores, se mostrarán en pantalla
5. Si todo está correcto, los repuestos se agregarán a la lista

## Validaciones

El sistema valida automáticamente:

- ✅ **Campos requeridos**: Nombre y Marca Vehiculo deben estar presentes
- ✅ **Año del vehículo**: Debe estar entre 1980 y 2026
- ✅ **Cantidad**: Debe ser un número mayor a 0
- ✅ **Formato del archivo**: Debe ser .xlsx o .xls válido

## Manejo de Errores

Si el archivo tiene errores, el sistema mostrará:

- El número de fila donde ocurrió el error
- Una descripción del problema
- Los primeros 5 errores encontrados (si hay más, se indica el total)

### Errores Comunes

1. **"Falta el nombre del repuesto"**: La columna Nombre está vacía
2. **"Falta la marca del vehículo"**: La columna Marca Vehiculo está vacía
3. **"Año inválido"**: El año está fuera del rango 1980-2026
4. **"Cantidad inválida"**: La cantidad no es un número o es menor a 1
5. **"El archivo Excel está vacío"**: No hay datos en el archivo

## Consejos

- 📝 Usa el template descargado como base para evitar errores de formato
- 🔤 No te preocupes por mayúsculas/minúsculas en los nombres de columnas
- ✏️ Puedes dejar columnas opcionales vacías
- 📊 Puedes importar múltiples veces - los repuestos se agregarán a la lista existente
- 🗑️ Puedes eliminar repuestos individuales después de importarlos

## Soporte Técnico

Si encuentras problemas con la importación:

1. Verifica que el archivo tenga las columnas requeridas
2. Revisa que los datos estén en el formato correcto
3. Intenta con el template de ejemplo primero
4. Contacta al equipo de soporte si el problema persiste
