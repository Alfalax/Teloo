# Implementation Plan

## Overview

Este plan de implementación convierte el diseño de TeLOO V3 en tareas específicas de código, organizadas de manera incremental para construir el marketplace de repuestos automotrices. Cada tarea está referenciada a los requirements correspondientes y diseñada para ser ejecutable por un desarrollador.

## Task Execution Guidelines

- Cada tarea debe completarse antes de pasar a la siguiente
- Las sub-tareas marcadas con `*` son opcionales (tests unitarios, documentación)
- Todas las tareas referencian requirements específicos del documento requirements.md
- El código debe ser funcional y testeable al completar cada tarea

---

## Tasks

- [x] 1. Configurar infraestructura base del proyecto








  - Crear estructura de directorios para microservicios (core-api, agent-ia, analytics, realtime-gateway, files, admin-frontend, advisor-frontend)
  - Configurar Docker Compose con PostgreSQL 15, Redis 7, MinIO para desarrollo
  - Crear Dockerfiles base para cada servicio
  - Configurar variables de entorno por servicio
  - Crear archivo .gitignore, .dockerignore y README.md base
  - Crear scripts de inicialización de base de datos
  - Configurar networks Docker para comunicación entre servicios
  - _Requirements: 11.1, 11.2, 11.3_

- [x] 2. Implementar modelos de datos core





- [x] 2.1 Crear modelos de Usuario, Cliente y Asesor


  - Definir schemas con Tortoise ORM
  - Implementar validaciones de email, teléfono (+57XXXXXXXXXX)
  - Crear enums para roles (ADMIN, ADVISOR, ANALYST, SUPPORT, CLIENT) y estados
  - _Requirements: 1.4, 11.6_

- [x] 2.2 Crear modelos de Solicitud y Repuesto


  - Implementar modelo Solicitud con estados (ABIERTA, EVALUADA, ACEPTADA, RECHAZADA, EXPIRADA, CERRADA_SIN_OFERTAS)
  - Implementar modelo RepuestoSolicitado con validaciones de año vehículo (1980-2025)
  - Establecer relaciones FK entre Solicitud, Cliente y Repuestos
  - _Requirements: 1.3, 1.5_

- [x] 2.3 Crear modelos de Oferta y Evaluación


  - Implementar modelo Oferta con estados simplificados (ENVIADA, GANADORA, NO_SELECCIONADA, EXPIRADA, RECHAZADA, ACEPTADA)
  - Implementar modelo OfertaDetalle con validaciones (precio 1000-50000000, garantía 1-60 meses, tiempo 0-90 días)
  - Implementar modelo AdjudicacionRepuesto para ofertas mixtas
  - Implementar modelo Evaluacion para auditoría
  - _Requirements: 4.5, 5.1, 5.2, 5.3_



- [x] 2.4 Crear modelos de soporte geográfico

  - Implementar modelo AreaMetropolitana (area_metropolitana, ciudad_nucleo, municipio_norm)
  - Implementar modelo HubLogistico (municipio_norm, hub_asignado_norm)
  - Implementar modelo EvaluacionAsesorTemp para cálculos de escalamiento

  - _Requirements: 2.1, 2.2, 2.3_

- [x] 2.5 Implementar importación de datos geográficos

  - Crear función importar_areas_metropolitanas_excel() para procesar Areas_Metropolitanas_TeLOO.xlsx
  - Crear función importar_hubs_logisticos_excel() para procesar Asignacion_Hubs_200km.xlsx
  - Implementar validación de datos geográficos (ciudades duplicadas, hubs inexistentes)
  - Crear endpoint POST /v1/admin/import/geografia para subir archivos Excel
  - Actualizar automáticamente las tablas AreaMetropolitana y HubLogistico
  - _Requirements: 2.2, 2.3_

- [x] 2.6 Crear modelos de analytics y métricas


  - Implementar modelo HistorialRespuestaOferta para actividad reciente
  - Implementar modelo OfertaHistorica para desempeño histórico
  - Implementar modelo AuditoriaTienda para nivel de confianza
  - Implementar modelo EventoSistema para captura de eventos
  - Implementar modelo MetricaCalculada para cache de KPIs
  - Implementar modelo Transaccion para métricas financieras
  - _Requirements: 8.1, 8.3, 9.1_

- [x] 2.7 Escribir tests unitarios de modelos






  - Tests de validación de rangos (precio, garantía, tiempo, año)
  - Tests de validación de formatos (teléfono, email)
  - Tests de relaciones entre modelos
  - _Requirements: 1.4, 1.5, 4.5_

- [x] 3. Implementar sistema de autenticación y autorización





