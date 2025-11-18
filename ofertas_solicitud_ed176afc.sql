-- Análisis completo de ofertas para solicitud ed176afc-da82-4cb3-82c8-5b5a42c2d24e

-- 1. Información de la solicitud
SELECT 'INFORMACIÓN DE LA SOLICITUD' as seccion;
SELECT id, estado, created_at
FROM solicitudes 
WHERE id = 'ed176afc-da82-4cb3-82c8-5b5a42c2d24e';

-- 2. Repuestos solicitados
SELECT 'REPUESTOS SOLICITADOS' as seccion;
SELECT rs.id, rs.nombre_repuesto, rs.cantidad
FROM repuestos_solicitados rs
WHERE rs.solicitud_id = 'ed176afc-da82-4cb3-82c8-5b5a42c2d24e'
ORDER BY rs.created_at;

-- 3. Resumen de ofertas totales
SELECT 'RESUMEN DE OFERTAS TOTALES' as seccion;
SELECT 
    COUNT(*) as total_ofertas,
    COUNT(DISTINCT o.asesor_id) as asesores_diferentes,
    MIN(o.monto_total) as monto_minimo,
    MAX(o.monto_total) as monto_maximo,
    AVG(o.monto_total) as monto_promedio,
    SUM(CASE WHEN o.cobertura_porcentaje = 100 THEN 1 ELSE 0 END) as ofertas_completas,
    SUM(CASE WHEN o.cobertura_porcentaje < 100 THEN 1 ELSE 0 END) as ofertas_parciales
FROM ofertas o
WHERE o.solicitud_id = 'ed176afc-da82-4cb3-82c8-5b5a42c2d24e';

-- 4. Detalle de cada oferta
SELECT 'DETALLE DE CADA OFERTA' as seccion;
SELECT 
    o.id as oferta_id,
    o.estado,
    o.origen,
    o.monto_total,
    o.cantidad_repuestos,
    o.cobertura_porcentaje,
    o.tiempo_entrega_dias,
    o.observaciones,
    o.created_at,
    u.email as asesor_email,
    u.nombre as asesor_nombre
FROM ofertas o
LEFT JOIN usuarios u ON o.asesor_id = u.id
WHERE o.solicitud_id = 'ed176afc-da82-4cb3-82c8-5b5a42c2d24e'
ORDER BY o.created_at;

-- 5. Detalle de ofertas parciales (por repuesto)
SELECT 'DETALLE DE OFERTAS PARCIALES (POR REPUESTO)' as seccion;
SELECT 
    o.id as oferta_id,
    o.monto_total as total_oferta,
    od.precio_unitario,
    od.cantidad,
    od.tiempo_entrega_dias,
    od.garantia_meses,
    od.marca_repuesto,
    od.origen_repuesto,
    rs.nombre_repuesto
FROM ofertas o
JOIN ofertas_detalle od ON o.id = od.oferta_id
JOIN repuestos_solicitados rs ON od.repuesto_solicitado_id = rs.id
WHERE o.solicitud_id = 'ed176afc-da82-4cb3-82c8-5b5a42c2d24e'
ORDER BY o.created_at, od.created_at;

-- 6. Verificar si los asesor_id existen en usuarios
SELECT 'VERIFICACIÓN DE ASESORES' as seccion;
SELECT 
    o.asesor_id,
    CASE 
        WHEN u.id IS NULL THEN 'NO EXISTE EN USUARIOS'
        ELSE u.email 
    END as estado_asesor,
    COUNT(*) as num_ofertas
FROM ofertas o
LEFT JOIN usuarios u ON o.asesor_id = u.id
WHERE o.solicitud_id = 'ed176afc-da82-4cb3-82c8-5b5a42c2d24e'
GROUP BY o.asesor_id, u.id, u.email;
