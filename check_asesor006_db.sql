\c teloo_v3

-- 1. Buscar el asesor
SELECT 
    u.id as usuario_id, 
    u.email, 
    u.nombre,
    u.apellido,
    a.id as asesor_id, 
    a.nivel
FROM usuarios u
INNER JOIN asesores a ON a.usuario_id = u.id
WHERE u.email = 'asesor006_1762827727@teloo.com';

-- 2. Contar ofertas del asesor
SELECT COUNT(*) as total_ofertas
FROM ofertas o
INNER JOIN asesores a ON a.id = o.asesor_id
INNER JOIN usuarios u ON u.id = a.usuario_id
WHERE u.email = 'asesor006_1762827727@teloo.com';

-- 3. Ver detalles de TODAS las ofertas del asesor
SELECT 
    o.id as oferta_id,
    o.estado as estado_oferta,
    s.id as solicitud_id,
    s.codigo as codigo_solicitud,
    s.estado as estado_solicitud,
    s.nivel_actual,
    o.created_at as fecha_oferta,
    (SELECT COUNT(*) FROM ofertas_detalles WHERE oferta_id = o.id) as num_repuestos_ofertados,
    (SELECT COUNT(*) FROM adjudicaciones WHERE oferta_id = o.id) as num_repuestos_ganados
FROM ofertas o
INNER JOIN asesores a ON a.id = o.asesor_id
INNER JOIN usuarios u ON u.id = a.usuario_id
INNER JOIN solicitudes s ON s.id = o.solicitud_id
WHERE u.email = 'asesor006_1762827727@teloo.com'
ORDER BY o.created_at DESC;
