-- Script SQL para generar datos históricos simulados
-- Se ejecuta directamente en PostgreSQL

-- Generar historial de respuestas (5-20 por asesor, últimos 30 días)
DO $$
DECLARE
    asesor_record RECORD;
    num_respuestas INT;
    i INT;
    fecha_envio TIMESTAMP;
    respondio BOOLEAN;
    tiempo_respuesta INT;
BEGIN
    FOR asesor_record IN SELECT id FROM asesores WHERE estado = 'ACTIVO' LOOP
        num_respuestas := 5 + floor(random() * 16)::INT; -- 5 a 20
        
        FOR i IN 1..num_respuestas LOOP
            fecha_envio := NOW() - (random() * INTERVAL '30 days');
            respondio := random() > 0.3; -- 70% responde
            tiempo_respuesta := CASE WHEN respondio THEN 300 + floor(random() * 6900)::INT ELSE NULL END;
            
            INSERT INTO historial_respuestas_ofertas (asesor_id, fecha_envio, respondio, tiempo_respuesta_seg)
            VALUES (asesor_record.id, fecha_envio, respondio, tiempo_respuesta);
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Historial de respuestas generado';
END $$;

-- Generar ofertas históricas (10-50 por asesor, últimos 6 meses)
DO $$
DECLARE
    asesor_record RECORD;
    num_ofertas INT;
    i INT;
    fecha DATE;
    monto DECIMAL(12,2);
    adjudicada BOOLEAN;
    aceptada BOOLEAN;
    exitosa BOOLEAN;
    tiempo_respuesta INT;
BEGIN
    FOR asesor_record IN SELECT id FROM asesores WHERE estado = 'ACTIVO' LOOP
        num_ofertas := 10 + floor(random() * 41)::INT; -- 10 a 50
        
        FOR i IN 1..num_ofertas LOOP
            fecha := CURRENT_DATE - (random() * 180)::INT;
            monto := 100000 + (random() * 4900000)::DECIMAL(12,2);
            adjudicada := random() > 0.7; -- 30% gana
            aceptada := adjudicada AND random() > 0.2; -- 80% de ganadoras son aceptadas
            exitosa := aceptada AND random() > 0.1; -- 90% de aceptadas son exitosas
            tiempo_respuesta := 300 + floor(random() * 6900)::INT;
            
            INSERT INTO ofertas_historicas (asesor_id, fecha, monto, adjudicada, aceptada_cliente, entrega_exitosa, tiempo_respuesta_seg)
            VALUES (asesor_record.id, fecha, monto, adjudicada, aceptada, exitosa, tiempo_respuesta);
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Ofertas históricas generadas';
END $$;

-- Generar auditorías de confianza (50% de asesores, últimos 25 días)
DO $$
DECLARE
    asesor_record RECORD;
    fecha_revision TIMESTAMP;
    puntaje DECIMAL(3,2);
BEGIN
    FOR asesor_record IN SELECT id FROM asesores WHERE estado = 'ACTIVO' AND random() > 0.5 LOOP
        fecha_revision := NOW() - (random() * INTERVAL '25 days');
        puntaje := 2.5 + (random() * 2.5)::DECIMAL(3,2); -- 2.5 a 5.0
        
        INSERT INTO auditorias_tiendas (asesor_id, fecha_revision, puntaje_confianza, vigencia_dias, observaciones)
        VALUES (asesor_record.id, fecha_revision, puntaje, 30, 'Auditoría automática - Puntaje: ' || puntaje);
    END LOOP;
    
    RAISE NOTICE 'Auditorías generadas';
END $$;

-- Mostrar resumen
SELECT 
    (SELECT COUNT(*) FROM historial_respuestas_ofertas) as historial_respuestas,
    (SELECT COUNT(*) FROM ofertas_historicas) as ofertas_historicas,
    (SELECT COUNT(*) FROM auditorias_tiendas) as auditorias;
