-- Corregir codificación UTF-8 en los parámetros de ofertas

-- Tiempo de entrega mínimo
UPDATE parametros_config 
SET metadata_json = '{"min": 0, "max": 30, "step": 1, "unit": "dias", "help_text": "Cantidad minima de dias para entregar un repuesto"}'::jsonb
WHERE clave = 'tiempo_entrega_minimo_dias';

-- Tiempo de entrega máximo
UPDATE parametros_config 
SET metadata_json = '{"min": 30, "max": 180, "step": 5, "unit": "dias", "help_text": "Cantidad maxima de dias para entregar un repuesto"}'::jsonb
WHERE clave = 'tiempo_entrega_maximo_dias';

-- Verificar cambios
SELECT 
    clave,
    metadata_json->>'unit' as unit,
    metadata_json->>'help_text' as help_text
FROM parametros_config
WHERE clave IN ('tiempo_entrega_minimo_dias', 'tiempo_entrega_maximo_dias');
