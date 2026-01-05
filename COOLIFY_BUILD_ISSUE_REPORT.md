# 🐛 Coolify Build Issue Report

## Problema
El build de Docker en Coolify **NO está copiando archivos `.ts`** del repositorio al contenedor, causando que Vite falle durante el build.

## Error
```
Could not load /app/src/lib/utils.ts (imported by src/components/layout/Sidebar.tsx): 
ENOENT: no such file or directory, open '/app/src/lib/utils.ts'
```

## Configuración Actual
- **Repository**: Alfalax/Teloo
- **Branch**: develop
- **Base Directory**: `frontend/admin`
- **Dockerfile Location**: `Dockerfile`
- **Build Target**: `production`

## Archivos Verificados

### 1. El archivo existe en el repositorio
```
frontend/admin/src/lib/utils.ts ✅ EXISTE
```

### 2. .dockerignore es mínimo
```dockerignore
# frontend/admin/.dockerignore
node_modules
dist
build
.git
.env.local
.env.*.local
```

### 3. Dockerfile usa COPY correcto
```dockerfile
COPY . .
```

### 4. Build context muestra 900KB transferidos
```
#7 [internal] load build context
#7 transferring context: 900.06kB 0.0s done
```

## Intentos de Solución

1. ✅ Configurado Base Directory correcto: `frontend/admin`
2. ✅ Creado `.dockerignore` mínimo en `frontend/admin/`
3. ✅ Modificado `.gitignore` para permitir `.dockerignore` en subdirectorios
4. ✅ Agregado extensiones `.ts` explícitas en imports
5. ✅ Verificado que Vite config tiene alias correctos
6. ❌ **El archivo NUNCA se copia al contenedor**

## Evidencia del Problema

El mismo Dockerfile funciona perfectamente en:
- ✅ Docker local
- ✅ GitHub Actions CI/CD
- ❌ **Coolify** (falla consistentemente)

## Hipótesis

Coolify puede estar:
1. Aplicando un `.dockerignore` global que excluye `.ts`
2. Filtrando archivos TypeScript por alguna razón
3. Teniendo un bug en cómo maneja el contexto de build con Base Directory

## Solución Temporal Recomendada

**Usar el stage `development` en lugar de `production`** hasta resolver el issue:

En Coolify:
- Build Target: `development` (en lugar de `production`)
- Esto evita el build de Vite y corre el dev server

## Solicitud de Soporte

¿Puede el equipo de Coolify investigar por qué los archivos `.ts` no se están copiando al contexto de build cuando se usa Base Directory?

---

**Fecha**: 2026-01-05
**Commit**: b208b4465a661fb98015eb9475caba65fd285472
