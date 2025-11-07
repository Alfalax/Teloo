import axios from 'axios';
import { PQR, PQRCreate, PQRUpdate, PQRList, PQRMetrics, PQRFilters } from '@/types/pqr';

export const pqrService = {
  // Obtener lista de PQRs con filtros
  async getPQRs(
    page: number = 1,
    limit: number = 50,
    filters?: PQRFilters
  ): Promise<PQRList> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });

    if (filters?.search) params.append('search', filters.search);
    if (filters?.estado) params.append('estado', filters.estado);
    if (filters?.tipo) params.append('tipo', filters.tipo);
    if (filters?.prioridad) params.append('prioridad', filters.prioridad);

    const response = await axios.get(`/pqr?${params.toString()}`);
    return response.data;
  },

  // Obtener métricas de PQRs
  async getPQRMetrics(): Promise<PQRMetrics> {
    const response = await axios.get('/pqr/metrics');
    return response.data;
  },

  // Obtener una PQR específica
  async getPQR(id: string): Promise<PQR> {
    const response = await axios.get(`/pqr/${id}`);
    return response.data;
  },

  // Crear nueva PQR
  async createPQR(data: PQRCreate): Promise<PQR> {
    const response = await axios.post('/pqr', data);
    return response.data;
  },

  // Actualizar PQR
  async updatePQR(id: string, data: PQRUpdate): Promise<PQR> {
    const response = await axios.put(`/pqr/${id}`, data);
    return response.data;
  },

  // Responder a una PQR
  async responderPQR(id: string, respuesta: string): Promise<PQR> {
    const response = await axios.post(`/pqr/${id}/responder`, { respuesta });
    return response.data;
  },

  // Cambiar estado de PQR
  async cambiarEstado(
    id: string, 
    nuevo_estado: 'ABIERTA' | 'EN_PROCESO' | 'CERRADA'
  ): Promise<PQR> {
    const response = await axios.post(`/pqr/${id}/cambiar-estado`, { nuevo_estado });
    return response.data;
  },

  // Cambiar prioridad de PQR
  async cambiarPrioridad(
    id: string, 
    nueva_prioridad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA'
  ): Promise<PQR> {
    const response = await axios.post(`/pqr/${id}/cambiar-prioridad`, { nueva_prioridad });
    return response.data;
  },

  // Eliminar PQR
  async deletePQR(id: string): Promise<void> {
    await axios.delete(`/pqr/${id}`);
  },

  // Obtener PQRs de un cliente específico
  async getPQRsByCliente(clienteId: string): Promise<PQR[]> {
    const response = await axios.get(`/pqr/cliente/${clienteId}`);
    return response.data;
  },
};