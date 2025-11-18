-- Investigar por qué Sandra y Andrea tienen mismos valores de actividad y desempeño

-- 1. Ver historial real de ofertas de Sandra Romero
SELECT 
    '=== HISTORIAL DE OFERTAS - SANDRA ROMERO ===' as seccion;

SELECT 
    o.id,
    o.created_at,
    o.estado,
    o.monto_total,
    o.cantidad_repuestos,
    o.cobertura_porcentaje,
    s.id as solicitud_id,
    s.created_at as solicitud_fecha
FROM ofertas o
JOIN solicitudes s ON o.solicitud_id = s.id
JOIN asesores a ON o.asesor_id = a.id
JOIN usuarios u ON a.usuario_id = u.id
WHERE u.nombre = 'Sandra' AND u.apellido = 'Romero'
ORDER BY o.created_at DESC;

-- 2. Ver historial real de ofertas de Andrea Herrera
SELECT 
    '=== HISTORIAL DE OFERTAS - ANDREA HERRERA ===' as seccion;

SELECT 
    o.id,
    o.created_at,
    o.estado,
    o.monto_total,
    o.cantidad_repuestos,
    o.cobertura_porcentaje,
    s.id as solicitud_id,
    s.created_at as solicitud_fecha
FROM ofertas o
JOIN solicitudes s ON o.solicitud_id = s.id
JOIN asesores a ON o.asesor_id = a.id
JOIN usuarios u ON a.usuario_id = u.id
WHERE u.nombre = 'Andrea' AND u.apellido = 'Herrera'
ORDER BY o.created_at DESC;

-- 3. Contar ofertas en últimos 30 días para Sandra
SELECT 
    '=== ACTIVIDAD RECIENTE SANDRA (últimos 30 días) ===' as seccion;

SELECT 
    COUNT(*) as total_ofertas,
    COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras,
    COUNT(CASE WHEN o.created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as ofertas_ultimos_30_dias
FROM ofertas o
JOIN asesores a ON o.asesor_id = a.id
JOIN usuarios u ON a.usuario_id = u.id
WHERE u.nombre = 'Sandra' AND u.apellido = 'Romero';

-- 4. Contar ofertas en últimos 30 días para Andrea
SELECT 
    '=== ACTIVIDAD RECIENTE ANDREA (últimos 30 días) ===' as seccion;

SELECT 
    COUNT(*) as total_ofertas,
    COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras,
    COUNT(CASE WHEN o.created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as ofertas_ultimos_30_dias
FROM ofertas o
JOIN asesores a ON o.asesor_id = a.id
JOIN usuarios u ON a.usuario_id = u.id
WHERE u.nombre = 'Andrea' AND u.apellido = 'Herrera';

-- 5. Ver adjudicaciones históricas de Sandra
SELECT 
    '=== ADJUDICACIONES HISTÓRICAS - SANDRA ===' as seccion;

SELECT 
    adj.created_at,
    adj.precio_adjudicado,
    adj.cantidad_adjudicada,
    s.id as solicitud_id
FROM adjudicaciones_repuesto adj
JOIN ofertas o ON adj.oferta_id = o.id
JOIN solicitudes s ON adj.solicitud_id = s.id
JOIN asesores a ON o.asesor_id = a.id
JOIN usuarios u ON a.usuario_id = u.id
WHERE u.nombre = 'Sandra' AND u.apellido = 'Romero'
ORDER BY adj.created_at DESC;

-- 6. Ver adjudicaciones históricas de Andrea
SELECT 
    '=== ADJUDICACIONES HISTÓRICAS - ANDREA ===' as seccion;

SELECT 
    adj.created_at,
    adj.precio_adjudicado,
    adj.cantidad_adjudicada,
    s.id as solicitud_id
FROM adjudicaciones_repuesto adj
JOIN ofertas o ON adj.oferta_id = o.id
JOIN solicitudes s ON adj.solicitud_id = s.id
JOIN asesores a ON o.asesor_id = a.id
JOIN usuarios u ON a.usuario_id = u.id
WHERE u.nombre = 'Andrea' AND u.apellido = 'Herrera'
ORDER BY adj.created_at DESC;

-- 7. Ver fecha de creación de los asesores
SELECT 
    '=== FECHA DE CREACIÓN DE ASESORES ===' as seccion;

SELECT 
    u.nombre || ' ' || u.apellido as asesor,
    a.created_at as asesor_creado,
    u.created_at as usuario_creado
FROM asesores a
JOIN usuarios u ON a.usuario_id = u.id
WHERE (u.nombre = 'Sandra' AND u.apellido = 'Romero')
   OR (u.nombre = 'Andrea' AND u.apellido = 'Herrera')
ORDER BY u.apellido;
