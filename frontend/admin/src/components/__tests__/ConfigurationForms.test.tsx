import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PesosEscalamientoForm } from '@/components/configuracion/PesosEscalamientoForm';
import { ConfiguracionPage } from '@/pages/ConfiguracionPage';
import { BrowserRouter } from 'react-router-dom';
import type { CategoriaConfiguracion } from '@/types/configuracion';

// Mock the configuration service
vi.mock('@/services/configuracion', () => ({
  configuracionService: {
    validatePesos: vi.fn(),
    getConfiguracion: vi.fn(),
    updateConfiguracion: vi.fn(),
    resetConfiguracion: vi.fn(),
  },
}));

// Mock the configuration hook
const mockUseConfiguracion = {
  configuracion: {
    pesos_escalamiento: {
      proximidad: 0.4,
      actividad: 0.25,
      desempeno: 0.2,
      confianza: 0.15,
    },
    umbrales_niveles: {
      nivel1_min: 4.5,
      nivel2_min: 4.0,
      nivel3_min: 3.5,
      nivel4_min: 3.0,
    },
  },
  summary: {
    estadisticas: {
      total_categorias: 6,
      total_parametros: 24,
      ultima_modificacion: '2024-01-15T10:30:00Z',
      modificado_por: 'admin@teloo.com',
    },
  },
  isLoading: false,
  error: null,
  updateConfiguracion: vi.fn(),
  resetConfiguracion: vi.fn(),
};

