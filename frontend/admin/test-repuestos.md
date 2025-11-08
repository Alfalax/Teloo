# Test Manual - Importación de Repuestos desde Excel

## Pasos para Probar

### 1. Preparar archivo Excel de prueba

Crea un archivo Excel con las siguientes columnas y datos:

```
| Nombre                        | Marca Vehiculo | Linea   | Año  | Cantidad | Codigo | Observaciones  | Urgente |
|-------------------------------|----------------|---------|------|----------|--------|----------------|---------|
| Pastillas de freno delanteras | Toyota         | Corolla | 2015 | 2        | BR-001 | Cerámicas      | NO      |
| Filtro de aceite              | Honda          | Civic   | 2018 | 1        | FO-123 | Original       | SI      |
| Amortiguadores traseros       | Chevrolet      | Spark   | 2020 | 2        |        | Par completo   | NO      |
```

### 2. Probar la funcionalidad

1. ✅ Iniciar el frontend admin: `npm run dev`
2. ✅ Navegar a "Solicitudes" → "Nueva Solicitud"
3. ✅ Completar el paso 1 (Datos del Cliente)
4. ✅ En el paso 2 (Repuestos), ir a la pestaña "Excel"
5. ✅ Hacer clic en "Descargar Template Excel" - debe descargar un archivo
6. ✅ Abrir el template descargado y verificar que tenga datos de ejemplo
7. ✅ Subir el archivo Excel de prueba
8. ✅ Verificar que se muestren los 3 repuestos en la tabla
9. ✅ Verificar que los datos se hayan importado correctamente

### 3. Casos de Error a Probar

#### Caso 1: Archivo sin columnas requeridas
- Crear Excel sin columna "Nombre"
- Debe mostrar error: "Falta el nombre del repuesto"

#### Caso 2: Año inválido
- Crear Excel con año 1900
- Debe mostrar error: "Año inválido"

#### Caso 3: Cantidad inválida
- Crear Excel con cantidad -1 o 0
- Debe mostrar error: "Cantidad inválida"

#### Caso 4: Archivo vacío
- Subir Excel sin datos (solo headers)
- Debe mostrar error: "El archivo Excel está vacío"

### 4. Verificaciones de UX

- ✅ El botón de descarga de template funciona
- ✅ El spinner de carga aparece mientras procesa
- ✅ Los mensajes de éxito se muestran en verde
- ✅ Los mensajes de error se muestran en rojo
- ✅ Después de importar, cambia automáticamente al tab "Manual"
- ✅ Los repuestos importados aparecen en la tabla
- ✅ Se pueden eliminar repuestos importados individualmente
- ✅ Se pueden agregar más repuestos manualmente después de importar

## Resultado Esperado

✅ **PASS**: La funcionalidad de importación de Excel funciona correctamente
- Los repuestos se importan sin errores
- Las validaciones funcionan correctamente
- La UX es clara y fluida
- Los mensajes de error son descriptivos

❌ **FAIL**: Si alguno de los casos anteriores no funciona como se espera

## Notas

- La librería `xlsx` debe estar instalada: `npm install xlsx`
- El componente usa `XLSX.read()` para parsear el archivo
- El componente usa `XLSX.utils.sheet_to_json()` para convertir a JSON
- El componente usa `XLSX.writeFile()` para generar el template
