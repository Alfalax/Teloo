-- Cleanup duplicate ofertas (keep only the most recent one per asesor+solicitud)
-- This fixes the issue caused by previous delete+create logic

-- First, identify duplicates
WITH duplicates AS (
    SELECT 
        solicitud_id,
        asesor_id,
        COUNT(*) as count,
        ARRAY_AGG(id ORDER BY created_at DESC) as ids
    FROM ofertas
    GROUP BY solicitud_id, asesor_id
    HAVING COUNT(*) > 1
)
-- Delete all but the most recent offer for each asesor+solicitud
DELETE FROM ofertas
WHERE id IN (
    SELECT UNNEST(ids[2:]) -- Keep first (most recent), delete rest
    FROM duplicates
);

-- Show remaining duplicates (should be empty)
SELECT 
    solicitud_id,
    asesor_id,
    COUNT(*) as count
FROM ofertas
GROUP BY solicitud_id, asesor_id
HAVING COUNT(*) > 1;
