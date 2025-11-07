import axios from 'axios';
import { DashboardData, AnalyticsResponse } from '@/types/dashboard';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const analyticsApi = axios.create({
  baseURL: `${API_BASE_URL}/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
analyticsApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle errors
analyticsApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const analyticsService = {
  async getDashboardPrincipal(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<DashboardData> {
    const params = new URLSearchParams();
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);

    const response = await analyticsApi.get<AnalyticsResponse<DashboardData>>(
      `/dashboards/principal?${params.toString()}`
    );
    
    return response.data.data;
  },

  async getGraficosDelMes(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<any[]> {
    const params = new URLSearchParams();
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);

    const response = await analyticsApi.get(
      `/dashboards/graficos-mes?${params.toString()}`
    );
    
    return response.data.data || [];
  },

  async getTopSolicitudesAbiertas(limit: number = 15): Promise<any[]> {
    const response = await analyticsApi.get(
      `/dashboards/top-solicitudes-abiertas?limit=${limit}`
    );
    
    return response.data.data || [];
  },

  async getEmbudoOperativo(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);

    const response = await analyticsApi.get(
      `/dashboards/embudo-operativo?${params.toString()}`
    );
    
    return response.data.data;
  },

  async getSaludMarketplace(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);

    const response = await analyticsApi.get(
      `/dashboards/salud-marketplace?${params.toString()}`
    );
    
    return response.data.data;
  },

  async getDashboardFinanciero(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);

    const response = await analyticsApi.get(
      `/dashboards/financiero?${params.toString()}`
    );
    
    return response.data.data;
  },

  async getAnalisisAsesores(
    fechaInicio?: string,
    fechaFin?: string,
    ciudad?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);
    if (ciudad) params.append('ciudad', ciudad);

    const response = await analyticsApi.get(
      `/dashboards/asesores?${params.toString()}`
    );
    
    return response.data.data;
  },
};