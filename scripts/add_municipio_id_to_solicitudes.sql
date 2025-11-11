-- ============================================================================
-- MIGRACIÓN: Agregar municipio_id a tabla solicitudes
-- Objetivo: Usar códigos DIVIPOLA como fuente única de verdad
-- ============================================================================

-- Paso 1: Agregar columna municipio_id (nullable temporalmente)
ALTER TABLE solicitudes 
ADD COLUMN IF NOT EXISTS municipio_id UUID REFERENCES municipios(id);

-- Paso 2: Crear índice para performance
CREATE INDEX IF NOT EXISTS idx_solicitudes_municipio ON solicitudes(municipio_id);

-- Paso 3: Migrar datos existentes - Mapeo inteligente de ciudades
UPDATE solicitudes s
SET municipio_id = (
    SELECT m.id 
    FROM municipios m
    WHERE m.municipio_norm = UPPER(
        TRIM(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(
                                        REPLACE(s.ciudad_origen, 'á', 'a'),
                                    'é', 'e'),
                                'í', 'i'),
                            'ó', 'o'),
                        'ú', 'u'),
                    'Á', 'A'),
                'É', 'E'),
            'Í', 'I')
        )
    )
    AND m.departamento = UPPER(
        TRIM(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(s.departamento_origen, 'á', 'a'),
                    'é', 'e'),
                'í', 'i'),
            'ó', 'o')
        )
    )
    LIMIT 1
)
WHERE s.municipio_id IS NULL;

-- Mapeo especial para Bogotá
UPDATE solicitudes 
SET municipio_id = (
    SELECT id FROM municipios 
    WHERE municipio_norm = 'BOGOTA, D.C.' 
    LIMIT 1
)
WHERE UPPER(TRIM(ciudad_origen)) IN ('BOGOTÁ', 'BOGOTA', 'BOGOTÁ D.C.', 'BOGOTA D.C.', 'BOGOTÁ, D.C.', 'BOGOTA, D.C.')
    AND municipio_id IS NULL;

-- Paso 4: Verificar cuántas solicitudes NO se pudieron mapear
SELECT 
    'Solicitudes sin mapear' as status,
    COUNT(*) as total,
    STRING_AGG(DISTINCT ciudad_origen || ', ' || departamento_origen, ' | ') as ciudades_problematicas
FROM solicitudes 
WHERE municipio_id IS NULL;

-- Paso 5: Mostrar estadísticas de migración
SELECT 
    CASE 
        WHEN municipio_id IS NOT NULL THEN 'Mapeadas correctamente'
        ELSE 'Sin mapear'
    END as status,
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM solicitudes), 2) as porcentaje
FROM solicitudes
GROUP BY (municipio_id IS NOT NULL)
ORDER BY status;

-- Paso 6: Hacer NOT NULL después de verificar que todas están mapeadas
-- DESCOMENTAR SOLO DESPUÉS DE VERIFICAR QUE TODAS LAS SOLICITUDES ESTÁN MAPEADAS
-- ALTER TABLE solicitudes ALTER COLUMN municipio_id SET NOT NULL;

-- Paso 7: Agregar constraint para asegurar integridad
-- ALTER TABLE solicitudes 
-- ADD CONSTRAINT fk_solicitudes_municipio 
-- FOREIGN KEY (municipio_id) REFERENCES municipios(id) ON DELETE RESTRICT;

COMMENT ON COLUMN solicitudes.municipio_id IS 'FK a municipios - Fuente única de verdad para ubicación geográfica';
COMMENT ON COLUMN solicitudes.ciudad_origen IS 'Campo de texto para display - NO usar para lógica de negocio';
COMMENT ON COLUMN solicitudes.departamento_origen IS 'Campo de texto para display - NO usar para lógica de negocio';
