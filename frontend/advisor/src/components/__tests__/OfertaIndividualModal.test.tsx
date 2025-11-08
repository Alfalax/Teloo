import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import OfertaIndividualModal from '../ofertas/OfertaIndividualModal';
import { ofertasService } from '@/services/ofertas';

// Mock the ofertas service
vi.mock('@/services/ofertas', () => ({
  ofertasService: {
    createOferta: vi.fn(),
  },
}));

describe('OfertaIndividualModal', () => {
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

  const mockOnClose = vi.fn();
  const mockOnSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders modal with solicitud information', () => {
    render(
      <OfertaIndividualModal
        solicitud={mockSolicitud}
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    expect(screen.getByText(/Crear Oferta/i)).toBeInTheDocument();
    expect(screen.getByText(/Toyota Corolla 2015/i)).toBeInTheDocument();
    expect(screen.getByText(/Filtro de aceite/i)).toBeInTheDocument();
    expect(screen.getByText(/Pastillas de freno/i)).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();
    render(
      <OfertaIndividualModal
        solicitud={mockSolicitud}
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/tiempo de entrega es requerido/i)).toBeInTheDocument();
    });
  });

  it('validates precio range (1000-50000000)', async () => {
    const user = userEvent.setup();
    render(
      <OfertaIndividualModal
        solicitud={mockSolicitud}
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const precioInputs = screen.getAllByPlaceholderText(/1000 - 50000000/i);
    await user.type(precioInputs[0], '500');

    const tiempoInput = screen.getByPlaceholderText(/0 - 90/i);
    await user.type(tiempoInput, '5');

    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Precio debe estar entre/i)).toBeInTheDocument();
    });
  });

  it('validates garantia range (1-60 months)', async () => {
    const user = userEvent.setup();
    render(
      <OfertaIndividualModal
        solicitud={mockSolicitud}
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const precioInputs = screen.getAllByPlaceholderText(/1000 - 50000000/i);
    await user.type(precioInputs[0], '50000');

    const garantiaInputs = screen.getAllByPlaceholderText(/1 - 60/i);
    await user.type(garantiaInputs[0], '70');

    const tiempoInput = screen.getByPlaceholderText(/0 - 90/i);
    await user.type(tiempoInput, '5');

    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Garantía debe estar entre 1 y 60 meses/i)).toBeInTheDocument();
    });
  });

  it('validates tiempo entrega range (0-90 days)', async () => {
    const user = userEvent.setup();
    render(
      <OfertaIndividualModal
        solicitud={mockSolicitud}
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const tiempoInput = screen.getByPlaceholderText(/0 - 90/i);
    await user.type(tiempoInput, '100');

    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/tiempo de entrega debe estar entre 0 y 90 días/i)).toBeInTheDocument();
    });
  });

  it('allows selecting/deselecting repuestos', async () => {
    const user = userEvent.setup();
    render(
      <OfertaIndividualModal
        solicitud={mockSolicitud}
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes).toHaveLength(2);

    // Deselect first repuesto
    await user.click(checkboxes[0]);

    // Verify the input fields are disabled/hidden for deselected repuesto
    const precioInputs = screen.queryAllByPlaceholderText(/1000 - 50000000/i);
    expect(precioInputs).toHaveLength(1); // Only one visible now
  });

  it('calculates total estimado correctly', async () => {
    const user = userEvent.setup();
    render(
      <OfertaIndividualModal
        solicitud={mockSolicitud}
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const precioInputs = screen.getAllByPlaceholderText(/1000 - 50000000/i);
    await user.type(precioInputs[0], '50000'); // Filtro: 50000 * 1 = 50000
    await user.type(precioInputs[1], '120000'); // Pastillas: 120000 * 2 = 240000

    await waitFor(() => {
      expect(screen.getByText(/290,000/i)).toBeInTheDocument(); // Total: 290000
    });
  });

  it('submits valid oferta successfully', async () => {
    const user = userEvent.setup();
    vi.mocked(ofertasService.createOferta).mockResolvedValue({} as any);

    render(
      <OfertaIndividualModal
        solicitud={mockSolicitud}
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Fill in all required fields
    const precioInputs = screen.getAllByPlaceholderText(/1000 - 50000000/i);
    await user.type(precioInputs[0], '50000');
    await user.type(precioInputs[1], '120000');

    const garantiaInputs = screen.getAllByPlaceholderText(/1 - 60/i);
    await user.type(garantiaInputs[0], '12');
    await user.type(garantiaInputs[1], '24');

    const tiempoInput = screen.getByPlaceholderText(/0 - 90/i);
    await user.type(tiempoInput, '5');

    const observacionesInput = screen.getByPlaceholderText(/Información adicional/i);
    await user.type(observacionesInput, 'Repuestos originales');

    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(ofertasService.createOferta).toHaveBeenCalledWith({
        solicitud_id: 'SOL-001',
        tiempo_entrega_dias: 5,
        observaciones: 'Repuestos originales',
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
      expect(mockOnSuccess).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('displays error message on submission failure', async () => {
    const user = userEvent.setup();
    const errorMessage = 'Error al crear la oferta';
    vi.mocked(ofertasService.createOferta).mockRejectedValue({
      response: { data: { detail: errorMessage } },
    });

    render(
      <OfertaIndividualModal
        solicitud={mockSolicitud}
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Fill in valid data
    const precioInputs = screen.getAllByPlaceholderText(/1000 - 50000000/i);
    await user.type(precioInputs[0], '50000');

    const garantiaInputs = screen.getAllByPlaceholderText(/1 - 60/i);
    await user.type(garantiaInputs[0], '12');

    const tiempoInput = screen.getByPlaceholderText(/0 - 90/i);
    await user.type(tiempoInput, '5');

    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('validates at least one repuesto must be included', async () => {
    const user = userEvent.setup();
    render(
      <OfertaIndividualModal
        solicitud={mockSolicitud}
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Deselect all repuestos
    const checkboxes = screen.getAllByRole('checkbox');
    for (const checkbox of checkboxes) {
      await user.click(checkbox);
    }

    const tiempoInput = screen.getByPlaceholderText(/0 - 90/i);
    await user.type(tiempoInput, '5');

    const submitButton = screen.getByRole('button', { name: /Enviar Oferta/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Debe incluir al menos un repuesto/i)).toBeInTheDocument();
    });
  });
});
