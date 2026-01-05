# 🔧 Fix: Base Directory en Coolify

## ❌ Problema Actual
```
Base Directory: /
Dockerfile Location: /frontend/admin/Dockerfile
```

Coolify está buscando `package.json` en la raíz del repo, pero está en `frontend/admin/`.

## ✅ Solución

### Cambiar Base Directory

En la sección **Build** de tu aplicación en Coolify:

1. **Base Directory**: Cambia de `/` a `frontend/admin`
2. **Dockerfile Location**: Cambia de `/frontend/admin/Dockerfile` a `Dockerfile`

### Configuración Correcta Final

```
Base Directory: frontend/admin
Dockerfile Location: Dockerfile
Docker Build Stage Target: production
```

## 🎯 Por Qué Funciona

- **Base Directory** le dice a Coolify: "trabaja desde este subdirectorio"
- **Dockerfile Location** es relativo al Base Directory
- Entonces buscará: `frontend/admin/Dockerfile` ✅
- Y encontrará: `frontend/admin/package.json` ✅

## 📋 Pasos

1. En Coolify, sección **Build**
2. Campo **Base Directory**: escribe `frontend/admin`
3. Campo **Dockerfile Location**: escribe `Dockerfile` (sin la ruta completa)
4. Click **Save**
5. Click **Deploy**

## ⏰ Después del Deploy

El build debería tomar 3-5 minutos y verás:
```
✓ Cloning repository
✓ Building from frontend/admin/Dockerfile
✓ npm ci
✓ npm run build:prod
✓ Container started on port 7000
```
