import { apiClient } from '@/lib/axios';
import { CreateOfertaRequest, Oferta } from '@/types/solicitud';

export const ofertasService = {
  async createOferta(data: CreateOfertaRequest): Promise<Oferta> {
    const response = await apiClient.post<Oferta>('/v1/ofertas', data);
    return response.data;
  },

  async uploadOfertaExcel(solicitudId: string, file: File): Promise<Oferta> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('solicitud_id', solicitudId);

    const response = await apiClient.post<Oferta>('/v1/ofertas/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getOfertasBySolicitud(solicitudId: string): Promise<Oferta[]> {
    const response = await apiClient.get<Oferta[]>('/v1/ofertas', {
      params: { solicitud_id: solicitudId },
    });
    return response.data;
  },
};
