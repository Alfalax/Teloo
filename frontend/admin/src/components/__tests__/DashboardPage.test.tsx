import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DashboardPage } from '@/pages/DashboardPage';

// Mock the analytics service
vi.mock('@/services/analytics', () => ({
  analyticsService: {
    getDashboardPrincipal: vi.fn(() => Promise.resolve({
      kpis: {
        ofertas_totales_asignadas: { valor: 1234, cambio_porcentual: 12.5 },
        monto_total_aceptado: { valor: 45200000, cambio_porcentual: 8.3 },
        solicitudes_abiertas: { valor: 89, cambio_porcentual: -2.1 },
        tasa_conversion: { valor: 68.4, cambio_porcentual: 5.2 },
      }
    })),
    getGraficosDelMes: vi.fn(() => Promise.resolve([])),
    getTopSolicitudesAbiertas: vi.fn(() => Promise.resolve([])),
  },
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </QueryClientProvider>
);

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard header correctly', () => {
    render(
      <TestWrapper>
        <DashboardPage />
      </TestWrapper>
    );

    expect(screen.getByText('Dashboard Principal')).toBeInTheDocument();
    expect(screen.getByText(/Resumen general del marketplace TeLOO/)).toBeInTheDocument();
  });

  it('renders KPI cards', () => {
    render(
      <TestWrapper>
        <DashboardPage />
      </TestWrapper>
    );

    expect(screen.getByText('Ofertas Totales Asignadas')).toBeInTheDocument();
    expect(screen.getByText('Monto Total Aceptado')).toBeInTheDocument();
    expect(screen.getByText('Solicitudes Abiertas')).toBeInTheDocument();
    expect(screen.getByText('Tasa de Conversión')).toBeInTheDocument();
  });

  it('renders chart section', () => {
    render(
      <TestWrapper>
        <DashboardPage />
      </TestWrapper>
    );

    expect(screen.getByText('Solicitudes del Mes')).toBeInTheDocument();
    expect(screen.getByText('Top 15 Solicitudes Abiertas')).toBeInTheDocument();
  });

  it('renders recent activity section', () => {
    render(
      <TestWrapper>
        <DashboardPage />
      </TestWrapper>
    );

    expect(screen.getByText('Actividad Reciente')).toBeInTheDocument();
  });
});