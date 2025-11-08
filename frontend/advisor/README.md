# TeLOO Advisor Frontend

Portal web para asesores de repuestos automotrices del marketplace TeLOO V3.

## Características Implementadas

### ✅ Autenticación y Seguridad
- Login específico para asesores (solo rol ADVISOR)
- Gestión de tokens JWT con refresh automático
- Rutas protegidas con redirección automática
- Persistencia de sesión en localStorage

### ✅ Dashboard con KPIs
- 4 KPIs superiores en tiempo real:
  - Ofertas Asignadas
  - Monto Total Ganado
  - Solicitudes Abiertas
  - Tasa de Conversión
- Navegación por pestañas (Abiertas, Cerradas, Ganadas)

### ✅ Pestaña de Solicitudes Abiertas
- Lista de solicitudes disponibles para ofertar
- Información detallada de vehículo y repuestos
- Indicador de tiempo restante con alertas visuales
- Botón "Hacer Oferta" para ofertas individuales
- Botón "Carga Masiva Excel" para ofertas múltiples

### ✅ Modal de Oferta Individual
- Formulario por repuesto con precio y garantía
- Selección de repuestos a incluir (checkboxes)
- Campo de tiempo de entrega total del pedido
- Validaciones en tiempo real:
  - Precio: $1,000 - $50,000,000 COP
  - Garantía: 1 - 60 meses
  - Tiempo de entrega: 0 - 90 días
- Cálculo automático del total estimado
- Campo de observaciones opcional

### ✅ Modal de Carga Masiva Excel
- Drag & drop para archivos Excel (.xlsx, .xls)
- Descarga de plantilla Excel con formato requerido
- Preview de datos antes de enviar
- Validación por fila con reporte de errores detallado
- Indicadores visuales de filas válidas vs errores
- Límite de tamaño: 5MB

### ✅ Pestaña de Solicitudes Cerradas
- Historial de solicitudes no adjudicadas
- Comparación entre tu oferta y la oferta ganadora
- Información de por qué no fue seleccionada
- Datos del vehículo y repuestos solicitados

### ✅ Pestaña de Ofertas Ganadas
- Lista de ofertas ganadoras con estado del cliente
- Estados: Pendiente respuesta, Aceptada, Rechazada
- Información de contacto del cliente (si fue aceptada)
- Botón directo para contactar por WhatsApp
- Detalles completos de la oferta ganadora

## Tecnologías Utilizadas

- **React 18** - Framework UI
- **TypeScript** - Tipado estático
- **Vite** - Build tool y dev server
- **React Router** - Navegación
- **Tailwind CSS** - Estilos con tema Amber Minimal
- **shadcn/ui** - Componentes UI (Radix UI)
- **Axios** - Cliente HTTP
- **React Hook Form** - Gestión de formularios
- **Zod** - Validación de esquemas
- **React Dropzone** - Upload de archivos
- **XLSX** - Procesamiento de archivos Excel
- **Lucide React** - Iconos

## Estructura del Proyecto

```
src/
├── components/
│   ├── auth/
│   │   └── ProtectedRoute.tsx
│   ├── dashboard/
│   │   └── KPIDashboard.tsx
│   ├── layout/
│   │   ├── Header.tsx
│   │   └── MainLayout.tsx
│   ├── ofertas/
│   │   ├── OfertaIndividualModal.tsx
│   │   └── CargaMasivaModal.tsx
│   ├── solicitudes/
│   │   ├── SolicitudCard.tsx
│   │   ├── SolicitudesAbiertas.tsx
│   │   ├── SolicitudesCerradas.tsx
│   │   └── SolicitudesGanadas.tsx
│   └── ui/
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       ├── input.tsx
│       ├── tabs.tsx
│       ├── badge.tsx
│       ├── checkbox.tsx
│       ├── label.tsx
│       └── textarea.tsx
├── contexts/
│   └── AuthContext.tsx
├── pages/
│   ├── LoginPage.tsx
│   └── DashboardPage.tsx
├── services/
│   ├── auth.ts
│   ├── solicitudes.ts
│   └── ofertas.ts
├── types/
│   ├── auth.ts
│   ├── solicitud.ts
│   └── kpi.ts
├── lib/
│   └── utils.ts
├── App.tsx
├── main.tsx
└── index.css
```

## Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Comandos Disponibles

```bash
# Instalar dependencias
npm install

# Desarrollo (puerto 3001)
npm run dev

# Build de producción
npm run build

# Preview del build
npm run preview

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix

# Formateo de código
npm run format

# Tests
npm run test
npm run test:watch
npm run test:coverage
```

## Integración con Backend

El frontend se conecta a los siguientes endpoints del Core API:

### Autenticación
- `POST /auth/login` - Login de asesor
- `POST /auth/refresh` - Refresh de token
- `GET /auth/me` - Obtener usuario actual

### Solicitudes
- `GET /v1/solicitudes?estado=ABIERTA` - Solicitudes abiertas
- `GET /v1/solicitudes/cerradas` - Solicitudes cerradas
- `GET /v1/solicitudes/ganadas` - Ofertas ganadoras
- `GET /v1/solicitudes/{id}` - Detalle de solicitud

### Ofertas
- `POST /v1/ofertas` - Crear oferta individual
- `POST /v1/ofertas/upload` - Carga masiva Excel
- `GET /v1/ofertas?solicitud_id={id}` - Ofertas por solicitud

## Tema Visual

El proyecto utiliza el **Amber Minimal Theme** de shadcn/ui:
- Color primario: Amber/Orange (#F59E0B)
- Tipografía: Inter (sans-serif)
- Soporte para modo claro/oscuro
- Componentes con sombras sutiles y bordes redondeados

## Validaciones Implementadas

### Ofertas Individuales
- Al menos un repuesto debe ser incluido
- Precio unitario: $1,000 - $50,000,000 COP
- Garantía: 1 - 60 meses
- Tiempo de entrega: 0 - 90 días

### Carga Masiva Excel
- Formato de archivo: .xlsx, .xls
- Tamaño máximo: 5MB
- Validación de columnas requeridas
- Validación de rangos por fila
- Reporte detallado de errores

## Próximas Mejoras

- [ ] Notificaciones en tiempo real con WebSocket
- [ ] Filtros avanzados en solicitudes
- [ ] Historial completo de ofertas
- [ ] Estadísticas detalladas de performance
- [ ] Chat directo con clientes
- [ ] Sistema de calificaciones

## Soporte

Para problemas o preguntas, contactar al equipo de desarrollo de TeLOO.
