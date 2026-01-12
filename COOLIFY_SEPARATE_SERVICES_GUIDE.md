# Guía de Despliegue en Coolify (Servicios Separados)

Esta guía detalla la configuración necesaria para desplegar cada componente de la aplicación `Teloo` como un servicio individual en Coolify.

## 1. Servicios de Infraestructura (Base de Datos y Almacenamiento)
Despliega estos primero para obtener sus nombres de host o IPs internas.

### Redis
*   **Imagen**: `redis:7-alpine`
*   **Puerto Interno**: `6379`
*   **Command**: `redis-server --appendonly yes`
*   **Healthcheck**: `redis-cli ping`

### MinIO (Object Storage)
*   **Imagen**: `minio/minio:latest`
*   **Puertos**: `9000` (API), `9001` (Consola)
*   **Environment Variables**:
    *   `MINIO_ROOT_USER`: (Tu usuario, e.g., `admin`)
    *   `MINIO_ROOT_PASSWORD`: (Tu contraseña segura)
*   **Command**: `server /data --console-address ":9001"`

---

## 2. Servicios Backend (API)
Para cada servicio, usa el repositorio de Git. En "Configuration" -> "General":

### Common Configuration
*   **Build Pack**: Dockerfile

### A. Core API (`core-api`)
*   **Base Directory**: `/services/core-api`
*   **Dockerfile Location**: `/services/core-api/Dockerfile`
*   **Port Exposes**: `9002`
*   **Environment Variables**:
    *   `DATABASE_URL`: `postgres://user:pass@host:5432/db_name` (Usa los datos de tu Postgres)
    *   `REDIS_URL`: `redis://:password@host:6379`
    *   `MINIO_ENDPOINT`: `minio:9000`
    *   `MINIO_ACCESS_KEY`: ...
    *   `MINIO_SECRET_KEY`: ...
    *   `JWT_SECRET_KEY`: ...
    *   `ENVIRONMENT`: `production`

### B. Agent IA (`agent-ia`)
*   **Base Directory**: `/services/agent-ia`
*   **Dockerfile Location**: `/services/agent-ia/Dockerfile`
*   **Port Exposes**: `9003`
*   **Environment Variables**:
    *   `CORE_API_URL`: `http://core-api:9002` (Atención al puerto 9002)
    *   `REDIS_URL`: `redis://:password@host:6379`

### C. Analytics (`analytics`)
*   **Base Directory**: `/services/analytics`
*   **Dockerfile Location**: `/services/analytics/Dockerfile`
*   **Port Exposes**: `9004`
*   **Environment Variables**:
    *   `DATABASE_URL`: ...
    *   `REDIS_URL`: ...

### D. Realtime Gateway (`realtime-gateway`)
*   **Base Directory**: `/services/realtime-gateway`
*   **Dockerfile Location**: `/services/realtime-gateway/Dockerfile`
*   **Port Exposes**: `9005`
*   **Environment Variables**:
    *   `REDIS_URL`: ...
    *   `JWT_SECRET_KEY`: ...

### E. Files Service (`files`)
*   **Base Directory**: `/services/files`
*   **Dockerfile Location**: `/services/files/Dockerfile`
*   **Port Exposes**: `9006`
*   **Environment Variables**:
    *   `MINIO_ENDPOINT`: `minio:9000`
    *   `MINIO_ACCESS_KEY`: ...
    *   `MINIO_SECRET_KEY`: ...
    *   `REDIS_URL`: ...

---

## 3. Frontends
Estos servicios consumen la API.

### A. Admin Frontend (`frontend/admin`)
*   **Base Directory**: `/frontend/admin`
*   **Dockerfile Location**: `/frontend/admin/Dockerfile`
*   **Target Stage**: `production` (IMPORTANTE: asegúrate de especificar el target `production` si Coolify lo permite, o asegúrate de que el Dockerfile construya la imagen final nginx por defecto, lo cual `admin` hace ya que es la última etapa).
*   **Port Exposes**: `80`
*   **Environment Variables**:
    *   `VITE_API_URL`: `https://api.tudominio.com` (URL Pública donde desplegaste el Core API o Gateway)

### B. Advisor Frontend (`frontend/advisor`)
*   **Base Directory**: `/frontend/advisor`
*   **Dockerfile Location**: `/frontend/advisor/Dockerfile`
*   **Port Exposes**: `3001`
*   **Environment Variables**:
    *   `VITE_API_URL`: `https://api.tudominio.com`
