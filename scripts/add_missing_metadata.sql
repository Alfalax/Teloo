-- Add missing metadata for parameters that should appear in admin frontend
-- Date: 2025-11-11

UPDATE parametros_config 
SET metadata_json = '{
    "min": 0,
    "max": 100,
    "default": 50,
    "unit": "%",
    "description": "Porcentaje mínimo de cobertura de repuestos requerido"
}'
WHERE clave = 'cobertura_minima_porcentaje';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1.0,
    "max": 5.0,
    "default": 2.0,
    "step": 0.1,
    "unit": "puntos",
    "description": "Nivel mínimo de confianza requerido para operar"
}'
WHERE clave = 'confianza_minima_operar';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1,
    "max": 24,
    "default": 2,
    "unit": "horas",
    "description": "Horas antes de expiración para enviar notificación"
}'
WHERE clave = 'notificacion_expiracion_horas_antes';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 7,
    "max": 90,
    "default": 30,
    "unit": "días",
    "description": "Días para calcular actividad reciente de asesores"
}'
WHERE clave = 'periodo_actividad_reciente_dias';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1,
    "max": 24,
    "default": 6,
    "unit": "meses",
    "description": "Meses para calcular desempeño histórico de asesores"
}'
WHERE clave = 'periodo_desempeno_historico_meses';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 0,
    "max": 100,
    "default": 50,
    "unit": "puntos",
    "description": "Puntaje por defecto para asesores sin historial"
}'
WHERE clave = 'puntaje_defecto_asesores_nuevos';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1,
    "max": 30,
    "default": 5,
    "unit": "segundos",
    "description": "Tiempo máximo para completar evaluación de ofertas"
}'
WHERE clave = 'timeout_evaluacion_segundos';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1,
    "max": 168,
    "default": 20,
    "unit": "horas",
    "description": "Horas antes de marcar ofertas como expiradas"
}'
WHERE clave = 'timeout_ofertas_horas';

-- Verification
SELECT clave, metadata_json 
FROM parametros_config 
WHERE clave IN (
    'cobertura_minima_porcentaje',
    'confianza_minima_operar',
    'notificacion_expiracion_horas_antes',
    'periodo_actividad_reciente_dias',
    'periodo_desempeno_historico_meses',
    'puntaje_defecto_asesores_nuevos',
    'timeout_evaluacion_segundos',
    'timeout_ofertas_horas'
)
ORDER BY clave;
