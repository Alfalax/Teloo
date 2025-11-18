-- Buscar el asesor
SELECT u.id as usuario_id, u.email, u.nombre, a.id as asesor_id, a.nivel
FROM usuarios u
INNER JOIN asesores a ON a.usuario_id = u.id
WHERE u.email = 'asesor006_1762827727@teloo.com';

-- Contar ofertas del asesor
SELECT COUNT(*) as total_ofertas
FROM ofertas o
INNER JOIN asesores a ON a.id = o.asesor_id
INNER JOIN usuarios u ON u.id = a.usuario_id
WHERE u.email = 'asesor006_1762827727@teloo.com';

-- Ver detalles de las ofertas
SELECT 
    o.id as oferta_id,
    o.estado as estado_oferta,
    s.id as solicitud_id,
    s.estado as estado_solicitud,
    s.codigo as codigo_solicitud,
    o.created_at as fecha_oferta
FROM ofertas o
INNER JOIN asesores a ON a.id = o.asesor_id
INNER JOIN usuarios u ON u.id = a.usuario_id
INNER JOIN solicitudes s ON s.id = o.solicitud_id
WHERE u.email = 'asesor006_1762827727@teloo.com'
ORDER BY o.created_at DESC;
