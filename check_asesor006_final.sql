\c teloo_v3

-- Ver ofertas del asesor006
SELECT 
    o.id as oferta_id,
    o.estado as estado_oferta,
    s.id as solicitud_id,
    s.estado as estado_solicitud,
    s.nivel_actual,
    o.created_at as fecha_oferta
FROM ofertas o
INNER JOIN asesores a ON a.id = o.asesor_id
INNER JOIN usuarios u ON u.id = a.usuario_id
INNER JOIN solicitudes s ON s.id = o.solicitud_id
WHERE u.email = 'asesor006_1762827727@teloo.com'
ORDER BY o.created_at DESC;
