import axios from 'axios';
import { Solicitud, SolicitudConOferta } from '@/types/solicitud';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const solicitudesApi = axios.create({
  baseURL: `${API_BASE_URL}/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
solicitudesApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const solicitudesService = {
  async getSolicitudesAbiertas(): Promise<Solicitud[]> {
    const response = await solicitudesApi.get<Solicitud[]>('/solicitudes', {
      params: { estado: 'ABIERTA' },
    });
    return response.data;
  },

  async getSolicitudesCerradas(): Promise<SolicitudConOferta[]> {
    // Cerradas son las rechazadas, expiradas o cerradas sin ofertas
    const response = await solicitudesApi.get<SolicitudConOferta[]>('/solicitudes', {
      params: { estado: 'RECHAZADA' },
    });
    return response.data;
  },

  async getSolicitudesGanadas(): Promise<SolicitudConOferta[]> {
    // Ganadas son las aceptadas
    const response = await solicitudesApi.get<SolicitudConOferta[]>('/solicitudes', {
      params: { estado: 'ACEPTADA' },
    });
    return response.data;
  },

  async getSolicitudById(id: string): Promise<Solicitud> {
    const response = await solicitudesApi.get<Solicitud>(`/solicitudes/${id}`);
    return response.data;
  },

  async getMetrics(): Promise<{
    ofertas_asignadas: number;
    monto_total_ganado: number;
    solicitudes_abiertas: number;
    tasa_conversion: number;
  }> {
    const response = await solicitudesApi.get('/solicitudes/metrics');
    return response.data;
  },
};