- [x] 3.1 Implementar OAuth2 + JWT local



  - Crear generación de tokens (access 15min, refresh 7d)
  - Implementar algoritmo RS256 con JWKS interno
  - Crear endpoints /auth/login y /auth/refresh
  - _Requirements: 11.6_

- [x] 3.2 Implementar RBAC (Role-Based Access Control)


  - Definir permisos por rol (ADMIN, ADVISOR, ANALYST, SUPPORT, CLIENT)
  - Crear decoradores de autorización para endpoints
  - Implementar middleware de verificación de permisos
  - _Requirements: 11.6_

- [x] 3.3 Escribir tests de autenticación







  - Tests de generación y validación de tokens
  - Tests de permisos por rol
  - _Requirements: 11.6_

- [x] 4. Implementar sistema de escalamiento de asesores





- [x] 4.1 Implementar cálculo de proximidad geográfica


  - Crear función normalizar_ciudad (upper, sin tildes, trim)
  - Implementar get_municipios_am(ciudad) para obtener área metropolitana
  - Implementar get_municipios_hub(ciudad) para obtener hub logístico
  - Implementar calcular_proximidad con 4 niveles (5.0, 4.0, 3.5, 3.0)
  - _Requirements: 2.1, 3.1_

- [x] 4.2 Implementar cálculo de actividad reciente

  - Crear función calcular_actividad_reciente(asesor_id) con período configurable (default 30 días)
  - Calcular (ofertas_respondidas / ofertas_enviadas) * 100
  - Normalizar a escala 1-5: actividad_5 = 1 + 4 * (pct / 100)
  - Implementar fallback a 0% si no hay datos
  - _Requirements: 3.1_

- [x] 4.3 Implementar cálculo de desempeño histórico

  - Crear función calcular_desempeno_historico(asesor_id) con período configurable (default 6 meses)
  - Calcular tasa_adjudicacion (50%), tasa_cumplimiento (30%), eficiencia_respuesta (20%)
  - Normalizar a escala 1-5: desempeno_5 = 1 + 4 * (pct / 100)
  - Implementar fallback a 0% si no hay datos
  - _Requirements: 3.1_

- [x] 4.4 Implementar obtención de nivel de confianza

  - Crear función obtener_nivel_confianza(asesor_id)
  - Buscar auditoría más reciente en AuditoriaTienda
  - Validar vigencia (default 30 días)
  - Implementar fallback a 3.0 si no hay auditoría
  - _Requirements: 3.1_

- [x] 4.5 Implementar determinación de asesores elegibles

  - Crear función determinar_asesores_elegibles(solicitud) con 3 características geográficas
  - Característica 1: Asesores de misma ciudad
  - Característica 2: Asesores de todas las áreas metropolitanas nacionales
  - Característica 3: Asesores del hub logístico de la ciudad
  - Unir conjuntos sin duplicados
  - Registrar en auditoría el conjunto final
  - _Requirements: 2.1, 2.4, 2.5_

- [x] 4.6 Implementar cálculo de puntaje total

  - Crear función calcular_puntaje_asesor(asesor, solicitud)
  - Calcular las 4 variables (proximidad, actividad, desempeño, confianza)
  - Aplicar pesos configurables (40%, 25%, 20%, 15%)
  - Retornar puntaje_total y variables individuales
  - _Requirements: 3.1_

- [x] 4.7 Implementar clasificación por niveles


  - Crear función clasificar_por_niveles(evaluaciones)
  - Clasificar en niveles 1-5 según umbrales configurables (4.5, 4.0, 3.5, 3.0)
  - Guardar en EvaluacionAsesorTemp con canal y tiempo por nivel
  - _Requirements: 3.2, 3.3_

- [x] 4.8 Implementar ejecución de oleadas


  - Crear función ejecutar_oleada(solicitud, nivel)
  - Obtener asesores del nivel desde EvaluacionAsesorTemp
  - Enviar notificaciones según canal (WhatsApp niveles 1-2, Push niveles 3-4)
  - Programar timeout según tiempo configurado por nivel
  - Publicar evento solicitud.oleada a Redis
  - _Requirements: 3.3, 3.4, 4.1, 4.2_

- [x] 4.9 Implementar verificación de cierre anticipado


  - Crear función verificar_cierre_anticipado(solicitud)
  - Contar ofertas recibidas
  - Comparar con ofertas_minimas_deseadas (default 2)
  - Retornar true si se alcanza el mínimo
  - _Requirements: 3.5_

