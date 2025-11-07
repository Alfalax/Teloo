export interface Asesor {
  id: string;
  usuario: {
    id: string;
    nombre: string;
    apellido: string;
    email: string;
    telefono: string;
    estado: 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO' | 'BLOQUEADO';
  };
  ciudad: string;
  departamento: string;
  punto_venta: string;
  direccion_punto_venta?: string;
  confianza: number;
  nivel_actual: number;
  actividad_reciente_pct: number;
  desempeno_historico_pct: number;
  estado: 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO';
  total_ofertas: number;
  ofertas_ganadoras: number;
  monto_total_ventas: number;
  created_at: string;
  updated_at: string;
}

export interface AsesorCreate {
  nombre: string;
  apellido: string;
  email: string;
  telefono: string;
  ciudad: string;
  departamento: string;
  punto_venta: string;
  direccion_punto_venta?: string;
  password: string;
}

export interface AsesorUpdate {
  nombre?: string;
  apellido?: string;
  email?: string;
  telefono?: string;
  ciudad?: string;
  departamento?: string;
  punto_venta?: string;
  direccion_punto_venta?: string;
  estado?: 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO';
}

export interface AsesoresKPIs {
  total_asesores_habilitados: {
    valor: number;
    cambio_porcentual: number;
    periodo: string;
  };
  total_puntos_venta: {
    valor: number;
    cambio_porcentual: number;
    periodo: string;
  };
  cobertura_nacional: {
    valor: number;
    cambio_porcentual: number;
    periodo: string;
  };
}

export interface AsesoresResponse {
  success: boolean;
  data: Asesor[];
  total: number;
  page: number;
  limit: number;
}

export interface AsesorResponse {
  success: boolean;
  data: Asesor;
}

export interface AsesoresKPIsResponse {
  success: boolean;
  data: AsesoresKPIs;
  timestamp: string;
}

export interface ExcelImportResult {
  success: boolean;
  message: string;
  total_procesados: number;
  exitosos: number;
  errores: number;
  detalles_errores?: Array<{
    fila: number;
    errores: string[];
  }>;
}

export interface ExcelExportData {
  nombre: string;
  apellido: string;
  email: string;
  telefono: string;
  ciudad: string;
  departamento: string;
  punto_venta: string;
  direccion_punto_venta: string;
  estado: string;
  confianza: number;
  nivel_actual: number;
  actividad_reciente_pct: number;
  desempeno_historico_pct: number;
  total_ofertas: number;
  ofertas_ganadoras: number;
  monto_total_ventas: number;
  tasa_adjudicacion: number;
  created_at: string;
}