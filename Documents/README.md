# TeLOO V3 - Marketplace Inteligente de Repuestos Automotrices

TeLOO V3 es un marketplace automatizado que conecta clientes que necesitan repuestos automotrices con asesores/proveedores mediante algoritmos inteligentes de escalamiento, evaluación y adjudicación de ofertas.

## 🏗️ Arquitectura

El sistema está construido con una arquitectura de microservicios que incluye:

### Backend Services
- **Core API** (Puerto 8000): Motor central del sistema - gestión de solicitudes, ofertas, evaluación y escalamiento
- **Agent IA** (Puerto 8001): Interfaz conversacional con clientes vía WhatsApp usando múltiples proveedores LLM
- **Analytics** (Puerto 8002): Métricas, dashboards y reportes del sistema con 34 KPIs
- **Realtime Gateway** (Puerto 8003): Comunicación WebSocket en tiempo real
- **Files** (Puerto 8004): Gestión de archivos Excel con validación y antivirus

### Frontend Applications
- **Admin Frontend** (Puerto 3000): Interfaz administrativa completa con dashboards y gestión
- **Advisor Frontend** (Puerto 3001): Interfaz para asesores con gestión de ofertas

### Infrastructure
- **PostgreSQL 15**: Base de datos principal con extensiones pg_cron y uuid-ossp
- **Redis 7**: Cache, pub/sub y locks distribuidos
- **MinIO**: Almacenamiento S3-compatible para archivos

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker y Docker Compose
- Git

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd teloo-v3-marketplace
```

2. **Configurar variables de entorno**
```bash
# Copiar archivos de ejemplo para cada servicio
cp services/core-api/.env.example services/core-api/.env
cp services/agent-ia/.env.example services/agent-ia/.env
cp services/analytics/.env.example services/analytics/.env
cp services/realtime-gateway/.env.example services/realtime-gateway/.env
cp services/files/.env.example services/files/.env
cp frontend/admin/.env.example frontend/admin/.env
cp frontend/advisor/.env.example frontend/advisor/.env

# Editar las variables según tu entorno
```

3. **Levantar la infraestructura**
```bash
# Levantar solo la base de datos y servicios de soporte
docker-compose up -d postgres redis minio

# Esperar a que los servicios estén listos
docker-compose logs -f postgres
```

4. **Levantar todos los servicios**
```bash
# Desarrollo con hot reload
docker-compose up

# O en background
docker-compose up -d
```

5. **Verificar que todo esté funcionando**
```bash
# Verificar estado de los servicios
docker-compose ps

# Ver logs
docker-compose logs -f core-api
```

## 📋 URLs de Acceso

Una vez que todos los servicios estén ejecutándose:

- **Admin Frontend**: http://localhost:3000
- **Advisor Frontend**: http://localhost:3001
- **Core API Docs**: http://localhost:8000/docs
- **Agent IA Docs**: http://localhost:8001/docs
- **Analytics Docs**: http://localhost:8002/docs
- **Realtime Gateway**: http://localhost:8003
- **Files Service Docs**: http://localhost:8004/docs
- **MinIO Console**: http://localhost:9001 (teloo_minio / teloo_minio_password)

## 🔧 Configuración

### Variables de Entorno Críticas

#### Core API
```env
DATABASE_URL=postgresql://teloo_user:teloo_password@postgres:5432/teloo_v3
REDIS_URL=redis://redis:6379
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
```

#### Agent IA
```env
WHATSAPP_ACCESS_TOKEN=your-whatsapp-access-token
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

#### MinIO
```env
MINIO_ROOT_USER=teloo_minio
MINIO_ROOT_PASSWORD=teloo_minio_password
```

### Configuración de WhatsApp

1. Configurar webhook en Meta Developer Console
2. URL del webhook: `https://your-domain.com/v1/webhooks/whatsapp`
3. Token de verificación: configurar en `WHATSAPP_VERIFY_TOKEN`

### Configuración de LLM

El sistema soporta múltiples proveedores:
- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- Modelos locales (configuración adicional requerida)

## 🏢 Estructura del Proyecto

```
teloo-v3-marketplace/
├── services/
│   ├── core-api/          # Motor central del sistema
│   ├── agent-ia/          # Procesamiento NLP y WhatsApp
│   ├── analytics/         # Métricas y dashboards
│   ├── realtime-gateway/  # WebSocket y notificaciones
│   └── files/             # Gestión de archivos
├── frontend/
│   ├── admin/             # Interfaz administrativa
│   └── advisor/           # Interfaz para asesores
├── scripts/
│   └── init-db.sql        # Inicialización de base de datos
├── docker-compose.yml     # Configuración de servicios
└── docker-compose.override.yml  # Overrides para desarrollo
```

## 🔄 Flujo del Sistema

1. **Cliente solicita repuestos** vía WhatsApp
2. **Agent IA** procesa el mensaje con NLP y crea solicitud estructurada
3. **Sistema de Escalamiento** determina asesores elegibles y los clasifica en 5 niveles
4. **Notificaciones** se envían por oleadas (WhatsApp niveles 1-2, Push niveles 3-4)
5. **Asesores** envían ofertas individuales o masivas vía Excel
6. **Evaluación Automática** selecciona mejores ofertas por repuesto individual
7. **Cliente** recibe resultado y puede aceptar/rechazar
8. **Analytics** captura métricas en tiempo real para dashboards

## 📊 Dashboards y KPIs

El sistema incluye 4 dashboards principales con 34 KPIs:

1. **Embudo Operativo** (11 KPIs): Solicitudes, ofertas, evaluaciones, conversiones
2. **Salud del Marketplace** (5 KPIs): Tiempos de respuesta, participación, satisfacción
3. **Dashboard Financiero** (5 KPIs): Volumen transaccional, comisiones, rentabilidad
4. **Análisis de Asesores** (13 KPIs): Performance, rankings, especialización

## 🛠️ Comandos Útiles

### Docker
```bash
# Reconstruir servicios
docker-compose build

# Ver logs de un servicio específico
docker-compose logs -f core-api

# Reiniciar un servicio
docker-compose restart core-api

# Limpiar volúmenes (¡CUIDADO! Borra datos)
docker-compose down -v
```

### Base de Datos
```bash
# Conectar a PostgreSQL
docker-compose exec postgres psql -U teloo_user -d teloo_v3

# Backup de base de datos
docker-compose exec postgres pg_dump -U teloo_user teloo_v3 > backup.sql

# Restaurar backup
docker-compose exec -T postgres psql -U teloo_user teloo_v3 < backup.sql
```

### Desarrollo
```bash
# Instalar dependencias de frontend
cd frontend/admin && npm install
cd frontend/advisor && npm install

# Ejecutar tests (cuando estén implementados)
docker-compose exec core-api pytest
```

## 🔒 Seguridad

- JWT con algoritmo RS256 para autenticación
- Validación de webhooks de WhatsApp
- Rate limiting en APIs
- Validación de archivos con antivirus
- Logs de auditoría completos
- Variables de entorno para secretos

## 📈 Monitoreo

- Health checks en todos los servicios
- Logs estructurados en formato JSON
- Métricas de Prometheus (configuración adicional)
- Alertas automáticas por umbrales configurables

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto es propiedad de TeLOO. Todos los derechos reservados.

## 📞 Soporte

Para soporte técnico, contactar al equipo de desarrollo de TeLOO.

---

**TeLOO V3** - Conectando el futuro de los repuestos automotrices 🚗⚡