-- Verificar si existen solicitudes con estados incorrectos en la base de datos
-- Estados incorrectos: ACEPTADA, RECHAZADA, EXPIRADA

SELECT 
    'Solicitudes con estados incorrectos' as tipo,
    estado,
    COUNT(*) as cantidad,
    MIN(created_at) as primera_creacion,
    MAX(created_at) as ultima_creacion
FROM solicitudes
WHERE estado IN ('ACEPTADA', 'RECHAZADA', 'EXPIRADA')
GROUP BY estado

UNION ALL

SELECT 
    'Solicitudes con estados correctos' as tipo,
    estado,
    COUNT(*) as cantidad,
    MIN(created_at) as primera_creacion,
    MAX(created_at) as ultima_creacion
FROM solicitudes
WHERE estado IN ('ABIERTA', 'EVALUADA', 'CERRADA_SIN_OFERTAS')
GROUP BY estado

ORDER BY tipo, estado;

-- Detalle de solicitudes con estados incorrectos (si existen)
SELECT 
    id,
    estado,
    nivel_actual,
    ciudad_origen,
    created_at,
    updated_at
FROM solicitudes
WHERE estado IN ('ACEPTADA', 'RECHAZADA', 'EXPIRADA')
ORDER BY created_at DESC
LIMIT 10;
