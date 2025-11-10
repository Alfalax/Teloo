-- Migration: Add metadata_json column to parametros_config table
-- Date: 2025-11-09
-- Description: Allows storing validation metadata (min, max, default, unit) for each parameter

-- Add metadata_json column
ALTER TABLE parametros_config 
ADD COLUMN IF NOT EXISTS metadata_json JSONB DEFAULT '{}';

-- Add comment to column
COMMENT ON COLUMN parametros_config.metadata_json IS 'Validation metadata including min, max, default values and unit';

-- Initialize metadata for existing parameters
UPDATE parametros_config 
SET metadata_json = '{
    "min": 1,
    "max": 10,
    "default": 2,
    "unit": "ofertas",
    "description": "Número mínimo de ofertas antes de cierre anticipado"
}'
WHERE clave = 'ofertas_minimas_deseadas';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1,
    "max": 30,
    "default": 5,
    "unit": "segundos",
    "description": "Tiempo máximo para completar evaluación"
}'
WHERE clave = 'timeout_evaluacion_segundos';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1,
    "max": 365,
    "default": 30,
    "unit": "días",
    "description": "Días de vigencia de auditorías de confianza"
}'
WHERE clave = 'vigencia_auditoria_dias';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1,
    "max": 90,
    "default": 30,
    "unit": "días",
    "description": "Días para calcular actividad reciente"
}'
WHERE clave = 'periodo_actividad_reciente_dias';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1,
    "max": 24,
    "default": 6,
    "unit": "meses",
    "description": "Meses para calcular desempeño histórico"
}'
WHERE clave = 'periodo_desempeno_historico_meses';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1.0,
    "max": 5.0,
    "default": 2.0,
    "unit": "puntos",
    "description": "Nivel mínimo de confianza requerido"
}'
WHERE clave = 'confianza_minima_operar';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 0,
    "max": 100,
    "default": 50,
    "unit": "%",
    "description": "Porcentaje mínimo de cobertura de repuestos"
}'
WHERE clave = 'cobertura_minima_porcentaje';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1,
    "max": 168,
    "default": 20,
    "unit": "horas",
    "description": "Horas antes de marcar ofertas como expiradas"
}'
WHERE clave = 'timeout_ofertas_horas';

UPDATE parametros_config 
SET metadata_json = '{
    "min": 1,
    "max": 12,
    "default": 2,
    "unit": "horas",
    "description": "Horas antes de expiración para notificar"
}'
WHERE clave = 'notificacion_expiracion_horas_antes';

-- Initialize metadata for configuration categories
UPDATE parametros_config 
SET metadata_json = '{
    "description": "Pesos del algoritmo de escalamiento de asesores"
}'
WHERE clave = 'pesos_escalamiento';

UPDATE parametros_config 
SET metadata_json = '{
    "description": "Umbrales para clasificación por niveles"
}'
WHERE clave = 'umbrales_niveles';

UPDATE parametros_config 
SET metadata_json = '{
    "description": "Tiempos de espera por nivel antes de escalar"
}'
WHERE clave = 'tiempos_espera_minutos';

UPDATE parametros_config 
SET metadata_json = '{
    "description": "Canales de notificación por nivel"
}'
WHERE clave = 'canales_notificacion';

UPDATE parametros_config 
SET metadata_json = '{
    "description": "Pesos para evaluación de ofertas"
}'
WHERE clave = 'pesos_evaluacion';

-- Create index for faster metadata queries
CREATE INDEX IF NOT EXISTS idx_parametros_config_metadata 
ON parametros_config USING GIN (metadata_json);

-- Verification query
SELECT 
    clave,
    valor_json,
    metadata_json,
    updated_at
FROM parametros_config
ORDER BY clave;
