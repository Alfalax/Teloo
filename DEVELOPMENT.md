# TeLOO V3 - Guía de Desarrollo

Esta guía te ayudará a configurar y ejecutar el entorno de desarrollo de TeLOO V3.

## 🚀 Inicio Rápido

### 1. Prerrequisitos

- **Docker Desktop** instalado y ejecutándose
- **Git** para clonar el repositorio
- **Node.js 18+** (opcional, para desarrollo frontend local)
- **Python 3.11+** (opcional, para desarrollo backend local)

### 2. Configuración Inicial

```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd teloo-v3-marketplace

# 2. Configurar variables de entorno
scripts\setup-env.bat

# 3. Editar archivos .env según tus necesidades
# Especialmente importante:
# - services\core-api\.env (JWT_SECRET_KEY)
# - services\agent-ia\.env (API keys de WhatsApp y LLM)
```

### 3. Levantar el Sistema

```bash
# Opción A: Levantar solo la infraestructura
scripts\start-infrastructure.bat

# Opción B: Levantar todo el sistema
scripts\start-services.bat

# Para detener todo
scripts\stop-all.bat
```

## 🏗️ Arquitectura del Proyecto

```
teloo-v3-marketplace/
├── services/                    # Microservicios backend
│   ├── core-api/               # Motor central del sistema
│   ├── agent-ia/               # Procesamiento NLP y WhatsApp
│   ├── analytics/              # Métricas y dashboards
│   ├── realtime-gateway/       # WebSocket y notificaciones
│   └── files/                  # Gestión de archivos
├── frontend/                   # Aplicaciones frontend
│   ├── admin/                  # Interfaz administrativa
│   └── advisor/                # Interfaz para asesores
├── scripts/                    # Scripts de utilidad
│   ├── init-db.sql            # Inicialización de BD
│   ├── start-infrastructure.bat
│   ├── start-services.bat
│   └── setup-env.bat
├── docker-compose.yml          # Configuración de servicios
└── docker-compose.override.yml # Overrides para desarrollo
```

## 🔧 Desarrollo por Servicio

### Backend Services (Python/FastAPI)

Cada servicio backend tiene la siguiente estructura:
```
services/{service-name}/
├── main.py              # Punto de entrada
├── requirements.txt     # Dependencias Python
├── Dockerfile          # Configuración Docker
├── .env.example        # Variables de entorno ejemplo
└── .env               # Variables de entorno (crear desde .example)
```

**Desarrollo local (sin Docker):**
```bash
cd services/core-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Desarrollo con Docker:**
```bash
# Reconstruir un servicio específico
docker-compose build core-api

# Ejecutar solo un servicio
docker-compose up core-api

# Ver logs de un servicio
docker-compose logs -f core-api
```

### Frontend Services (React/Vite)

Cada frontend tiene la siguiente estructura:
```
frontend/{frontend-name}/
├── src/                # Código fuente React
├── public/             # Archivos estáticos
├── package.json        # Dependencias Node.js
├── vite.config.ts      # Configuración Vite
├── tailwind.config.js  # Configuración Tailwind
├── Dockerfile          # Configuración Docker
├── .env.example        # Variables de entorno ejemplo
└── .env               # Variables de entorno (crear desde .example)
```

**Desarrollo local (sin Docker):**
```bash
cd frontend/admin
npm install
npm run dev
# Acceder a http://localhost:3000
```

**Desarrollo con Docker:**
```bash
# Reconstruir frontend
docker-compose build admin-frontend

# Ejecutar solo frontend
docker-compose up admin-frontend
```

## 🗄️ Base de Datos

### Conexión a PostgreSQL

```bash
# Conectar a la base de datos
docker-compose exec postgres psql -U teloo_user -d teloo_v3

# Backup
docker-compose exec postgres pg_dump -U teloo_user teloo_v3 > backup.sql

