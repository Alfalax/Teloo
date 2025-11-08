import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardPage from '@/pages/DashboardPage';
import { solicitudesService } from '@/services/solicitudes';
import { ofertasService } from '@/services/ofertas';

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

describe('E2E: Complete Offer Flow', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const mockSolicitud = {
    id: 'SOL-001',
    cliente_id: 'CLI-001',
    estado: 'ABIERTA' as const,
    nivel_actual: 1,
    ciudad_origen: 'Bogotá',
    departamento_origen: 'Cundinamarca',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    repuestos: [
      {
        id: 'REP-001',
        nombre: 'Filtro de aceite',
        codigo: 'FO-123',
        marca_vehiculo: 'Toyota',
        linea_vehiculo: 'Corolla',
        anio_vehiculo: 2015,
        cantidad: 1,
      },
      {
        id: 'REP-002',
        nombre: 'Pastillas de freno',
        codigo: 'PF-456',
        marca_vehiculo: 'Toyota',
        linea_vehiculo: 'Corolla',
        anio_vehiculo: 2015,
        cantidad: 2,
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(solicitudesService.getSolicitudesAbiertas).mockResolvedValue([mockSolicitud]);
    vi.mocked(solicitudesService.getSolicitudesCerradas).mockResolvedValue([]);
    vi.mocked(solicitudesService.getSolicitudesGanadas).mockResolvedValue([]);
  });

  it('completes full flow: view solicitud -> create offer -> submit successfully', async () => {
    const user = userEvent.setup();
    vi.mocked(ofertasService.createOferta).mockResolvedValue({} as any);

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    // Step 1: Wait for solicitudes to load
    await waitFor(() => {
      expect(screen.getByText(/Solicitudes Disponibles/i)).toBeInTheDocument();
      expect(screen.getByText(/Filtro de aceite/i)).toBeInTheDocument();
    });

    // Step 2: Click "Hacer Oferta" button
    const hacerOfertaButton = screen.getByRole('button', { name: /Hacer Oferta/i });
    await user.click(hacerOfertaButton);

    // Step 3: Modal should open with solicitud details
    await waitFor(() => {
      expect(screen.getByText(/Crear Oferta/i)).toBeInTheDocument();
      expect(screen.getByText(/Toyota Corolla 2015/i)).toBeInTheDocument();
    });

    // Step 4: Fill in offer details for first repuesto
    const precioInputs = screen.getAllByPlaceholderText(/1000 - 50000000/i);
    await user.type(precioInputs[0], '50000');

    const garantiaInputs = screen.getAllByPlaceholderText(/1 - 60/i);
    await user.type(garantiaInputs[0], '12');

    // Step 5: Fill in offer details for second repuesto
    await user.type(precioInputs[1], '120000');
    await user.type(garantiaInputs[1], '24');

    // Step 6: Fill in delivery time
    const tiempoInput = screen.getByPlaceholderText(/0 - 90/i);
    await user.type(tiempoInput, '5');

    // Step 7: Add observations
    const observacionesInput = screen.getByPlaceholderText(/Información adicional/i);
    await user.type(observacionesInput, 'Repuestos originales de alta calidad');

    // Step 8: Verify total is calculated correctly
    await waitFor(() => {
      // Filtro: 50000 * 1 = 50000
      // Pastillas: 120000 * 2 = 240000
      // Total: 290000
      expect(screen.getByText(/290,000/i)).toBeInTheDocument();
    });

    // Step 9: Submit the offer
    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    // Step 10: Verify API was called with correct data
    await waitFor(() => {
      expect(ofertasService.createOferta).toHaveBeenCalledWith({
        solicitud_id: 'SOL-001',
        tiempo_entrega_dias: 5,
        observaciones: 'Repuestos originales de alta calidad',
        detalles: [
          {
            repuesto_solicitado_id: 'REP-001',
            precio_unitario: 50000,
            cantidad: 1,
            garantia_meses: 12,
          },
          {
            repuesto_solicitado_id: 'REP-002',
            precio_unitario: 120000,
            cantidad: 2,
            garantia_meses: 24,
          },
        ],
      });
    });

    // Step 11: Modal should close after successful submission
    await waitFor(() => {
      expect(screen.queryByText(/Crear Oferta/i)).not.toBeInTheDocument();
    });
  });

  it('completes partial offer flow: deselect one repuesto and submit', async () => {
    const user = userEvent.setup();
    vi.mocked(ofertasService.createOferta).mockResolvedValue({} as any);

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    // Wait for solicitudes to load
    await waitFor(() => {
      expect(screen.getByText(/Filtro de aceite/i)).toBeInTheDocument();
    });

    // Click "Hacer Oferta"
    const hacerOfertaButton = screen.getByRole('button', { name: /Hacer Oferta/i });
    await user.click(hacerOfertaButton);

    await waitFor(() => {
      expect(screen.getByText(/Crear Oferta/i)).toBeInTheDocument();
    });

    // Deselect second repuesto
    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[1]);

    // Fill in details for first repuesto only
    const precioInputs = screen.getAllByPlaceholderText(/1000 - 50000000/i);
    await user.type(precioInputs[0], '50000');

    const garantiaInputs = screen.getAllByPlaceholderText(/1 - 60/i);
    await user.type(garantiaInputs[0], '12');

    const tiempoInput = screen.getByPlaceholderText(/0 - 90/i);
    await user.type(tiempoInput, '3');

    // Submit
    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    // Verify only one repuesto was included
    await waitFor(() => {
      expect(ofertasService.createOferta).toHaveBeenCalledWith({
        solicitud_id: 'SOL-001',
        tiempo_entrega_dias: 3,
        observaciones: undefined,
        detalles: [
          {
            repuesto_solicitado_id: 'REP-001',
            precio_unitario: 50000,
            cantidad: 1,
            garantia_meses: 12,
          },
        ],
      });
    });
  });

  it('handles validation errors and allows correction', async () => {
    const user = userEvent.setup();
    vi.mocked(ofertasService.createOferta).mockResolvedValue({} as any);

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Filtro de aceite/i)).toBeInTheDocument();
    });

    const hacerOfertaButton = screen.getByRole('button', { name: /Hacer Oferta/i });
    await user.click(hacerOfertaButton);

    await waitFor(() => {
      expect(screen.getByText(/Crear Oferta/i)).toBeInTheDocument();
    });

    // Try to submit without filling anything
    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/tiempo de entrega es requerido/i)).toBeInTheDocument();
    });

    // Fill in invalid precio (too low)
    const precioInputs = screen.getAllByPlaceholderText(/1000 - 50000000/i);
    await user.type(precioInputs[0], '500');

    const tiempoInput = screen.getByPlaceholderText(/0 - 90/i);
    await user.type(tiempoInput, '5');

    await user.click(submitButton);

    // Should show precio validation error
    await waitFor(() => {
      expect(screen.getByText(/Precio debe estar entre/i)).toBeInTheDocument();
    });

    // Correct the precio
    await user.clear(precioInputs[0]);
    await user.type(precioInputs[0], '50000');

    // Add garantia
    const garantiaInputs = screen.getAllByPlaceholderText(/1 - 60/i);
    await user.type(garantiaInputs[0], '12');

    // Deselect second repuesto to make it valid
    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[1]);

    // Now submit should work
    await user.click(submitButton);

    await waitFor(() => {
      expect(ofertasService.createOferta).toHaveBeenCalled();
    });
  });

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup();
    const errorMessage = 'La solicitud ya no está disponible';
    vi.mocked(ofertasService.createOferta).mockRejectedValue({
      response: { data: { detail: errorMessage } },
    });

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Filtro de aceite/i)).toBeInTheDocument();
    });

    const hacerOfertaButton = screen.getByRole('button', { name: /Hacer Oferta/i });
    await user.click(hacerOfertaButton);

    await waitFor(() => {
      expect(screen.getByText(/Crear Oferta/i)).toBeInTheDocument();
    });

    // Fill in valid data
    const precioInputs = screen.getAllByPlaceholderText(/1000 - 50000000/i);
    await user.type(precioInputs[0], '50000');

    const garantiaInputs = screen.getAllByPlaceholderText(/1 - 60/i);
    await user.type(garantiaInputs[0], '12');

    const tiempoInput = screen.getByPlaceholderText(/0 - 90/i);
    await user.type(tiempoInput, '5');

    // Deselect second repuesto
    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[1]);

    // Submit
    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    // Modal should still be open
    expect(screen.getByText(/Crear Oferta/i)).toBeInTheDocument();
  });

  it('allows canceling offer creation', async () => {
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Filtro de aceite/i)).toBeInTheDocument();
    });

    const hacerOfertaButton = screen.getByRole('button', { name: /Hacer Oferta/i });
    await user.click(hacerOfertaButton);

    await waitFor(() => {
      expect(screen.getByText(/Crear Oferta/i)).toBeInTheDocument();
    });

    // Fill in some data
    const precioInputs = screen.getAllByPlaceholderText(/1000 - 50000000/i);
    await user.type(precioInputs[0], '50000');

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /Cancelar/i });
    await user.click(cancelButton);

    // Modal should close
    await waitFor(() => {
      expect(screen.queryByText(/Crear Oferta/i)).not.toBeInTheDocument();
    });

    // Should not have called the API
    expect(ofertasService.createOferta).not.toHaveBeenCalled();
  });

  it('refreshes solicitudes list after successful offer submission', async () => {
    const user = userEvent.setup();
    vi.mocked(ofertasService.createOferta).mockResolvedValue({} as any);

    // Mock will be called twice: initial load and after submission
    let callCount = 0;
    vi.mocked(solicitudesService.getSolicitudesAbiertas).mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve([mockSolicitud]);
      } else {
        // After submission, solicitud is no longer available
        return Promise.resolve([]);
      }
    });

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </BrowserRouter>
    );

    // Initial load
    await waitFor(() => {
      expect(screen.getByText(/Filtro de aceite/i)).toBeInTheDocument();
    });

    const hacerOfertaButton = screen.getByRole('button', { name: /Hacer Oferta/i });
    await user.click(hacerOfertaButton);

    await waitFor(() => {
      expect(screen.getByText(/Crear Oferta/i)).toBeInTheDocument();
    });

    // Fill and submit
    const precioInputs = screen.getAllByPlaceholderText(/1000 - 50000000/i);
    await user.type(precioInputs[0], '50000');

    const garantiaInputs = screen.getAllByPlaceholderText(/1 - 60/i);
    await user.type(garantiaInputs[0], '12');

    const tiempoInput = screen.getByPlaceholderText(/0 - 90/i);
    await user.type(tiempoInput, '5');

    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[1]);

    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    // Wait for modal to close and list to refresh
    await waitFor(() => {
      expect(screen.queryByText(/Crear Oferta/i)).not.toBeInTheDocument();
    });

    // List should be refreshed (called at least twice)
    await waitFor(() => {
      expect(solicitudesService.getSolicitudesAbiertas).toHaveBeenCalledTimes(2);
    });
  });
});