- [x] 4.10 Implementar sistema de configuración de parámetros


  - Crear servicio ConfiguracionService para gestionar parámetros del sistema
  - Implementar funciones get_config() y update_config() con validaciones
  - Crear endpoints GET/PUT /v1/admin/configuracion para gestión de parámetros
  - Validar que pesos sumen 1.0 con tolerancia ±1e-6
  - Validar que umbrales sean decrecientes (nivel1_min > nivel2_min > nivel3_min > nivel4_min)
  - Implementar cache de configuración en Redis con invalidación automática
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [x] 4.11 Implementar importación de datos geográficos

  - Crear endpoint POST /v1/admin/import/areas-metropolitanas para subir Excel
  - Crear endpoint POST /v1/admin/import/hubs-logisticos para subir Excel
  - Parsear archivos Excel y validar estructura requerida (area_metropolitana, ciudad_nucleo, municipio_norm)
  - Actualizar tablas AreaMetropolitana y HubLogistico con nuevos datos
  - Implementar validación de integridad de datos geográficos
  - _Requirements: 2.2, 2.3_

- [x] 4.12 Implementar manejo de errores y casos edge del escalamiento


  - Implementar manejo de ciudades sin AM ni HUB (proximidad por defecto + log warning)
  - Implementar fallbacks para métricas faltantes (actividad/desempeño → 1.0, confianza → 3.0)
  - Crear validación de confianza mínima para operar (configurable, default 2.0)
  - Implementar exclusión automática de asesores con confianza crítica
  - _Requirements: 14.1, 14.2_

- [x] 4.13 Escribir tests del sistema de escalamiento







  - Tests de cálculo de proximidad con diferentes escenarios
  - Tests de normalización de variables (actividad, desempeño)
  - Tests de clasificación por niveles
  - Tests de determinación de asesores elegibles
  - Tests de importación de datos geográficos
  - Tests de manejo de casos edge (ciudades sin AM/HUB, métricatantes)
  - _quirements: 2.1, 3.2, 14.1, 14


- [x] 5. Implementar sistema de ofertas









- [x] 5.1 Crear servicio de ofertas individuales


  - Implementar endpoint POST /v1/ofertas para crear ofertas por formulario
  - Validar que solicitud esté en estado ABIERTA
  - Validar rangos de precio (1000-50000000), garantía (1-60), tiempo (0-90)
  - Crear OfertaDetalle por cada repuesto incluido
  - Publicar evento oferta.created a Redis
  - _Requirements: 4.3, 4.5_

- [x] 5.2 Implementar carga masiva de ofertas Excel





  - Crear endpoint POST /v1/ofertas/upload para subir archivos Excel
  - Validar formato .xlsx y tamaño máximo 5MB
  - Parsear Excel con pandas y validar columnas requeridas
  - Validar datos fila por fila con reporte de errores detallado
  - Crear oferta con múltiples OfertaDetalle si validación exitosa
  - Publicar evento oferta.bulk_uploaded a Redis
  - _Requirements: 4.4_

- [x] 5.3 Implementar gestión de estados de ofertas





  - Crear función actualizar_estado_oferta(oferta_id, nuevo_estado)
  - Validar transiciones permitidas según estados simplificados
  - Registrar cambios en logs de auditoría
  - Publicar eventos de cambio de estado a Redis
  - _Requirements: 5.1, 6.4_

- [x] 5.4 Escribir tests del sistema de ofertas







  - Tests de validación de rangos y formatos
  - Tests de carga masiva Excel (casos válidos e inválidos)
  - Tests de transiciones de estado
  - _Requirements: 4.3, 4.4, 4.5_

- [x] 6. Implementar sistema de evaluación de ofertas




- [x] 6.1 Implementar evaluación por repuesto individual


  - Crear función evaluar_repuesto(repuesto, ofertas_disponibles)
  - Filtrar ofertas que incluyen el repuesto específico
  - Calcular puntaje por oferta: precio(50%) + tiempo(35%) + garantía(15%)
  - Ordenar por puntaje descendente
  - _Requirements: 5.1, 5.2_

- [x] 6.2 Implementar regla de cobertura mínima y cascada


  - Aplicar regla de cobertura ≥50% en evaluar_repuesto
  - Implementar cascada: si mejor oferta <50%, evaluar siguiente
  - Implementar excepción: si única oferta disponible, adjudicar sin importar cobertura
  - Calcular cobertura como (repuestos_cubiertos / total_repuestos)
  - _Requirements: 5.3, 5.4, 5.5_

- [x] 6.3 Implementar evaluación completa de solicitud


  - Crear función evaluar_solicitud(solicitud_id)
  - Evaluar cada repuesto individualmente usando evaluar_repuesto
  - Generar adjudicaciones por repuesto ganador
  - Actualizar estados: GANADORA, NO_SELECCIONADA
  - Guardar adjudicaciones en AdjudicacionRepuesto
  - Cambiar solicitud a estado EVALUADA
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 6.4 Implementar endpoint de evaluación forzada


  - Crear endpoint POST /v1/evaluaciones/{solicitud_id}/run
  - Validar que solicitud tenga ofertas en estado ENVIADA
  - Implementar timeout de evaluación (máximo 5 segundos, configurable)
  - Ejecutar evaluación completa con manejo de timeout
  - Retornar resultado con adjudicaciones y ofertas ganadoras
  - Publicar evento evaluacion.completed a Redis
  - _Requirements: 5.1, 5.2, 14.5_