# Restaurar
docker-compose exec -T postgres psql -U teloo_user teloo_v3 < backup.sql
```

### Esquema de Base de Datos

La base de datos se inicializa automáticamente con:
- Todas las tablas necesarias
- Índices optimizados
- Funciones y triggers
- Datos de configuración por defecto
- Usuario administrador por defecto

Ver `scripts/init-db.sql` para detalles completos.

## 🔍 URLs de Desarrollo

Una vez que todos los servicios estén ejecutándose:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Admin Frontend | http://localhost:3000 | Interfaz administrativa |
| Advisor Frontend | http://localhost:3001 | Interfaz para asesores |
| Core API | http://localhost:8000/docs | Documentación API principal |
| Agent IA | http://localhost:8001/docs | Documentación API de IA |
| Analytics | http://localhost:8002/docs | Documentación API de analytics |
| Realtime Gateway | http://localhost:8003 | WebSocket gateway |
| Files Service | http://localhost:8004/docs | Documentación API de archivos |
| MinIO Console | http://localhost:9001 | Consola de almacenamiento |

### Credenciales por Defecto

- **PostgreSQL**: `teloo_user` / `teloo_password`
- **MinIO**: `teloo_minio` / `teloo_minio_password`
- **Admin Usuario**: `admin@teloo.com` (sin contraseña configurada aún)

## 🧪 Testing

### Backend Tests
```bash
# Ejecutar tests de un servicio
docker-compose exec core-api pytest

# Con cobertura
docker-compose exec core-api pytest --cov
```

### Frontend Tests
```bash
# Ejecutar tests de frontend
cd frontend/admin
npm test

# Tests en modo watch
npm run test:watch
```

## 🔧 Comandos Útiles

### Docker
```bash
# Ver estado de todos los servicios
docker-compose ps

# Reconstruir todo
docker-compose build

# Ver logs de todos los servicios
docker-compose logs -f

# Reiniciar un servicio específico
docker-compose restart core-api

# Ejecutar comando en un contenedor
docker-compose exec core-api bash
```

### Limpieza
```bash
# Limpiar contenedores parados
docker container prune

# Limpiar imágenes no utilizadas
docker image prune

# Limpieza completa (¡CUIDADO! Borra datos)
scripts\clean-all.bat
```

## 🐛 Troubleshooting

### Problemas Comunes

1. **Puerto ya en uso**
   ```bash
   # Verificar qué proceso usa el puerto
   netstat -ano | findstr :8000
   # Matar proceso si es necesario
   taskkill /PID <PID> /F
   ```

2. **Servicios no se conectan**
   - Verificar que la red Docker esté creada: `docker network ls`
   - Reiniciar Docker Desktop
   - Verificar variables de entorno en archivos `.env`

3. **Base de datos no se inicializa**
   - Verificar logs: `docker-compose logs postgres`
   - Eliminar volumen y recrear: `docker-compose down -v`

4. **Frontend no carga**
   - Verificar que las variables `VITE_API_URL` estén correctas
   - Limpiar cache del navegador
   - Verificar logs: `docker-compose logs admin-frontend`

### Logs y Debugging

```bash
# Ver logs en tiempo real
docker-compose logs -f [service-name]

# Ver logs de los últimos 100 líneas
docker-compose logs --tail=100 [service-name]

# Entrar a un contenedor para debugging
docker-compose exec [service-name] bash
```

## 📝 Configuración de Desarrollo

### Variables de Entorno Importantes

**Core API (.env)**:
```env
DATABASE_URL=postgresql://teloo_user:teloo_password@postgres:5432/teloo_v3
REDIS_URL=redis://redis:6379
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
ENVIRONMENT=development
DEBUG=true
```

**Agent IA (.env)**:
```env
WHATSAPP_ACCESS_TOKEN=your-whatsapp-access-token
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
CORE_API_URL=http://core-api:8000
```

### Hot Reload

Todos los servicios están configurados para hot reload en desarrollo:
- **Backend**: Uvicorn con `--reload`
- **Frontend**: Vite con hot module replacement
- **Volúmenes**: Código fuente montado en contenedores

## 🚀 Deployment

Para producción, ver la documentación específica de deployment en el README principal.

## 📞 Soporte

Si encuentras problemas durante el desarrollo:

1. Revisar esta guía de troubleshooting
2. Verificar logs de los servicios
3. Consultar la documentación de la API en `/docs`
4. Contactar al equipo de desarrollo

---

**¡Happy Coding!** 🚗⚡