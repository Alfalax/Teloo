# Guía de Deployment con Coolify - Puertos 7000-7008

## 📋 Configuración de Puertos

Esta aplicación usa los puertos 7000-7008 para todos los servicios:

| Servicio | Puerto | URL de Acceso |
|----------|--------|---------------|
| **Frontend Admin** | 7000 | `http://YOUR_IP:7000` |
| **Frontend Advisor** | 7001 | `http://YOUR_IP:7001` |
| **API Backend (core-api)** | 7002 | `http://YOUR_IP:7002` |
| **Agent IA** | 7003 | `http://YOUR_IP:7003` |
| **Analytics** | 7004 | `http://YOUR_IP:7004` |
| **Realtime Gateway** | 7005 | `http://YOUR_IP:7005` |
| **Files Service** | 7006 | `http://YOUR_IP:7006` |
| **MinIO Console** | 7007 | `http://YOUR_IP:7007` |

---

## 🚀 Pasos de Deployment

### 1. Instalar Coolify en VPS
```bash
ssh root@YOUR_IP
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

### 2. Acceder a Coolify
- URL: `http://YOUR_IP:8000`
- Crear cuenta admin

### 3. Agregar Repositorio Público
- **Sources** → **Public Repository**
- URL: `https://github.com/Alfalax/Teloo`
- Branch: `develop`

### 4. Crear Proyecto
- **Projects** → **New Project**: `teloo-production`
- **New Resource** → **Docker Compose**
- Docker Compose File: `docker-compose.prod.yml`

### 5. Variables de Entorno

```env
# Base de datos
POSTGRES_USER=teloo_admin
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD
POSTGRES_DB=teloo_production
DATABASE_URL=postgresql://teloo_admin:YOUR_SECURE_PASSWORD@postgres:5432/teloo_production

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=YOUR_MINIO_PASSWORD
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET=teloo-files
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=YOUR_MINIO_PASSWORD

# JWT
JWT_SECRET_KEY=YOUR_SECRET_KEY_MINIMUM_32_CHARACTERS
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS y URLs (Reemplazar YOUR_IP)
CORS_ORIGINS=http://YOUR_IP:7000,http://YOUR_IP:7001,http://YOUR_IP:7002
FRONTEND_ADMIN_URL=http://YOUR_IP:7000
FRONTEND_ADVISOR_URL=http://YOUR_IP:7001
API_URL=http://YOUR_IP:7002

# APIs Externas (Opcional)
WHATSAPP_TOKEN=your_token
TELEGRAM_BOT_TOKEN=your_token
OPENAI_API_KEY=your_key
GEMINI_API_KEY=your_key

# Configuración
ENVIRONMENT=production
LOG_LEVEL=INFO
WORKERS=4
```

### 6. Configurar Puertos en Coolify

En la pestaña **"Domains"** agregar:
- Puerto 7000 (Admin Frontend)
- Puerto 7001 (Advisor Frontend)
- Puerto 7002 (API Backend)
- Puerto 7003 (Agent IA) - Opcional
- Puerto 7004 (Analytics) - Opcional
- Puerto 7005 (Realtime Gateway) - Opcional
- Puerto 7006 (Files Service) - Opcional
- Puerto 7007 (MinIO Console) - Opcional

### 7. Abrir Puertos en Firewall

```bash
# En el VPS
sudo ufw allow 7000:7008/tcp
sudo ufw reload
```

O desde el panel de Hostinger: Firewall → Agregar regla para puertos 7000-7008 TCP

### 8. Deploy

Click en **"Deploy"** y esperar 10-15 minutos.

### 9. Inicializar Base de Datos

En Coolify, terminal del servicio `core-api`:
```bash
python init_data.py
```

### 10. Verificar

- Health Check: `http://YOUR_IP:7002/health`
- Admin: `http://YOUR_IP:7000`
- Advisor: `http://YOUR_IP:7001`
- API Docs: `http://YOUR_IP:7002/docs`

---

## 🔐 Credenciales Iniciales

**Admin Panel:**
- Email: `admin@teloo.com`
- Password: `admin123`

**MinIO Console:**
- Usuario: `minioadmin`
- Password: (el que configuraste en MINIO_ROOT_PASSWORD)

⚠️ **IMPORTANTE:** Cambiar todas las contraseñas después del primer login.

---

## 🔄 Actualizaciones

Para actualizar la aplicación:
1. Hacer push de cambios a GitHub
2. En Coolify: **Deployments** → **Deploy**

---

## 📞 Soporte

Para problemas de deployment, revisar:
- Logs en Coolify: **Services** → Click en servicio → **Logs**
- Health checks de cada servicio
- Firewall y puertos abiertos
