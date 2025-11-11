/**
 * Hook for Configuration Management
 */

import { useState, useEffect, useCallback } from 'react';
import { configuracionService } from '@/services/configuracion';
import type { 
  ConfiguracionCompleta,
  ConfiguracionConMetadata,
  ConfiguracionSummary, 
  CategoriaConfiguracion,
  Usuario,
  Rol
} from '@/types/configuracion';

export function useConfiguracion() {
  const [configuracion, setConfiguracion] = useState<ConfiguracionCompleta | null>(null);
  const [metadata, setMetadata] = useState<Record<string, any>>({});
  const [summary, setSummary] = useState<ConfiguracionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadConfiguracion = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [configData, summaryData] = await Promise.all([
        configuracionService.getConfiguracion(),
        configuracionService.getConfiguracionSummary()
      ]);
      
      setConfiguracion(configData.configuracion_completa);
      setMetadata(configData.metadata);
      setSummary(summaryData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando configuración');
    } finally {
      setLoading(false);
    }
  }, []);

  const updateConfiguracion = useCallback(async (
    categoria: CategoriaConfiguracion,
    valores: any
  ) => {
    try {
      setError(null);
      
      const result = await configuracionService.updateConfiguracion(categoria, valores);
      
      // Small delay to ensure DB is updated before reloading
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Reload configuration after update
      await loadConfiguracion();
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error actualizando configuración';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [loadConfiguracion]);

  const resetConfiguracion = useCallback(async (categoria?: CategoriaConfiguracion) => {
    try {
      setError(null);
      
      const result = await configuracionService.resetConfiguracion(categoria);
      
      // Reload configuration after reset
      await loadConfiguracion();
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error reseteando configuración';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [loadConfiguracion]);

  useEffect(() => {
    loadConfiguracion();
  }, [loadConfiguracion]);

  return {
    configuracion,
    metadata,
    summary,
    loading,
    error,
    loadConfiguracion,
    updateConfiguracion,
    resetConfiguracion
  };
}

export function useUsuarios() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadUsuarios = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await configuracionService.getUsuarios();
      setUsuarios(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando usuarios');
    } finally {
      setLoading(false);
    }
  }, []);

  const createUsuario = useCallback(async (usuario: Omit<Usuario, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      setError(null);
      
      const newUsuario = await configuracionService.createUsuario(usuario);
      
      // Reload users after creation
      await loadUsuarios();
      
      return newUsuario;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error creando usuario';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [loadUsuarios]);

  const updateUsuario = useCallback(async (id: string, usuario: Partial<Usuario>) => {
    try {
      setError(null);
      
      const updatedUsuario = await configuracionService.updateUsuario(id, usuario);
      
      // Update local state
      setUsuarios(prev => prev.map(u => u.id === id ? updatedUsuario : u));
      
      return updatedUsuario;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error actualizando usuario';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  const deleteUsuario = useCallback(async (id: string) => {
    try {
      setError(null);
      
      await configuracionService.deleteUsuario(id);
      
      // Remove from local state
      setUsuarios(prev => prev.filter(u => u.id !== id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error eliminando usuario';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  useEffect(() => {
    loadUsuarios();
  }, [loadUsuarios]);

  return {
    usuarios,
    loading,
    error,
    loadUsuarios,
    createUsuario,
    updateUsuario,
    deleteUsuario
  };
}

export function useRoles() {
  const [roles, setRoles] = useState<Rol[]>([]);
  const [permisosDisponibles, setPermisosDisponibles] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRoles = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [rolesData, permisosData] = await Promise.all([
        configuracionService.getRoles(),
        configuracionService.getPermisosDisponibles()
      ]);
      
      setRoles(rolesData);
      setPermisosDisponibles(permisosData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando roles');
    } finally {
      setLoading(false);
    }
  }, []);

  const createRol = useCallback(async (rol: Omit<Rol, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      setError(null);
      
      const newRol = await configuracionService.createRol(rol);
      
      // Reload roles after creation
      await loadRoles();
      
      return newRol;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error creando rol';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [loadRoles]);

  const updateRol = useCallback(async (id: string, rol: Partial<Rol>) => {
    try {
      setError(null);
      
      const updatedRol = await configuracionService.updateRol(id, rol);
      
      // Update local state
      setRoles(prev => prev.map(r => r.id === id ? updatedRol : r));
      
      return updatedRol;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error actualizando rol';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  const deleteRol = useCallback(async (id: string) => {
    try {
      setError(null);
      
      await configuracionService.deleteRol(id);
      
      // Remove from local state
      setRoles(prev => prev.filter(r => r.id !== id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error eliminando rol';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  useEffect(() => {
    loadRoles();
  }, [loadRoles]);

  return {
    roles,
    permisosDisponibles,
    loading,
    error,
    loadRoles,
    createRol,
    updateRol,
    deleteRol
  };
}