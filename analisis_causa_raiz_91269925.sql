-- ANÁLISIS EXHAUSTIVO SOLICITUD 91269925

-- 1. Datos completos de la solicitud
SELECT 
    id,
    estado,
    nivel_actual,
    ofertas_minimas_deseadas,
    fecha_escalamiento,
    created_at,
    updated_at,
    EXTRACT(EPOCH FROM (updated_at - fecha_escalamiento))/60 as minutos_desde_escalamiento
FROM solicitudes 
WHERE id::text LIKE '91269925%';

-- 2. Ofertas recibidas con timestamps
SELECT 
    id,
    estado,
    cobertura_porcentaje,
    monto_total,
    cantidad_repuestos,
    created_at,
    EXTRACT(EPOCH FROM (created_at - (SELECT fecha_escalamiento FROM solicitudes WHERE id::text LIKE '91269925%')))/60 as minutos_desde_escalamiento
FROM ofertas 
WHERE solicitud_id::text LIKE '91269925%'
ORDER BY created_at;

-- 3. Detalles de ofertas (para verificar cobertura)
SELECT 
    o.id as oferta_id,
    COUNT(DISTINCT od.repuesto_solicitado_id) as repuestos_cubiertos,
    (SELECT COUNT(*) FROM repuestos_solicitados WHERE solicitud_id::text LIKE '91269925%') as total_repuestos
FROM ofertas o
LEFT JOIN ofertas_detalle od ON o.id = od.oferta_id
WHERE o.solicitud_id::text LIKE '91269925%'
GROUP BY o.id;

-- 4. Evaluaciones temporales guardadas
SELECT 
    nivel_entrega,
    COUNT(*) as asesores_en_nivel,
    MIN(puntaje_total) as puntaje_min,
    MAX(puntaje_total) as puntaje_max,
    AVG(puntaje_total) as puntaje_promedio
FROM evaluaciones_asesores_temp
WHERE solicitud_id::text LIKE '91269925%'
GROUP BY nivel_entrega
ORDER BY nivel_entrega;

-- 5. Adjudicaciones (para ver cuándo se evaluó)
SELECT 
    id,
    created_at,
    motivo_adjudicacion,
    puntaje_obtenido
FROM adjudicaciones_repuesto
WHERE solicitud_id::text LIKE '91269925%'
ORDER BY created_at;

-- 6. Configuración de tiempos
SELECT clave, valor_json 
FROM parametros_config 
WHERE clave IN ('tiempos_espera_nivel', 'ofertas_minimas_deseadas_default');
