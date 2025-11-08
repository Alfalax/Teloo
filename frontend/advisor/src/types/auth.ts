export interface User {
  id: string;
  email: string;
  nombre: string;
  rol: 'ADVISOR' | 'ADMIN' | 'ANALYST' | 'SUPPORT' | 'CLIENT';
  asesor_id?: string;
  estado: 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO';
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
