import apiClient from '@/lib/axios';

export interface Municipio {
  id: string;
  codigo_dane: string | null;
  municipio: string;
  departamento: string;
  area_metropolitana: string | null;
  hub_logistico: string;
}

export interface MunicipiosResponse {
  success: boolean;
  total: number;
  municipios: Municipio[];
}

export interface DepartamentosResponse {
  success: boolean;
  data: string[];
}

export interface CiudadesPorDepartamentoResponse {
  success: boolean;
  departamento: string;
  ciudades: string[];
}

export const geografiaService = {
  // Get all departamentos
  async getDepartamentos(): Promise<string[]> {
    const response = await apiClient.get<{ success: boolean; data: string[] }>(
      '/admin/geografia/departamentos'
    );
    return response.data.data;
  },

  // Get ciudades by departamento
  async getCiudadesByDepartamento(departamento: string): Promise<string[]> {
    const response = await apiClient.get<{ success: boolean; data: string[] }>(
      `/admin/geografia/ciudades?departamento=${encodeURIComponent(departamento)}`
    );
    return response.data.data;
  },

  // Get all ciudades
  async getCiudades(): Promise<string[]> {
    const response = await apiClient.get<{ success: boolean; data: string[] }>(
      '/admin/geografia/ciudades'
    );
    return response.data.data;
  },

  // Search municipios with filters
  async buscarMunicipios(
    query?: string,
    departamento?: string,
    limit: number = 50
  ): Promise<Municipio[]> {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (departamento) params.append('departamento', departamento);
    params.append('limit', limit.toString());

    const response = await apiClient.get<MunicipiosResponse>(
      `/admin/geografia/municipios?${params.toString()}`
    );
    return response.data.municipios;
  },

  // Validate ciudad
  async validarCiudad(ciudad: string, departamento?: string): Promise<boolean> {
    const params = new URLSearchParams();
    params.append('ciudad', ciudad);
    if (departamento) params.append('departamento', departamento);

    const response = await apiClient.get<{ success: boolean; existe: boolean }>(
      `/admin/geografia/validar-ciudad?${params.toString()}`
    );
    return response.data.existe;
  },

  // Get estadisticas
  async getEstadisticas(): Promise<any> {
    const response = await apiClient.get('/admin/geografia/estadisticas');
    return response.data;
  },
};
