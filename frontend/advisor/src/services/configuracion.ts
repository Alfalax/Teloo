import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const configuracionApi = axios.create({
  baseURL: `${API_BASE_URL}/admin/configuracion`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
configuracionApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface ParametroMetadata {
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  options?: string[];
  placeholder?: string;
  help_text?: string;
}

export interface ParametroConfig {
  id: string;
  categoria: string;
  nombre: string;
  clave: string;
  valor: any;
  tipo_dato: string;
  descripcion?: string;
  metadata?: ParametroMetadata;
  activo: boolean;
}

export const configuracionService = {
  async getParametros(): Promise<ParametroConfig[]> {
    const response = await configuracionApi.get<any>('/public');
    // Backend returns {configuracion_completa: {...}, metadata: {...}}
    // Convert to array format
    const config = response.data.configuracion_completa || {};
    const metadata = response.data.metadata || {};
    
    const parametros: ParametroConfig[] = [];
    
    // Convert nested config object to flat array
    Object.entries(config).forEach(([categoria, valores]: [string, any]) => {
      if (typeof valores === 'object' && valores !== null) {
        Object.entries(valores).forEach(([clave, valor]: [string, any]) => {
          const metadataItem = metadata[categoria]?.[clave];
          parametros.push({
            id: `${categoria}_${clave}`,
            categoria,
            nombre: clave,
            clave,
            valor,
            tipo_dato: typeof valor,
            descripcion: metadataItem?.descripcion,
            metadata: metadataItem,
            activo: true,
          });
        });
      }
    });
    
    return parametros;
  },

  async getParametrosByClave(claves: string[]): Promise<Record<string, ParametroConfig>> {
    const parametros = await this.getParametros();
    const result: Record<string, ParametroConfig> = {};
    
    parametros.forEach((param) => {
      if (claves.includes(param.clave)) {
        result[param.clave] = param;
      }
    });
    
    return result;
  },

  async getParametroByClaveOrDefault(clave: string, defaultValue: any): Promise<any> {
    try {
      const parametros = await this.getParametros();
      const param = parametros.find((p) => p.clave === clave);
      return param?.valor ?? defaultValue;
    } catch (error) {
      console.error(`Error getting parameter ${clave}:`, error);
      return defaultValue;
    }
  },
};