- [x] 6.5 Implementar validaciones de concurrencia en ofertas


  - Validar que no se puedan crear ofertas durante evaluación activa
  - Retornar error 409 Conflict si solicitud está siendo evaluada
  - Implementar locks distribuidos en Redis para evaluaciones
  - Crear función is_evaluacion_en_progreso(solicitud_id)
  - _Requirements: 14.3_

- [x] 6.6 Implementar timeouts y expiración de ofertas









  - Crear job programado para marcar ofertas como EXPIRADA después de 20h
  - Implementar timeout configurable por solicitud
  - Crear función procesar_expiracion_ofertas() que corre cada hora
  - Notificar a clientes 2 horas antes de expiración (configurable)
  - _Requirements: 6.5_

- [x] 6.7 Escribir tests del sistema de evaluación








  - Tests de cálculo de puntajes de ofertas
  - Tests de regla de cobertura mínima
  - Tests de cascada cuando mejor oferta no cumple 50%
  - Tests de adjudicación por excepción (única oferta)
  - Tests de evaluación completa con múltiples repuestos
  - Tests de timeout de evaluación y manejo de errores
  - Tests de validaciones de concurrencia
  - Tests de expiración de ofertas
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 14.3, 14.5, 6.5_

- [-] 7. Implementar Agent IA Service



- [x] 7.1 Crear webhook de WhatsApp


  - Implementar endpoint POST /v1/webhooks/whatsapp
  - Validar formato de mensajes entrantes de Meta
  - Extraer información básica (from, text, timestamp)
  - Implementar rate limiting (100 req/min/IP) con Redis
  - Implementar validación de webhook signature de Meta
  - Crear cola de mensajes pendientes para procesamiento asíncrono
  - _Requirements: 1.1_



- [x] 7.2 Implementar procesamiento NLP con múltiples proveedores LLM





  - Crear función procesar_mensaje_whatsapp(mensaje)
  - Implementar extracción con regex para casos simples:
    - Patrones para repuestos comunes (filtro, aceite, pastillas, etc.)
    - Patrones para vehículos (marca año modelo)
    - Patrones para datos de contacto (teléfono, nombre)
    - Patrones para ciudades principales
  - Implementar estrategia de múltiples proveedores LLM por complejidad:
    - **Nivel 1 - Texto simple** (Deepseek/Ollama local): Mensajes cortos y directos
    - **Nivel 2 - Texto complejo** (Gemini): Mensajes largos, múltiples repuestos, jerga
    - **Nivel 3 - Documentos estructurados** (OpenAI GPT-4): Extracción desde Excel, PDFs
    - **Nivel 4 - Contenido multimedia** (Anthropic Claude): Análisis de audios, imágenes
  - Crear sistema de clasificación automática de complejidad:
    - Longitud del mensaje, número de entidades, tipo de contenido
    - Confianza del regex, presencia de archivos adjuntos
  - Extraer: repuestos, vehículo (marca, línea, año), cliente (nombre, teléfono, ciudad)
  - Implementar fallback en cascada: regex → Deepseek → Gemini → OpenAI → Anthropic → procesamiento básico
  - Implementar circuit breaker individual por proveedor (failure_threshold=3, timeout=300s)
  - Implementar retry con backoff exponencial y rotación de proveedores
  - Crear métricas de costo y precisión por proveedor para optimización automática
  - _Requirements: 1.1, 1.6, 14.4_



- [x] 7.2.1 Implementar servicio de múltiples proveedores LLM


  - Crear LLMProviderService con interfaz unificada
  - Implementar adaptadores para cada proveedor:
    - DeepseekAdapter (API + costo bajo)
    - OllamaAdapter (local + gratis)
    - GeminiAdapter (Google AI + costo medio)
    - OpenAIAdapter (GPT-4 + costo alto)
    - AnthropicAdapter (Claude + costo premium)
  - Implementar LLMRouter para selección automática de proveedor
  - Crear sistema de métricas: latencia, costo, precisión, disponibilidad


  - Implementar cache de respuestas por hash de entrada (Redis, TTL 24h)
  - Crear configuración dinámica de proveedores (habilitado/deshabilitado, límites de costo)
  - _Requirements: 1.1, 1.6, 14.4_

- [x] 7.3 Implementar gestión de conversaciones


  - Crear función gestionar_conversacion(telefono, mensaje)
  - Mantener contexto de conversación en Redis (TTL 1 hora)
  - Identificar información faltante y solicitar aclaraciones
  - Validar completitud antes de crear solicitud
  - _Requirements: 1.2_

