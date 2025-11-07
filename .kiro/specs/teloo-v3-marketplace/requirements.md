# Requirements Document

## Introduction

TeLOO V3 es un marketplace inteligente de repuestos automotrices que actúa como intermediario automatizado entre clientes que necesitan repuestos y asesores/proveedores que los venden. El sistema utiliza algoritmos avanzados de escalamiento automático por niveles geográficos, evaluación inteligente de ofertas, y comunicación multicanal para optimizar la experiencia de compra y venta de repuestos automotrices.

## Glossary

- **TeLOO_System**: El sistema completo de marketplace de repuestos automotrices
- **Asesor**: Proveedor/vendedor de repuestos registrado en el sistema
- **Cliente**: Usuario final que solicita repuestos a través de WhatsApp
- **Solicitud**: Petición de uno o más repuestos realizada por un cliente
- **Oferta**: Propuesta comercial de un asesor para una solicitud específica
- **Evaluacion_Automatica**: Proceso algorítmico que determina ofertas ganadoras
- **Sistema_Escalamiento**: Algoritmo de 5 niveles para distribución inteligente de solicitudes
- **Adjudicacion_Mixta**: Resultado donde diferentes repuestos de una misma solicitud son adjudicados a diferentes asesores, permitiendo que múltiples asesores ganen parcialmente
- **Agente_IA**: Servicio que recibe mensajes de WhatsApp vía webhook y los estructura usando APIs de múltiples proveedores LLM con selección automática basada en complejidad
- **Core_Platform**: Motor central que gestiona solicitudes, ofertas y evaluaciones
- **Analytics_Service**: Servicio de métricas y dashboards del sistema
- **Proximidad_Geografica**: Cercanía lógica basada en ciudad, área metropolitana y hub logístico
- **Nivel_Asesor**: Clasificación dinámica del asesor (1-5) basada en múltiples variables
- **Cobertura_Minima**: Porcentaje mínimo de repuestos que debe cubrir una oferta (50% por defecto)
- **WhatsApp_API**: Servicio externo de Meta que se consume a través de webhook para recibir y enviar mensajes de clientes

## Requirements

### Requirement 1

**User Story:** Como cliente necesitando repuestos automotrices, quiero solicitar repuestos a través de WhatsApp de manera natural, para que el sistema encuentre automáticamente los mejores proveedores disponibles.

#### Acceptance Criteria

1. WHEN el Cliente envía un mensaje de WhatsApp con información de repuestos, THE Agente_IA SHALL extraer y estructurar automáticamente los datos del repuesto, vehículo y cliente
2. WHEN la información está incompleta, THE Agente_IA SHALL solicitar aclaraciones específicas al cliente mediante preguntas dirigidas
3. WHEN toda la información requerida está completa, THE Agente_IA SHALL crear una Solicitud estructurada en el Core_Platform
4. THE Agente_IA SHALL validar que el teléfono tenga formato colombiano +57XXXXXXXXXX
5. THE Agente_IA SHALL verificar que la ciudad exista en el catálogo del sistema
6. THE Agente_IA SHALL seleccionar automáticamente el modelo LLM más apropiado (local, OpenAI, u otros proveedores) basado en la complejidad de los datos para optimizar costos y precisión

### Requirement 2

**User Story:** Como sistema automatizado, quiero determinar el conjunto de asesores elegibles para cada solicitud basado en criterios geográficos, para optimizar la cobertura y relevancia antes de calcular puntajes.

#### Acceptance Criteria

1. WHEN se crea una nueva Solicitud, THE Sistema_Escalamiento SHALL determinar el conjunto de asesores elegibles incluyendo: asesores de la misma ciudad de la solicitud, asesores de todas las áreas metropolitanas nacionales de Colombia, y asesores del hub logístico asignado a la ciudad de la solicitud
2. THE TeLOO_System SHALL mantener actualizada la información de áreas metropolitanas y hubs logísticos desde archivos Excel proporcionados por el administrador
3. THE Sistema_Escalamiento SHALL integrar automáticamente los datos de Areas_Metropolitanas_TeLOO y Asignacion_Hubs_200km a las bases de datos del sistema
4. THE Sistema_Escalamiento SHALL excluir asesores que no pertenezcan a ninguna de estas categorías geográficas
5. THE Sistema_Escalamiento SHALL registrar en auditoría el conjunto final de asesores elegibles por solicitud

