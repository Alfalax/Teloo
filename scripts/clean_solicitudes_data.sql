-- Script para limpiar todas las tablas relacionadas con solicitudes
-- Esto permite empezar desde cero con la implementación correcta de eventos

-- ADVERTENCIA: Este script borra TODOS los datos de solicitudes, ofertas y relacionados
-- Usar solo en ambiente de desarrollo/testing

BEGIN;

-- 1. Limpiar tablas de análisis y métricas (si existen)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'ofertas_historicas') THEN
        DELETE FROM ofertas_historicas;
    END IF;
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'historial_respuestas_ofertas') THEN
        DELETE FROM historial_respuestas_ofertas;
    END IF;
END $$;

-- 2. Limpiar evaluaciones temporales
DELETE FROM evaluaciones_asesores_temp;

-- 3. Limpiar adjudicaciones
DELETE FROM adjudicaciones_repuesto;

-- 4. Limpiar detalles de ofertas
DELETE FROM ofertas_detalle;

-- 5. Limpiar ofertas
DELETE FROM ofertas;

-- 6. Limpiar evaluaciones
DELETE FROM evaluaciones;

-- 7. Limpiar repuestos solicitados
DELETE FROM repuestos_solicitados;

-- 8. Limpiar solicitudes
DELETE FROM solicitudes;

-- 9. Limpiar clientes (opcional - comentar si quieres mantener clientes)
DELETE FROM clientes;

-- Verificar que todo quedó limpio
SELECT 'solicitudes' as tabla, COUNT(*) as registros FROM solicitudes
UNION ALL
SELECT 'repuestos_solicitados', COUNT(*) FROM repuestos_solicitados
UNION ALL
SELECT 'ofertas', COUNT(*) FROM ofertas
UNION ALL
SELECT 'ofertas_detalle', COUNT(*) FROM ofertas_detalle
UNION ALL
SELECT 'adjudicaciones_repuesto', COUNT(*) FROM adjudicaciones_repuesto
UNION ALL
SELECT 'evaluaciones', COUNT(*) FROM evaluaciones
UNION ALL
SELECT 'evaluaciones_asesores_temp', COUNT(*) FROM evaluaciones_asesores_temp
UNION ALL
SELECT 'clientes', COUNT(*) FROM clientes;

COMMIT;

-- Mensaje de confirmación
SELECT '✅ Todas las tablas de solicitudes han sido limpiadas' as status;
