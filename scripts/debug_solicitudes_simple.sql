-- Debug simple: Ver solicitudes abiertas y sus ofertas

-- 1. Ver todas las solicitudes ABIERTAS
SELECT 
    s.id,
    s.codigo_solicitud,
    s.estado,
    s.cliente_nombre
FROM solicitudes s
WHERE s.estado = 'ABIERTA'
ORDER BY s.created_at DESC;

-- 2. Ver ofertas por solicitud ABIERTA
SELECT 
    s.codigo_solicitud,
    s.estado as solicitud_estado,
    o.id as oferta_id,
    o.asesor_id,
    o.estado as oferta_estado,
    o.monto_total
FROM solicitudes s
LEFT JOIN ofertas o ON s.id = o.solicitud_id
WHERE s.estado = 'ABIERTA'
ORDER BY s.created_at DESC, o.created_at DESC;

-- 3. Ver cuántos asesores únicos tienen ofertas en solicitudes ABIERTAS
SELECT 
    o.asesor_id,
    COUNT(DISTINCT s.id) as solicitudes_count
FROM solicitudes s
INNER JOIN ofertas o ON s.id = o.solicitud_id
WHERE s.estado = 'ABIERTA'
GROUP BY o.asesor_id;

-- 4. Ver el primer asesor (probablemente el logueado)
SELECT 
    a.id as asesor_id,
    u.email,
    u.nombre as nombre_usuario
FROM asesores a
JOIN usuarios u ON a.usuario_id = u.id
LIMIT 1;
