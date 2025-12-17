import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TrendingUp, Users, ShoppingCart, DollarSign, RefreshCw, AlertCircle, Activity, CheckCircle, Download } from 'lucide-react';
import { KPICard } from '@/components/dashboard/KPICard';
import { LineChart } from '@/components/charts/LineChart';
import { TopSolicitudesTable } from '@/components/dashboard/TopSolicitudesTable';
import { useDashboardData } from '@/hooks/useDashboard';
import { analyticsService } from '@/services/analytics';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

// MetricRow component for Salud del Sistema
interface MetricRowProps {
  label: string;
  value: string | number;
  status?: 'good' | 'warning' | 'critical';
  unit?: string;
}

const MetricRow: React.FC<MetricRowProps> = ({ label, value, status, unit }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'good':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'critical':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="flex justify-between items-center py-3 border-b border-gray-100 last:border-b-0">
      <div className="flex items-center gap-2">
        {getStatusIcon()}
        <span className="font-medium text-gray-700">{label}</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="font-semibold text-gray-900">{value}</span>
        {unit && <span className="text-sm text-gray-500">{unit}</span>}
      </div>
    </div>
  );
};

export function DashboardPage() {
  const {
    dashboardData,
    graficosData,
    topSolicitudes,
    isLoading,
    hasError,
    refetchDashboard,
    periodo,
  } = useDashboardData();

  // Query for Salud del Sistema
  const { data: saludData, isLoading: saludLoading } = useQuery({
    queryKey: ['salud-marketplace'],
    queryFn: () => analyticsService.getSaludMarketplace(),
    refetchInterval: 120000, // Refetch every 2 minutes
  });

  const handleExportDashboard = () => {
    const exportData = {
      dashboard_principal: dashboardData,
      graficos_mes: graficosData,
      top_solicitudes: topSolicitudes,
      exported_at: new Date().toISOString()
    };

    analyticsService.exportToJSON(exportData, `dashboard-${new Date().toISOString().split('T')[0]}.json`);
  };

  // Format KPI data for display
  const formatKPIValue = (value: number | string, type: 'currency' | 'number' | 'percentage') => {
    // Convertir a número si es string
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    
    // Validar que sea un número válido
    if (isNaN(numValue)) {
      return type === 'percentage' ? '0%' : '0';
    }
    
    switch (type) {
      case 'currency':
        return new Intl.NumberFormat('es-CO', {
          style: 'currency',
          currency: 'COP',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(numValue);
      case 'percentage':
        return `${numValue.toFixed(1)}%`;
      default:
        return numValue.toLocaleString('es-CO');
    }
  };

  const getTrend = (change: number): 'up' | 'down' | 'neutral' => {
    if (change > 0) return 'up';
    if (change < 0) return 'down';
    return 'neutral';
  };

  // Prepare chart data
  const chartLines = [
    { key: 'solicitudes', name: 'Solicitudes', color: '#f59e0b' },
    { key: 'aceptadas', name: 'Aceptadas', color: '#10b981' },
    { key: 'cerradas', name: 'Cerradas sin ofertas', color: '#ef4444' },
  ];

  if (hasError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard Principal</h1>
          <p className="text-muted-foreground">
            Resumen general del marketplace TeLOO
          </p>
        </div>
        
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <div className="text-center space-y-4">
              <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto" />
              <div>
                <h3 className="text-lg font-semibold">Error al cargar datos</h3>
                <p className="text-muted-foreground">
                  No se pudieron cargar los datos del dashboard. Verifique la conexión con el servicio de analytics.
                </p>
              </div>
              <button
                onClick={() => refetchDashboard()}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              >
                <RefreshCw className="h-4 w-4" />
                Reintentar
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between rounded-xl bg-gradient-to-r from-accent to-secondary p-4 text-white shadow-sm">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard Principal</h1>
          <p className="text-white/80">
            Resumen general del marketplace TeLOO - {format(new Date(periodo.inicio), 'MMMM yyyy', { locale: es })}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => refetchDashboard()}
            disabled={isLoading}
            variant="ghost"
            className="flex items-center gap-2 border border-white/30 text-white hover:bg-white/10"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          <Button onClick={handleExportDashboard} variant="ghost" className="flex items-center gap-2 border border-white/30 text-white hover:bg-white/10">
            <Download className="h-4 w-4" />
            Exportar
          </Button>
        </div>
      </div>

      <div className="space-y-6">
          {/* KPIs Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Ofertas Totales Asignadas"
          value={dashboardData?.kpis?.ofertas_totales_asignadas?.valor 
            ? formatKPIValue(dashboardData.kpis.ofertas_totales_asignadas.valor, 'number')
            : '0'
          }
          change={dashboardData?.kpis?.ofertas_totales_asignadas?.cambio_porcentual}
          trend={dashboardData?.kpis?.ofertas_totales_asignadas?.cambio_porcentual 
            ? getTrend(dashboardData.kpis.ofertas_totales_asignadas.cambio_porcentual)
            : 'neutral'
          }
          description="Mes actual"
          icon={ShoppingCart}
          isLoading={isLoading}
        />
        
        <KPICard
          title="Monto Total Aceptado"
          value={dashboardData?.kpis?.monto_total_aceptado?.valor 
            ? formatKPIValue(dashboardData.kpis.monto_total_aceptado.valor, 'currency')
            : '$0'
          }
          change={dashboardData?.kpis?.monto_total_aceptado?.cambio_porcentual}
          trend={dashboardData?.kpis?.monto_total_aceptado?.cambio_porcentual 
            ? getTrend(dashboardData.kpis.monto_total_aceptado.cambio_porcentual)
            : 'neutral'
          }
          description="Mes actual"
          icon={DollarSign}
          isLoading={isLoading}
        />
        
        <KPICard
          title="Solicitudes Abiertas"
          value={dashboardData?.kpis?.solicitudes_abiertas?.valor 
            ? formatKPIValue(dashboardData.kpis.solicitudes_abiertas.valor, 'number')
            : '0'
          }
          change={dashboardData?.kpis?.solicitudes_abiertas?.cambio_porcentual}
          trend={dashboardData?.kpis?.solicitudes_abiertas?.cambio_porcentual 
            ? getTrend(dashboardData.kpis.solicitudes_abiertas.cambio_porcentual)
            : 'neutral'
          }
          description="Actualmente"
          icon={TrendingUp}
          isLoading={isLoading}
        />
        
        <KPICard
          title="Tasa de Conversión"
          value={dashboardData?.kpis?.tasa_conversion?.valor 
            ? formatKPIValue(dashboardData.kpis.tasa_conversion.valor, 'percentage')
            : '0%'
          }
          change={dashboardData?.kpis?.tasa_conversion?.cambio_porcentual}
          trend={dashboardData?.kpis?.tasa_conversion?.cambio_porcentual 
            ? getTrend(dashboardData.kpis.tasa_conversion.cambio_porcentual)
            : 'neutral'
          }
          description="Promedio mensual"
          icon={Users}
          isLoading={isLoading}
        />
      </div>

      {/* Charts Section */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Solicitudes del Mes</CardTitle>
            <CardDescription>
              Evolución diaria de solicitudes, aceptadas y cerradas sin ofertas
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            {isLoading ? (
              <div className="h-[300px] flex items-center justify-center">
                <div className="text-center space-y-2">
                  <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">Cargando gráfico...</p>
                </div>
              </div>
            ) : graficosData && graficosData.length > 0 ? (
              <LineChart
                data={graficosData}
                lines={chartLines}
                xAxisKey="date"
                height={300}
                showLegend={true}
              />
            ) : (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                <div className="text-center space-y-2">
                  <TrendingUp className="h-8 w-8 mx-auto" />
                  <p>No hay datos disponibles para el período seleccionado</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        
        <TopSolicitudesTable 
          solicitudes={topSolicitudes || []} 
          isLoading={isLoading}
        />
      </div>

      {/* Salud del Sistema */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-green-600" />
            Salud del Sistema
          </CardTitle>
          <CardDescription>
            Métricas de rendimiento y disponibilidad del sistema
          </CardDescription>
        </CardHeader>
        <CardContent>
          {saludLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 animate-pulse rounded"></div>
              ))}
            </div>
          ) : (
            <div className="space-y-1">
              <MetricRow
                label="Disponibilidad Sistema"
                value={saludData?.metricas?.disponibilidad_sistema || 99.5}
                unit="%"
                status={
                  (saludData?.metricas?.disponibilidad_sistema || 99.5) > 99 ? 'good' :
                  (saludData?.metricas?.disponibilidad_sistema || 99.5) > 95 ? 'warning' : 'critical'
                }
              />
              <MetricRow
                label="Latencia Promedio"
                value={saludData?.metricas?.latencia_promedio || 150}
                unit="ms"
                status={
                  (saludData?.metricas?.latencia_promedio || 150) < 200 ? 'good' :
                  (saludData?.metricas?.latencia_promedio || 150) < 500 ? 'warning' : 'critical'
                }
              />
              <MetricRow
                label="Tasa de Error"
                value={((saludData?.metricas?.tasa_error || 0.02) * 100).toFixed(2)}
                unit="%"
                status={
                  (saludData?.metricas?.tasa_error || 0.02) < 0.01 ? 'good' :
                  (saludData?.metricas?.tasa_error || 0.02) < 0.05 ? 'warning' : 'critical'
                }
              />
              <MetricRow
                label="Asesores Activos"
                value={saludData?.metricas?.asesores_activos || 0}
              />
              <MetricRow
                label="Carga del Sistema"
                value={saludData?.metricas?.carga_sistema || 65}
                unit="%"
                status={
                  (saludData?.metricas?.carga_sistema || 65) < 70 ? 'good' :
                  (saludData?.metricas?.carga_sistema || 65) < 85 ? 'warning' : 'critical'
                }
              />
            </div>
          )}
        </CardContent>
      </Card>
      </div>
    </div>
  );
}
