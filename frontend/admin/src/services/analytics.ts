import axios from 'axios';
import { DashboardData, AnalyticsResponse } from '@/types/dashboard';

// Analytics API uses a different base URL (port 8002)
const ANALYTICS_API_URL = import.meta.env.VITE_ANALYTICS_API_URL || 'http://localhost:8002';

// Create a separate axios instance for analytics with auth
const analyticsClient = axios.create({
  baseURL: `${ANALYTICS_API_URL}/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
analyticsClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
analyticsClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Dispatch logout event (handled by main apiClient)
      const event = new CustomEvent('auth:logout', { 
        detail: { reason: 'analytics_401' } 
      });
      window.dispatchEvent(event);
    }
    return Promise.reject(error);
  }
);

export const analyticsService = {
  // Helper para convertir fecha a ISO si es necesario
  _toISOString(fecha?: string): string | undefined {
    if (!fecha) return undefined;
    // Si ya es ISO (contiene 'T'), retornar tal cual
    if (fecha.includes('T')) return fecha;
    // Si es formato YYYY-MM-DD, convertir a ISO
    return new Date(fecha + 'T00:00:00Z').toISOString();
  },

  async getDashboardPrincipal(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<DashboardData> {
    const params = new URLSearchParams();
    const inicio = this._toISOString(fechaInicio);
    const fin = this._toISOString(fechaFin);
    
    if (inicio) params.append('fecha_inicio', inicio);
    if (fin) params.append('fecha_fin', fin);

    const response = await analyticsClient.get<AnalyticsResponse<DashboardData>>(
      `/dashboards/principal?${params.toString()}`
    );
    
    return response.data.data;
  },

  async getGraficosDelMes(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<any[]> {
    const params = new URLSearchParams();
    const inicio = this._toISOString(fechaInicio);
    const fin = this._toISOString(fechaFin);
    
    if (inicio) params.append('fecha_inicio', inicio);
    if (fin) params.append('fecha_fin', fin);

    const response = await analyticsClient.get(
      `/dashboards/graficos-mes?${params.toString()}`
    );
    
    return response.data.data || [];
  },

  async getTopSolicitudesAbiertas(limit: number = 15): Promise<any[]> {
    const response = await analyticsClient.get(
      `/dashboards/top-solicitudes-abiertas?limit=${limit}`
    );
    
    return response.data.data || [];
  },

  async getEmbudoOperativo(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    const inicio = this._toISOString(fechaInicio);
    const fin = this._toISOString(fechaFin);
    
    if (inicio) params.append('fecha_inicio', inicio);
    if (fin) params.append('fecha_fin', fin);

    const response = await analyticsClient.get(
      `/dashboards/embudo-operativo?${params.toString()}`
    );
    
    return response.data;
  },

  async getSaludMarketplace(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    const inicio = this._toISOString(fechaInicio);
    const fin = this._toISOString(fechaFin);
    
    if (inicio) params.append('fecha_inicio', inicio);
    if (fin) params.append('fecha_fin', fin);

    const response = await analyticsClient.get(
      `/dashboards/salud-marketplace?${params.toString()}`
    );
    
    return response.data;
  },

  async getDashboardFinanciero(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    const inicio = this._toISOString(fechaInicio);
    const fin = this._toISOString(fechaFin);
    
    if (inicio) params.append('fecha_inicio', inicio);
    if (fin) params.append('fecha_fin', fin);

    const response = await analyticsClient.get(
      `/dashboards/financiero?${params.toString()}`
    );
    
    return response.data;
  },

  async getAnalisisAsesores(
    fechaInicio?: string,
    fechaFin?: string,
    ciudad?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    const inicio = this._toISOString(fechaInicio);
    const fin = this._toISOString(fechaFin);
    
    if (inicio) params.append('fecha_inicio', inicio);
    if (fin) params.append('fecha_fin', fin);
    if (ciudad) params.append('ciudad', ciudad);

    const response = await analyticsClient.get(
      `/dashboards/asesores?${params.toString()}`
    );
    
    return response.data;
  },

  // Funciones de exportación
  async exportDashboardData(
    dashboard: string,
    format: 'json' | 'csv',
    fechaInicio?: string,
    fechaFin?: string,
    ciudad?: string
  ): Promise<Blob> {
    const params = new URLSearchParams();
    const inicio = this._toISOString(fechaInicio);
    const fin = this._toISOString(fechaFin);
    
    if (inicio) params.append('fecha_inicio', inicio);
    if (fin) params.append('fecha_fin', fin);
    if (ciudad) params.append('ciudad', ciudad);
    params.append('format', format);

    const response = await analyticsClient.get(
      `/dashboards/${dashboard}/export?${params.toString()}`,
      { responseType: 'blob' }
    );
    
    return response.data;
  },

  // Utilidades para exportación local
  exportToCSV(data: any, filename: string): void {
    const csvContent = this.convertToCSV(data);
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  exportToJSON(data: any, filename: string): void {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },

  convertToCSV(data: any): string {
    if (!data || typeof data !== 'object') {
      return '';
    }

    // Si es un objeto con métricas, convertir a formato tabular
    if (data.metricas) {
      const headers = ['Métrica', 'Valor', 'Unidad', 'Cambio %'];
      const rows = Object.entries(data.metricas).map(([key, value]) => [
        key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        String(value),
        '',
        ''
      ]);
      
      return [headers, ...rows].map(row => 
        row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')
      ).join('\n');
    }

    // Si es un array, convertir directamente
    if (Array.isArray(data)) {
      if (data.length === 0) return '';
      
      const headers = Object.keys(data[0]);
      const rows = data.map(item => 
        headers.map(header => `"${String(item[header] || '').replace(/"/g, '""')}"`)
      );
      
      return [headers, ...rows].map(row => row.join(',')).join('\n');
    }

    // Para objetos simples, convertir a formato clave-valor
    const entries = Object.entries(data);
    const headers = ['Campo', 'Valor'];
    const rows = entries.map(([key, value]) => [
      key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      String(value)
    ]);
    
    return [headers, ...rows].map(row => 
      row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')
    ).join('\n');
  },

  // Función para obtener métricas calculadas
  async getCalculatedMetrics(
    nombreMetrica?: string,
    fechaInicio?: string,
    fechaFin?: string,
    limit: number = 100
  ): Promise<any> {
    const params = new URLSearchParams();
    const inicio = this._toISOString(fechaInicio);
    const fin = this._toISOString(fechaFin);
    
    if (nombreMetrica) params.append('nombre_metrica', nombreMetrica);
    if (inicio) params.append('fecha_inicio', inicio);
    if (fin) params.append('fecha_fin', fin);
    params.append('limit', limit.toString());

    const response = await analyticsClient.get(
      `/dashboards/metrics/calculated?${params.toString()}`
    );
    
    return response.data;
  },

  // Funciones para batch jobs
  async getBatchJobsStatus(): Promise<any> {
    const response = await analyticsClient.get('/dashboards/batch-jobs/status');
    return response.data;
  },

  async triggerBatchJob(jobId: string): Promise<any> {
    const response = await analyticsClient.post(`/dashboards/batch-jobs/trigger/${jobId}`);
    return response.data;
  },

  async runDailyBatchJob(fecha?: string): Promise<any> {
    const params = new URLSearchParams();
    if (fecha) params.append('fecha', fecha);

    const response = await analyticsClient.post(
      `/dashboards/batch-jobs/daily?${params.toString()}`
    );
    return response.data;
  },

  async runWeeklyBatchJob(fechaFin?: string): Promise<any> {
    const params = new URLSearchParams();
    if (fechaFin) params.append('fecha_fin', fechaFin);

    const response = await analyticsClient.post(
      `/dashboards/batch-jobs/weekly?${params.toString()}`
    );
    return response.data;
  }
};

