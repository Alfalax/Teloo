import axios from 'axios';
import { CreateOfertaRequest, Oferta } from '@/types/solicitud';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const ofertasApi = axios.create({
  baseURL: `${API_BASE_URL}/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
ofertasApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const ofertasService = {
  async createOferta(data: CreateOfertaRequest): Promise<Oferta> {
    const response = await ofertasApi.post<Oferta>('/ofertas', data);
    return response.data;
  },

  async uploadOfertaExcel(solicitudId: string, file: File): Promise<Oferta> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('solicitud_id', solicitudId);

    const response = await ofertasApi.post<Oferta>('/ofertas/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getOfertasBySolicitud(solicitudId: string): Promise<Oferta[]> {
    const response = await ofertasApi.get<Oferta[]>('/ofertas', {
      params: { solicitud_id: solicitudId },
    });
    return response.data;
  },
};
