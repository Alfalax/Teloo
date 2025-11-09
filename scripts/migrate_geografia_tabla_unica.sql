-- Migration Script: Consolidate geographic tables into single municipios table
-- Date: 2025-11-08
-- Description: Replace areas_metropolitanas and hubs_logisticos with unified municipios table

-- Step 1: Create new municipios table
CREATE TABLE IF NOT EXISTS municipios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_dane VARCHAR(10) UNIQUE,
    municipio VARCHAR(100) NOT NULL,
    municipio_norm VARCHAR(100) NOT NULL,
    departamento VARCHAR(100) NOT NULL,
    area_metropolitana VARCHAR(100),
    hub_logistico VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 2: Migrate existing data (if any)
-- Combine data from both old tables
INSERT INTO municipios (municipio_norm, departamento, area_metropolitana, hub_logistico, created_at)
SELECT 
    COALESCE(am.municipio_norm, hl.municipio_norm) as municipio_norm,
    '' as departamento,  -- Will be populated from DIVIPOLA import
    am.area_metropolitana,
    hl.hub_asignado_norm as hub_logistico,
    NOW() as created_at
FROM areas_metropolitanas am
FULL OUTER JOIN hubs_logisticos hl ON am.municipio_norm = hl.municipio_norm
ON CONFLICT (municipio_norm) DO NOTHING;

-- Step 3: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_municipios_norm ON municipios(municipio_norm);
CREATE INDEX IF NOT EXISTS idx_municipios_departamento ON municipios(departamento);
CREATE INDEX IF NOT EXISTS idx_municipios_area_metropolitana ON municipios(area_metropolitana);
CREATE INDEX IF NOT EXISTS idx_municipios_hub ON municipios(hub_logistico);
CREATE INDEX IF NOT EXISTS idx_municipios_codigo_dane ON municipios(codigo_dane);

-- Step 4: Drop old tables (only after verifying data migration)
-- IMPORTANT: Uncomment these lines only after verifying the migration was successful
-- DROP TABLE IF EXISTS areas_metropolitanas CASCADE;
-- DROP TABLE IF EXISTS hubs_logisticos CASCADE;

-- Step 5: Verify migration
SELECT 
    'Migration Summary' as info,
    COUNT(*) as total_municipios,
    COUNT(DISTINCT area_metropolitana) as total_areas_metropolitanas,
    COUNT(DISTINCT hub_logistico) as total_hubs,
    COUNT(DISTINCT departamento) as total_departamentos
FROM municipios;

-- Show sample data
SELECT * FROM municipios LIMIT 10;
