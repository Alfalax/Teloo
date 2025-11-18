-- Script para verificar el sistema de eventos
-- Reemplaza SOLICITUD_ID con el ID de la solicitud que crees

\set solicitud_id 'SOLICITUD_ID'

\echo '========================================='
\echo 'VERIFICACIÓN SISTEMA DE EVENTOS'
\echo '========================================='

\echo ''
\echo '1. INFORMACIÓN DE LA SOLICITUD'
\echo '-----------------------------------------'
SELECT 
    id,
    codigo_solicitud,
    estado,
    nivel_actual,
    ciudad_origen
FROM solicitudes 
WHERE id::text LIKE :'solicitud_id' || '%';

\echo ''
\echo '2. EVALUACIONES_ASESORES_TEMP'
\echo '-----------------------------------------'
SELECT 
    COUNT(*) as total_asesores,
    COUNT(CASE WHEN fecha_notificacion IS NOT NULL THEN 1 END) as con_fecha_notificacion,
    COUNT(CASE WHEN fecha_notificacion IS NULL THEN 1 END) as sin_fecha_notificacion
FROM evaluaciones_asesores_temp 
WHERE solicitud_id::text LIKE :'solicitud_id' || '%';

\echo ''
\echo '3. OFERTAS CREADAS'
\echo '-----------------------------------------'
SELECT 
    o.id,
    o.codigo_oferta,
    a.nombre as asesor,
    o.monto_total,
    o.cantidad_repuestos,
    o.cobertura_porcentaje,
    o.estado,
    o.created_at
FROM ofertas o
INNER JOIN asesores a ON a.id = o.asesor_id
WHERE o.solicitud_id::text LIKE :'solicitud_id' || '%'
ORDER BY o.created_at;

\echo ''
\echo '4. OFERTAS_HISTORICAS'
\echo '-----------------------------------------'
SELECT 
    COUNT(*) as total_registros,
    COUNT(CASE WHEN adjudicada = true THEN 1 END) as adjudicadas,
    SUM(monto_total) as monto_total,
    AVG(tiempo_respuesta_seg) as tiempo_promedio_seg
FROM ofertas_historicas 
WHERE solicitud_id::text LIKE :'solicitud_id' || '%';

\echo ''
\echo '5. DETALLE OFERTAS_HISTORICAS'
\echo '-----------------------------------------'
SELECT 
    oh.ciudad_asesor,
    oh.monto_total,
    oh.cantidad_repuestos,
    oh.adjudicada,
    oh.tiempo_respuesta_seg,
    oh.fecha
FROM ofertas_historicas oh
WHERE oh.solicitud_id::text LIKE :'solicitud_id' || '%'
ORDER BY oh.adjudicada DESC, oh.monto_total DESC;

\echo ''
\echo '6. HISTORIAL_RESPUESTAS_OFERTAS'
\echo '-----------------------------------------'
SELECT 
    COUNT(*) as total_asesores,
    COUNT(CASE WHEN respondio = true THEN 1 END) as respondieron,
    COUNT(CASE WHEN respondio = false THEN 1 END) as no_respondieron,
    COUNT(CASE WHEN fecha_respuesta IS NOT NULL THEN 1 END) as con_fecha_respuesta,
    AVG(CASE WHEN tiempo_respuesta_seg > 0 THEN tiempo_respuesta_seg END) as tiempo_promedio_seg
FROM historial_respuestas_ofertas 
WHERE solicitud_id::text LIKE :'solicitud_id' || '%';

\echo ''
\echo '7. ASESORES QUE RESPONDIERON'
\echo '-----------------------------------------'
SELECT 
    a.nombre as asesor,
    a.ciudad,
    h.respondio,
    h.tiempo_respuesta_seg,
    h.fecha_envio,
    h.fecha_respuesta
FROM historial_respuestas_ofertas h
INNER JOIN asesores a ON a.id = h.asesor_id
WHERE h.solicitud_id::text LIKE :'solicitud_id' || '%'
  AND h.respondio = true
ORDER BY h.fecha_respuesta;

\echo ''
\echo '8. VERIFICACIÓN DE INTEGRIDAD'
\echo '-----------------------------------------'
SELECT 
    'Ofertas creadas' as tabla,
    COUNT(*) as registros
FROM ofertas 
WHERE solicitud_id::text LIKE :'solicitud_id' || '%'
UNION ALL
SELECT 
    'ofertas_historicas' as tabla,
    COUNT(*) as registros
FROM ofertas_historicas 
WHERE solicitud_id::text LIKE :'solicitud_id' || '%'
UNION ALL
SELECT 
    'historial_respuestas_ofertas (total)' as tabla,
    COUNT(*) as registros
FROM historial_respuestas_ofertas 
WHERE solicitud_id::text LIKE :'solicitud_id' || '%'
UNION ALL
SELECT 
    'historial_respuestas_ofertas (respondieron)' as tabla,
    COUNT(*) as registros
FROM historial_respuestas_ofertas 
WHERE solicitud_id::text LIKE :'solicitud_id' || '%'
  AND respondio = true;

\echo ''
\echo '========================================='
\echo 'VERIFICACIÓN COMPLETADA'
\echo '========================================='
