-- ============================================================================
-- MIGRACIÓN: Agregar municipio_id a tabla clientes
-- Objetivo: Usar códigos DIVIPOLA como fuente única de verdad
-- ============================================================================

-- Paso 1: Agregar columna municipio_id (nullable temporalmente)
ALTER TABLE clientes 
ADD COLUMN IF NOT EXISTS municipio_id UUID REFERENCES municipios(id);

-- Paso 2: Crear índice para performance
CREATE INDEX IF NOT EXISTS idx_clientes_municipio ON clientes(municipio_id);

-- Paso 3: Migrar datos existentes
UPDATE clientes c
SET municipio_id = (
    SELECT m.id 
    FROM municipios m
    WHERE m.municipio_norm = UPPER(
        TRIM(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(c.ciudad, 'á', 'a'),
                    'é', 'e'),
                'í', 'i'),
            'ó', 'o')
        )
    )
    LIMIT 1
)
WHERE c.municipio_id IS NULL;

-- Mapeo especial para Bogotá
UPDATE clientes 
SET municipio_id = (
    SELECT id FROM municipios 
    WHERE municipio_norm = 'BOGOTA, D.C.' 
    LIMIT 1
)
WHERE UPPER(TRIM(ciudad)) IN ('BOGOTÁ', 'BOGOTA', 'BOGOTÁ D.C.', 'BOGOTA D.C.')
    AND municipio_id IS NULL;

-- Verificar
SELECT 
    CASE 
        WHEN municipio_id IS NOT NULL THEN 'Mapeados'
        ELSE 'Sin mapear'
    END as status,
    COUNT(*) as total
FROM clientes
GROUP BY (municipio_id IS NOT NULL);

-- Hacer NOT NULL
ALTER TABLE clientes ALTER COLUMN municipio_id SET NOT NULL;
ALTER TABLE clientes ADD CONSTRAINT fk_clientes_municipio 
    FOREIGN KEY (municipio_id) REFERENCES municipios(id) ON DELETE RESTRICT;

COMMENT ON COLUMN clientes.municipio_id IS 'FK a municipios - Fuente única de verdad';
COMMENT ON COLUMN clientes.ciudad IS 'Campo de texto para display - NO usar para lógica';
COMMENT ON COLUMN clientes.departamento IS 'Campo de texto para display - NO usar para lógica';
