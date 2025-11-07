export interface User {
  id: string;
  email: string;
  nombre: string;
  rol: 'ADMIN' | 'ADVISOR' | 'ANALYST' | 'SUPPORT' | 'CLIENT';
  estado: 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO';
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}