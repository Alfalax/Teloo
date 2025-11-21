-- Enhanced Materialized Views for TeLOO V3 Analytics
-- This script creates enhanced materialized views for historical KPIs

-- Drop existing views if they exist (to recreate with enhancements)
DROP MATERIALIZED VIEW IF EXISTS mv_metricas_mensuales CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_ranking_asesores CASCADE;

-- Create enhanced mv_metricas_mensuales with more comprehensive metrics
CREATE MATERIALIZED VIEW mv_metricas_mensuales AS
SELECT 
    DATE_TRUNC('month', s.created_at) as mes,
    COUNT(*) as solicitudes_creadas,
    COUNT(CASE WHEN s.cliente_acepto = true THEN 1 END) as solicitudes_aceptadas,
    COUNT(CASE WHEN s.cliente_acepto = false THEN 1 END) as solicitudes_rechazadas,
    COUNT(CASE WHEN s.estado = 'CERRADA_SIN_OFERTAS' THEN 1 END) as solicitudes_expiradas,
    COUNT(CASE WHEN s.estado = 'CERRADA_SIN_OFERTAS' THEN 1 END) as solicitudes_sin_ofertas,
    AVG(EXTRACT(EPOCH FROM (s.updated_at - s.created_at))) as tiempo_promedio_cierre_seg,
    COUNT(DISTINCT o.id) as ofertas_totales,
    COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END) as ofertas_ganadoras,
    COUNT(CASE WHEN o.estado = 'ACEPTADA' THEN 1 END) as ofertas_aceptadas,
    AVG(od.precio_unitario) as precio_promedio_ofertas,
    MIN(od.precio_unitario) as precio_minimo_ofertas,
    MAX(od.precio_unitario) as precio_maximo_ofertas,
    AVG(o.tiempo_entrega_dias) as tiempo_entrega_promedio,
    AVG(od.garantia_meses) as garantia_promedio_meses,
    COUNT(DISTINCT s.cliente_id) as clientes_activos,
    COUNT(DISTINCT o.asesor_id) as asesores_activos,
    COUNT(DISTINCT rs.marca_vehiculo) as marcas_vehiculos_solicitadas,
    SUM(od.precio_unitario * od.cantidad) as volumen_transaccional_total,
    -- Métricas calculadas
    CASE 
        WHEN COUNT(*) > 0 THEN 
            (COUNT(CASE WHEN s.cliente_acepto = true THEN 1 END)::float / COUNT(*)::float) * 100
        ELSE 0 
    END as tasa_aceptacion_pct,
    CASE 
        WHEN COUNT(DISTINCT o.id) > 0 THEN 
            (COUNT(CASE WHEN o.estado = 'GANADORA' THEN 1 END)::float / COUNT(DISTINCT o.id)::float) * 100
        ELSE 0 
    END as tasa_conversion_ofertas_pct,
    CASE 
        WHEN COUNT(*) > 0 THEN 
            COUNT(DISTINCT o.id)::float / COUNT(*)::float
        ELSE 0 
    END as ofertas_promedio_por_solicitud
FROM solicitudes s
LEFT JOIN ofertas o ON s.id = o.solicitud_id
LEFT JOIN ofertas_detalle od ON o.id = od.oferta_id
LEFT JOIN repuestos_solicitados rs ON s.id = rs.solicitud_id
GROUP BY DATE_TRUNC('month', s.created_at)
ORDER BY mes DESC;

