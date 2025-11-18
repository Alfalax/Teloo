export interface Solicitud {
  id: string;
  cliente_id: string;
  cliente_nombre?: string;
  cliente_telefono?: string;
  estado: 'ABIERTA' | 'EVALUADA' | 'CERRADA_SIN_OFERTAS';
  nivel_actual: number;
  ciudad_origen: string;
  departamento_origen: string;
  repuestos_solicitados: RepuestoSolicitado[];
  // Alias for backward compatibility
  repuestos?: RepuestoSolicitado[];
  tiempo_restante_horas?: number; // Deprecated - usar tiempo_restante_minutos
  tiempo_restante_minutos?: number; // Tiempo restante en minutos
  tiempo_total_nivel_minutos?: number; // Tiempo total configurado para el nivel actual en minutos
  // Backend returns fecha_creacion
  fecha_creacion?: string;
  // Alias for backward compatibility
  created_at?: string;
  updated_at?: string;
}

export interface RepuestoSolicitado {
  id: string;
  solicitud_id: string;
  nombre: string;
  codigo?: string;
  marca_vehiculo: string;
  linea_vehiculo: string;
  anio_vehiculo: number;
  cantidad: number;
  observaciones?: string;
}

export interface Oferta {
  id: string;
  solicitud_id: string;
  asesor_id: string;
  tiempo_entrega_dias: number;
  observaciones?: string;
  estado: 'ENVIADA' | 'GANADORA' | 'NO_SELECCIONADA' | 'EXPIRADA' | 'RECHAZADA' | 'ACEPTADA';
  detalles: OfertaDetalle[];
  created_at: string;
  updated_at: string;
}

export interface OfertaDetalle {
  id: string;
  oferta_id: string;
  repuesto_solicitado_id: string;
  repuesto_nombre?: string;
  precio_unitario: number;
  cantidad: number;
  garantia_meses: number;
  tiempo_entrega_dias: number;
  origen: 'FORM' | 'EXCEL';
}

export interface CreateOfertaRequest {
  solicitud_id: string;
  tiempo_entrega_dias: number;
  observaciones?: string;
  detalles: CreateOfertaDetalle[];
}

export interface CreateOfertaDetalle {
  repuesto_solicitado_id: string;
  precio_unitario: number;
  cantidad: number;
  garantia_meses: number;
}

export type EstadoOfertaAsesor = 
  | 'ABIERTA'           // No ha enviado oferta
  | 'ENVIADA'           // Oferta enviada
  | 'GANADORA'          // Ganó repuestos
  | 'NO_SELECCIONADA'   // No ganó
  | 'ACEPTADA'          // Cliente aceptó
  | 'RECHAZADA'         // Cliente rechazó
  | 'EXPIRADA';         // Expiró

export interface SolicitudConOferta extends Solicitud {
  mi_oferta?: Oferta;
  oferta_ganadora?: Oferta;
  cliente_contacto?: {
    nombre: string;
    telefono: string;
    ciudad: string;
  };
  // Estado de la oferta desde perspectiva del asesor
  estado_oferta_asesor?: EstadoOfertaAsesor;
  repuestos_ganados?: number;
  repuestos_totales_ofertados?: number;
}
