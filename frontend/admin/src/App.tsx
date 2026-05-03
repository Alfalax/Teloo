import { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { ToastContextProvider } from '@/contexts/ToastContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Layout } from '@/components/layout/Layout';

// Lazy load pages
const LoginPage = lazy(() => import('@/pages/LoginPage').then(module => ({ default: module.LoginPage })));
const DashboardPage = lazy(() => import('@/pages/DashboardPage').then(module => ({ default: module.DashboardPage })));
const SolicitudesPage = lazy(() => import('@/pages/SolicitudesPage')); // Default export
const AsesoresPage = lazy(() => import('@/pages/AsesoresPage').then(module => ({ default: module.AsesoresPage })));
const ReportesPage = lazy(() => import('@/pages/ReportesPage').then(module => ({ default: module.ReportesPage })));
const PQRPage = lazy(() => import('@/pages/PQRPage').then(module => ({ default: module.PQRPage })));
const ConfiguracionPage = lazy(() => import('@/pages/ConfiguracionPage').then(module => ({ default: module.ConfiguracionPage })));

// Loading component
const PageLoader = () => (
  <div className="flex h-screen w-full items-center justify-center">
    <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
  </div>
);

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
      <Router>
        <AuthProvider>
          <ToastContextProvider>
            <Suspense fallback={<PageLoader />}>
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
            </Suspense>
          </ToastContextProvider>
        </AuthProvider>
      </Router>
    </QueryClientProvider>
  );
}

export default App;