-- TeLOO V3 Database Initialization Script
-- This script creates the initial database structure and default data

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS teloo;
SET search_path TO teloo, public;

-- Create enum types
CREATE TYPE estado_solicitud AS ENUM (
    'ABIERTA', 
    'EVALUADA', 
    'ACEPTADA', 
    'RECHAZADA', 
    'EXPIRADA', 
    'CERRADA_SIN_OFERTAS'
);

CREATE TYPE estado_oferta AS ENUM (
    'ENVIADA', 
    'GANADORA', 
    'NO_SELECCIONADA', 
    'EXPIRADA', 
    'RECHAZADA', 
    'ACEPTADA'
);

CREATE TYPE estado_asesor AS ENUM (
    'ACTIVO', 
    'INACTIVO', 
    'SUSPENDIDO'
);

CREATE TYPE rol_usuario AS ENUM (
    'ADMIN', 
    'ADVISOR', 
    'ANALYST', 
    'SUPPORT', 
    'CLIENT'
);

CREATE TYPE tipo_pqr AS ENUM (
    'PETICION', 
    'QUEJA', 
    'RECLAMO'
);

CREATE TYPE prioridad_pqr AS ENUM (
    'BAJA', 
    'MEDIA', 
    'ALTA', 
    'CRITICA'
);

CREATE TYPE estado_pqr AS ENUM (
    'ABIERTA', 
    'EN_PROCESO', 
    'CERRADA'
);

CREATE TYPE tipo_transaccion AS ENUM (
    'VENTA', 
    'COMISION', 
    'DEVOLUCION'
);

CREATE TYPE estado_transaccion AS ENUM (
    'PENDIENTE', 
    'COMPLETADA', 
    'FALLIDA'
);

-- Create core tables
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    nombre VARCHAR(255) NOT NULL,
    rol rol_usuario NOT NULL DEFAULT 'CLIENT',
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    telefono VARCHAR(20) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    ciudad VARCHAR(255) NOT NULL,
    departamento VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS asesores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    ciudad VARCHAR(255) NOT NULL,
    departamento VARCHAR(255),
    punto_venta VARCHAR(255),
    confianza DECIMAL(3,2) DEFAULT 3.0 CHECK (confianza >= 1.0 AND confianza <= 5.0),
    nivel_actual INTEGER DEFAULT 3 CHECK (nivel_actual >= 1 AND nivel_actual <= 5),
    estado estado_asesor DEFAULT 'ACTIVO',
    actividad_reciente_pct DECIMAL(5,2) DEFAULT 0.0,
    desempeno_historico_pct DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create geographic support tables
CREATE TABLE IF NOT EXISTS areas_metropolitanas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    area_metropolitana VARCHAR(255) NOT NULL,
    ciudad_nucleo VARCHAR(255) NOT NULL,
    municipio_norm VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hubs_logisticos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    municipio_norm VARCHAR(255) NOT NULL,
    hub_asignado_norm VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create solicitudes and related tables
