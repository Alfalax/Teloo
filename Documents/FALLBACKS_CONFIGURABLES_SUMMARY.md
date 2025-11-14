# ✅ Fallbacks Configurables Implementados

## 🎯 Objetivo Completado

Implementar fallbacks configurables desde BD para asesores sin historial, con valor por defecto 3.0 (neutral en escala 1-5).

## 📊 Métricas con Fallbacks

### 1. **Actividad Reciente** (25%)
- **Parámetro BD**: `fallback_actividad_asesores_nuevos`
- **Valor por defecto**: 3.0
- **Escala**: 1.0 - 5.0
- **Cuándo se usa**: Cuando el asesor no tiene historial de respuestas a ofertas

### 2. **Desempeño Histórico** (20%)
- **Parámetro BD**: `fallback_desempeno_asesores_nuevos`
- **Valor por defecto**: 3.0
- **Escala**: 1.0 - 5.0
- **Cuándo se usa**: Cuando el asesor no tiene historial de ofertas ganadoras

### 3. **Proximidad** (40%)
- ❌ NO necesita fallback
- Siempre se calcula basado en ubicación geográfica

### 4. **Confianza** (15%)
- ❌ NO necesita fallback
- Usa el campo `confianza` del asesor (default: 3.0)

## 🔧 Implementación

### 1. Script SQL
**Archivo**: `scripts/add_puntaje_defecto_param.sql`

```sql
INSERT INTO parametros_config (clave, valor_json, descripcion, categoria)
VALUES (
  'fallback_actividad_asesores_nuevos',
  '3.0'::jsonb,
  'Puntaje por defecto (escala 1.0-5.0) para actividad de asesores sin historial',
  'escalamiento'
) ON CONFLICT (clave) DO NOTHING;

INSERT INTO parametros_config (clave, valor_json, descripcion, categoria)
VALUES (
  'fallback_desempeno_asesores_nuevos',
  '3.0'::jsonb,
  'Puntaje por defecto (escala 1.0-5.0) para desempeño de asesores sin historial',
  'escalamiento'
) ON CONFLICT (clave) DO NOTHING;
```

### 2. Función Actualizada
**Archivo**: `services/core-api/services/escalamiento_service.py`

**Función**: `aplicar_fallbacks_metricas()`

```python
@staticmethod
async def aplicar_fallbacks_metricas(asesor_id: str) -> Dict[str, Decimal]:
    """
    Aplica valores fallback para métricas faltantes
    Lee valores configurables desde BD, con fallback a 3.0 si no existen
    """
    from models.analytics import ParametroConfig
    
    # Obtener valores configurables desde BD
    try:
        fallback_actividad = await ParametroConfig.get_valor(
            'fallback_actividad_asesores_nuevos',
            default=3.0
        )
        fallback_desempeno = await ParametroConfig.get_valor(
            'fallback_desempeno_asesores_nuevos',
            default=3.0
        )
    except Exception as e:
        logger.warning(f"Error obteniendo fallbacks: {e}. Usando 3.0")
        fallback_actividad = 3.0
        fallback_desempeno = 3.0
    
    fallbacks = {
        'actividad_reciente': Decimal(str(fallback_actividad)),
        'desempeno_historico': Decimal(str(fallback_desempeno)),
        'nivel_confianza': Decimal('3.0')
    }
    
    return fallbacks
```

### 3. Integración Automática
**Archivo**: `services/core-api/services/solicitudes_service.py`

Al crear una solicitud, se ejecuta automáticamente el escalamiento:

```python
# Ejecutar escalamiento automáticamente si la solicitud está abierta
if solicitud.estado == EstadoSolicitud.ABIERTA:
    try:
        from services.escalamiento_service import EscalamientoService
        escalamiento_service = EscalamientoService()
        await escalamiento_service.ejecutar_escalamiento(solicitud.id)
        logger.info(f"Escalamiento automático ejecutado para solicitud {solicitud.id}")
    except Exception as e:
        logger.error(f"Error en escalamiento automático: {e}")
```

## ✅ Verificación

### Parámetros en BD:
```sql
SELECT clave, valor_json FROM parametros_config WHERE clave LIKE 'fallback%';
```

**Resultado**:
```
               clave                | valor_json 
------------------------------------+------------
 fallback_actividad_asesores_nuevos | 3.0
 fallback_desempeno_asesores_nuevos | 3.0
```

## 🎉 Beneficios

1. **Configurabilidad**: Admin puede ajustar los valores desde BD sin cambiar código
2. **Valor neutral por defecto**: 3.0 no penaliza ni favorece a asesores nuevos
3. **Fallback robusto**: Si falla la lectura de BD, usa 3.0 hardcodeado
4. **Escalable**: A medida que acumulan historial, los valores reales reemplazan los fallbacks

## 📈 Ejemplo de Cálculo

### Asesor Nuevo (sin historial):
- **Proximidad**: 100 (misma ciudad) → 40% = 40 puntos
- **Actividad**: 3.0 (fallback) → 25% = 0.75 puntos
- **Desempeño**: 3.0 (fallback) → 20% = 0.6 puntos
- **Confianza**: 3.0 (campo) → 15% = 0.45 puntos
- **Total**: 41.8 puntos → Nivel 3-4

### Asesor Experimentado (con historial):
- **Proximidad**: 100 (misma ciudad) → 40% = 40 puntos
- **Actividad**: 4.5 (histórico) → 25% = 1.125 puntos
- **Desempeño**: 4.8 (histórico) → 20% = 0.96 puntos
- **Confianza**: 4.0 (campo) → 15% = 0.6 puntos
- **Total**: 42.685 puntos → Nivel 1-2

## 🚀 Próximos Pasos

1. ✅ Fallbacks configurables implementados
2. ✅ Integración automática en create_solicitud
3. ⏳ Probar flujo completo creando una solicitud
4. ⏳ Verificar que asesores reciben notificaciones según su nivel

## 🔧 Cómo Cambiar los Valores

Desde psql o cualquier cliente SQL:

```sql
-- Cambiar fallback de actividad a 3.5
UPDATE parametros_config 
SET valor_json = '3.5'::jsonb 
WHERE clave = 'fallback_actividad_asesores_nuevos';

-- Cambiar fallback de desempeño a 2.5
UPDATE parametros_config 
SET valor_json = '2.5'::jsonb 
WHERE clave = 'fallback_desempeno_asesores_nuevos';
```

Los cambios se aplican inmediatamente en el próximo escalamiento.