- [x] 7.4 Implementar procesamiento de archivos multimedia





  - Crear función procesar_archivo_adjunto(archivo, tipo_contenido)
  - Implementar procesamiento de Excel/CSV:
    - Usar OpenAI GPT-4 para extracción estructurada
    - Detectar columnas de repuestos, cantidades, especificaciones
    - Validar y normalizar datos extraídos
  - Implementar procesamiento de audios:
    - Usar Anthropic Claude para transcripción y análisis
    - Extraer información de repuestos desde audio


    - Manejar ruido de fondo y calidad variable
  - Implementar procesamiento de imágenes:
    - Usar Anthropic Claude Vision para análisis de imágenes
    - Extraer texto de facturas, catálogos, fotos de repuestos
    - Identificar códigos de parte y especificaciones
  - Crear sistema de validación cruzada entre proveedores para archivos críticos

  - _Requirements: 1.1, 1.6, 14.4_

- [x] 7.5 Implementar creación de solicitudes desde WhatsApp





  - Crear función crear_solicitud_desde_whatsapp(datos_extraidos)
  - Validar datos extraídos (teléfono, ciudad, año vehículo)
  - Crear Cliente si no existe
  - Crear Solicitud con RepuestosSolicitados
  - Enviar confirmación por WhatsApp
  - _Requirements: 1.3_

- [x] 7.6 Implementar envío de resultados a clientes





  - Crear función enviar_resultado_evaluacion(solicitud_id)
  - Formatear mensaje según tipo: oferta única vs oferta mixta
  - Incluir información: precio, tiempo, garantía, proveedor(es)
  - Manejar respuestas del cliente (SÍ, NO, DETALLES)
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 7.7 Implementar manejo robusto de errores y timeouts





  - Implementar circuit breaker para WhatsApp API con retry exponencial
  - Crear manejo de timeout para evaluaciones (máximo 5 segundos)
  - Implementar fallbacks para APIs de LLM (regex → LLM secundario → básico)
  - Crear logs de advertencia para ciudades sin AM ni HUB
  - Implementar valores por defecto para métricas faltantes de asesores
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 7.7 Escribir tests del Agent IA










  - Tests de procesamiento NLP con diferentes formatos de mensaje
  - Tests de extracción de datos de repuestos y vehículos
  - Tests de gestión de conversaciones incompletas
  - Tests de creación de solicitudes válidas
  - _Requirements: 1.1, 1.2, 1.3, 1.6_

- [ ] 8. Implementar Analytics Service
- [x] 8.1 Crear capturador de eventos
  - Implementar EventCollector que consume Redis pub/sub
  - Suscribirse a eventos: solicitud.*, oferta.*, evaluacion.*, cliente.*
  - Almacenar eventos en EventoSistema para auditoría
  - Procesar eventos en tiempo real para métricas
  - _Requirements: 8.1_

- [x] 8.2 Implementar calculadora de métricas básicas
  - Crear MetricsCalculator con funciones para KPIs simples
  - Implementar cálculo de KPIs en tiempo real (4 KPIs críticos)
  - Implementar cache de KPIs frecuentes con TTL configurable
  - Usar réplica de lectura de PostgreSQL para consultas
  - _Requirements: 8.3_

- [x] 8.3 Implementar generador de dashboards
  - Crear DashboardGenerator para los 5 dashboards principales
  - Dashboard Principal: 4 KPIs superiores + gráficos del mes
  - Embudo Operativo: 11 KPIs de proceso
  - Salud del Marketplace: 5 KPIs de sistema
  - Dashboard Financiero: 5 KPIs de transacciones
  - Análisis de Asesores: 13 KPIs de performance
  - _Requirements: 8.2, 8.3_

- [x] 8.4 Implementar jobs batch para métricas complejas






  - Crear jobs programados para KPIs que requieren cálculos pesados
  - Job diario (2 AM): ranking de asesores, especialización por repuesto
  - Job semanal: evolución temporal, análisis de tendencias
  - Almacenar resultados en MetricaCalculada
  - _Requirements: 8.3_

- [x] 8.5 Implementar vistas materializadas para KPIs históricos






  - Crear vista materializada mv_metricas_mensuales para datos históricos
  - Crear vista materializada mv_ranking_asesores para rankings por ciudad
  - Implementar job de refresh automático (1 AM diario) con pg_cron
  - Crear función refresh_all_mv() en PostgreSQL
  - _Requirements: 8.3_

- [x] 8.6 Implementar sistema de alertas





  - Crear AlertManager para umbrales configurables
  - Monitorear KPIs críticos y generar alertas automáticas
  - Enviar notificaciones por email/Slack cuando se superen umbrales
  - Configurar alertas por: error rate, latencia, conversión baja
  - _Requirements: 8.4_

