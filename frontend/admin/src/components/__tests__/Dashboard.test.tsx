import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DashboardPage } from '@/pages/DashboardPage';
import { KPICard } from '@/components/dashboard/KPICard';
import { TopSolicitudesTable } from '@/components/dashboard/TopSolicitudesTable';

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
    getGraficosDelMes: vi.fn(() => Promise.resolve([
      { date: '2024-01-01', solicitudes: 10, aceptadas: 8, cerradas: 2 },
      { date: '2024-01-02', solicitudes: 15, aceptadas: 12, cerradas: 3 },
    ])),
    getTopSolicitudesAbiertas: vi.fn(() => Promise.resolve([
      {
        id: 'SOL-001',
        cliente_nombre: 'Juan Pérez',
        repuestos_count: 3,
        tiempo_abierta_horas: 48,
        ciudad: 'Bogotá',
        estado: 'ABIERTA'
      }
    ])),
    exportToJSON: vi.fn(),
  },
}));

// Mock the dashboard hook
vi.mock('@/hooks/useDashboard', () => ({
  useDashboardData: vi.fn(() => ({
    dashboardData: {
      kpis: {
        ofertas_totales_asignadas: { valor: 1234, cambio_porcentual: 12.5 },
        monto_total_aceptado: { valor: 45200000, cambio_porcentual: 8.3 },
        solicitudes_abiertas: { valor: 89, cambio_porcentual: -2.1 },
        tasa_conversion: { valor: 68.4, cambio_porcentual: 5.2 },
      }
    },
    graficosData: [
      { date: '2024-01-01', solicitudes: 10, aceptadas: 8, cerradas: 2 },
      { date: '2024-01-02', solicitudes: 15, aceptadas: 12, cerradas: 3 },
    ],
    topSolicitudes: [
      {
        id: 'SOL-001',
        cliente_nombre: 'Juan Pérez',
        repuestos_count: 3,
        tiempo_abierta_horas: 48,
        ciudad: 'Bogotá',
        estado: 'ABIERTA'
      }
    ],
    isLoading: false,
    hasError: false,
    refetchDashboard: vi.fn(),
    periodo: { inicio: '2024-01-01', fin: '2024-01-31' },
  })),
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

describe('Dashboard Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('DashboardPage', () => {
    it('renders dashboard header correctly', () => {
      render(
        <TestWrapper>
          <DashboardPage />
        </TestWrapper>
      );

      expect(screen.getByText('Dashboard Principal')).toBeInTheDocument();
      expect(screen.getByText(/Resumen general del marketplace TeLOO/)).toBeInTheDocument();
    });

    it('renders all KPI cards', () => {
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

    it('renders chart and table sections', () => {
      render(
        <TestWrapper>
          <DashboardPage />
        </TestWrapper>
      );

      expect(screen.getByText('Solicitudes del Mes')).toBeInTheDocument();
      expect(screen.getByText('Top 15 Solicitudes Abiertas')).toBeInTheDocument();
      expect(screen.getByText('Actividad Reciente')).toBeInTheDocument();
    });

    it('renders tabs navigation', () => {
      render(
        <TestWrapper>
          <DashboardPage />
        </TestWrapper>
      );

      expect(screen.getByRole('tab', { name: /Resumen/ })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Analytics Completo/ })).toBeInTheDocument();
    });

    it('renders action buttons', () => {
      render(
        <TestWrapper>
          <DashboardPage />
        </TestWrapper>
      );

      expect(screen.getByRole('button', { name: /Actualizar/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Exportar/ })).toBeInTheDocument();
    });
  });

  describe('KPICard', () => {
    it('renders KPI data correctly', () => {
      render(
        <KPICard
          title="Test KPI"
          value="1,234"
          change={12.5}
          trend="up"
          description="Test description"
          isLoading={false}
        />
      );

      expect(screen.getByText('Test KPI')).toBeInTheDocument();
      expect(screen.getByText('1,234')).toBeInTheDocument();
      expect(screen.getByText('Test description')).toBeInTheDocument();
    });

    it('shows loading state', () => {
      render(
        <KPICard
          title="Test KPI"
          value="1,234"
          isLoading={true}
        />
      );

      // Loading state should show skeleton instead of content
      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
      
      // Title should not be visible in loading state
      expect(screen.queryByText('Test KPI')).not.toBeInTheDocument();
    });

    it('displays trend indicators correctly', () => {
      const { rerender } = render(
        <KPICard
          title="Test KPI"
          value="1,234"
          change={12.5}
          trend="up"
        />
      );

      expect(screen.getByText('+12.5%')).toBeInTheDocument();

      rerender(
        <KPICard
          title="Test KPI"
          value="1,234"
          change={-5.2}
          trend="down"
        />
      );

      expect(screen.getByText('-5.2%')).toBeInTheDocument();
    });
  });

  describe('TopSolicitudesTable', () => {
    const mockSolicitudes = [
      {
        id: 'SOL-001',
        codigo: 'SOL-001',
        vehiculo: 'Toyota Corolla 2020',
        cliente: 'Juan Pérez',
        ciudad: 'Bogotá',
        tiempo_proceso_horas: 48,
        created_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 'SOL-002',
        codigo: 'SOL-002',
        vehiculo: 'Chevrolet Spark 2019',
        cliente: 'María García',
        ciudad: 'Medellín',
        tiempo_proceso_horas: 72,
        created_at: '2024-01-02T00:00:00Z'
      }
    ];

    it('renders solicitudes table correctly', () => {
      render(
        <TopSolicitudesTable 
          solicitudes={mockSolicitudes} 
          isLoading={false} 
        />
      );

      expect(screen.getByText('Top 15 Solicitudes Abiertas')).toBeInTheDocument();
      expect(screen.getByText('SOL-001')).toBeInTheDocument();
      expect(screen.getByText('Juan Pérez')).toBeInTheDocument();
      expect(screen.getByText('SOL-002')).toBeInTheDocument();
      expect(screen.getByText('María García')).toBeInTheDocument();
    });

    it('shows loading state', () => {
      render(
        <TopSolicitudesTable 
          solicitudes={[]} 
          isLoading={true} 
        />
      );

      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('shows empty state when no solicitudes', () => {
      render(
        <TopSolicitudesTable 
          solicitudes={[]} 
          isLoading={false} 
        />
      );

      expect(screen.getByText('No hay solicitudes abiertas')).toBeInTheDocument();
    });

    it('formats time correctly', () => {
      render(
        <TopSolicitudesTable 
          solicitudes={mockSolicitudes} 
          isLoading={false} 
        />
      );

      // Check that time formatting is displayed (exact text may vary based on locale)
      expect(screen.getByText(/días?/)).toBeInTheDocument();
    });
  });
});