-- =====================================================
-- MIGRACIÓN: Eliminar campo nivel_actual de tabla asesores
-- =====================================================
-- Fecha: 2025-11-14
-- Razón: El campo nivel_actual en asesores es redundante y no se usa
--        en ningún proceso crítico. Solo se usaba para display.
--        Los niveles reales se calculan dinámicamente y se almacenan
--        en evaluaciones_asesores_temp por cada solicitud.
-- =====================================================

-- Verificar que la columna existe antes de eliminarla
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'asesores' 
        AND column_name = 'nivel_actual'
    ) THEN
        -- Eliminar la columna nivel_actual
        ALTER TABLE asesores DROP COLUMN nivel_actual;
        
        RAISE NOTICE 'Columna nivel_actual eliminada exitosamente de la tabla asesores';
    ELSE
        RAISE NOTICE 'La columna nivel_actual no existe en la tabla asesores';
    END IF;
END $$;

-- Verificar el resultado
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'asesores'
ORDER BY ordinal_position;