- [x] 8.7 Escribir tests del Analytics Service







  - Tests de captura y procesamiento de eventos
  - Tests de cálculo de KPIs individuales
  - Tests de generación de dashboards
  - Tests de jobs batch programados
  - _Requirements: 8.1, 8.2, 8.3_

- [-] 9. Implementar Admin Frontend



- [x] 9.1 Crear estructura base y autenticación


  - Configurar React + Vite + Tailwind + shadcn/ui con tema Amber Minimal
  - Implementar login con JWT y manejo de tokens
  - Crear layout principal con sidebar y header
  - Implementar rutas protegidas por rol
  - _Requirements: 12.1, 12.5_

- [x] 9.2 Implementar dashboard principal





  - Crear componente Dashboard con 4 KPIs superiores
  - Implementar gráficos de líneas del mes actual (solicitudes, aceptadas, cerradas)
  - Crear tabla de top 15 solicitudes abiertas con mayor tiempo
  - Conectar con Analytics Service para obtener datos
  - _Requirements: 12.1, 12.2, 12.3_

- [x] 9.3 Implementar módulo de gestión de asesores









  - Crear componente AsesoresTable con información completa
  - Implementar funciones: crear, editar, suspender/activar asesor
  - Crear formularios de importar/exportar Excel
  - Mostrar 3 KPIs superiores del módulo
  - _Requirements: 12.4_

- [x] 9.4 Implementar módulo de reportes y analytics








  - Crear 4 dashboards con sus respectivos KPIs
  - Implementar filtros por fecha y otros criterios
  - Crear funcionalidad de exportar datos
  - Conectar con Analytics Service para datos en tiempo real
  - _Requirements: 12.4, 8.2, 8.5_

- [x] 9.5 Implementar módulo de PQR








  - Crear lista de PQR por estado (Abiertas, En proceso, Cerradas)
  - Implementar formulario de respuesta y seguimiento
  - Mostrar métricas de tiempo de resolución
  - Crear endpoints CRUD para gestión de PQR
  - Implementar sistema de prioridades (BAJA, MEDIA, ALTA, CRITICA)
  - Crear notificaciones automáticas para PQR de alta prioridad
  - _Requirements: 12.4_

- [x] 9.6 Implementar módulo de configuración
- [x] 9.6.1 Crear servicio de configuración frontend
  - Implementar configuracionService con API client para backend
  - Crear tipos TypeScript para todas las categorías de configuración
  - Implementar validaciones de pesos (suman 1.0) y umbrales (decrecientes)
  - Crear hooks useConfiguracion, useUsuarios, useRoles para gestión de estado
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 9.6.2 Implementar página principal de configuración
  - Crear ConfiguracionPage con 3 tabs: Sistema, Usuarios, Roles
  - Implementar indicadores de validación en tiempo real
  - Crear botón de reset completo con confirmación
  - Mostrar estadísticas de configuración (categorías, parámetros, última modificación)
  - _Requirements: 12.5_

- [x] 9.6.3 Implementar formularios de parámetros del sistema
  - Crear PesosEscalamientoForm con validación de suma 1.0 y progress bar
  - Crear UmbralesNivelesForm con validación de orden decreciente
  - Crear TiemposEsperaForm para configurar tiempos por nivel (1-5)
  - Crear CanalesNotificacionForm para seleccionar canales por nivel
  - Crear PesosEvaluacionForm para pesos de evaluación de ofertas
  - Crear ParametrosGeneralesForm para parámetros operativos
  - Implementar validación en tiempo real y feedback visual
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 9.6.4 Implementar gestión de usuarios
  - Crear GestionUsuarios con tabla completa de usuarios del sistema
  - Implementar CRUD completo: crear, editar, eliminar, activar/desactivar
  - Crear UsuarioForm con validaciones de email y roles
  - Implementar filtros por rol y estado con búsqueda por nombre/email
  - Mostrar estadísticas de usuarios por estado (activos, inactivos, suspendidos)
  - _Requirements: 12.5_

- [x] 9.6.5 Implementar gestión de roles y permisos
  - Crear GestionRoles con tabla de roles del sistema
  - Implementar CRUD de roles con asignación de permisos
  - Crear RolForm con selección múltiple de permisos por categoría
  - Implementar activación/desactivación de roles
  - Organizar permisos por categorías (admin, solicitudes, ofertas, etc.)
  - Crear funcionalidad de seleccionar/deseleccionar todos los permisos
  - _Requirements: 12.5_

