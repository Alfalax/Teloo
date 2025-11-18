-- Agregar parámetro cobertura_minima_pct faltante
INSERT INTO parametros_config (
    clave,
    categoria,
    valor_json,
    descripcion,
    created_at,
    updated_at
) VALUES (
    'cobertura_minima_pct',
    'parametros_generales',
    '70',
    'Porcentaje mínimo de cobertura requerido para adjudicación',
    NOW(),
    NOW()
) ON CONFLICT (clave) DO NOTHING;