CREATE TABLE IF NOT EXISTS solicitudes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE,
    estado estado_solicitud DEFAULT 'ABIERTA',
    nivel_actual INTEGER DEFAULT 1 CHECK (nivel_actual >= 1 AND nivel_actual <= 5),
    ciudad_origen VARCHAR(255) NOT NULL,
    departamento_origen VARCHAR(255),
    metadata_json JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS repuestos_solicitados (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    solicitud_id UUID REFERENCES solicitudes(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    codigo VARCHAR(100),
    marca_vehiculo VARCHAR(100) NOT NULL,
    linea_vehiculo VARCHAR(100) NOT NULL,
    anio_vehiculo INTEGER NOT NULL CHECK (anio_vehiculo >= 1980 AND anio_vehiculo <= 2025),
    cantidad INTEGER DEFAULT 1 CHECK (cantidad > 0),
    observaciones TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create ofertas and related tables
CREATE TABLE IF NOT EXISTS ofertas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    solicitud_id UUID REFERENCES solicitudes(id) ON DELETE CASCADE,
    asesor_id UUID REFERENCES asesores(id) ON DELETE CASCADE,
    tiempo_entrega_dias INTEGER NOT NULL CHECK (tiempo_entrega_dias >= 0 AND tiempo_entrega_dias <= 90),
    observaciones TEXT,
    estado estado_oferta DEFAULT 'ENVIADA',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ofertas_detalle (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    oferta_id UUID REFERENCES ofertas(id) ON DELETE CASCADE,
    repuesto_solicitado_id UUID REFERENCES repuestos_solicitados(id) ON DELETE CASCADE,
    precio_unitario DECIMAL(12,2) NOT NULL CHECK (precio_unitario >= 1000 AND precio_unitario <= 50000000),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    garantia_meses INTEGER NOT NULL CHECK (garantia_meses >= 1 AND garantia_meses <= 60),
    tiempo_entrega_dias INTEGER NOT NULL CHECK (tiempo_entrega_dias >= 0 AND tiempo_entrega_dias <= 90),
    origen VARCHAR(20) DEFAULT 'FORM' CHECK (origen IN ('FORM', 'EXCEL')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create evaluation and adjudication tables
CREATE TABLE IF NOT EXISTS evaluaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    solicitud_id UUID REFERENCES solicitudes(id) ON DELETE CASCADE,
    duracion_ms INTEGER,
    resultado_json JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS adjudicaciones_repuesto (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    solicitud_id UUID REFERENCES solicitudes(id) ON DELETE CASCADE,
    oferta_id UUID REFERENCES ofertas(id) ON DELETE CASCADE,
    repuesto_solicitado_id UUID REFERENCES repuestos_solicitados(id) ON DELETE CASCADE,
    puntaje_obtenido DECIMAL(5,2) NOT NULL,
    precio_adjudicado DECIMAL(12,2) NOT NULL,
    tiempo_entrega_adjudicado INTEGER NOT NULL,
    garantia_adjudicada INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create escalamiento temporal table
CREATE TABLE IF NOT EXISTS evaluaciones_asesores_temp (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    solicitud_id UUID REFERENCES solicitudes(id) ON DELETE CASCADE,
    asesor_id UUID REFERENCES asesores(id) ON DELETE CASCADE,
    proximidad DECIMAL(3,2) NOT NULL,
    actividad_reciente_5 DECIMAL(3,2) NOT NULL,
    desempeno_historico_5 DECIMAL(3,2) NOT NULL,
    nivel_confianza DECIMAL(3,2) NOT NULL,
    puntaje_total DECIMAL(5,2) NOT NULL,
    nivel_entrega INTEGER NOT NULL CHECK (nivel_entrega >= 1 AND nivel_entrega <= 5),
    canal VARCHAR(20) NOT NULL,
    tiempo_espera_min INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create configuration table
CREATE TABLE IF NOT EXISTS parametros_config (
    clave VARCHAR(100) PRIMARY KEY,
    valor_json JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analytics tables
CREATE TABLE IF NOT EXISTS historial_respuestas_ofertas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asesor_id UUID REFERENCES asesores(id) ON DELETE CASCADE,
    solicitud_id UUID REFERENCES solicitudes(id) ON DELETE CASCADE,
    fecha_envio TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_vista TIMESTAMP WITH TIME ZONE,
    respondio BOOLEAN DEFAULT false,
    tiempo_respuesta_seg INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ofertas_historicas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asesor_id UUID REFERENCES asesores(id) ON DELETE CASCADE,
    solicitud_id UUID REFERENCES solicitudes(id) ON DELETE CASCADE,
    fecha TIMESTAMP WITH TIME ZONE NOT NULL,
    adjudicada BOOLEAN DEFAULT false,
    aceptada_cliente BOOLEAN DEFAULT false,
    entrega_exitosa BOOLEAN DEFAULT false,
    tiempo_respuesta_seg INTEGER,
    monto_total DECIMAL(12,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS auditoria_tiendas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asesor_id UUID REFERENCES asesores(id) ON DELETE CASCADE,
    fecha_revision TIMESTAMP WITH TIME ZONE NOT NULL,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('APROBADA', 'OBSERVACIONES', 'RECHAZADA')),
    puntaje_confianza DECIMAL(3,2) NOT NULL CHECK (puntaje_confianza >= 1.0 AND puntaje_confianza <= 5.0),
    observaciones TEXT,
    auditor_id UUID REFERENCES usuarios(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eventos_sistema (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tipo_evento VARCHAR(100) NOT NULL,
    entidad VARCHAR(100) NOT NULL,
    entidad_id UUID NOT NULL,
    datos_evento JSONB DEFAULT '{}',
    usuario_id UUID REFERENCES usuarios(id),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS metricas_calculadas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre_metrica VARCHAR(100) NOT NULL,
    periodo VARCHAR(20) NOT NULL,
    fecha_periodo DATE NOT NULL,
    valor_numerico DECIMAL(15,4),
    valor_json JSONB DEFAULT '{}',
    calculado_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create PQR and notification tables
CREATE TABLE IF NOT EXISTS pqr (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE,
    tipo tipo_pqr NOT NULL,
    prioridad prioridad_pqr DEFAULT 'MEDIA',
    estado estado_pqr DEFAULT 'ABIERTA',
    resumen VARCHAR(255) NOT NULL,
    detalle TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notificaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    mensaje TEXT NOT NULL,
    leida BOOLEAN DEFAULT false,
    datos_adicionales JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create session and transaction tables
CREATE TABLE IF NOT EXISTS sesiones_usuario (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    inicio_sesion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fin_sesion TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT,
    duracion_seg INTEGER,
    acciones_realizadas INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transacciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    solicitud_id UUID REFERENCES solicitudes(id) ON DELETE CASCADE,
    asesor_id UUID REFERENCES asesores(id) ON DELETE CASCADE,
    tipo tipo_transaccion NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    estado estado_transaccion DEFAULT 'PENDIENTE',
    fecha_transaccion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    referencia_externa VARCHAR(255),
    metadata_json JSONB DEFAULT '{}'
);

-- Create audit log table
CREATE TABLE IF NOT EXISTS logs_auditoria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id UUID REFERENCES usuarios(id),
    accion VARCHAR(100) NOT NULL,
    entidad VARCHAR(100) NOT NULL,
    entidad_id UUID NOT NULL,
    diff_json JSONB DEFAULT '{}',
    ts TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_solicitudes_estado_fecha ON solicitudes(estado, created_at);
CREATE INDEX IF NOT EXISTS idx_ofertas_estado_fecha ON ofertas(estado, created_at);
CREATE INDEX IF NOT EXISTS idx_ofertas_solicitud_asesor ON ofertas(solicitud_id, asesor_id);
CREATE INDEX IF NOT EXISTS idx_repuestos_solicitud ON repuestos_solicitados(solicitud_id);
CREATE INDEX IF NOT EXISTS idx_ofertas_detalle_oferta ON ofertas_detalle(oferta_id);
CREATE INDEX IF NOT EXISTS idx_asesores_ciudad_estado ON asesores(ciudad, estado);
CREATE INDEX IF NOT EXISTS idx_evaluaciones_asesores_temp_solicitud ON evaluaciones_asesores_temp(solicitud_id);
CREATE INDEX IF NOT EXISTS idx_historial_respuestas_asesor_fecha ON historial_respuestas_ofertas(asesor_id, fecha_envio);
CREATE INDEX IF NOT EXISTS idx_ofertas_historicas_asesor_fecha ON ofertas_historicas(asesor_id, fecha);
CREATE INDEX IF NOT EXISTS idx_eventos_sistema_tipo_fecha ON eventos_sistema(tipo_evento, created_at);
CREATE INDEX IF NOT EXISTS idx_metricas_calculadas_nombre_periodo ON metricas_calculadas(nombre_metrica, periodo, fecha_periodo);
CREATE INDEX IF NOT EXISTS idx_areas_metropolitanas_municipio ON areas_metropolitanas(municipio_norm);
CREATE INDEX IF NOT EXISTS idx_hubs_logisticos_municipio ON hubs_logisticos(municipio_norm);

-- Insert default configuration parameters
INSERT INTO parametros_config (clave, valor_json) VALUES
('pesos_escalamiento', '{"proximidad": 0.40, "actividad": 0.25, "desempeno": 0.20, "confianza": 0.15}'),
('umbrales_niveles', '{"nivel1_min": 4.5, "nivel2_min": 4.0, "nivel3_min": 3.5, "nivel4_min": 3.0}'),
('tiempos_espera_minutos', '{"nivel1": 15, "nivel2": 20, "nivel3": 25, "nivel4": 30}'),
('canales_notificacion', '{"nivel1": "whatsapp", "nivel2": "whatsapp", "nivel3": "push", "nivel4": "push"}'),
('pesos_evaluacion', '{"precio": 0.50, "tiempo": 0.35, "garantia": 0.15}'),
('ofertas_minimas_deseadas', '2'),
('timeout_evaluacion_segundos', '5'),
('periodo_actividad_reciente_dias', '30'),
('periodo_desempeno_historico_meses', '6'),
('vigencia_auditoria_dias', '30'),
('cobertura_minima_porcentaje', '50')
ON CONFLICT (clave) DO NOTHING;

-- Create default admin user
INSERT INTO usuarios (id, email, nombre, rol) VALUES
(uuid_generate_v4(), 'admin@teloo.com', 'Administrador TeLOO', 'ADMIN')
ON CONFLICT (email) DO NOTHING;

-- Create materialized views for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_metricas_mensuales AS
SELECT 
    DATE_TRUNC('month', created_at) as mes,
    COUNT(*) as solicitudes_creadas,
    COUNT(CASE WHEN estado = 'ACEPTADA' THEN 1 END) as solicitudes_aceptadas,
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as tiempo_promedio_cierre_seg
FROM solicitudes 
GROUP BY DATE_TRUNC('month', created_at);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ranking_asesores AS
SELECT 
    a.id,
    a.ciudad,
    COUNT(oh.adjudicada) as ofertas_ganadoras,
    AVG(oh.tiempo_respuesta_seg) as tiempo_promedio_respuesta,
    AVG(at.puntaje_confianza) as confianza_promedio,
    RANK() OVER (PARTITION BY a.ciudad ORDER BY COUNT(oh.adjudicada) DESC) as ranking_ciudad
FROM asesores a
LEFT JOIN ofertas_historicas oh ON a.id = oh.asesor_id 
    AND oh.fecha >= NOW() - INTERVAL '30 days'
LEFT JOIN auditoria_tiendas at ON a.id = at.asesor_id
WHERE a.estado = 'ACTIVO'
GROUP BY a.id, a.ciudad;

-- Create function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_all_mv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_metricas_mensuales;
    REFRESH MATERIALIZED VIEW mv_ranking_asesores;
END;
$$ LANGUAGE plpgsql;

-- Schedule materialized view refresh (requires pg_cron extension)
-- SELECT cron.schedule('refresh-mv', '0 1 * * *', 'SELECT refresh_all_mv();');

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_usuarios_updated_at BEFORE UPDATE ON usuarios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_clientes_updated_at BEFORE UPDATE ON clientes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_asesores_updated_at BEFORE UPDATE ON asesores FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_solicitudes_updated_at BEFORE UPDATE ON solicitudes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ofertas_updated_at BEFORE UPDATE ON ofertas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pqr_updated_at BEFORE UPDATE ON pqr FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_parametros_config_updated_at BEFORE UPDATE ON parametros_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;