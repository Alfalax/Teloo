-- Script para agregar configuración de branding
-- Ejecutar después de inicializar la base de datos

-- Insertar configuración de branding por defecto
INSERT INTO parametros_config (clave, descripcion, valor_json, categoria, created_at, updated_at)
VALUES (
    'branding',
    'Configuración de personalización de marca (logo, nombre, colores)',
    '{"logo_url": "/logo.png", "nombre_empresa": "TeLOO", "color_primario": "#3b82f6", "color_secundario": "#1e40af"}'::jsonb,
    'sistema',
    NOW(),
    NOW()
)
ON CONFLICT (clave) DO UPDATE SET
    valor_json = EXCLUDED.valor_json,
    updated_at = NOW();

-- Verificar que se insertó correctamente
SELECT clave, descripcion, valor_json, categoria FROM parametros_config WHERE clave = 'branding';
