# Guía de Despliegue en Coolify - TeLOO V8 Backend

## Problema Identificado

El error que estás experimentando ocurre porque Coolify intenta construir **todos los servicios simultáneamente** desde `docker-compose.prod.yml`, lo que consume demasiados recursos y causa que el build falle.

## Solución: Despliegue por Etapas

He creado archivos Docker Compose separados para desplegar los servicios en etapas:

### **Etapa 1: Infraestructura**
Archivo: `docker-compose.infrastructure.yml`
- PostgreSQL
- Redis  
- MinIO

### **Etapa 2: Core API**
Archivo: `docker-compose.core-api.yml`
- Servicio Core API

### **Etapa 3: Servicios Adicionales** (opcional, desplegar después)
- Agent IA
- Analytics
- Realtime Gateway
- Files

## Pasos para Desplegar en Coolify

### **Paso 1: Desplegar Infraestructura**

1. En Coolify, crea un nuevo proyecto/servicio
2. Selecciona "Docker Compose"
3. Apunta al repositorio: `Alfalax/Teloo`
4. Branch: `develop`
5. **Archivo Docker Compose**: `docker-compose.infrastructure.yml`
6. Configura las variables de entorno:
   ```
   POSTGRES_DB=teloo_production
   POSTGRES_USER=tu_usuario
   POSTGRES_PASSWORD=tu_password_seguro
   MINIO_ROOT_USER=tu_minio_user
   MINIO_ROOT_PASSWORD=tu_minio_password
   ```
7. Despliega y espera a que todos los servicios estén "Healthy"

### **Paso 2: Desplegar Core API**

1. Crea otro proyecto/servicio en Coolify
2. Selecciona "Docker Compose"
3. Mismo repositorio y branch
4. **Archivo Docker Compose**: `docker-compose.core-api.yml`
5. Configura las variables de entorno:
   ```
   DATABASE_URL=postgresql://usuario:password@postgres:5432/teloo_production
   REDIS_URL=redis://redis:6379
   MINIO_ENDPOINT=minio:9000
   MINIO_ROOT_USER=tu_minio_user
   MINIO_ROOT_PASSWORD=tu_minio_password
   JWT_SECRET_KEY=tu_jwt_secret_muy_seguro
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
   JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   CORS_ORIGINS=https://tu-dominio.com,https://admin.tu-dominio.com
   ```
6. Despliega

### **Paso 3: Verificar**

Una vez desplegado, verifica que el Core API esté funcionando:

```bash
curl https://tu-core-api-url.com/health
```

Deberías recibir una respuesta exitosa.

## Alternativa: Despliegue con Dockerfile Individual

Si prefieres no usar Docker Compose, puedes desplegar cada servicio usando su Dockerfile individual:

1. En Coolify, selecciona "Dockerfile"
2. Apunta al repositorio
3. **Dockerfile Path**: `services/core-api/Dockerfile`
4. **Build Context**: `services/core-api`
5. Configura las mismas variables de entorno
6. Despliega

## Solución al Error Original

El error que viste ocurría porque:

1. ❌ **Problema**: `docker-compose.prod.yml` intenta construir 5 servicios a la vez
2. ❌ **Resultado**: Consumo excesivo de memoria/CPU → Build falla
3. ✅ **Solución**: Desplegar servicios por separado usando archivos específicos

## Notas Importantes

### Red Docker
Los archivos separados usan una red externa `teloo-network`. Asegúrate de que:
- El `docker-compose.infrastructure.yml` crea la red
- Los demás servicios se conectan a esa red existente

### Orden de Despliegue
**Siempre despliega en este orden:**
1. Infraestructura (PostgreSQL, Redis, MinIO)
2. Core API
3. Otros servicios (Agent IA, Analytics, etc.)

### Variables de Entorno
Asegúrate de configurar **todas** las variables de entorno necesarias en Coolify antes de desplegar.

## Troubleshooting

### Si el build sigue fallando:

1. **Verifica los logs completos** en Coolify
2. **Aumenta los recursos** del servidor (RAM, CPU)
3. **Desactiva el build cache** en Coolify temporalmente
4. **Intenta con Dockerfile individual** en lugar de Docker Compose

### Si los servicios no se conectan:

1. Verifica que todos estén en la misma red Docker
2. Usa nombres de servicio (ej: `postgres`, `redis`) en lugar de IPs
3. Verifica que los puertos internos sean correctos (no los externos)

## Próximos Pasos

Una vez que Core API esté funcionando:

1. Crea el usuario admin usando el script de inicialización
2. Despliega los demás servicios de backend
3. Despliega el frontend (admin y advisor)
4. Configura los dominios y SSL en Coolify

---

**¿Necesitas ayuda?** Si sigues teniendo problemas, comparte:
- Los logs completos del error en Coolify
- Las variables de entorno que configuraste
- El archivo Docker Compose que estás usando
