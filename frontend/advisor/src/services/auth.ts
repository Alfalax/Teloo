import { apiClient } from '@/lib/axios';
import { LoginRequest, LoginResponse, User } from '@/types/auth';

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
    
    // Verify user is an advisor
    if (response.data.user.rol !== 'ADVISOR') {
      throw new Error('Solo asesores pueden acceder a este portal');
    }
    
    return response.data;
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },

  async refreshToken(refreshToken: string): Promise<{ access_token: string }> {
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  // Local storage helpers
  saveTokens(tokens: { access_token: string; refresh_token: string }): void {
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
  },

  saveUser(user: User): void {
    localStorage.setItem('user', JSON.stringify(user));
  },

  getStoredUser(): User | null {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  getStoredToken(): string | null {
    return localStorage.getItem('access_token');
  },

  getStoredRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  },

  clearStorage(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
};
