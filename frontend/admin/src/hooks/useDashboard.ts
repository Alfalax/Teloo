import { useQuery } from '@tanstack/react-query';
import { analyticsService } from '@/services/analytics';
import { startOfMonth, endOfMonth } from 'date-fns';

export function useDashboardData() {
  const currentMonth = new Date();
  const fechaInicio = startOfMonth(currentMonth).toISOString();
  const fechaFin = endOfMonth(currentMonth).toISOString();

  const {
    data: dashboardData,
    isLoading: isDashboardLoading,
    error: dashboardError,
    refetch: refetchDashboard,
  } = useQuery({
    queryKey: ['dashboard-principal', fechaInicio, fechaFin],
    queryFn: () => analyticsService.getDashboardPrincipal(fechaInicio, fechaFin),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // 10 minutes
  });

  const {
    data: graficosData,
    isLoading: isGraficosLoading,
    error: graficosError,
  } = useQuery({
    queryKey: ['graficos-mes', fechaInicio, fechaFin],
    queryFn: () => analyticsService.getGraficosDelMes(fechaInicio, fechaFin),
    staleTime: 5 * 60 * 1000,
    refetchInterval: 10 * 60 * 1000,
  });

  const {
    data: topSolicitudes,
    isLoading: isTopSolicitudesLoading,
    error: topSolicitudesError,
  } = useQuery({
    queryKey: ['top-solicitudes-abiertas'],
    queryFn: () => analyticsService.getTopSolicitudesAbiertas(15),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // 5 minutes
  });

  return {
    // Data
    dashboardData,
    graficosData,
    topSolicitudes,
    
    // Loading states
    isDashboardLoading,
    isGraficosLoading,
    isTopSolicitudesLoading,
    isLoading: isDashboardLoading || isGraficosLoading || isTopSolicitudesLoading,
    
    // Errors
    dashboardError,
    graficosError,
    topSolicitudesError,
    hasError: !!(dashboardError || graficosError || topSolicitudesError),
    
    // Actions
    refetchDashboard,
    
    // Metadata
    periodo: {
      inicio: fechaInicio,
      fin: fechaFin,
    },
  };
}