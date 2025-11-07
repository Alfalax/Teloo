import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthProvider } from '@/contexts/AuthContext';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { AsesoresPage } from '@/pages/AsesoresPage';
import { ConfiguracionPage } from '@/pages/ConfiguracionPage';
import { User } from '@/types/auth';

// Mock all services
vi.mock('@/services/auth', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    getStoredUser: vi.fn(),
    getStoredToken: vi.fn(),
    getStoredRefreshToken: vi.fn(),
    saveTokens: vi.fn(),
    saveUser: vi.fn(),
    clearStorage: vi.fn(),
  },
}));

vi.mock('@/services/analytics', () => ({
  analyticsService: {
    getDashboardPrincipal: vi.fn(),
    getGraficosDelMes: vi.fn(),
    getTopSolicitudesAbiertas: vi.fn(),
    exportToJSON: vi.fn(),
  },
}));

vi.mock('@/services/asesores', () => ({
  asesoresService: {
    getAsesores: vi.fn(),
    createAsesor: vi.fn(),
    updateAsesor: vi.fn(),
    deleteAsesor: vi.fn(),
    updateEstado: vi.fn(),
    importExcel: vi.fn(),
    exportExcel: vi.fn(),
  },
}));

vi.mock('@/services/configuracion', () => ({
  configuracionService: {
    getConfiguracion: vi.fn(),
    updateConfiguracion: vi.fn(),
    resetConfiguracion: vi.fn(),
    validatePesos: vi.fn(),
  },
}));

// Mock hooks
vi.mock('@/hooks/useDashboard', () => ({
  useDashboardData: () => ({
    dashboardData: {
      kpis: {
        ofertas_totales_asignadas: { valor: 1234, cambio_porcentual: 12.5 },
        monto_total_aceptado: { valor: 45200000, cambio_porcentual: 8.3 },
        solicitudes_abiertas: { valor: 89, cambio_porcentual: -2.1 },
        tasa_conversion: { valor: 68.4, cambio_porcentual: 5.2 },
      }
    },
    graficosData: [],
    topSolicitudes: [],
    isLoading: false,
    hasError: false,
    refetchDashboard: vi.fn(),
    periodo: { inicio: '2024-01-01', fin: '2024-01-31' },
  }),
}));

vi.mock('@/hooks/useConfiguracion', () => ({
  useConfiguracion: () => ({
    configuracion: {
      pesos_escalamiento: {
        proximidad: 0.4,
        actividad: 0.25,
        desempeno: 0.2,
        confianza: 0.15,
      },
    },
    summary: {
      estadisticas: {
        total_categorias: 6,
        total_parametros: 24,
        ultima_modificacion: '2024-01-15T10:30:00Z',
      },
    },
    isLoading: false,
    error: null,
    updateConfiguracion: vi.fn(),
    resetConfiguracion: vi.fn(),
  }),
}));

const mockAdminUser: User = {
  id: 'user-1',
  nombre: 'Admin User',
  email: 'admin@teloo.com',
  rol: 'ADMIN',
  estado: 'ACTIVO',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const TestWrapper = ({ 
  children, 
  initialEntries = ['/'] 
}: { 
  children: React.ReactNode;
  initialEntries?: string[];
}) => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <MemoryRouter initialEntries={initialEntries}>
        {children}
      </MemoryRouter>
    </AuthProvider>
  </QueryClientProvider>
);

