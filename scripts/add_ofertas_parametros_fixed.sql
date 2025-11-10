-- Agregar parámetros configurables para ofertas
-- Estos parámetros controlan los rangos de validación en los formularios de ofertas

-- Precio mínimo de oferta
INSERT INTO parametros_config (
    categoria, nombre, clave, valor, tipo_dato, descripcion, metadata_json, activo
) VALUES (
    'PARAMETROS_GENERALES',
    'Precio Mínimo Oferta',
    'precio_minimo_oferta',
    1000,
    'INTEGER',
    'Precio mínimo permitido para una oferta de repuesto (en COP)',
    '{"min": 100, "max": 10000000, "step": 100, "unit": "COP", "help_text": "Valor mínimo que puede tener el precio de un repuesto en una oferta"}',
    true
) ON CONFLICT (clave) DO UPDATE SET
    metadata_json = EXCLUDED.metadata_json,
    descripcion = EXCLUDED.descripcion;

-- Precio máximo de oferta
INSERT INTO parametros_config (
    categoria, nombre, clave, valor, tipo_dato, descripcion, metadata_json, activo
) VALUES (
    'PARAMETROS_GENERALES',
    'Precio Máximo Oferta',
    'precio_maximo_oferta',
    50000000,
    'INTEGER',
    'Precio máximo permitido para una oferta de repuesto (en COP)',
    '{"min": 1000000, "max": 100000000, "step": 1000000, "unit": "COP", "help_text": "Valor máximo que puede tener el precio de un repuesto en una oferta"}',
    true
) ON CONFLICT (clave) DO UPDATE SET
    metadata_json = EXCLUDED.metadata_json,
    descripcion = EXCLUDED.descripcion;

-- Garantía mínima
INSERT INTO parametros_config (
    categoria, nombre, clave, valor, tipo_dato, descripcion, metadata_json, activo
) VALUES (
    'PARAMETROS_GENERALES',
    'Garantía Mínima',
    'garantia_minima_meses',
    1,
    'INTEGER',
    'Garantía mínima permitida para un repuesto (en meses)',
    '{"min": 1, "max": 12, "step": 1, "unit": "meses", "help_text": "Cantidad mínima de meses de garantía que debe ofrecer un asesor"}',
    true
) ON CONFLICT (clave) DO UPDATE SET
    metadata_json = EXCLUDED.metadata_json,
    descripcion = EXCLUDED.descripcion;

-- Garantía máxima
INSERT INTO parametros_config (
    categoria, nombre, clave, valor, tipo_dato, descripcion, metadata_json, activo
) VALUES (
    'PARAMETROS_GENERALES',
    'Garantía Máxima',
    'garantia_maxima_meses',
    60,
    'INTEGER',
    'Garantía máxima permitida para un repuesto (en meses)',
    '{"min": 12, "max": 120, "step": 6, "unit": "meses", "help_text": "Cantidad máxima de meses de garantía que puede ofrecer un asesor"}',
    true
) ON CONFLICT (clave) DO UPDATE SET
    metadata_json = EXCLUDED.metadata_json,
    descripcion = EXCLUDED.descripcion;

-- Tiempo de entrega mínimo
INSERT INTO parametros_config (
    categoria, nombre, clave, valor, tipo_dato, descripcion, metadata_json, activo
) VALUES (
    'PARAMETROS_GENERALES',
    'Tiempo Entrega Mínimo',
    'tiempo_entrega_minimo_dias',
    0,
    'INTEGER',
    'Tiempo mínimo de entrega permitido (en días)',
    '{"min": 0, "max": 30, "step": 1, "unit": "días", "help_text": "Cantidad mínima de días para entregar un repuesto"}',
    true
) ON CONFLICT (clave) DO UPDATE SET
    metadata_json = EXCLUDED.metadata_json,
    descripcion = EXCLUDED.descripcion;

-- Tiempo de entrega máximo
INSERT INTO parametros_config (
    categoria, nombre, clave, valor, tipo_dato, descripcion, metadata_json, activo
) VALUES (
    'PARAMETROS_GENERALES',
    'Tiempo Entrega Máximo',
    'tiempo_entrega_maximo_dias',
    90,
    'INTEGER',
    'Tiempo máximo de entrega permitido (en días)',
    '{"min": 30, "max": 180, "step": 5, "unit": "días", "help_text": "Cantidad máxima de días para entregar un repuesto"}',
    true
) ON CONFLICT (clave) DO UPDATE SET
    metadata_json = EXCLUDED.metadata_json,
    descripcion = EXCLUDED.descripcion;

-- Verificar que se insertaron correctamente
SELECT 
    clave, 
    nombre, 
    valor, 
    metadata_json->>'min' as min_value,
    metadata_json->>'max' as max_value,
    metadata_json->>'unit' as unit
FROM parametros_config
WHERE clave IN (
    'precio_minimo_oferta',
    'precio_maximo_oferta',
    'garantia_minima_meses',
    'garantia_maxima_meses',
    'tiempo_entrega_minimo_dias',
    'tiempo_entrega_maximo_dias'
)
ORDER BY clave;
