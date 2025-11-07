/**
 * Configuration Service for TeLOO V3 Admin Frontend
 * Handles system configuration management
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

import type { 
  PesosEscalamiento,
  UmbralesNiveles,
  PesosEvaluacionOfertas,
  ConfiguracionCompleta,
  ConfiguracionSummary,
  Usuario,
  Rol
} from '@/types/configuracion';

export type CategoriaConfiguracion = 
  | 'pesos_escalamiento'
  | 'umbrales_niveles'
  | 'tiempos_espera_nivel'
  | 'canales_por_nivel'
  | 'pesos_evaluacion_ofertas'
  | 'parametros_generales';

class ConfiguracionService {
  /**
   * Obtiene la configuración completa del sistema
   */
  async getConfiguracion(): Promise<ConfiguracionCompleta> {
    const response = await api.get('/admin/configuracion');
    return response.data.configuracion_completa;
  }

  /**
   * Obtiene configuración de una categoría específica
   */
  async getConfiguracionCategoria<T>(categoria: CategoriaConfiguracion): Promise<T> {
    const response = await api.get(`/admin/configuracion?categoria=${categoria}`);
    return response.data.configuracion;
  }

  /**
   * Actualiza configuración de una categoría
   */
  async updateConfiguracion(
    categoria: CategoriaConfiguracion,
    valores: any
  ): Promise<{ success: boolean; message: string; configuracion: any }> {
    const response = await api.put(`/admin/configuracion/${categoria}`, valores);
    return response.data;
  }

  /**
   * Resetea configuración a valores por defecto
   */
  async resetConfiguracion(categoria?: CategoriaConfiguracion): Promise<{
    success: boolean;
    message: string;
    configuracion: any;
  }> {
    const params = categoria ? `?categoria=${categoria}` : '';
    const response = await api.post(`/admin/configuracion/reset${params}`);
    return response.data;
  }

  /**
   * Obtiene resumen de configuración con metadatos
   */
  async getConfiguracionSummary(): Promise<ConfiguracionSummary> {
    const response = await api.get('/admin/configuracion/summary');
    return response.data;
  }

  /**
   * Valida pesos que deben sumar 1.0
   */
  validatePesos(pesos: PesosEscalamiento | PesosEvaluacionOfertas): { valid: boolean; error?: string } {
    const suma = Object.values(pesos).reduce((acc, val) => acc + val, 0);
    const tolerance = 1e-6;
    
    if (Math.abs(suma - 1.0) > tolerance) {
      return {
        valid: false,
        error: `Los pesos deben sumar 1.0 (suma actual: ${suma.toFixed(6)})`
      };
    }
    
    return { valid: true };
  }

  /**
   * Valida umbrales decrecientes
   */
  validateUmbrales(umbrales: UmbralesNiveles): { valid: boolean; error?: string } {
    const valores = [
      umbrales.nivel1_min,
      umbrales.nivel2_min,
      umbrales.nivel3_min,
      umbrales.nivel4_min
    ];

    for (let i = 0; i < valores.length - 1; i++) {
      if (valores[i] <= valores[i + 1]) {
        return {
          valid: false,
          error: 'Los umbrales deben ser decrecientes (nivel1_min > nivel2_min > nivel3_min > nivel4_min)'
        };
      }
    }

    return { valid: true };
  }

  /**
   * Obtiene lista de usuarios del sistema
   */
  async getUsuarios(): Promise<Usuario[]> {
    const response = await api.get('/admin/usuarios');
    return response.data.usuarios;
  }

  /**
   * Crea nuevo usuario
   */
  async createUsuario(usuario: Omit<Usuario, 'id' | 'created_at' | 'updated_at'>): Promise<Usuario> {
    const response = await api.post('/admin/usuarios', usuario);
    return response.data.usuario;
  }

  /**
   * Actualiza usuario existente
   */
  async updateUsuario(id: string, usuario: Partial<Usuario>): Promise<Usuario> {
    const response = await api.put(`/admin/usuarios/${id}`, usuario);
    return response.data.usuario;
  }

  /**
   * Elimina usuario
   */
  async deleteUsuario(id: string): Promise<void> {
    await api.delete(`/admin/usuarios/${id}`);
  }

  /**
   * Obtiene lista de roles del sistema
   */
  async getRoles(): Promise<Rol[]> {
    const response = await api.get('/admin/roles');
    return response.data.roles;
  }

  /**
   * Crea nuevo rol
   */
  async createRol(rol: Omit<Rol, 'id' | 'created_at' | 'updated_at'>): Promise<Rol> {
    const response = await api.post('/admin/roles', rol);
    return response.data.rol;
  }

  /**
   * Actualiza rol existente
   */
  async updateRol(id: string, rol: Partial<Rol>): Promise<Rol> {
    const response = await api.put(`/admin/roles/${id}`, rol);
    return response.data.rol;
  }

  /**
   * Elimina rol
   */
  async deleteRol(id: string): Promise<void> {
    await api.delete(`/admin/roles/${id}`);
  }

  /**
   * Obtiene permisos disponibles en el sistema
   */
  async getPermisosDisponibles(): Promise<string[]> {
    const response = await api.get('/admin/permisos');
    return response.data.permisos;
  }
}

export const configuracionService = new ConfiguracionService();