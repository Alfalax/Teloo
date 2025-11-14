# Git Workflow para TeLOO V3

## Estructura de Ramas

- `main`: Rama principal con código estable
- `develop`: Rama de desarrollo principal
- `feature/frontend`: Para desarrollo del frontend
- `feature/backend`: Para desarrollo del backend
- `feature/testing`: Para mejoras en testing

## Comandos Útiles

### Cambiar de rama
```bash
git checkout develop
git checkout feature/frontend
```

### Crear nueva rama desde develop
```bash
git checkout develop
git checkout -b feature/nueva-funcionalidad
```

### Guardar cambios
```bash
git add .
git commit -m "Descripción del cambio"
```

### Sincronizar ramas
```bash
# Traer cambios de develop a tu rama
git checkout feature/mi-rama
git merge develop

# Llevar cambios de tu rama a develop
git checkout develop
git merge feature/mi-rama
```

### Ver estado y historial
```bash
git status
git log --oneline
git branch -a
```

### Commits recomendados por tipo

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bugs
- `docs:` Documentación
- `style:` Cambios de formato
- `refactor:` Refactorización
- `test:` Agregar o modificar tests
- `chore:` Tareas de mantenimiento

### Ejemplo de commits
```bash
git commit -m "feat: add user authentication service"
git commit -m "fix: resolve WhatsApp webhook timeout issue"
git commit -m "docs: update API documentation"
git commit -m "test: add unit tests for offer evaluation"
```

## Flujo de Trabajo Recomendado

1. Trabajar en ramas feature específicas
2. Hacer commits frecuentes con mensajes descriptivos
3. Mergear a develop cuando la funcionalidad esté completa
4. Mergear a main solo cuando esté listo para producción