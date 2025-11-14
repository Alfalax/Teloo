-- Verificación completa de ofertas para asesor006_1762827727@teloo.com

-- 1. Información del asesor
SELECT 'INFORMACIÓN DEL ASESOR' as seccion;
SELECT id, email, nombre, rol 
FROM usuarios 
WHERE email = 'asesor006_1762827727@teloo.com';

-- 2. Ofertas totales (tabla ofertas)
SELECT 'OFERTAS TOTALES' as seccion;
SELECT COUNT(*) as total_ofertas_generales
FROM ofertas o
JOIN usuarios u ON o.asesor_id = u.id
WHERE u.email = 'asesor006_1762827727@teloo.com';

-- 3. Ofertas parciales (tabla ofertas_detalle)
SELECT 'OFERTAS PARCIALES (DETALLE)' as seccion;
SELECT COUNT(*) as total_ofertas_detalle
FROM ofertas_detalle od
JOIN ofertas o ON od.oferta_id = o.id
JOIN usuarios u ON o.asesor_id = u.id
WHERE u.email = 'asesor006_1762827727@teloo.com';

-- 4. Resumen completo
SELECT 'RESUMEN COMPLETO' as seccion;
SELECT 
    u.email,
    u.nombre,
    COUNT(DISTINCT o.id) as ofertas_totales,
    COUNT(od.id) as ofertas_parciales,
    COUNT(DISTINCT o.solicitud_id) as solicitudes_con_oferta
FROM usuarios u
LEFT JOIN ofertas o ON u.id = o.asesor_id
LEFT JOIN ofertas_detalle od ON o.id = od.oferta_id
WHERE u.email = 'asesor006_1762827727@teloo.com'
GROUP BY u.email, u.nombre;

-- 5. Verificar si hay ofertas con asesor_id que no existe en usuarios
SELECT 'OFERTAS HUÉRFANAS (sin asesor válido)' as seccion;
SELECT COUNT(*) as ofertas_sin_asesor_valido
FROM ofertas o
LEFT JOIN usuarios u ON o.asesor_id = u.id
WHERE u.id IS NULL;
