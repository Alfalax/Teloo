-- ANÁLISIS COMPLETO DE SOLICITUD

\echo '================================================================================'
\echo 'ANÁLISIS DE SOLICITUD #91269925'
\echo '================================================================================'

\echo ''
\echo '1. INFORMACIÓN BÁSICA'
\echo '--------------------------------------------------------------------------------'

SELECT 
    s.id,
    s.estado,
    s.ciudad_origen,
    s.ciudad_destino,
    s.created_at,
    s.updated_at,
    c.nombre as cliente_nombre,
    c.telefono as cliente_telefono,
    c.email as cliente_email
FROM solicitudes s
LEFT JOIN clientes c ON s.cliente_id = c.id
WHERE s.id::text LIKE '91269925%';

\echo ''
\echo '2. REPUESTOS SOLICITADOS'
\echo '--------------------------------------------------------------------------------'

SELECT 
    nombre,
    cantidad,
    marca_vehiculo,
    linea_vehiculo,
    anio_vehiculo
FROM repuestos
WHERE solicitud_id::text LIKE '91269925%'
ORDER BY nombre;

\echo ''
\echo '3. OFERTAS RECIBIDAS'
\echo '--------------------------------------------------------------------------------'

SELECT 
    o.id,
    o.estado,
    o.tiempo_entrega_dias,
    o.created_at,
    a.nombre as asesor_nombre,
    a.codigo as asesor_codigo,
    a.ciudad as asesor_ciudad
FROM ofertas o
JOIN asesores a ON o.asesor_id = a.id
WHERE o.solicitud_id::text LIKE '91269925%'
ORDER BY o.created_at DESC;

\echo ''
\echo '4. DETALLES DE OFERTAS'
\echo '--------------------------------------------------------------------------------'

SELECT 
    SUBSTRING(o.id::text, 1, 8) as oferta_id_corto,
    o.estado as estado_oferta,
    od.repuesto_nombre,
    od.cantidad,
    od.precio_unitario,
    od.garantia_meses,
    (od.precio_unitario * od.cantidad) as subtotal
FROM ofertas o
JOIN oferta_detalles od ON o.id = od.oferta_id
WHERE o.solicitud_id::text LIKE '91269925%'
ORDER BY o.created_at DESC, od.repuesto_nombre;

\echo ''
\echo '5. TOTALES POR OFERTA'
\echo '--------------------------------------------------------------------------------'

SELECT 
    SUBSTRING(o.id::text, 1, 8) as oferta_id_corto,
    o.estado,
    a.nombre as asesor,
    COUNT(od.id) as num_items,
    SUM(od.precio_unitario * od.cantidad) as total_oferta
FROM ofertas o
JOIN asesores a ON o.asesor_id = a.id
LEFT JOIN oferta_detalles od ON o.id = od.oferta_id
WHERE o.solicitud_id::text LIKE '91269925%'
GROUP BY o.id, o.estado, a.nombre
ORDER BY total_oferta ASC NULLS LAST;

\echo ''
\echo '6. HISTORIAL DE ESCALAMIENTO'
\echo '--------------------------------------------------------------------------------'

SELECT 
    nivel_anterior,
    nivel_nuevo,
    motivo,
    created_at
FROM historial_escalamiento
WHERE solicitud_id::text LIKE '91269925%'
ORDER BY created_at DESC;

\echo ''
\echo '================================================================================'
\echo 'FIN DEL ANÁLISIS'
\echo '================================================================================'
