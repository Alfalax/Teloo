import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { AuthState, User, LoginRequest } from '@/types/auth';
import { authService } from '@/services/auth';

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User }
  | { type: 'SET_TOKENS'; payload: { token: string; refreshToken: string } }
  | { type: 'CLEAR_AUTH' }
  | { type: 'INIT_AUTH'; payload: { user: User; token: string; refreshToken: string } };

const initialState: AuthState = {
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
      };
    
    case 'SET_TOKENS':
      return {
        ...state,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken,
      };
    
    case 'CLEAR_AUTH':
      return {
        ...initialState,
        isLoading: false,
      };
    
    case 'INIT_AUTH':
      return {
        user: action.payload.user,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken,
        isAuthenticated: true,
        isLoading: false,
      };
    
    default:
      return state;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedUser = authService.getStoredUser();
        const storedToken = authService.getStoredToken();
        const storedRefreshToken = authService.getStoredRefreshToken();

        if (storedUser && storedToken && storedRefreshToken) {
          // Verify user is advisor
          if (storedUser.rol !== 'ADVISOR') {
            authService.clearStorage();
            dispatch({ type: 'CLEAR_AUTH' });
            return;
          }

          // Verify token is still valid
          try {
            const currentUser = await authService.getCurrentUser();
            dispatch({
              type: 'INIT_AUTH',
              payload: {
                user: currentUser,
                token: storedToken,
                refreshToken: storedRefreshToken,
              },
            });
          } catch (error) {
            authService.clearStorage();
            dispatch({ type: 'CLEAR_AUTH' });
          }
        } else {
          dispatch({ type: 'CLEAR_AUTH' });
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        dispatch({ type: 'CLEAR_AUTH' });
      }
    };

    initAuth();

    // Listen for logout events from axios interceptor
    const handleAuthLogout = (event: Event) => {
      const customEvent = event as CustomEvent;
      console.log('Auth logout event received:', customEvent.detail);
      dispatch({ type: 'CLEAR_AUTH' });
      // Force navigation to login
      window.location.href = '/login';
    };

    window.addEventListener('auth:logout', handleAuthLogout);

    return () => {
      window.removeEventListener('auth:logout', handleAuthLogout);
    };
  }, []);

  const login = async (credentials: LoginRequest) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    
    try {
      const response = await authService.login(credentials);
      
      // Save tokens and user to localStorage
      authService.saveTokens({
        access_token: response.access_token,
        refresh_token: response.refresh_token,
      });
      authService.saveUser(response.user);
      
      // Update state
      dispatch({
        type: 'SET_TOKENS',
        payload: {
          token: response.access_token,
          refreshToken: response.refresh_token,
        },
      });
      dispatch({ type: 'SET_USER', payload: response.user });
    } catch (error) {
      dispatch({ type: 'SET_LOADING', payload: false });
      throw error;
    }
  };

  const logout = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch({ type: 'CLEAR_AUTH' });
    }
  };

  const refreshUser = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      authService.saveUser(currentUser);
      dispatch({ type: 'SET_USER', payload: currentUser });
    } catch (error) {
      console.error('Refresh user error:', error);
      await logout();
    }
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
