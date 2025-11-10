import { useState, useEffect } from 'react';
import { configuracionService, ParametroConfig } from '@/services/configuracion';

export function useConfiguracion(claves: string[]) {
  const [parametros, setParametros] = useState<Record<string, ParametroConfig>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadParametros();
  }, []);

  const loadParametros = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await configuracionService.getParametrosByClaves(claves);
      setParametros(data);
    } catch (err: any) {
      console.error('Error loading configuracion:', err);
      setError(err.response?.data?.detail || 'Error al cargar configuración');
    } finally {
      setIsLoading(false);
    }
  };

  const getMetadata = (clave: string, metadataKey: string): any => {
    const param = parametros[clave];
    if (!param || !param.metadata) return null;
    return param.metadata[metadataKey];
  };

  const getValor = (clave: string): string | null => {
    return parametros[clave]?.valor || null;
  };

  return {
    parametros,
    isLoading,
    error,
    getMetadata,
    getValor,
    reload: loadParametros,
  };
}
