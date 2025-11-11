-- Agregar parámetros para fallbacks de asesores nuevos
-- Escala 1.0 - 5.0 (neutral = 3.0)

INSERT INTO parametros_config (clave, valor_json, descripcion, categoria, metadata_json)
VALUES (
  'fallback_actividad_asesores_nuevos',
  '3.0'::jsonb,
  'Puntaje por defecto (escala 1.0-5.0) para actividad de asesores sin historial',
  'parametros_generales',
  '{
    "min": 1.0,
    "max": 5.0,
    "default": 3.0,
    "unit": "puntos",
    "description": "Puntaje de actividad para asesores sin historial de respuestas"
  }'::jsonb
) ON CONFLICT (clave) DO UPDATE SET
  metadata_json = EXCLUDED.metadata_json,
  categoria = EXCLUDED.categoria;

INSERT INTO parametros_config (clave, valor_json, descripcion, categoria, metadata_json)
VALUES (
  'fallback_desempeno_asesores_nuevos',
  '3.0'::jsonb,
  'Puntaje por defecto (escala 1.0-5.0) para desempeño de asesores sin historial',
  'parametros_generales',
  '{
    "min": 1.0,
    "max": 5.0,
    "default": 3.0,
    "unit": "puntos",
    "description": "Puntaje de desempeño para asesores sin historial de ofertas"
  }'::jsonb
) ON CONFLICT (clave) DO UPDATE SET
  metadata_json = EXCLUDED.metadata_json,
  categoria = EXCLUDED.categoria;
