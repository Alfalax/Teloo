-- Monitoreo solicitud 74bdcb21

SELECT 
    'ESTADO ACTUAL' as seccion,
    id,
    estado,
    nivel_actual,
    ofertas_minimas_deseadas,
    fecha_escalamiento,
    EXTRACT(EPOCH FROM (NOW() - fecha_escalamiento))/60 as minutos_desde_escalamiento,
    (SELECT COUNT(*) FROM ofertas WHERE solicitud_id = s.id) as ofertas_recibidas,
    (SELECT COUNT(*) FROM ofertas WHERE solicitud_id = s.id AND cobertura_porcentaje = 100) as ofertas_completas
FROM solicitudes s
WHERE id::text LIKE '74bdcb21%';

SELECT 
    'ASESORES POR NIVEL' as seccion,
    nivel_entrega,
    COUNT(*) as asesores
FROM evaluaciones_asesores_temp
WHERE solicitud_id::text LIKE '74bdcb21%'
GROUP BY nivel_entrega
ORDER BY nivel_entrega;
