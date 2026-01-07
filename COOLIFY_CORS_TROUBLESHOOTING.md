# Troubleshooting CORS en Coolify

## Problema Actual
El error de CORS persiste después de configurar `BACKEND_CORS_ORIGINS`.

## Posibles Causas

### 1. El backend no está leyendo la variable
- La variable puede no estar disponible en el contenedor
- El backend puede no haberse reiniciado correctamente

### 2. Formato JSON incorrecto
- El JSON debe ser válido
- Las comillas deben ser dobles `"`
- No debe haber espacios extra

### 3. El backend está cacheado
- Coolify puede estar usando una imagen vieja

## Verificaciones

### Paso 1: Verificar logs del backend

En Coolify, ve a tu aplicación backend y revisa los logs. Busca líneas que mencionen CORS o que muestren qué origins están configurados.

Deberías ver algo como:
```
INFO: CORS origins: ['http://rcsg4sg84kkso80gcko0gw4o.72.62.130.152.sslip.io']
```

### Paso 2: Verificar que la variable existe

En los logs del backend al iniciar, debería aparecer la configuración de CORS.

### Paso 3: Probar con wildcard (temporal)

Para verificar que el problema es solo de configuración, prueba temporalmente con:

```
BACKEND_CORS_ORIGINS=["*"]
```

**⚠️ ADVERTENCIA**: Esto permite CUALQUIER origen. Solo para testing, NO para producción.

Si esto funciona, confirma que el problema es el formato o valor de la URL.

## Soluciones Alternativas

### Opción A: Usar variable sin JSON

Cambia el código del backend para aceptar una lista separada por comas:

En `services/core-api/main.py`, línea 58-64, cambiar a:

```python
cors_origins_env = os.getenv("BACKEND_CORS_ORIGINS")
if cors_origins_env:
    # Intentar parsear como JSON primero
    try:
        origins = json.loads(cors_origins_env)
    except Exception:
        # Si falla, asumir que es una lista separada por comas
        origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
```

Luego en Coolify usar:
```
BACKEND_CORS_ORIGINS=http://rcsg4sg84kkso80gcko0gw4o.72.62.130.152.sslip.io,http://localhost:3000
```

### Opción B: Hardcodear temporalmente

Para verificar que todo lo demás funciona, hardcodear en el código:

En `services/core-api/main.py`, línea 58-64:

```python
# Temporal - hardcoded para testing
origins = [
    "http://rcsg4sg84kkso80gcko0gw4o.72.62.130.152.sslip.io",
    "http://localhost:3000",
    "http://localhost:3001",
]
```

Commit, push, redeploy.

Si esto funciona, confirma que el problema es cómo Coolify pasa las variables de entorno.

### Opción C: Usar allow_origins=["*"] temporalmente

En `services/core-api/main.py`, línea 76:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporal - permite todo
    allow_credentials=True,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
)
```

**⚠️ Solo para testing - NO dejar en producción**

## Formato Correcto de la Variable

La variable debe ser exactamente así:

```
BACKEND_CORS_ORIGINS=["http://rcsg4sg84kkso80gcko0gw4o.72.62.130.152.sslip.io"]
```

**Importante**:
- Corchetes `[]`
- Comillas dobles `"` (no simples `'`)
- Sin espacios después de las comas
- Sin saltos de línea

## Siguiente Paso

Por favor comparte:
1. Los logs del backend al iniciar (primeras 50 líneas)
2. Una captura de la variable `BACKEND_CORS_ORIGINS` en Coolify
3. Confirma que hiciste Redeploy después de cambiar la variable

Con esa información podré identificar exactamente qué está fallando.
