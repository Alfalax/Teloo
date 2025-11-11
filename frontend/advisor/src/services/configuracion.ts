import { apiClient } from '@/lib/axios';

export interface ParametroConfig {
  clave: string;
  valor: string;
  tipo_dato: string;
  descripcion?: string;
  metadata?: Record<string, any>;
}

export const configuracionService = {
  /**
   * Get public configuration parameters
   */
  async getParametrosPublic(): Promise<ParametroConfig[]> {
    const response = await apiClient.get<ParametroConfig[]>('/v1/configuracion/public');
    return response.data;
  },

  /**
   * Get configuration parameters by keys
   */
  async getParametrosByClaves(claves: string[]): Promise<Record<string, ParametroConfig>> {
    const params = new URLSearchParams();
    claves.forEach(clave => params.append('claves', clave));
    
    const response = await apiClient.get<ParametroConfig[]>(
      `/v1/configuracion/public?${params.toString()}`
    );
    
    // Convert array to object keyed by clave
    const result: Record<string, ParametroConfig> = {};
    response.data.forEach(param => {
      result[param.clave] = param;
    });
    
    return result;
  },
};
