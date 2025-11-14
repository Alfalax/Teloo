/*  */import { apiClient } from '@/lib/axios';
import { SolicitudConOferta } from '@/types/solicitud';

// Service for managing solicitudes with offers
export const solicitudesService = {
  async getMisSolicitudes(): Promise<SolicitudConOferta[]> {
    // Trae TODAS las solicitudes del asesor (sin filtrar por estado)
    const response = await apiClient.get<{ items: SolicitudConOferta[] }>('/v1/solicitudes', {
      params: { page: 1, page_size: 100 },
    });
    return response.data.items || [];
  },

  async getSolicitudesAbiertas(): Promise<SolicitudConOferta[]> {
    const response = await apiClient.get<{ items: SolicitudConOferta[] }>('/v1/solicitudes', {
      params: { estado: 'ABIERTA', page: 1, page_size: 100 },
    });
    return response.data.items || [];
  },

  async getSolicitudesCerradas(): Promise<SolicitudConOferta[]> {
    // Cerradas son las que están sin ofertas
    const response = await apiClient.get<{ items: SolicitudConOferta[] }>('/v1/solicitudes', {
      params: { estado: 'CERRADA_SIN_OFERTAS', page: 1, page_size: 100 },
    });
    return response.data.items || [];
  },

  async getSolicitudesGanadas(): Promise<SolicitudConOferta[]> {
    // Ganadas son las evaluadas donde el asesor ganó
    const response = await apiClient.get<{ items: SolicitudConOferta[] }>('/v1/solicitudes', {
      params: { estado: 'EVALUADA', page: 1, page_size: 100 },
    });
    return response.data.items || [];
  },

  async getSolicitudById(id: string): Promise<SolicitudConOferta> {
    const response = await apiClient.get<SolicitudConOferta>(`/v1/solicitudes/${id}`);
    return response.data;
  },

  async getMetrics(): Promise<{
    ofertas_asignadas: number;
    monto_total_ganado: number;
    solicitudes_abiertas: number;
    tasa_conversion: number;
  }> {
    const response = await apiClient.get('/v1/solicitudes/metrics');
    return response.data;
  },

  async descargarPlantillaOferta(solicitudId: string): Promise<void> {
    const response = await apiClient.get(`/v1/solicitudes/${solicitudId}/plantilla-oferta`, {
      responseType: 'blob',
    });
    
    // Crear URL del blob y descargar
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `plantilla_oferta_${solicitudId}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
