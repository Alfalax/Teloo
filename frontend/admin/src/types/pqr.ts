export interface Cliente {
  id: string;
  nombre_completo: string;
  telefono: string;
  email?: string;
}

export interface Usuario {
  id: string;
  nombre_completo: string;
  email: string;
}

export interface PQR {
  id: string;
  tipo: 'PETICION' | 'QUEJA' | 'RECLAMO';
  prioridad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA';
  estado: 'ABIERTA' | 'EN_PROCESO' | 'CERRADA';
  resumen: string;
  detalle: string;
  cliente: Cliente;
  respuesta?: string;
  fecha_respuesta?: string;
  respondido_por?: Usuario;
  tiempo_resolucion_horas?: number;
  created_at: string;
  updated_at: string;
}

export interface PQRCreate {
  cliente_id: string;
  tipo: 'PETICION' | 'QUEJA' | 'RECLAMO';
  prioridad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA';
  resumen: string;
  detalle: string;
}

export interface PQRUpdate {
  tipo?: 'PETICION' | 'QUEJA' | 'RECLAMO';
  prioridad?: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA';
  resumen?: string;
  detalle?: string;
  respuesta?: string;
}

export interface PQRList {
  data: PQR[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface PQRMetrics {
  total_abiertas: number;
  total_en_proceso: number;
  total_cerradas: number;
  tiempo_promedio_resolucion_horas: number;
  pqrs_alta_prioridad: number;
  pqrs_criticas: number;
  tasa_resolucion_24h: number;
  distribucion_por_tipo: Record<string, number>;
  distribucion_por_prioridad: Record<string, number>;
}

export interface PQRFilters {
  search?: string;
  estado?: 'ABIERTA' | 'EN_PROCESO' | 'CERRADA';
  tipo?: 'PETICION' | 'QUEJA' | 'RECLAMO';
  prioridad?: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA';
}