-- Create enhanced mv_ranking_asesores with comprehensive advisor metrics
CREATE MATERIALIZED VIEW mv_ranking_asesores AS
SELECT 
    a.id as asesor_id,
    u.nombre as asesor_nombre,
    u.email as asesor_email,
    a.ciudad,
    a.departamento,
    a.punto_venta,
    a.confianza,
    a.nivel_actual,
    a.estado as estado_asesor,
    a.actividad_reciente_pct,
    a.desempeno_historico_pct,
    -- Métricas de ofertas históricas (últimos 30 días)
    COUNT(oh.id) as ofertas_historicas_total,
    COUNT(CASE WHEN oh.adjudicada = true THEN 1 END) as ofertas_ganadoras,
    COUNT(CASE WHEN oh.aceptada_cliente = true THEN 1 END) as ofertas_aceptadas_cliente,
    COUNT(CASE WHEN oh.entrega_exitosa = true THEN 1 END) as entregas_exitosas,
    AVG(oh.tiempo_respuesta_seg) as tiempo_promedio_respuesta_seg,
    AVG(oh.monto_total) as monto_promedio_ofertas,
    SUM(oh.monto_total) as volumen_total_ofertas,
    -- Métricas de confianza y auditoría
    COALESCE(AVG(at.puntaje_confianza), a.confianza) as confianza_auditada,
    COUNT(DISTINCT at.id) as auditorias_realizadas,
    MAX(at.fecha_revision) as ultima_auditoria,
    -- Métricas de respuesta a notificaciones (últimos 30 días)
    COUNT(hr.id) as notificaciones_recibidas,
    COUNT(CASE WHEN hr.respondio = true THEN 1 END) as notificaciones_respondidas,
    AVG(hr.tiempo_respuesta_seg) as tiempo_promedio_respuesta_notif_seg,
    -- Tasa de respuesta calculada
    CASE 
        WHEN COUNT(hr.id) > 0 THEN 
            (COUNT(CASE WHEN hr.respondio = true THEN 1 END)::float / COUNT(hr.id)::float) * 100
        ELSE 0 
    END as tasa_respuesta_pct,
    -- Tasa de conversión de ofertas
    CASE 
        WHEN COUNT(oh.id) > 0 THEN 
            (COUNT(CASE WHEN oh.adjudicada = true THEN 1 END)::float / COUNT(oh.id)::float) * 100
        ELSE 0 
    END as tasa_conversion_ofertas_pct,
    -- Tasa de éxito completo (oferta ganadora + aceptada + entregada)
    CASE 
        WHEN COUNT(oh.id) > 0 THEN 
            (COUNT(CASE WHEN oh.entrega_exitosa = true THEN 1 END)::float / COUNT(oh.id)::float) * 100
        ELSE 0 
    END as tasa_exito_completo_pct,
    -- Rankings
    RANK() OVER (
        PARTITION BY a.ciudad 
        ORDER BY COUNT(CASE WHEN oh.adjudicada = true THEN 1 END) DESC,
                 AVG(oh.tiempo_respuesta_seg) ASC NULLS LAST,
                 a.confianza DESC
    ) as ranking_ciudad,
    RANK() OVER (
        ORDER BY COUNT(CASE WHEN oh.adjudicada = true THEN 1 END) DESC,
                 AVG(oh.tiempo_respuesta_seg) ASC NULLS LAST,
                 a.confianza DESC
    ) as ranking_nacional,
    -- Percentiles de desempeño
    PERCENT_RANK() OVER (
        PARTITION BY a.ciudad 
        ORDER BY COUNT(CASE WHEN oh.adjudicada = true THEN 1 END)
    ) * 100 as percentil_ofertas_ganadoras_ciudad,
    PERCENT_RANK() OVER (
        ORDER BY COUNT(CASE WHEN oh.adjudicada = true THEN 1 END)
    ) * 100 as percentil_ofertas_ganadoras_nacional,
    -- Timestamp de cálculo
    NOW() as calculado_at
FROM asesores a
INNER JOIN usuarios u ON a.usuario_id = u.id
LEFT JOIN ofertas_historicas oh ON a.id = oh.asesor_id 
    AND oh.fecha >= NOW() - INTERVAL '30 days'
LEFT JOIN auditoria_tiendas at ON a.id = at.asesor_id
    AND at.fecha_revision >= NOW() - INTERVAL '90 days'
LEFT JOIN historial_respuestas_ofertas hr ON a.id = hr.asesor_id
    AND hr.fecha_envio >= NOW() - INTERVAL '30 days'
WHERE a.estado = 'ACTIVO'
GROUP BY a.id, u.nombre, u.email, a.ciudad, a.departamento, a.punto_venta,
         a.confianza, a.nivel_actual, a.estado, a.actividad_reciente_pct, 
         a.desempeno_historico_pct
ORDER BY ranking_nacional;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_mv_metricas_mensuales_mes 
ON mv_metricas_mensuales(mes);

CREATE INDEX IF NOT EXISTS idx_mv_metricas_mensuales_solicitudes_creadas 
ON mv_metricas_mensuales(solicitudes_creadas);

CREATE INDEX IF NOT EXISTS idx_mv_ranking_asesores_ciudad 
ON mv_ranking_asesores(ciudad);

