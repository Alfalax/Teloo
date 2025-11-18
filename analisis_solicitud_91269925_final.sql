-- ANÁLISIS SOLICITUD 91269925

-- 1. Información básica
SELECT 
    '=== INFORMACION BASICA ===' as titulo;

SELECT 
    s.id,
    s.estado,
    s.ciudad_origen,
    s.created_at,
    s.updated_at,
    c.nombre as cliente_nombre,
    c.telefono as cliente_telefono
FROM solicitudes s
LEFT JOIN clientes c ON s.cliente_id = c.id
WHERE s.id::text LIKE '91269925%';

-- 2. Repuestos solicitados
SELECT 
    '=== REPUESTOS SOLICITADOS ===' as titulo;

SELECT 
    nombre,
    cantidad,
    marca_vehiculo,
    linea_vehiculo,
    anio_vehiculo
FROM repuestos_solicitados
WHERE solicitud_id::text LIKE '91269925%'
ORDER BY nombre;

-- 3. Ofertas recibidas
SELECT 
    '=== OFERTAS RECIBIDAS ===' as titulo;

SELECT 
    SUBSTRING(o.id::text, 1, 8) as oferta_id,
    o.estado,
    o.tiempo_entrega_dias,
    o.created_at,
    a.codigo as asesor_codigo
FROM ofertas o
JOIN asesores a ON o.asesor_id = a.id
WHERE o.solicitud_id::text LIKE '91269925%'
ORDER BY o.created_at DESC;

-- 4. Detalles de ofertas
SELECT 
    '=== DETALLES DE OFERTAS ===' as titulo;

SELECT 
    SUBSTRING(o.id::text, 1, 8) as oferta_id,
    o.estado,
    od.repuesto_nombre,
    od.cantidad,
    od.precio_unitario,
    od.garantia_meses,
    (od.precio_unitario * od.cantidad) as subtotal
FROM ofertas o
JOIN ofertas_detalle od ON o.id = od.oferta_id
WHERE o.solicitud_id::text LIKE '91269925%'
ORDER BY o.created_at DESC, od.repuesto_nombre;

-- 5. Totales por oferta
SELECT 
    '=== TOTALES POR OFERTA ===' as titulo;

SELECT 
    SUBSTRING(o.id::text, 1, 8) as oferta_id,
    o.estado,
    a.codigo as asesor,
    o.tiempo_entrega_dias,
    COUNT(od.id) as num_items,
    SUM(od.precio_unitario * od.cantidad) as total_oferta
FROM ofertas o
JOIN asesores a ON o.asesor_id = a.id
LEFT JOIN ofertas_detalle od ON o.id = od.oferta_id
WHERE o.solicitud_id::text LIKE '91269925%'
GROUP BY o.id, o.estado, a.codigo, o.tiempo_entrega_dias
ORDER BY total_oferta ASC NULLS LAST;

-- 6. Evaluaciones
SELECT 
    '=== EVALUACIONES ===' as titulo;

SELECT 
    SUBSTRING(oferta_id::text, 1, 8) as oferta_id,
    puntaje_total,
    puntaje_precio,
    puntaje_tiempo,
    puntaje_garantia,
    puntaje_cobertura,
    created_at
FROM evaluaciones
WHERE solicitud_id::text LIKE '91269925%'
ORDER BY puntaje_total DESC;
