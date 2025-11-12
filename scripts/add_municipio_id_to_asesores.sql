-- ============================================================================
-- MIGRACIÓN: Agregar municipio_id a tabla asesores
-- Objetivo: Usar códigos DIVIPOLA como fuente única de verdad
-- ============================================================================

-- Paso 1: Agregar columna municipio_id (nullable temporalmente)
ALTER TABLE asesores 
ADD COLUMN IF NOT EXISTS municipio_id UUID REFERENCES municipios(id);

-- Paso 2: Crear índice para performance
CREATE INDEX IF NOT EXISTS idx_asesores_municipio ON asesores(municipio_id);

-- Paso 3: Migrar datos existentes - Mapeo inteligente de ciudades
-- Normalización: quitar tildes, convertir a mayúsculas, trim espacios

UPDATE asesores a
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
                                        REPLACE(a.ciudad, 'á', 'a'),
                                    'é', 'e'),
                                'í', 'i'),
                            'ó', 'o'),
                        'ú', 'u'),
                    'Á', 'A'),
                'É', 'E'),
            'Í', 'I')
        )
    )
    LIMIT 1
)
WHERE a.municipio_id IS NULL;

-- Paso 4: Verificar cuántos asesores NO se pudieron mapear
SELECT 
    'Asesores sin mapear' as status,
    COUNT(*) as total,
    STRING_AGG(DISTINCT ciudad, ', ') as ciudades_problematicas
FROM asesores 
WHERE municipio_id IS NULL AND estado = 'ACTIVO';

-- Paso 5: Mostrar estadísticas de migración
SELECT 
    CASE 
        WHEN municipio_id IS NOT NULL THEN 'Mapeados correctamente'
        ELSE 'Sin mapear'
    END as status,
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM asesores), 2) as porcentaje
FROM asesores
GROUP BY (municipio_id IS NOT NULL)
ORDER BY status;

-- Paso 6: Hacer NOT NULL después de verificar que todos están mapeados
-- DESCOMENTAR SOLO DESPUÉS DE VERIFICAR QUE TODOS LOS ASESORES ACTIVOS ESTÁN MAPEADOS
-- ALTER TABLE asesores ALTER COLUMN municipio_id SET NOT NULL;

-- Paso 7: Agregar constraint para asegurar integridad
-- ALTER TABLE asesores 
-- ADD CONSTRAINT fk_asesores_municipio 
-- FOREIGN KEY (municipio_id) REFERENCES municipios(id) ON DELETE RESTRICT;

COMMENT ON COLUMN asesores.municipio_id IS 'FK a municipios - Fuente única de verdad para ubicación geográfica';
COMMENT ON COLUMN asesores.ciudad IS 'Campo de texto para display - NO usar para lógica de negocio';
COMMENT ON COLUMN asesores.departamento IS 'Campo de texto para display - NO usar para lógica de negocio';