- [x] 9.6.6 Implementar componentes UI faltantes
  - Crear componente Progress para barras de progreso de validación
  - Crear componente Alert para mensajes de error y éxito
  - Crear componente Checkbox para selección de permisos
  - Crear componente Switch para activar/desactivar elementos
  - Integrar todos los componentes con el tema Amber Minimal
  - _Requirements: 12.5_

- [x] 9.7 Escribir tests del Admin Frontend








  - Tests de componentes principales (Dashboard, AsesoresTable)
  - Tests de autenticación y rutas protegidas
  - Tests de formularios de configuración
  - Tests E2E de flujos críticos
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 10. Implementar Advisor Frontend




- [x] 10.1 Crear estructura base y autenticación de asesor


  - Configurar React + Vite + Tailwind + shadcn/ui con tema Amber Minimal
  - Implementar login específico para asesores
  - Crear layout con dashboard de KPIs y navegación por pestañas
  - _Requirements: 13.1, 13.2_

- [x] 10.2 Implementar pestaña de solicitudes abiertas


  - Crear lista de solicitudes disponibles para ofertar
  - Mostrar información de vehículo y repuestos con tiempo restante
  - Implementar botón "Hacer Oferta" que abre modal de oferta individual
  - Implementar botón "Carga Masiva Excel" con upload component
  - _Requirements: 13.3, 13.4_

- [x] 10.3 Implementar modal de oferta individual


  - Crear formulario por repuesto con precio y garantía
  - Permitir seleccionar qué repuestos incluir en la oferta
  - Campo de tiempo de entrega total del pedido
  - Validaciones en tiempo real de rangos permitidos
  - _Requirements: 13.3_

- [x] 10.4 Implementar carga masiva Excel


  - Crear componente de drag & drop para archivos Excel
  - Implementar descarga de template Excel
  - Mostrar preview de datos antes de enviar
  - Mostrar errores de validación por fila
  - _Requirements: 13.4_

- [x] 10.5 Implementar pestañas de cerradas y ganadas


  - Pestaña CERRADAS: historial de solicitudes no adjudicadas
  - Pestaña GANADAS: ofertas ganadoras con estado del cliente
  - Mostrar información de contacto si oferta fue aceptada
  - _Requirements: 13.2_

- [ ] 10.6 Escribir tests del Advisor Frontend






  - Tests de componentes de ofertas (individual y masiva)
  - Tests de navegación entre pestañas
  - Tests de validaciones de formularios
  - Tests E2E de flujo completo de oferta
  - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 11. Implementar servicios de soporte






- [x] 11.1 Implementar Realtime Gateway


  - Configurar WebSocket server con Socket.IO
  - Implementar autenticación de WebSocket con JWT
  - Crear rooms por rol (admin, advisor) para broadcasting
  - Conectar con Redis adapter para escalabilidad
  - _Requirements: 10.1, 10.2_

- [x] 11.2 Implementar Files Service


  - Crear servicio para gestión de archivos Excel
  - Implementar validación de archivos (formato, tamaño, antivirus)
  - Configurar almacenamiento en MinIO
  - Crear endpoints para upload/download de templates
  - _Requirements: 4.4_

- [x] 11.3 Implementar sistema de notificaciones


  - Crear servicio de notificaciones push internas
  - Implementar fallback a WhatsApp cuando WebSocket no disponible
  - Crear cola de notificaciones pendientes en Redis
  - _Requirements: 10.3, 10.4, 10.5_

- [ ]* 11.4 Escribir tests de servicios de soporte
  - Tests de WebSocket connections y broadcasting
  - Tests de upload/validación de archivos
  - Tests de sistema de notificaciones
  - _Requirements: 10.1, 10.2, 4.4_

- [-] 12. Configurar observabilidad y monitoreo


- [x] 12.1 Implementar logging estructurado y auditoría


  - Configurar logging con formato JSON en todos los servicios
  - Implementar correlation IDs para trazabilidad
  - Configurar niveles de log por ambiente (dev/staging/prod)
  - Crear sistema de logs de auditoría para todas las operaciones críticas
  - Implementar LogAuditoria para registrar cambios en entidades
  - Crear función log_auditoria(actor, accion, entidad, entidad_id, diff)
  - _Requirements: 9.1, 9.2, 9.4, 9.5_

- [x] 12.2 Configurar métricas y alertas


  - Implementar métricas de Prometheus en todos los servicios
  - Configurar Grafana con dashboards de sistema
  - Crear alertas para SLOs: disponibilidad >99.5%, latencia p95 <300ms
  - _Requirements: 14.5_

- [x] 12.3 Implementar health checks
  - Crear endpoints /health, /health/ready, /health/live en todos los servicios
  - Implementar checks de dependencias (DB, Redis, MinIO)
  - Configurar readiness y liveness probes para Kubernetes
  - Implementar health checks en Docker Compose con intervalos optimizados
  - Crear scripts de testing de health checks (bash y Python)
  - Documentar configuración de health checks en HEALTH_CHECKS.md
  - _Requirements: 14.5_