### Requirement 3

**User Story:** Como administrador del sistema, quiero que las solicitudes se distribuyan inteligentemente a los asesores elegibles más apropiados, para maximizar la probabilidad de obtener ofertas de calidad.

#### Acceptance Criteria

1. WHEN se determina el conjunto de asesores elegibles, THE Sistema_Escalamiento SHALL calcular el puntaje total de cada asesor usando la fórmula: proximidad(40%) + actividad_reciente(25%) + desempeño_histórico(20%) + nivel_confianza(15%)
2. THE Sistema_Escalamiento SHALL clasificar a los asesores en 5 niveles basados en umbrales configurables de puntaje total
3. WHEN se ejecuta una oleada de nivel, THE Sistema_Escalamiento SHALL notificar a los asesores del nivel correspondiente usando el canal configurado (WhatsApp para niveles 1-2, Push para niveles 3-4)
4. THE Sistema_Escalamiento SHALL esperar el tiempo configurado por nivel antes de escalar al siguiente nivel
5. WHEN se reciben 2 ofertas mínimas, THE Sistema_Escalamiento SHALL proceder automáticamente a la evaluación

### Requirement 4

**User Story:** Como asesor registrado en el sistema, quiero recibir notificaciones de solicitudes relevantes y poder enviar ofertas fácilmente, para participar efectivamente en el marketplace.

#### Acceptance Criteria

1. WHEN el asesor está en nivel 1 o 2, THE TeLOO_System SHALL enviar notificaciones por WhatsApp
2. WHEN el asesor está en nivel 3 o 4, THE TeLOO_System SHALL enviar notificaciones por Push
3. THE TeLOO_System SHALL permitir al asesor crear ofertas individuales a través del formulario web
4. THE TeLOO_System SHALL permitir al asesor cargar ofertas masivas mediante archivos Excel válidos
5. WHEN el asesor envía una oferta, THE TeLOO_System SHALL validar que los precios unitarios estén entre 1,000 y 50,000,000 COP, la garantía de cada repuesto esté entre 1 y 60 meses, y el tiempo de entrega general esté entre 0 y 90 días

### Requirement 5

**User Story:** Como sistema automatizado, quiero evaluar las ofertas recibidas de manera objetiva y transparente, para seleccionar las mejores opciones por cada repuesto individual.

#### Acceptance Criteria

1. WHEN se activa la evaluación automática, THE Evaluacion_Automatica SHALL evaluar cada repuesto individualmente contra todas las ofertas disponibles
2. THE Evaluacion_Automatica SHALL calcular el puntaje de cada oferta usando: precio(50%) + tiempo_entrega(35%) + garantía(15%)
3. WHEN una oferta tiene cobertura ≥50%, THE Evaluacion_Automatica SHALL adjudicar el repuesto a la oferta con mejor puntaje
4. WHEN la mejor oferta tiene cobertura <50% y existen otras ofertas, THE Evaluacion_Automatica SHALL aplicar regla de cascada evaluando la siguiente mejor oferta
5. WHEN una oferta es la única disponible para un repuesto, THE Evaluacion_Automatica SHALL adjudicar por excepción sin importar la cobertura

### Requirement 6

**User Story:** Como cliente que recibió ofertas, quiero entender claramente qué se me está ofreciendo y poder aceptar o rechazar fácilmente, para completar mi compra de manera informada.

#### Acceptance Criteria

1. WHEN hay una sola oferta ganadora, THE Agente_IA SHALL presentar al cliente un resumen claro con precio, tiempo, garantía y proveedor
2. WHEN hay múltiples ofertas ganadoras (adjudicación mixta), THE Agente_IA SHALL presentar un resumen consolidado indicando el número de asesores y cobertura total
3. THE Agente_IA SHALL permitir al cliente responder "SÍ", "NO" o "DETALLES" para gestionar la oferta
4. WHEN el cliente acepta, THE TeLOO_System SHALL cambiar el estado de las ofertas a ACEPTADA y establecer comunicación directa
5. WHEN el cliente no responde en 20 horas, THE TeLOO_System SHALL marcar las ofertas como EXPIRADA

