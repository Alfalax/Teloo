import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface BrandingState {
  logoUrl: string | null;
  nombreEmpresa: string;
}

const BrandingContext = createContext<BrandingState>({
  logoUrl: null,
  nombreEmpresa: 'TeLOO',
});

export function BrandingProvider({ children }: { children: ReactNode }) {
  const [branding, setBranding] = useState<BrandingState>({
    logoUrl: null,
    nombreEmpresa: 'TeLOO',
  });

  useEffect(() => {
    fetch(`${API_BASE_URL}/v1/configuracion/branding/public`)
      .then((r) => r.json())
      .then((data) => {
        if (data.success && data.data) {
          const { logo_url, nombre_empresa } = data.data;
          setBranding({
            logoUrl: logo_url
              ? logo_url.startsWith('http')
                ? logo_url
                : `${API_BASE_URL}${logo_url}`
              : null,
            nombreEmpresa: nombre_empresa || 'TeLOO',
          });
        }
      })
      .catch(() => {});
  }, []);

  return (
    <BrandingContext.Provider value={branding}>
      {children}
    </BrandingContext.Provider>
  );
}

export function useBranding() {
  return useContext(BrandingContext);
}
