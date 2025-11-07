import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { User } from '@/types/auth';

// Mock the auth service
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

const mockAdminUser: User = {
  id: 'user-1',
  nombre: 'Admin User',
  email: 'admin@teloo.com',
  rol: 'ADMIN',
  estado: 'ACTIVO',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockAdvisorUser: User = {
  ...mockAdminUser,
  id: 'user-2',
  nombre: 'Advisor User',
  rol: 'ADVISOR',
};

describe('Authentication and Protected Routes', () => {
  const mockAuthService = vi.mocked(require('@/services/auth').authService);

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset localStorage
    localStorage.clear();
  });

  describe('ProtectedRoute', () => {
    it('shows loading spinner while checking authentication', () => {
      // Mock loading state
      mockAuthService.getStoredUser.mockReturnValue(null);
      mockAuthService.getStoredToken.mockReturnValue(null);
      mockAuthService.getStoredRefreshToken.mockReturnValue(null);

      render(
        <TestWrapper>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Should show loading spinner initially
      expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('redirects to login when not authenticated', async () => {
      mockAuthService.getStoredUser.mockReturnValue(null);
      mockAuthService.getStoredToken.mockReturnValue(null);
      mockAuthService.getStoredRefreshToken.mockReturnValue(null);

      render(
        <TestWrapper initialEntries={['/dashboard']}>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Wait for auth check to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      // Should not show protected content
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('renders protected content when authenticated with correct role', async () => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdminUser);
      mockAuthService.getStoredToken.mockReturnValue('valid-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('valid-refresh-token');
      mockAuthService.getCurrentUser.mockResolvedValue(mockAdminUser);

      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['ADMIN']}>
            <div>Admin Protected Content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Wait for auth check to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(screen.getByText('Admin Protected Content')).toBeInTheDocument();
    });

    it('shows access denied when user lacks required role', async () => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdvisorUser);
      mockAuthService.getStoredToken.mockReturnValue('valid-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('valid-refresh-token');
      mockAuthService.getCurrentUser.mockResolvedValue(mockAdvisorUser);

      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['ADMIN']}>
            <div>Admin Only Content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Wait for auth check to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(screen.getByText('Acceso Denegado')).toBeInTheDocument();
      expect(screen.getByText('No tienes permisos para acceder a esta página.')).toBeInTheDocument();
      expect(screen.queryByText('Admin Only Content')).not.toBeInTheDocument();
    });

    it('allows access when user has one of multiple required roles', async () => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdvisorUser);
      mockAuthService.getStoredToken.mockReturnValue('valid-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('valid-refresh-token');
      mockAuthService.getCurrentUser.mockResolvedValue(mockAdvisorUser);

      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['ADMIN', 'ADVISOR']}>
            <div>Multi Role Content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Wait for auth check to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(screen.getByText('Multi Role Content')).toBeInTheDocument();
    });

    it('allows access when no specific roles required (default ADMIN)', async () => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdminUser);
      mockAuthService.getStoredToken.mockReturnValue('valid-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('valid-refresh-token');
      mockAuthService.getCurrentUser.mockResolvedValue(mockAdminUser);

      render(
        <TestWrapper>
          <ProtectedRoute>
            <div>Default Protected Content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Wait for auth check to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(screen.getByText('Default Protected Content')).toBeInTheDocument();
    });

    it('handles token validation failure', async () => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdminUser);
      mockAuthService.getStoredToken.mockReturnValue('invalid-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('invalid-refresh-token');
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Token invalid'));

      render(
        <TestWrapper>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Wait for auth check to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      // Should clear storage and not show protected content
      expect(mockAuthService.clearStorage).toHaveBeenCalled();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('AuthContext', () => {
    it('initializes with loading state', () => {
      mockAuthService.getStoredUser.mockReturnValue(null);
      mockAuthService.getStoredToken.mockReturnValue(null);
      mockAuthService.getStoredRefreshToken.mockReturnValue(null);

      render(
        <TestWrapper>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Should show loading initially
      expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('restores authentication from localStorage', async () => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdminUser);
      mockAuthService.getStoredToken.mockReturnValue('stored-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('stored-refresh-token');
      mockAuthService.getCurrentUser.mockResolvedValue(mockAdminUser);

      render(
        <TestWrapper>
          <ProtectedRoute>
            <div>Restored Content</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Wait for auth restoration
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockAuthService.getCurrentUser).toHaveBeenCalled();
      expect(screen.getByText('Restored Content')).toBeInTheDocument();
    });

    it('clears auth state when stored tokens are invalid', async () => {
      mockAuthService.getStoredUser.mockReturnValue(mockAdminUser);
      mockAuthService.getStoredToken.mockReturnValue('expired-token');
      mockAuthService.getStoredRefreshToken.mockReturnValue('expired-refresh-token');
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Unauthorized'));

      render(
        <TestWrapper>
          <ProtectedRoute>
            <div>Should Not Show</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      // Wait for auth check
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockAuthService.clearStorage).toHaveBeenCalled();
      expect(screen.queryByText('Should Not Show')).not.toBeInTheDocument();
    });
  });
});