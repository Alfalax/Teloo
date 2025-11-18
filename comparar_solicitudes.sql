-- COMPARACIÓN ENTRE LAS DOS SOLICITUDES

-- Solicitud 91269925 (la que NO escaló correctamente)
SELECT 
    '91269925 - NO ESCALÓ' as caso,
    id,
    estado,
    nivel_actual,
    ciudad_origen,
    created_at,
    fecha_escalamiento,
    updated_at,
    (SELECT COUNT(*) FROM ofertas WHERE solicitud_id = s.id) as ofertas_recibidas,
    (SELECT COUNT(*) FROM ofertas WHERE solicitud_id = s.id AND cobertura_porcentaje = 100) as ofertas_completas
FROM solicitudes s
WHERE id::text LIKE '91269925%'

UNION ALL

-- Solicitud 74bdcb21 (la que SÍ escaló correctamente)
SELECT 
    '74bdcb21 - SÍ ESCALÓ' as caso,
    id,
    estado,
    nivel_actual,
    ciudad_origen,
    created_at,
    fecha_escalamiento,
    updated_at,
    (SELECT COUNT(*) FROM ofertas WHERE solicitud_id = s.id) as ofertas_recibidas,
    (SELECT COUNT(*) FROM ofertas WHERE solicitud_id = s.id AND cobertura_porcentaje = 100) as ofertas_completas
FROM solicitudes s
WHERE id::text LIKE '74bdcb21%';

-- Evaluaciones por nivel de cada solicitud
SELECT 
    '91269925' as solicitud,
    nivel_entrega,
    COUNT(*) as asesores
FROM evaluaciones_asesores_temp
WHERE solicitud_id::text LIKE '91269925%'
GROUP BY nivel_entrega
ORDER BY nivel_entrega;

SELECT 
    '74bdcb21' as solicitud,
    nivel_entrega,
    COUNT(*) as asesores
FROM evaluaciones_asesores_temp
WHERE solicitud_id::text LIKE '74bdcb21%'
GROUP BY nivel_entrega
ORDER BY nivel_entrega;