### Requirement 7

**User Story:** Como administrador del sistema, quiero configurar todos los parámetros del algoritmo de escalamiento y evaluación, para adaptar el comportamiento del sistema a las necesidades del negocio.

#### Acceptance Criteria

1. THE TeLOO_System SHALL permitir configurar los pesos de la fórmula de puntaje total (proximidad, actividad, desempeño, confianza)
2. THE TeLOO_System SHALL permitir configurar los umbrales de nivel (nivel1_min, nivel2_min, nivel3_min, nivel4_min)
3. THE TeLOO_System SHALL permitir configurar los tiempos de espera por nivel (15, 20, 25, 30 minutos por defecto)
4. THE TeLOO_System SHALL permitir configurar el canal de notificación por nivel (WhatsApp para niveles 1-2, Push para niveles 3-4 por defecto)
5. THE TeLOO_System SHALL permitir configurar los pesos de evaluación de ofertas (precio, tiempo, garantía)
6. THE TeLOO_System SHALL validar que todos los pesos sumen 1.0 con tolerancia de ±1e-6

### Requirement 8

**User Story:** Como analista de negocio, quiero acceder a métricas y dashboards en tiempo real del sistema, para monitorear el desempeño y tomar decisiones informadas.

#### Acceptance Criteria

1. THE Analytics_Service SHALL capturar eventos en tiempo real del Core_Platform
2. THE Analytics_Service SHALL generar dashboards de funnel, salud del mercado, finanzas y asesores
3. THE Analytics_Service SHALL calcular y mostrar 34 KPIs específicos organizados en 4 dashboards: Embudo Operativo (11 KPIs), Salud del Marketplace (5 KPIs), Dashboard Financiero (5 KPIs), y Análisis de Asesores (13 KPIs)
4. THE Analytics_Service SHALL generar alertas automáticas cuando se superen umbrales configurables
5. THE Analytics_Service SHALL permitir exportar datos para análisis externos

### Requirement 9

**User Story:** Como desarrollador del sistema, quiero que todas las operaciones críticas sean auditables y trazables, para garantizar transparencia y facilitar debugging.

#### Acceptance Criteria

1. THE TeLOO_System SHALL registrar por cada solicitud y asesor: variables calculadas, puntaje total, nivel asignado y criterios de desempate
2. THE TeLOO_System SHALL mantener historial completo de transiciones de estado de solicitudes y ofertas
3. THE TeLOO_System SHALL registrar todos los eventos del sistema en Redis pub/sub con timestamps precisos
4. THE TeLOO_System SHALL generar logs estructurados para todas las operaciones de evaluación y escalamiento
5. THE TeLOO_System SHALL permitir reconstruir el estado completo de cualquier solicitud desde los logs de auditoría

### Requirement 10

**User Story:** Como usuario del sistema (asesor o administrador), quiero recibir notificaciones en tiempo real sobre cambios relevantes, para mantenerme informado del estado de mis solicitudes y ofertas.

#### Acceptance Criteria

1. THE TeLOO_System SHALL enviar notificaciones WebSocket en tiempo real a asesores conectados
2. WHEN se crea una nueva solicitud, THE TeLOO_System SHALL notificar a asesores elegibles según su nivel
3. WHEN se completa una evaluación, THE TeLOO_System SHALL notificar a todos los asesores participantes el resultado
4. WHEN un cliente acepta o rechaza ofertas, THE TeLOO_System SHALL notificar inmediatamente a los asesores afectados
5. THE TeLOO_System SHALL mantener fallback a notificaciones por WhatsApp cuando WebSocket no esté disponible

### Requirement 11

**User Story:** Como arquitecto del sistema, quiero que TeLOO sea autónomo y no dependa de servicios externos innecesarios, para garantizar control total y reducir dependencias.

#### Acceptance Criteria