describe('E2E Critical Flows', () => {
  const mockAuthService = vi.mocked(require('@/services/auth').authService);
  const mockAsesoresService = vi.mocked(require('@/services/asesores').asesoresService);
  const mockConfiguracionService = vi.mocked(require('@/services/configuracion').configuracionService);

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    
    // Default mocks
    mockAuthService.getStoredUser.mockReturnValue(null);
    mockAuthService.getStoredToken.mockReturnValue(null);
    mockAuthService.getStoredRefreshToken.mockReturnValue(null);
    mockConfiguracionService.validatePesos.mockReturnValue({ valid: true });
  });

  describe('Login Flow', () => {
    it('completes successful login flow', async () => {
      mockAuthService.login.mockResolvedValue({
        access_token: 'new-token',
        refresh_token: 'new-refresh-token',
        user: mockAdminUser,
      });

      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      // Fill login form
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Contraseña');
      const submitButton = screen.getByRole('button', { name: /iniciar sesión/i });

      fireEvent.change(emailInput, { target: { value: 'admin@teloo.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockAuthService.login).toHaveBeenCalledWith({
          email: 'admin@teloo.com',
          password: 'password123',
        });
      });

      expect(mockAuthService.saveTokens).toHaveBeenCalledWith({
        access_token: 'new-token',
        refresh_token: 'new-refresh-token',
      });
      expect(mockAuthService.saveUser).toHaveBeenCalledWith(mockAdminUser);
    });

    it('handles login validation errors', async () => {
      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /iniciar sesión/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Email inválido')).toBeInTheDocument();
        expect(screen.getByText('La contraseña debe tener al menos 6 caracteres')).toBeInTheDocument();
      });
    });

    it('handles login API errors', async () => {
      mockAuthService.login.mockRejectedValue(new Error('Invalid credentials'));

      render(
        <TestWrapper>
          <LoginPage />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Contraseña');
      const submitButton = screen.getByRole('button', { name: /iniciar sesión/i });

      fireEvent.change(emailInput, { target: { value: 'admin@teloo.com' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockAuthService.login).toHaveBeenCalled();
      });
    });
  });

  describe('Dashboard Navigation Flow', () => {
    beforeEach(() => {
      // Mock authenticated state
      mockAuthService.getStoredUser.mockReturnValue(mockAdminUser);
      mockAuthService.getStoredToken.mockReturnValue('valid-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('valid-refresh-token');
      mockAuthService.getCurrentUser.mockResolvedValue(mockAdminUser);
    });

    it('loads dashboard with KPIs and charts', async () => {
      render(
        <TestWrapper>
          <DashboardPage />
        </TestWrapper>
      );

      // Wait for component to load
      await waitFor(() => {
        expect(screen.getByText('Dashboard Principal')).toBeInTheDocument();
      });

      // Check KPIs are displayed
      expect(screen.getByText('Ofertas Totales Asignadas')).toBeInTheDocument();
      expect(screen.getByText('Monto Total Aceptado')).toBeInTheDocument();
      expect(screen.getByText('Solicitudes Abiertas')).toBeInTheDocument();
      expect(screen.getByText('Tasa de Conversión')).toBeInTheDocument();

      // Check sections are present
      expect(screen.getByText('Solicitudes del Mes')).toBeInTheDocument();
      expect(screen.getByText('Top 15 Solicitudes Abiertas')).toBeInTheDocument();
      expect(screen.getByText('Actividad Reciente')).toBeInTheDocument();
    });

    it('switches between dashboard tabs', async () => {
      render(
        <TestWrapper>
          <DashboardPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Dashboard Principal')).toBeInTheDocument();
      });

      // Switch to Analytics tab
      const analyticsTab = screen.getByRole('tab', { name: /Analytics Completo/ });
      fireEvent.click(analyticsTab);

      // Should show analytics content
      expect(screen.getByRole('tabpanel')).toBeInTheDocument();
    });

    it('handles dashboard refresh', async () => {
      const mockRefetch = vi.fn();
      
      // Mock the hook to return our mock function
      vi.mocked(require('@/hooks/useDashboard').useDashboardData).mockReturnValue({
        dashboardData: { kpis: {} },
        graficosData: [],
        topSolicitudes: [],
        isLoading: false,
        hasError: false,
        refetchDashboard: mockRefetch,
        periodo: { inicio: '2024-01-01', fin: '2024-01-31' },
      });

      render(
        <TestWrapper>
          <DashboardPage />
        </TestWrapper>
      );

      const refreshButton = screen.getByRole('button', { name: /Actualizar/ });
      fireEvent.click(refreshButton);

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Asesores Management Flow', () => {
    beforeEach(() => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdminUser);
      mockAuthService.getStoredToken.mockReturnValue('valid-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('valid-refresh-token');
      mockAuthService.getCurrentUser.mockResolvedValue(mockAdminUser);
      
      mockAsesoresService.getAsesores.mockResolvedValue({
        asesores: [],
        total: 0,
        page: 1,
        limit: 10,
      });
    });

    it('loads asesores page and displays table', async () => {
      render(
        <TestWrapper>
          <AsesoresPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Gestión de Asesores')).toBeInTheDocument();
      });

      // Check table headers
      expect(screen.getByText('Asesor')).toBeInTheDocument();
      expect(screen.getByText('Contacto')).toBeInTheDocument();
      expect(screen.getByText('Estado')).toBeInTheDocument();
    });

    it('handles asesor creation flow', async () => {
      render(
        <TestWrapper>
          <AsesoresPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Gestión de Asesores')).toBeInTheDocument();
      });

      // Click create button
      const createButton = screen.getByRole('button', { name: /Nuevo Asesor/ });
      fireEvent.click(createButton);

      // Should open create dialog/form
      expect(screen.getByText('Crear Nuevo Asesor')).toBeInTheDocument();
    });
  });

  describe('Configuration Management Flow', () => {
    beforeEach(() => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdminUser);
      mockAuthService.getStoredToken.mockReturnValue('valid-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('valid-refresh-token');
      mockAuthService.getCurrentUser.mockResolvedValue(mockAdminUser);
    });

    it('loads configuration page and displays tabs', async () => {
      render(
        <TestWrapper>
          <ConfiguracionPage />
        </TestWrapper>
      );

      expect(screen.getByText('Configuración')).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Parámetros del Sistema/ })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Gestión de Usuarios/ })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Roles y Permisos/ })).toBeInTheDocument();
    });

    it('switches between configuration tabs', async () => {
      render(
        <TestWrapper>
          <ConfiguracionPage />
        </TestWrapper>
      );

      // Switch to Users tab
      const usersTab = screen.getByRole('tab', { name: /Gestión de Usuarios/ });
      fireEvent.click(usersTab);

      await waitFor(() => {
        expect(screen.getByText('Gestión de Usuarios')).toBeInTheDocument();
      });

      // Switch to Roles tab
      const rolesTab = screen.getByRole('tab', { name: /Roles y Permisos/ });
      fireEvent.click(rolesTab);

      await waitFor(() => {
        expect(screen.getByText('Roles y Permisos')).toBeInTheDocument();
      });
    });

    it('handles configuration reset flow', async () => {
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
      const mockReset = vi.fn();

      vi.mocked(require('@/hooks/useConfiguracion').useConfiguracion).mockReturnValue({
        configuracion: {},
        summary: { estadisticas: {} },
        isLoading: false,
        error: null,
        updateConfiguracion: vi.fn(),
        resetConfiguracion: mockReset,
      });

      render(
        <TestWrapper>
          <ConfiguracionPage />
        </TestWrapper>
      );

      const resetButton = screen.getByRole('button', { name: /Reset Completo/ });
      fireEvent.click(resetButton);

      expect(confirmSpy).toHaveBeenCalled();
      expect(mockReset).toHaveBeenCalled();

      confirmSpy.mockRestore();
    });
  });

  describe('Error Handling Flows', () => {
    it('handles authentication errors gracefully', async () => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdminUser);
      mockAuthService.getStoredToken.mockReturnValue('expired-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('expired-refresh');
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Unauthorized'));

      render(
        <TestWrapper>
          <DashboardPage />
        </TestWrapper>
      );

      // Should handle auth error and clear storage
      await waitFor(() => {
        expect(mockAuthService.clearStorage).toHaveBeenCalled();
      });
    });

    it('handles API errors in dashboard', async () => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdminUser);
      mockAuthService.getStoredToken.mockReturnValue('valid-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('valid-refresh-token');
      mockAuthService.getCurrentUser.mockResolvedValue(mockAdminUser);

      // Mock dashboard hook to return error state
      vi.mocked(require('@/hooks/useDashboard').useDashboardData).mockReturnValue({
        dashboardData: null,
        graficosData: [],
        topSolicitudes: [],
        isLoading: false,
        hasError: true,
        refetchDashboard: vi.fn(),
        periodo: { inicio: '2024-01-01', fin: '2024-01-31' },
      });

      render(
        <TestWrapper>
          <DashboardPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Error al cargar datos')).toBeInTheDocument();
        expect(screen.getByText('No se pudieron cargar los datos del dashboard. Verifique la conexión con el servicio de analytics.')).toBeInTheDocument();
      });

      // Should show retry button
      expect(screen.getByRole('button', { name: /Reintentar/ })).toBeInTheDocument();
    });
  });

  describe('Loading States', () => {
    it('shows loading states correctly', async () => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdminUser);
      mockAuthService.getStoredToken.mockReturnValue('valid-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('valid-refresh-token');
      mockAuthService.getCurrentUser.mockResolvedValue(mockAdminUser);

      // Mock loading state
      vi.mocked(require('@/hooks/useDashboard').useDashboardData).mockReturnValue({
        dashboardData: null,
        graficosData: [],
        topSolicitudes: [],
        isLoading: true,
        hasError: false,
        refetchDashboard: vi.fn(),
        periodo: { inicio: '2024-01-01', fin: '2024-01-31' },
      });

      render(
        <TestWrapper>
          <DashboardPage />
        </TestWrapper>
      );

      // Should show loading skeletons
      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });
});