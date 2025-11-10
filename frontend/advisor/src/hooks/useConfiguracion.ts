import { useState, useEffect } from 'react';
import { configuracionService, ParametroConfig } from '@/services/configuracion';

export function useConfiguracion(claves?: string[]) {
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
      
      if (claves && claves.length > 0) {
        const data = await configuracionService.getParametrosByClave(claves);
        setParametros(data);
      } else {
        const allParams = await configuracionService.getParametros();
        const mapped = allParams.reduce((acc, param) => {
          acc[param.clave] = param;
          return acc;
        }, {} as Record<string, ParametroConfig>);
        setParametros(mapped);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar configuración');
      console.error('Error loading configuracion:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getParametro = (clave: string): ParametroConfig | undefined => {
    return parametros[clave];
  };

  const getValor = (clave: string, defaultValue?: any): any => {
    return parametros[clave]?.valor ?? defaultValue;
  };

  const getMetadata = (clave: string) => {
    return parametros[clave]?.metadata;
  };

  return {
    parametros,
    isLoading,
    error,
    getParametro,
    getValor,
    getMetadata,
    reload: loadParametros,
  };
}