CREATE INDEX IF NOT EXISTS idx_mv_ranking_asesores_ranking_ciudad 
ON mv_ranking_asesores(ranking_ciudad);

CREATE INDEX IF NOT EXISTS idx_mv_ranking_asesores_ranking_nacional 
ON mv_ranking_asesores(ranking_nacional);

CREATE INDEX IF NOT EXISTS idx_mv_ranking_asesores_asesor_id 
ON mv_ranking_asesores(asesor_id);

CREATE INDEX IF NOT EXISTS idx_mv_ranking_asesores_ofertas_ganadoras 
ON mv_ranking_asesores(ofertas_ganadoras);

CREATE INDEX IF NOT EXISTS idx_mv_ranking_asesores_tasa_respuesta 
ON mv_ranking_asesores(tasa_respuesta_pct);

-- Create or replace the refresh function with enhanced error handling and logging
CREATE OR REPLACE FUNCTION refresh_all_mv()
RETURNS TABLE(
    view_name TEXT,
    refresh_status TEXT,
    refresh_time_ms BIGINT,
    error_message TEXT,
    rows_affected BIGINT
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    duration_ms BIGINT;
    row_count BIGINT;
BEGIN
    -- Refresh mv_metricas_mensuales
    BEGIN
        start_time := clock_timestamp();
        REFRESH MATERIALIZED VIEW mv_metricas_mensuales;
        end_time := clock_timestamp();
        duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
        
        -- Get row count
        SELECT COUNT(*) INTO row_count FROM mv_metricas_mensuales;
        
        RETURN QUERY SELECT 
            'mv_metricas_mensuales'::TEXT,
            'SUCCESS'::TEXT,
            duration_ms,
            NULL::TEXT,
            row_count;
            
    EXCEPTION WHEN OTHERS THEN
        end_time := clock_timestamp();
        duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
        
        RETURN QUERY SELECT 
            'mv_metricas_mensuales'::TEXT,
            'ERROR'::TEXT,
            duration_ms,
            SQLERRM::TEXT,
            0::BIGINT;
    END;
    
    -- Refresh mv_ranking_asesores
    BEGIN
        start_time := clock_timestamp();
        REFRESH MATERIALIZED VIEW mv_ranking_asesores;
        end_time := clock_timestamp();
        duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
        
        -- Get row count
        SELECT COUNT(*) INTO row_count FROM mv_ranking_asesores;
        
        RETURN QUERY SELECT 
            'mv_ranking_asesores'::TEXT,
            'SUCCESS'::TEXT,
            duration_ms,
            NULL::TEXT,
            row_count;
            
    EXCEPTION WHEN OTHERS THEN
        end_time := clock_timestamp();
        duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
        
        RETURN QUERY SELECT 
            'mv_ranking_asesores'::TEXT,
            'ERROR'::TEXT,
            duration_ms,
            SQLERRM::TEXT,
            0::BIGINT;
    END;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Create function to get materialized view statistics
CREATE OR REPLACE FUNCTION get_mv_stats()
RETURNS TABLE(
    view_name TEXT,
    row_count BIGINT,
    size_bytes BIGINT,
    last_refresh TIMESTAMP WITH TIME ZONE,
    is_populated BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mv.matviewname::TEXT as view_name,
        COALESCE(
            (SELECT reltuples::BIGINT 
             FROM pg_class 
             WHERE relname = mv.matviewname), 
            0
        ) as row_count,
        COALESCE(
            (SELECT pg_total_relation_size(oid) 
             FROM pg_class 
             WHERE relname = mv.matviewname), 
            0
        ) as size_bytes,
        NULL::TIMESTAMP WITH TIME ZONE as last_refresh, -- PostgreSQL doesn't track this natively
        mv.ispopulated
    FROM pg_matviews mv
    WHERE mv.matviewname IN ('mv_metricas_mensuales', 'mv_ranking_asesores')
    ORDER BY mv.matviewname;
END;
$$ LANGUAGE plpgsql;

-- Initial population of materialized views
SELECT refresh_all_mv();

-- Create pg_cron job for automatic refresh at 1 AM daily
-- Note: This requires pg_cron extension to be installed and configured
-- Uncomment the following line if pg_cron is available:
-- SELECT cron.schedule('refresh-materialized-views', '0 1 * * *', 'SELECT refresh_all_mv();');

COMMIT;