- [ ]* 12.4 Escribir tests de observabilidad
  - Tests de generación de métricas
  - Tests de health checks
  - Tests de logging estructurado
  - _Requirements: 9.4, 14.5_

- [-] 13. Configurar deployment y DevOps
- [x] 13.1 Crear configuración de Docker
  - Crear Dockerfiles optimizados para cada servicio (core-api, agent-ia, analytics, realtime-gateway, files)
  - Implementar multi-stage builds para optimizar tamaño de imágenes
  - Configurar Docker Compose para desarrollo local con PostgreSQL, Redis, MinIO
  - Crear docker-compose.override.yml para desarrollo con hot reload
  - Configurar networks y volumes apropiados para cada servicio
  - Crear .dockerignore para optimizar build context
  - _Requirements: 11.1, 11.2_

- [x] 13.1.1 Dockerizar frontends con multi-stage builds
  - Crear Dockerfiles multi-stage para admin-frontend y advisor-frontend
  - Implementar 4 stages: deps, builder, development, production
  - Configurar stage development con node:18-slim y hot reload
  - Configurar stage production optimizado con archivos compilados
  - Instalar @rollup/rollup-linux-x64-gnu para compatibilidad con Vite
  - Configurar usuario no-root (nextjs:nodejs) para seguridad
  - Implementar health checks con curl en ambos frontends
  - Configurar volúmenes anónimos para node_modules en docker-compose
  - Agregar frontends a docker-compose.yml con dependencias correctas
  - Verificar funcionamiento: admin-frontend (3000), advisor-frontend (3001)
  - _Requirements: 11.1, 11.2, 12.1, 13.1, 13.2_

- [x] 13.2 Configurar CI/CD pipeline con Docker




  - Crear GitHub Actions para build, test y deploy con Docker
  - Implementar build de imágenes Docker en pipeline
  - Configurar Docker Registry (GitHub Container Registry o Docker Hub)
  - Implementar tests automáticos en contenedores
  - Configurar deployment automático a staging con Docker Compose
  - Crear proceso de deployment manual a producción con Kubernetes/Docker Swarm
  - Implementar security scanning de imágenes Docker con Trivy
  - _Requirements: 11.1_

- [ ] 13.3 Configurar variables de entorno y secrets
  - Crear archivos .env por ambiente (dev/staging/prod)
  - Configurar Docker secrets para datos sensibles (JWT keys, DB passwords)
  - Documentar todas las variables requeridas por servicio
  - Implementar validación de configuración al inicio de cada contenedor
  - Crear docker-compose.prod.yml para producción con secrets
  - _Requirements: 11.2, 11.3_

- [ ] 13.4 Configurar orquestación para producción
  - Crear configuración de Kubernetes (deployments, services, ingress)
  - Configurar Docker Swarm como alternativa más simple
  - Implementar load balancing entre instancias de servicios
  - Configurar auto-scaling basado en CPU/memoria
  - Crear configuración de backup automático para volúmenes
  - Implementar rolling updates sin downtime
  - _Requirements: 11.1, 11.2_

- [ ]* 13.5 Escribir documentación de deployment
  - Guía de instalación local con Docker Compose
  - Guía de deployment a producción con Kubernetes/Docker Swarm
  - Documentación de configuración de variables de entorno
  - Troubleshooting común de contenedores
  - Guía de backup y restore de volúmenes Docker
  - Procedimientos de rollback en producción
  - _Requirements: 11.1, 11.2_
## Summary
ain sections, ~85 b-tasks**
- ✅ *al Tasks: 1m**: Tasks 1-6 (Infrastructure, Models, Auth, Escalamiento, Ofertas, Evaluación)
- ✅ **Services**: Tasks 7-8 (Agent IA, Analytics)  
- ✅ **Frontends**: Tasks 9-10 (Admin, Advisor)
- ✅ **Support**: Tasks 11-13 (Realtime, Files, Observability, DevOps)

**Key Additions**:
- ✅ **Sin Docker**: Configuración para instalación local directa
- ✅ **Importación de datos geográficos**: Excel de áreas metropolitanas y hubs
- ✅ **Sistema de configuración**: Gestión completa de parámetros del sistema
- ✅ **Manejo robusto de errores**: Circuit breakers, timeouts, fallbacks

**Optional Tasks**: ~22 tasks marked with `*` (mainly testing and documentation)
**Requirements Coverage**: All 14 requirements covered across tasks
**Implementation Approach**: Incremental, each task builds on previous onesocumentation)
**Requirements Coverage**: All 14 requirements covered across tasks
**Implementation Approach**: Incremental, each task builds on previous ones