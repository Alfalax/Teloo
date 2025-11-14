-- Script para limpiar solicitudes y ofertas manteniendo clientes
-- Ejecutar en orden para respetar dependencias de claves foráneas

-- 1. Eliminar ofertas
DELETE FROM ofertas;

-- 2. Eliminar evaluaciones de asesores (temporal y permanente)
DELETE FROM evaluaciones_asesores_temp;
DELETE FROM evaluaciones_asesores;

-- 3. Eliminar repuestos solicitados
DELETE FROM repuestos_solicitados;

-- 4. Eliminar solicitudes
DELETE FROM solicitudes;

-- Verificar que todo se eliminó correctamente
SELECT 'Ofertas restantes:' as tabla, COUNT(*) as total FROM ofertas
UNION ALL
SELECT 'Evaluaciones temp restantes:', COUNT(*) FROM evaluaciones_asesores_temp
UNION ALL
SELECT 'Evaluaciones restantes:', COUNT(*) FROM evaluaciones_asesores
UNION ALL
SELECT 'Repuestos restantes:', COUNT(*) FROM repuestos_solicitados
UNION ALL
SELECT 'Solicitudes restantes:', COUNT(*) FROM solicitudes
UNION ALL
SELECT 'Clientes (conservados):', COUNT(*) FROM clientes;
