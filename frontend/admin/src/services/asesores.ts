import apiClient from '@/lib/axios';
import { 
  AsesorCreate, 
  AsesorUpdate, 
  AsesoresResponse, 
  AsesorResponse, 
  AsesoresKPIs, 
  AsesoresKPIsResponse,
  ExcelImportResult
} from '@/types/asesores';

export const asesoresService = {
  // Get all asesores with pagination and filters
  async getAsesores(
    page: number = 1,
    limit: number = 50,
    search?: string,
    estado?: string,
    ciudad?: string,
    departamento?: string
  ): Promise<AsesoresResponse> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    
    if (search) params.append('search', search);
    if (estado) params.append('estado', estado);
    if (ciudad) params.append('ciudad', ciudad);
    if (departamento) params.append('departamento', departamento);

    const response = await apiClient.get<AsesoresResponse>(
      `/asesores?${params.toString()}`
    );
    
    return response.data;
  },

  // Get asesor by ID
  async getAsesor(id: string): Promise<AsesorResponse> {
    const response = await apiClient.get<AsesorResponse>(`/asesores/${id}`);
    return response.data;
  },

  // Create new asesor
  async createAsesor(asesorData: AsesorCreate): Promise<AsesorResponse> {
    const response = await apiClient.post<AsesorResponse>('/asesores', asesorData);
    return response.data;
  },

  // Update asesor
  async updateAsesor(id: string, asesorData: AsesorUpdate): Promise<AsesorResponse> {
    const response = await apiClient.put<AsesorResponse>(`/asesores/${id}`, asesorData);
    return response.data;
  },

  // Suspend/activate asesor
  async updateAsesorEstado(id: string, estado: 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO'): Promise<AsesorResponse> {
    const response = await apiClient.patch<AsesorResponse>(`/asesores/${id}/estado`, { estado });
    return response.data;
  },

  // Delete asesor
  async deleteAsesor(id: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(`/asesores/${id}`);
    return response.data;
  },

  // Get asesores KPIs
  async getAsesoresKPIs(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<AsesoresKPIs> {
    const params = new URLSearchParams();
    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);

    const response = await apiClient.get<AsesoresKPIsResponse>(
      `/asesores/kpis?${params.toString()}`
    );
    
    return response.data.data;
  },

  // Get unique cities for filters
  async getCiudades(): Promise<string[]> {
    const response = await apiClient.get<{ success: boolean; data: string[] }>('/asesores/ciudades');
    return response.data.data;
  },

  // Get unique departments for filters
  async getDepartamentos(): Promise<string[]> {
    const response = await apiClient.get<{ success: boolean; data: string[] }>('/asesores/departamentos');
    return response.data.data;
  },

  // Import asesores from Excel
  async importExcel(file: File): Promise<ExcelImportResult> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<ExcelImportResult>(
      '/asesores/import/excel',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  },

  // Export asesores to Excel
  async exportExcel(
    search?: string,
    estado?: string,
    ciudad?: string,
    departamento?: string
  ): Promise<Blob> {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (estado) params.append('estado', estado);
    if (ciudad) params.append('ciudad', ciudad);
    if (departamento) params.append('departamento', departamento);

    const response = await apiClient.get(
      `/asesores/export/excel?${params.toString()}`,
      {
        responseType: 'blob',
      }
    );

    return response.data;
  },

  // Download Excel template
  async downloadTemplate(): Promise<Blob> {
    const response = await apiClient.get('/asesores/template/excel', {
      responseType: 'blob',
    });

    return response.data;
  },

  // Get asesor metrics
  async getAsesorMetrics(id: string): Promise<any> {
    const response = await apiClient.get(`/asesores/${id}/metrics`);
    return response.data;
  },

  // Bulk update asesores estado
  async bulkUpdateEstado(
    asesorIds: string[], 
    estado: 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO'
  ): Promise<{ success: boolean; message: string; updated: number }> {
    const response = await apiClient.patch('/asesores/bulk/estado', {
      asesor_ids: asesorIds,
      estado
    });
    return response.data;
  },
};