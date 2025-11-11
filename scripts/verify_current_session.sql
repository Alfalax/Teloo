-- Verificar sesiones activas y tokens

-- 1. Ver todas las sesiones activas
SELECT 
    s.id,
    s.usuario_id,
    u.email,
    u.nombre,
    s.token_type,
    s.expires_at,
    s.is_active,
    s.created_at
FROM sesiones_usuarios s
JOIN usuarios u ON s.usuario_id = u.id
WHERE s.is_active = true
ORDER BY s.created_at DESC;

-- 2. Ver qué asesor corresponde a cada usuario
SELECT 
    u.id as usuario_id,
    u.email,
    u.nombre,
    a.id as asesor_id
FROM usuarios u
LEFT JOIN asesores a ON u.id = a.usuario_id
WHERE u.email LIKE '%asesor%'
ORDER BY u.email;

-- 3. Ver las últimas sesiones (activas e inactivas)
SELECT 
    s.id,
    u.email,
    s.token_type,
    s.is_active,
    s.created_at,
    s.expires_at
FROM sesiones_usuarios s
JOIN usuarios u ON s.usuario_id = u.id
WHERE u.email LIKE '%asesor%'
ORDER BY s.created_at DESC
LIMIT 10;
