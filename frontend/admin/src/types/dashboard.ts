export interface KPIData {
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
  icon?: React.ComponentType<any>;
}

export interface ChartDataPoint {
  date: string;
  solicitudes: number;
  aceptadas: number;
  cerradas: number;
}

export interface SolicitudAbierta {
  id: string;
  codigo: string;
  vehiculo: string;
  cliente: string;
  ciudad: string;
  tiempo_proceso_horas: number;
  created_at: string;
}

export interface DashboardData {
  kpis: {
    ofertas_totales_asignadas: {
      valor: number;
      cambio_porcentual: number;
      periodo: string;
    };
    monto_total_aceptado: {
      valor: number;
      cambio_porcentual: number;
      periodo: string;
    };
    solicitudes_abiertas: {
      valor: number;
      cambio_porcentual: number;
      periodo: string;
    };
    tasa_conversion: {
      valor: number;
      cambio_porcentual: number;
      periodo: string;
    };
  };
  graficos_mes: ChartDataPoint[];
  top_solicitudes_abiertas: SolicitudAbierta[];
}

export interface AnalyticsResponse<T> {
  success: boolean;
  data: T;
  timestamp: string;
  periodo?: {
    inicio: string;
    fin: string;
  };
}