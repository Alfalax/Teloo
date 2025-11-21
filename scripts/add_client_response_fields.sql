-- Migration: Add client response tracking fields to solicitudes table
-- Date: 2025-11-20
-- Description: Adds fields for tracking client notifications and responses to winning offers

-- Add notification and response timestamps
ALTER TABLE solicitudes 
ADD COLUMN IF NOT EXISTS fecha_notificacion_cliente TIMESTAMP NULL;

ALTER TABLE solicitudes 
ADD COLUMN IF NOT EXISTS fecha_respuesta_cliente TIMESTAMP NULL;

-- Add client acceptance tracking
ALTER TABLE solicitudes 
ADD COLUMN IF NOT EXISTS cliente_acepto BOOLEAN NULL;

ALTER TABLE solicitudes 
ADD COLUMN IF NOT EXISTS respuesta_cliente_texto TEXT NULL;

-- Add comments for documentation
COMMENT ON COLUMN solicitudes.fecha_notificacion_cliente IS 'Timestamp when client was notified about winning offers';
COMMENT ON COLUMN solicitudes.fecha_respuesta_cliente IS 'Timestamp when client responded to offers';
COMMENT ON COLUMN solicitudes.cliente_acepto IS 'Whether client accepted offers (true=accepted, false=rejected, null=no response)';
COMMENT ON COLUMN solicitudes.respuesta_cliente_texto IS 'Original text of client response';

-- Create index for querying pending responses
CREATE INDEX IF NOT EXISTS idx_solicitudes_pending_response 
ON solicitudes(estado, fecha_notificacion_cliente, fecha_respuesta_cliente)
WHERE fecha_notificacion_cliente IS NOT NULL AND fecha_respuesta_cliente IS NULL;

-- Add timeout configuration parameter if not exists
INSERT INTO parametros_configuracion (clave, valor, descripcion, tipo_dato, categoria, created_at, updated_at)
VALUES (
    'timeout_respuesta_cliente_horas',
    '24',
    'Horas que tiene el cliente para responder a las ofertas ganadoras antes de que expiren',
    'integer',
    'parametros_generales',
    NOW(),
    NOW()
)
ON CONFLICT (clave) DO NOTHING;

-- Verification query
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'solicitudes'
AND column_name IN (
    'fecha_notificacion_cliente',
    'fecha_respuesta_cliente',
    'cliente_acepto',
    'respuesta_cliente_texto'
)
ORDER BY column_name;