vi.mock('@/hooks/useConfiguracion', () => ({
  useConfiguracion: () => mockUseConfiguracion,
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

describe('Configuration Forms', () => {
  const mockConfiguracionService = vi.mocked(require('@/services/configuracion').configuracionService);

  beforeEach(() => {
    vi.clearAllMocks();
    mockConfiguracionService.validatePesos.mockReturnValue({ valid: true });
  });

  describe('PesosEscalamientoForm', () => {
    const mockData = {
      proximidad: 0.4,
      actividad: 0.25,
      desempeno: 0.2,
      confianza: 0.15,
    };

    const mockCategoria: CategoriaConfiguracion = 'pesos_escalamiento';

    it('renders form fields correctly', () => {
      render(
        <TestWrapper>
          <PesosEscalamientoForm data={mockData} categoria={mockCategoria} />
        </TestWrapper>
      );

      expect(screen.getByLabelText(/Proximidad Geográfica/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Actividad Reciente/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Desempeño Histórico/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Nivel de Confianza/)).toBeInTheDocument();
    });

    it('displays current values correctly', () => {
      render(
        <TestWrapper>
          <PesosEscalamientoForm data={mockData} categoria={mockCategoria} />
        </TestWrapper>
      );

      const proximidadInput = screen.getByDisplayValue('0.4');
      const actividadInput = screen.getByDisplayValue('0.25');
      const desempenoInput = screen.getByDisplayValue('0.2');
      const confianzaInput = screen.getByDisplayValue('0.15');

      expect(proximidadInput).toBeInTheDocument();
      expect(actividadInput).toBeInTheDocument();
      expect(desempenoInput).toBeInTheDocument();
      expect(confianzaInput).toBeInTheDocument();
    });

    it('shows progress bar for weight sum', () => {
      render(
        <TestWrapper>
          <PesosEscalamientoForm data={mockData} categoria={mockCategoria} />
        </TestWrapper>
      );

      expect(screen.getByText('Suma Total de Pesos')).toBeInTheDocument();
      expect(screen.getByText('1.000000')).toBeInTheDocument(); // Sum should be 1.0
    });

    it('updates progress bar when values change', async () => {
      render(
        <TestWrapper>
          <PesosEscalamientoForm data={mockData} categoria={mockCategoria} />
        </TestWrapper>
      );

      const proximidadInput = screen.getByDisplayValue('0.4');
      
      fireEvent.change(proximidadInput, { target: { value: '0.5' } });

      await waitFor(() => {
        expect(screen.getByText('1.100000')).toBeInTheDocument(); // Sum should be 1.1
      });
    });

    it('shows percentage values for each weight', () => {
      render(
        <TestWrapper>
          <PesosEscalamientoForm data={mockData} categoria={mockCategoria} />
        </TestWrapper>
      );

      expect(screen.getByText('Peso actual: 40.0%')).toBeInTheDocument();
      expect(screen.getByText('Peso actual: 25.0%')).toBeInTheDocument();
      expect(screen.getByText('Peso actual: 20.0%')).toBeInTheDocument();
      expect(screen.getByText('Peso actual: 15.0%')).toBeInTheDocument();
    });

    it('disables submit button when sum is not 1.0', async () => {
      render(
        <TestWrapper>
          <PesosEscalamientoForm data={mockData} categoria={mockCategoria} />
        </TestWrapper>
      );

      const proximidadInput = screen.getByDisplayValue('0.4');
      const submitButton = screen.getByRole('button', { name: /Guardar/ });

      // Change value to make sum != 1.0
      fireEvent.change(proximidadInput, { target: { value: '0.5' } });

      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });

    it('enables submit button when sum is 1.0 and form is dirty', async () => {
      render(
        <TestWrapper>
          <PesosEscalamientoForm data={mockData} categoria={mockCategoria} />
        </TestWrapper>
      );

      const proximidadInput = screen.getByDisplayValue('0.4');
      const actividadInput = screen.getByDisplayValue('0.25');
      const submitButton = screen.getByRole('button', { name: /Guardar/ });

      // Make changes that keep sum = 1.0
      fireEvent.change(proximidadInput, { target: { value: '0.35' } });
      fireEvent.change(actividadInput, { target: { value: '0.3' } });

      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });

    it('calls updateConfiguracion on form submit', async () => {
      mockConfiguracionService.validatePesos.mockReturnValue({ valid: true });

      render(
        <TestWrapper>
          <PesosEscalamientoForm data={mockData} categoria={mockCategoria} />
        </TestWrapper>
      );

      const proximidadInput = screen.getByDisplayValue('0.4');
      const submitButton = screen.getByRole('button', { name: /Guardar/ });

      // Make a small change
      fireEvent.change(proximidadInput, { target: { value: '0.35' } });
      fireEvent.change(screen.getByDisplayValue('0.25'), { target: { value: '0.3' } });

      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockUseConfiguracion.updateConfiguracion).toHaveBeenCalledWith(
          mockCategoria,
          expect.objectContaining({
            proximidad: 0.35,
            actividad: 0.3,
            desempeno: 0.2,
            confianza: 0.15,
          })
        );
      });
    });

    it('shows validation error when weights are invalid', async () => {
      mockConfiguracionService.validatePesos.mockReturnValue({ 
        valid: false, 
        error: 'Los pesos deben sumar exactamente 1.0' 
      });

      render(
        <TestWrapper>
          <PesosEscalamientoForm data={mockData} categoria={mockCategoria} />
        </TestWrapper>
      );

      const proximidadInput = screen.getByDisplayValue('0.4');
      const submitButton = screen.getByRole('button', { name: /Guardar/ });

      fireEvent.change(proximidadInput, { target: { value: '0.35' } });
      fireEvent.change(screen.getByDisplayValue('0.25'), { target: { value: '0.3' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Los pesos deben sumar exactamente 1.0')).toBeInTheDocument();
      });
    });

    it('shows success message after successful save', async () => {
      mockConfiguracionService.validatePesos.mockReturnValue({ valid: true });
      mockUseConfiguracion.updateConfiguracion.mockResolvedValue(undefined);

      render(
        <TestWrapper>
          <PesosEscalamientoForm data={mockData} categoria={mockCategoria} />
        </TestWrapper>
      );

      const proximidadInput = screen.getByDisplayValue('0.4');
      const submitButton = screen.getByRole('button', { name: /Guardar/ });

      fireEvent.change(proximidadInput, { target: { value: '0.35' } });
      fireEvent.change(screen.getByDisplayValue('0.25'), { target: { value: '0.3' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Configuración guardada exitosamente')).toBeInTheDocument();
      });
    });

    it('shows loading state during save', async () => {
      mockConfiguracionService.validatePesos.mockReturnValue({ valid: true });
      mockUseConfiguracion.updateConfiguracion.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <TestWrapper>
          <PesosEscalamientoForm data={mockData} categoria={mockCategoria} />
        </TestWrapper>
      );

      const proximidadInput = screen.getByDisplayValue('0.4');
      const submitButton = screen.getByRole('button', { name: /Guardar/ });

      fireEvent.change(proximidadInput, { target: { value: '0.35' } });
      fireEvent.change(screen.getByDisplayValue('0.25'), { target: { value: '0.3' } });
      fireEvent.click(submitButton);

      expect(screen.getByText('Guardando...')).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
    });
  });

  describe('ConfiguracionPage', () => {
    it('renders page header correctly', () => {
      render(
        <TestWrapper>
          <ConfiguracionPage />
        </TestWrapper>
      );

      expect(screen.getByText('Configuración')).toBeInTheDocument();
      expect(screen.getByText('Gestión de parámetros del sistema, usuarios y permisos')).toBeInTheDocument();
    });

    it('renders configuration statistics', () => {
      render(
        <TestWrapper>
          <ConfiguracionPage />
        </TestWrapper>
      );

      expect(screen.getByText('6 categorías')).toBeInTheDocument();
      expect(screen.getByText('24 parámetros')).toBeInTheDocument();
    });

    it('renders last modification info', () => {
      render(
        <TestWrapper>
          <ConfiguracionPage />
        </TestWrapper>
      );

      expect(screen.getByText(/Última modificación:/)).toBeInTheDocument();
      expect(screen.getByText('por admin@teloo.com')).toBeInTheDocument();
    });

    it('renders tab navigation', () => {
      render(
        <TestWrapper>
          <ConfiguracionPage />
        </TestWrapper>
      );

      expect(screen.getByRole('tab', { name: /Parámetros del Sistema/ })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Gestión de Usuarios/ })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Roles y Permisos/ })).toBeInTheDocument();
    });

    it('shows reset button', () => {
      render(
        <TestWrapper>
          <ConfiguracionPage />
        </TestWrapper>
      );

      expect(screen.getByRole('button', { name: /Reset Completo/ })).toBeInTheDocument();
    });

    it('handles reset confirmation', () => {
      // Mock window.confirm
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

      render(
        <TestWrapper>
          <ConfiguracionPage />
        </TestWrapper>
      );

      const resetButton = screen.getByRole('button', { name: /Reset Completo/ });
      fireEvent.click(resetButton);

      expect(confirmSpy).toHaveBeenCalledWith(
        '¿Está seguro de que desea resetear toda la configuración a valores por defecto? Esta acción no se puede deshacer.'
      );
      expect(mockUseConfiguracion.resetConfiguracion).toHaveBeenCalled();

      confirmSpy.mockRestore();
    });

    it('shows error alert when there is an error', () => {
      const errorUseConfiguracion = {
        ...mockUseConfiguracion,
        error: 'Error loading configuration',
      };

      vi.mocked(require('@/hooks/useConfiguracion').useConfiguracion).mockReturnValue(errorUseConfiguracion);

      render(
        <TestWrapper>
          <ConfiguracionPage />
        </TestWrapper>
      );

      expect(screen.getByText('Error loading configuration')).toBeInTheDocument();
    });
  });
});