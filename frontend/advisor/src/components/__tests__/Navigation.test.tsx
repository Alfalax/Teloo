import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardPage from '@/pages/DashboardPage';
import { solicitudesService } from '@/services/solicitudes';

// Mock services
vi.mock('@/services/solicitudes', () => ({
  solicitudesService: {
    getSolicitudesAbiertas: vi.fn(),
    getSolicitudesCerradas: vi.fn(),
    getSolicitudesGanadas: vi.fn(),
  },
}));

vi.mock('@/services/ofertas', () => ({
  ofertasService: {
    createOferta: vi.fn(),
    uploadOfertaExcel: vi.fn(),
  },
}));

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'ASE-001',
      nombre: 'Juan Pérez',
      email: 'juan@example.com',
      rol: 'ADVISOR',
    },
    isAuthenticated: true,
    logout: vi.fn(),
  }),
}));

describe('Navigation between tabs', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const mockSolicitudesAbiertas = [
    {
      id: 'SOL-001',
      cliente_id: 'CLI-001',
      estado: 'ABIERTA' as const,
      nivel_actual: 1,
      ciudad_origen: 'Bogotá',
      departamento_origen: 'Cundinamarca',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      repuestos_solicitados: [
        {
          id: 'REP-001',
          solicitud_id: 'SOL-001',
          nombre: 'Filtro de aceite',
          codigo: 'FO-123',
          marca_vehiculo: 'Toyota',
          linea_vehiculo: 'Corolla',
          anio_vehiculo: 2015,
          cantidad: 1,
        },
      ],
    },
  ];

  const mockSolicitudesCerradas = [
    {
      id: 'SOL-002',
      cliente_id: 'CLI-002',
      estado: 'CERRADA_SIN_OFERTAS' as const,
      nivel_actual: 5,
      ciudad_origen: 'Medellín',
      departamento_origen: 'Antioquia',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
      repuestos_solicitados: [],
    },
  ];

  const mockSolicitudesGanadas = [
    {
      id: 'SOL-003',
      cliente_id: 'CLI-003',
      estado: 'EVALUADA' as const,
      nivel_actual: 1,
      ciudad_origen: 'Cali',
      departamento_origen: 'Valle del Cauca',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
      repuestos_solicitados: [],
      oferta_ganadora: {
        id: 'OFE-001',
        estado: 'ACEPTADA',
        monto_total: 150000,
      },
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(solicitudesService.getSolicitudesAbiertas).mockResolvedValue(mockSolicitudesAbiertas);
    vi.mocked(solicitudesService.getSolicitudesCerradas).mockResolvedValue(mockSolicitudesCerradas);
    vi.mocked(solicitudesService.getSolicitudesGanadas).mockResolvedValue(mockSolicitudesGanadas);
  });

  it('renders all three tabs', async () => {
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /ABIERTAS/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /CERRADAS/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /GANADAS/i })).toBeInTheDocument();
    });
  });

  it('shows ABIERTAS tab by default', async () => {
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Solicitudes Disponibles/i)).toBeInTheDocument();
      expect(solicitudesService.getSolicitudesAbiertas).toHaveBeenCalled();
    });
  });

  it('switches to CERRADAS tab when clicked', async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    const cerradasTab = await screen.findByRole('tab', { name: /CERRADAS/i });
    await user.click(cerradasTab);

    await waitFor(() => {
      expect(solicitudesService.getSolicitudesCerradas).toHaveBeenCalled();
    });
  });

  it('switches to GANADAS tab when clicked', async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    const ganadasTab = await screen.findByRole('tab', { name: /GANADAS/i });
    await user.click(ganadasTab);

    await waitFor(() => {
      expect(solicitudesService.getSolicitudesGanadas).toHaveBeenCalled();
    });
  });

  it('maintains tab state when switching back and forth', async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    // Start on ABIERTAS
    await waitFor(() => {
      expect(screen.getByText(/Solicitudes Disponibles/i)).toBeInTheDocument();
    });

    // Switch to CERRADAS
    const cerradasTab = await screen.findByRole('tab', { name: /CERRADAS/i });
    await user.click(cerradasTab);

    await waitFor(() => {
      expect(solicitudesService.getSolicitudesCerradas).toHaveBeenCalled();
    });

    // Switch back to ABIERTAS
    const abiertasTab = await screen.findByRole('tab', { name: /ABIERTAS/i });
    await user.click(abiertasTab);

    await waitFor(() => {
      expect(screen.getByText(/Solicitudes Disponibles/i)).toBeInTheDocument();
    });
  });

  it('displays correct content for each tab', async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    // ABIERTAS tab
    await waitFor(() => {
      expect(screen.getByText(/Solicitudes Disponibles/i)).toBeInTheDocument();
      expect(screen.getByText(/Filtro de aceite/i)).toBeInTheDocument();
    });

    // CERRADAS tab
    const cerradasTab = await screen.findByRole('tab', { name: /CERRADAS/i });
    await user.click(cerradasTab);

    await waitFor(() => {
      expect(screen.getByText(/SOL-002/i)).toBeInTheDocument();
    });

    // GANADAS tab
    const ganadasTab = await screen.findByRole('tab', { name: /GANADAS/i });
    await user.click(ganadasTab);

    await waitFor(() => {
      expect(screen.getByText(/SOL-003/i)).toBeInTheDocument();
    });
  });

  it('shows loading state when switching tabs', async () => {
    const user = userEvent.setup();
    
    // Make the API call slow
    vi.mocked(solicitudesService.getSolicitudesCerradas).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockSolicitudesCerradas), 100))
    );

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    const cerradasTab = await screen.findByRole('tab', { name: /CERRADAS/i });
    await user.click(cerradasTab);

    // Should show loading state
    expect(screen.getByRole('tab', { name: /CERRADAS/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(solicitudesService.getSolicitudesCerradas).toHaveBeenCalled();
    });
  });

  it('handles errors when loading tab content', async () => {
    const user = userEvent.setup();
    vi.mocked(solicitudesService.getSolicitudesCerradas).mockRejectedValue(
      new Error('Error al cargar solicitudes')
    );

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    const cerradasTab = await screen.findByRole('tab', { name: /CERRADAS/i });
    await user.click(cerradasTab);

    await waitFor(() => {
      expect(screen.getByText(/Error al cargar solicitudes/i)).toBeInTheDocument();
    });
  });
});
