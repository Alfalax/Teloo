-- Debug: Verificar solicitudes abiertas vs indicador

-- 1. Ver todas las solicitudes ABIERTAS
SELECT 
    s.id,
    s.codigo_solicitud,
    s.estado,
    s.cliente_nombre,
    COUNT(DISTINCT e.asesor_id) as evaluaciones_count,
    COUNT(DISTINCT o.asesor_id) as ofertas_count
FROM solicitudes s
LEFT JOIN evaluaciones_asesores e ON s.id = e.solicitud_id
LEFT JOIN ofertas o ON s.id = o.solicitud_id
WHERE s.estado = 'ABIERTA'
GROUP BY s.id, s.codigo_solicitud, s.estado, s.cliente_nombre
ORDER BY s.created_at DESC;

-- 2. Ver qué asesor está logueado (asumiendo que es el primero)
SELECT 
    a.id as asesor_id,
    u.nombre_completo,
    u.email
FROM asesores a
JOIN usuarios u ON a.usuario_id = u.id
WHERE u.email LIKE '%asesor%'
LIMIT 1;

-- 3. Ver solicitudes ABIERTAS asignadas a un asesor específico (reemplazar con el ID real)
-- Primero obtener el asesor_id del usuario logueado
WITH asesor_actual AS (
    SELECT a.id as asesor_id
    FROM asesores a
    JOIN usuarios u ON a.usuario_id = u.id
    WHERE u.email LIKE '%asesor%'
    LIMIT 1
)
SELECT 
    s.id,
    s.codigo_solicitud,
    s.estado,
    s.cliente_nombre,
    CASE 
        WHEN e.asesor_id IS NOT NULL THEN 'Tiene evaluación'
        ELSE 'Sin evaluación'
    END as tiene_evaluacion,
    CASE 
        WHEN o.asesor_id IS NOT NULL THEN 'Tiene oferta'
        ELSE 'Sin oferta'
    END as tiene_oferta
FROM solicitudes s
LEFT JOIN evaluaciones_asesores e ON s.id = e.solicitud_id AND e.asesor_id = (SELECT asesor_id FROM asesor_actual)
LEFT JOIN ofertas o ON s.id = o.solicitud_id AND o.asesor_id = (SELECT asesor_id FROM asesor_actual)
WHERE s.estado = 'ABIERTA'
  AND (e.asesor_id IS NOT NULL OR o.asesor_id IS NOT NULL)
ORDER BY s.created_at DESC;

-- 4. Contar solicitudes según la lógica del endpoint
WITH asesor_actual AS (
    SELECT a.id as asesor_id
    FROM asesores a
    JOIN usuarios u ON a.usuario_id = u.id
    WHERE u.email LIKE '%asesor%'
    LIMIT 1
)
SELECT COUNT(DISTINCT s.id) as solicitudes_abiertas_count
FROM solicitudes s
LEFT JOIN evaluaciones_asesores e ON s.id = e.solicitud_id
LEFT JOIN ofertas o ON s.id = o.solicitud_id
WHERE s.estado = 'ABIERTA'
  AND (
    e.asesor_id = (SELECT asesor_id FROM asesor_actual)
    OR o.asesor_id = (SELECT asesor_id FROM asesor_actual)
  );
