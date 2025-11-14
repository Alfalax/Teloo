-- Monitoreo de solicitud 869c2081
SELECT 
    'ESTADO ACTUAL' as seccion,
    id,
    estado,
    nivel_actual,
    ofertas_minimas_deseadas,
    fecha_escalamiento,
    EXTRACT(EPOCH FROM (NOW() - fecha_escalamiento))/60 as minutos_desde_escalamiento,
    (SELECT COUNT(*) FROM ofertas WHERE solicitud_id = s.id) as ofertas_recibidas,
    (SELECT COUNT(*) FROM ofertas o 
     WHERE o.solicitud_id = s.id 
     AND (SELECT COUNT(DISTINCT od.repuesto_solicitado_id) 
          FROM ofertas_detalle od 
          WHERE od.oferta_id = o.id) = 
         (SELECT COUNT(*) FROM repuestos_solicitados WHERE solicitud_id = s.id)
    ) as ofertas_completas
FROM solicitudes s
WHERE id::text LIKE '869c2081%';

SELECT 
    'ASESORES POR NIVEL' as seccion,
    nivel_entrega,
    COUNT(*) as asesores
FROM evaluaciones_asesores_temp
WHERE solicitud_id::text LIKE '869c2081%'
GROUP BY nivel_entrega
ORDER BY nivel_entrega;
