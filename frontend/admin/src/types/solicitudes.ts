/**
 * Types for Solicitudes (Requests) module
 * Based on backend models: Solicitud and RepuestoSolicitado
 */

export type EstadoSolicitud =
  | "ABIERTA"
  | "EVALUADA"
  | "OFERTAS_ACEPTADAS"
  | "OFERTAS_RECHAZADAS"
  | "CERRADA_SIN_OFERTAS";

export interface RepuestoSolicitado {
  id?: string;
  nombre: string;
  codigo?: string;
  descripcion?: string;
  cantidad: number;
  marca_vehiculo: string;
  linea_vehiculo: string;
  anio_vehiculo: number;
  observaciones?: string;
  es_urgente: boolean;
}

export interface Solicitud {
  id: string;
  cliente_id: string;
  cliente_nombre?: string;
  cliente_telefono?: string;
  estado: EstadoSolicitud;
  nivel_actual: number;
  ciudad_origen: string;
  departamento_origen: string;
  ofertas_minimas_deseadas: number;
  timeout_horas: number;
  fecha_creacion: string;
  fecha_escalamiento?: string;
  fecha_evaluacion?: string;
  fecha_expiracion?: string;
  total_repuestos: number;
  monto_total_adjudicado: number;
  repuestos_solicitados?: RepuestoSolicitado[];
}

export interface CreateSolicitudData {
  cliente: {
    nombre: string;
    telefono: string;
    email?: string;
  };
  municipio_id: string;
  ciudad_origen: string;
  departamento_origen: string;
  repuestos: Omit<RepuestoSolicitado, "id">[];
}

export interface SolicitudesFilters {
  estado?: EstadoSolicitud;
  search?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  ciudad?: string;
  departamento?: string;
}

export interface SolicitudesPaginatedResponse {
  items: Solicitud[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SolicitudesStats {
  total: number;
  abiertas: number;
  evaluadas: number;
  aceptadas: number;
  rechazadas_expiradas: number;
}
