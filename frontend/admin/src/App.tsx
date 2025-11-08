import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Layout } from '@/components/layout/Layout';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import SolicitudesPage from '@/pages/SolicitudesPage';
import { AsesoresPage } from '@/pages/AsesoresPage';
import { ReportesPage } from '@/pages/ReportesPage';
import { PQRPage } from '@/pages/PQRPage';
import { ConfiguracionPage } from '@/pages/ConfiguracionPage';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            
            {/* Protected routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute requiredRoles={['ADMIN', 'ANALYST', 'SUPPORT']}>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<DashboardPage />} />
              <Route path="solicitudes" element={<SolicitudesPage />} />
              <Route path="asesores" element={<AsesoresPage />} />
              <Route path="reportes" element={<ReportesPage />} />
              <Route path="pqr" element={<PQRPage />} />
              <Route
                path="configuracion"
                element={
                  <ProtectedRoute requiredRoles={['ADMIN']}>
                    <ConfiguracionPage />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;