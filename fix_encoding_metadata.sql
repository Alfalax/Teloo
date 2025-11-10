-- Fix: Corregir codificación UTF-8 en metadata_json
-- Date: 2025-11-09
-- Description: Actualiza las descripciones con caracteres especiales correctos

-- Parámetros individuales con tildes
UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Número mínimo de ofertas antes de cierre anticipado"'::jsonb
)
WHERE clave = 'ofertas_minimas_deseadas';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Tiempo máximo para completar evaluación"'::jsonb
)
WHERE clave = 'timeout_evaluacion_segundos';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Días de vigencia de auditorías de confianza"'::jsonb
)
WHERE clave = 'vigencia_auditoria_dias';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Días para calcular actividad reciente"'::jsonb
)
WHERE clave = 'periodo_actividad_reciente_dias';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Meses para calcular desempeño histórico"'::jsonb
)
WHERE clave = 'periodo_desempeno_historico_meses';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Nivel mínimo de confianza requerido"'::jsonb
)
WHERE clave = 'confianza_minima_operar';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Porcentaje mínimo de cobertura de repuestos"'::jsonb
)
WHERE clave = 'cobertura_minima_porcentaje';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Horas antes de marcar ofertas como expiradas"'::jsonb
)
WHERE clave = 'timeout_ofertas_horas';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Horas antes de expiración para notificar"'::jsonb
)
WHERE clave = 'notificacion_expiracion_horas_antes';

-- Categorías de configuración
UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Pesos del algoritmo de escalamiento de asesores"'::jsonb
)
WHERE clave = 'pesos_escalamiento';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Umbrales para clasificación por niveles"'::jsonb
)
WHERE clave = 'umbrales_niveles';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Tiempos de espera por nivel antes de escalar"'::jsonb
)
WHERE clave = 'tiempos_espera_minutos';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Canales de notificación por nivel"'::jsonb
)
WHERE clave = 'canales_notificacion';

UPDATE parametros_config 
SET metadata_json = jsonb_set(
    metadata_json,
    '{description}',
    '"Pesos para evaluación de ofertas"'::jsonb
)
WHERE clave = 'pesos_evaluacion';

-- Verificación
SELECT 
    clave,
    metadata_json->>'description' as descripcion
FROM parametros_config
WHERE metadata_json ? 'description'
ORDER BY clave;
