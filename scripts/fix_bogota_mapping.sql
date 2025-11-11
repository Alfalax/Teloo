-- Mapeo especial para Bogotá
UPDATE asesores 
SET municipio_id = (
    SELECT id FROM municipios 
    WHERE municipio_norm = 'BOGOTA, D.C.' 
    LIMIT 1
)
WHERE UPPER(TRIM(ciudad)) IN ('BOGOTÁ', 'BOGOTA', 'BOGOTÁ D.C.', 'BOGOTA D.C.', 'BOGOTÁ, D.C.', 'BOGOTA, D.C.')
    AND municipio_id IS NULL;

-- Verificar resultado
SELECT 
    'Después de corrección Bogotá' as status,
    COUNT(*) as sin_mapear,
    STRING_AGG(DISTINCT ciudad, ', ') as ciudades_restantes
FROM asesores 
WHERE municipio_id IS NULL AND estado = 'ACTIVO';
