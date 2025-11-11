-- Verificar qué asesor está logueado y sus ofertas

-- 1. Ver todos los asesores
SELECT 
    a.id as asesor_id,
    u.email,
    u.nombre
FROM asesores a
JOIN usuarios u ON a.usuario_id = u.id;

-- 2. Ver todas las ofertas y a qué asesor pertenecen
SELECT 
    o.id as oferta_id,
    o.asesor_id,
    o.solicitud_id,
    o.estado,
    o.monto_total,
    o.created_at,
    s.estado as solicitud_estado
FROM ofertas o
JOIN solicitudes s ON o.solicitud_id = s.id
ORDER BY o.created_at DESC;

-- 3. Ver solicitudes ABIERTAS y si tienen ofertas
SELECT 
    s.id as solicitud_id,
    s.estado,
    s.cliente_nombre,
    COUNT(o.id) as ofertas_count,
    STRING_AGG(DISTINCT o.asesor_id::text, ', ') as asesores_con_ofertas
FROM solicitudes s
LEFT JOIN ofertas o ON s.id = o.solicitud_id
WHERE s.estado = 'ABIERTA'
GROUP BY s.id, s.estado, s.cliente_nombre
ORDER BY s.created_at DESC;

-- 4. Contar por cada asesor cuántas solicitudes ABIERTAS tiene con oferta
SELECT 
    a.id as asesor_id,
    u.email,
    COUNT(DISTINCT s.id) as solicitudes_abiertas_con_oferta
FROM asesores a
JOIN usuarios u ON a.usuario_id = u.id
LEFT JOIN ofertas o ON a.id = o.asesor_id
LEFT JOIN solicitudes s ON o.solicitud_id = s.id AND s.estado = 'ABIERTA'
GROUP BY a.id, u.email;
