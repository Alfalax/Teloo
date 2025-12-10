# Frontend Docker Implementation - TeLOO V3

## Resumen

Se implementó exitosamente la containerización de los frontends Admin y Advisor de TeLOO V3 usando Docker con una arquitectura multi-stage lista para producción.

## Problema Resuelto

Los frontends estaban corriendo con Vite development server directamente en el host. Se requería containerizarlos para:
- Consistencia entre entornos de desarrollo
- Facilitar el despliegue
- Aislar dependencias
- Preparar para producción

## Solución Implementada

### 1. Dockerfiles Multi-Stage

Se crearon Dockerfiles profesionales con 4 stages:
- **deps**: Instalación de dependencias de producción
- **builder**: Construcción de assets (preparado para producción)
- **development**: Entorno de desarrollo con Vite
- **production**: Entorno de producción optimizado

**Características clave:**
- Imagen base: `node:18-slim` (Debian) en lugar de Alpine para compatibilidad con Rollup
- Instalación explícita de `@rollup/rollup-linux-x64-gnu` para resolver problemas de dependencias opcionales
- Usuario no-root (nextjs:nodejs) para seguridad
- Health checks configurados
- Separación clara entre desarrollo y producción

### 2. Configuración Docker Compose

**docker-compose.yml:**
- Servicios frontend configurados con target `development`
- Variables de entorno para configuración de Vite
- Health checks con start_period de 40s
- Dependencias correctas (core-api)
- Sin volúmenes montados para evitar conflictos con node_modules

**docker-compose.override.yml:**
- Configuración de desarrollo simplificada
- Solo variables de entorno de debug
- **Importante:** No monta volúmenes para evitar sobrescribir node_modules

### 3. Problema Principal Resuelto

**Issue:** Rollup no encontraba el módulo `@rollup/rollup-linux-x64-gnu`

**Causa raíz:**
1. Alpine Linux usa musl en lugar de glibc
2. `npm ci` no instalaba correctamente las dependencias opcionales
3. `docker-compose.override.yml` montaba todo el directorio `/app`, sobrescribiendo node_modules

**Solución:**
1. Cambio de `node:18-alpine` a `node:18-slim` (Debian)
2. Instalación explícita: `RUN npm install --no-save @rollup/rollup-linux-x64-gnu`
3. Eliminación de volúmenes que sobrescribían node_modules

## Arquitectura Final

```
TeLOO V3 Docker Stack
├── Infrastructure
│   ├── postgres:15-alpine (Puerto 5432)
│   ├── redis:7-alpine (Puerto 6379)
│   └── minio:latest (Puertos 9000, 9001)
├── Backend Services
│   ├── core-api (Puerto 8000)
│   ├── agent-ia (Puerto 8001)
│   ├── analytics (Puerto 8002)
│   ├── realtime-gateway (Puerto 8003)
│   └── files (Puerto 8004)
└── Frontend Services
    ├── admin-frontend (Puerto 3000) ✓ NUEVO
    └── advisor-frontend (Puerto 3001) ✓ NUEVO
```

## Archivos Modificados

1. **frontend/admin/Dockerfile** - Dockerfile multi-stage con solución Rollup
2. **frontend/advisor/Dockerfile** - Dockerfile multi-stage con solución Rollup
3. **docker-compose.yml** - Configuración de servicios frontend
4. **docker-compose.override.yml** - Eliminación de volúmenes problemáticos

## Comandos de Uso

### Construir imágenes:
```bash
docker-compose build admin-frontend advisor-frontend
```

### Iniciar servicios:
```bash
docker-compose up -d admin-frontend advisor-frontend
```

### Ver logs:
```bash
docker logs teloo-admin-frontend
docker logs teloo-advisor-frontend
```

### Verificar estado:
```bash
docker ps --filter "name=frontend"
```

### Acceder a las aplicaciones:
- Admin Frontend: http://localhost:3000
- Advisor Frontend: http://localhost:3001

## Estado Actual

✅ **Todos los servicios corriendo y saludables:**
- teloo-admin-frontend: Up (healthy) - Puerto 3000
- teloo-advisor-frontend: Up (healthy) - Puerto 3001
- Vite development server funcionando correctamente en ambos
- Health checks pasando

## Consideraciones para Producción

### Para desplegar en producción:

1. **Descomentar la línea de build en Dockerfiles:**
   ```dockerfile
   # RUN npm run build
   ```

2. **Cambiar target en docker-compose:**
   ```yaml
   build:
     target: production
   ```

3. **Configurar variables de entorno de producción:**
   ```yaml
   environment:
     - VITE_API_URL=https://api.teloo.com
     - VITE_REALTIME_URL=https://realtime.teloo.com
     - VITE_ENVIRONMENT=production
     - NODE_ENV=production
   ```

4. **Usar servidor web para servir assets estáticos** (nginx recomendado)

## Hot Reload en Desarrollo

**Nota importante:** Los contenedores NO tienen hot reload actualmente porque no se montan volúmenes del código fuente. Esto es intencional para evitar problemas con node_modules.

**Opciones para habilitar hot reload:**

1. **Opción A - Montar solo src (Recomendado):**
   ```yaml
   volumes:
     - ./frontend/admin/src:/app/src:ro
   ```

2. **Opción B - Desarrollo local:**
   Continuar usando `npm run dev` localmente para desarrollo activo
   Usar Docker solo para testing de integración

## Lecciones Aprendidas

1. **Alpine vs Debian:** Alpine puede causar problemas con binarios nativos de Node.js
2. **Dependencias opcionales:** npm ci no siempre instala correctamente dependencias opcionales
3. **Docker Compose Override:** Puede sobrescribir configuraciones de forma inesperada
4. **Volúmenes y node_modules:** Montar directorios completos puede sobrescribir node_modules del contenedor

## Próximos Pasos Sugeridos

1. Configurar nginx como reverse proxy para producción
2. Implementar CI/CD para builds automáticos
3. Configurar volúmenes para hot reload si es necesario
4. Optimizar tamaño de imágenes (multi-stage build ya implementado)
5. Configurar secrets management para variables sensibles

## Soporte

Para problemas o preguntas sobre esta implementación, revisar:
- Logs de contenedores: `docker logs <container-name>`
- Estado de servicios: `docker ps -a`
- Configuración: `docker-compose.yml` y `docker-compose.override.yml`
