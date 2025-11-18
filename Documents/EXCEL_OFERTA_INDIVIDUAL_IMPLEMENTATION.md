# Implementación de Carga de Ofertas desde Excel - Modal Individual

## Resumen
Se agregó funcionalidad para facilitar la creación de ofertas cuando hay muchos repuestos, permitiendo al asesor descargar una plantilla Excel, completarla offline y cargarla para rellenar automáticamente el formulario.

## Flujo de Uso

### 1. Descargar Plantilla Excel
- El asesor abre el modal de "Hacer Oferta" en una solicitud
- Click en "📥 Descargar Plantilla Excel"
- Se descarga un archivo Excel con:
  - `repuesto_id`: ID del repuesto (oculto, para matching)
  - `repuesto_nombre`: Nombre del repuesto
  - `cantidad`: Cantidad solicitada
  - `precio_unitario`: **VACÍO** (para completar)
  - `garantia_meses`: **VACÍO** (para completar)
  - `marca_repuesto`: Opcional
  - `modelo_repuesto`: Opcional
  - `origen_repuesto`: Opcional
  - `observaciones`: Opcional

### 2. Completar Excel Offline
- El asesor completa los campos vacíos:
  - Precio unitario (requerido)
  - Garantía en meses (requerido)
  - Opcionalmente: marca, modelo, origen, observaciones

### 3. Cargar Excel Completado
- Click en "📤 Cargar desde Excel"
- Selecciona el archivo completado
- El sistema:
  - Parsea el Excel
  - Mapea los datos por `repuesto_id`
  - Rellena automáticamente el formulario
  - Marca como "incluir" los repuestos con precio y garantía

### 4. Revisar y Enviar
- El asesor puede revisar/ajustar los valores cargados
- Completa tiempo de entrega y observaciones generales
- Envía la oferta normalmente

## Implementación Técnica

### Backend

**Nuevo Endpoint:**
```
GET /v1/solicitudes/{solicitud_id}/plantilla-oferta
```

**Funcionalidad:**
- Obtiene los repuestos de la solicitud
- Genera un DataFrame con pandas
- Crea archivo Excel con openpyxl
- Retorna como StreamingResponse para descarga

**Archivo:** `services/core-api/routers/solicitudes.py`

### Frontend

**Servicio:**
- Nuevo método `descargarPlantillaOferta()` en `solicitudesService`
- Maneja la descarga del blob y trigger del download

**Componente:** `OfertaIndividualModal.tsx`

**Nuevas funciones:**
- `handleDescargarPlantilla()`: Descarga la plantilla
- `handleCargarExcel()`: Abre el file picker
- `handleFileChange()`: Parsea el Excel y rellena el formulario

**Librería:** `xlsx` (SheetJS)
- Parsea archivos Excel en el navegador
- Convierte hojas a JSON para procesamiento

**UI:**
- Dos botones en el DialogHeader:
  - "Descargar Plantilla Excel" (Download icon)
  - "Cargar desde Excel" (Upload icon)
- Input file oculto para selección de archivo

## Validaciones

- El Excel debe tener la estructura correcta
- Los `repuesto_id` deben coincidir con los de la solicitud
- Precio y garantía deben ser valores válidos
- Se mantienen las validaciones existentes del formulario

## Ventajas

✅ Facilita ofertas con muchos repuestos (10+)
✅ Permite trabajo offline
✅ Reduce errores de digitación
✅ Mantiene compatibilidad con flujo manual
✅ El asesor puede revisar antes de enviar

## Archivos Modificados

### Backend
- `services/core-api/routers/solicitudes.py`
  - Imports: StreamingResponse, pandas, io
  - Nuevo endpoint: `descargar_plantilla_oferta()`

### Frontend
- `frontend/advisor/src/services/solicitudes.ts`
  - Nuevo método: `descargarPlantillaOferta()`

- `frontend/advisor/src/components/ofertas/OfertaIndividualModal.tsx`
  - Imports: useRef, Download, Upload, XLSX
  - Nuevas funciones: handleDescargarPlantilla, handleCargarExcel, handleFileChange
  - Nuevos botones en DialogHeader
  - Input file oculto

- `frontend/advisor/package.json`
  - Nueva dependencia: `xlsx`

## Testing

Para probar:
1. Abrir modal de oferta en una solicitud con varios repuestos
2. Click "Descargar Plantilla Excel"
3. Abrir el Excel descargado
4. Completar precio_unitario y garantia_meses
5. Guardar el archivo
6. Click "Cargar desde Excel"
7. Seleccionar el archivo guardado
8. Verificar que los campos se rellenan automáticamente
9. Ajustar si es necesario y enviar oferta

## Notas

- La plantilla incluye el `repuesto_id` para hacer el matching correcto
- Si un repuesto no tiene precio o garantía en el Excel, se ignora
- Los repuestos cargados se marcan automáticamente como "incluir"
- El asesor puede mezclar: cargar Excel y luego ajustar manualmente