1. THE TeLOO_System SHALL operar de manera completamente autónoma sin consumir servicios externos excepto WhatsApp_API y proveedores LLM
2. THE TeLOO_System SHALL implementar todas las funcionalidades de cálculo, evaluación, escalamiento y auditoría internamente
3. THE TeLOO_System SHALL mantener sus propias bases de datos sin depender de servicios de terceros para almacenamiento
4. THE TeLOO_System SHALL generar sus propios dashboards y métricas sin servicios externos de analytics
5. THE TeLOO_System SHALL implementar notificaciones push internas sin servicios externos como Firebase
6. THE TeLOO_System SHALL manejar autenticación y seguridad con JWT local sin servicios externos como Auth0
7. THE TeLOO_System SHALL usar únicamente WhatsApp_API para comunicación con clientes y APIs de LLM para procesamiento de lenguaje natural
8. THE TeLOO_System SHALL diseñar la arquitectura para permitir integración futura opcional de servicios externos de push notifications y autenticación en fases posteriores

### Requirement 12

**User Story:** Como usuario administrativo, quiero una interfaz completa y organizada para gestionar el sistema, para tener control total sobre operaciones, configuración y análisis.

#### Acceptance Criteria

1. THE TeLOO_System SHALL proporcionar un dashboard principal con 4 KPIs superiores: ofertas totales asignadas (mes actual), monto total aceptado por clientes (mes actual), solicitudes abiertas actualmente, y tasa de conversión
2. THE TeLOO_System SHALL mostrar gráficos de líneas del mes actual con: solicitudes por día, solicitudes aceptadas por día, y solicitudes cerradas sin ofertas por día
3. THE TeLOO_System SHALL mostrar el top 15 de solicitudes abiertas con mayor tiempo en proceso
4. THE TeLOO_System SHALL proporcionar sidebar con módulos: INICIO (dashboard principal), ASESORES (gestión completa de asesores), REPORTES Y ANALYTICS (4 dashboards con 34 indicadores), PQR (atención de quejas y reclamos), y CONFIGURACIÓN (roles, permisos y parámetros del sistema)
6. THE TeLOO_System SHALL mostrar en el módulo ASESORES: 3 KPIs superiores (total asesores habilitados, total puntos de venta, cobertura nacional), tabla de asesores con información completa (nombre, teléfono, correo, punto de venta, ubicación, estado, calificaciones), y funciones de importar/exportar Excel y crear nuevo asesor
5. THE TeLOO_System SHALL permitir modificar todas las opciones configurables del sistema desde el módulo de configuración

### Requirement 13

**User Story:** Como asesor del sistema, quiero una interfaz personalizada que me permita gestionar mis ofertas eficientemente, para maximizar mis oportunidades de negocio.

#### Acceptance Criteria

1. THE TeLOO_System SHALL proporcionar al asesor un dashboard con 4 KPIs superiores: ofertas asignadas, monto total ofertas ganadas, solicitudes abiertas, y tasa de conversión personal
2. THE TeLOO_System SHALL organizar la interfaz del asesor en 3 pestañas: ABIERTAS (solicitudes disponibles para ofertar), CERRADAS (solicitudes finalizadas sin ganar), y GANADAS (solicitudes adjudicadas al asesor)
3. THE TeLOO_System SHALL permitir al asesor ofertar en solicitudes abiertas mediante formulario por repuesto (precio, garantía) con campo de tiempo de entrega total del pedido
4. THE TeLOO_System SHALL permitir al asesor cargar ofertas masivas vía Excel para solicitudes abiertas
5. THE TeLOO_System SHALL proporcionar notificaciones en tiempo real al asesor sobre nuevas solicitudes, resultados de evaluaciones y cambios de estado

### Requirement 14

**User Story:** Como administrador del sistema, quiero que el sistema maneje errores y casos edge de manera robusta, para garantizar operación continua y confiable.

#### Acceptance Criteria

1. WHEN una ciudad no está en área metropolitana ni hub logístico, THE Sistema_Escalamiento SHALL asignar proximidad por defecto y generar log de advertencia
2. WHEN un asesor tiene métricas faltantes, THE TeLOO_System SHALL usar valores por defecto (1.0 para actividad/desempeño, 3.0 para confianza)
3. WHEN se intenta crear una oferta durante evaluación activa, THE TeLOO_System SHALL rechazar con código 409 Conflict
4. WHEN la API de WhatsApp falla, THE TeLOO_System SHALL usar circuit breaker con retry exponencial
5. THE TeLOO_System SHALL completar evaluaciones en máximo 5 segundos o generar timeout con estado de error