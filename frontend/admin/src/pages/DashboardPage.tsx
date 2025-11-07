import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, Users, ShoppingCart, DollarSign, RefreshCw, AlertCircle, BarChart3, Download } from 'lucide-react';
import { KPICard } from '@/components/dashboard/KPICard';
import { LineChart } from '@/components/charts/LineChart';
import { TopSolicitudesTable } from '@/components/dashboard/TopSolicitudesTable';
import { AnalyticsDashboard } from '@/components/dashboard/AnalyticsDashboard';
import { useDashboardData } from '@/hooks/useDashboard';
import { analyticsService } from '@/services/analytics';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

export function DashboardPage() {
  const [activeTab, setActiveTab] = useState('overview');
  
  const {
    dashboardData,
    graficosData,
    topSolicitudes,
    isLoading,
    hasError,
    refetchDashboard,
    periodo,
  } = useDashboardData();

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
  const formatKPIValue = (value: number, type: 'currency' | 'number' | 'percentage') => {
    switch (type) {
      case 'currency':
        return new Intl.NumberFormat('es-CO', {
          style: 'currency',
          currency: 'COP',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(value);
      case 'percentage':
        return `${value.toFixed(1)}%`;
      default:
        return value.toLocaleString('es-CO');
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
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard Principal</h1>
          <p className="text-muted-foreground">
            Resumen general del marketplace TeLOO - {format(new Date(periodo.inicio), 'MMMM yyyy', { locale: es })}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => refetchDashboard()}
            disabled={isLoading}
            variant="outline"
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          <Button onClick={handleExportDashboard} variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Exportar
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Resumen
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Analytics Completo
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
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

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Actividad Reciente</CardTitle>
          <CardDescription>
            Últimas acciones en el sistema
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, index) => (
                <div key={index} className="flex items-center space-x-4">
                  <div className="w-2 h-2 bg-muted animate-pulse rounded-full"></div>
                  <div className="h-4 w-64 bg-muted animate-pulse rounded flex-1"></div>
                  <div className="h-3 w-16 bg-muted animate-pulse rounded"></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {[
                'Nueva solicitud creada: SOL-123',
                'Oferta ganadora: Asesor Juan Pérez',
                'Cliente aceptó oferta: SOL-120',
                'Evaluación completada: SOL-118',
                'Nuevo asesor registrado: María García',
              ].map((activity, index) => (
                <div key={index} className="flex items-center space-x-4">
                  <div className="w-2 h-2 bg-primary rounded-full"></div>
                  <p className="text-sm">{activity}</p>
                  <span className="text-xs text-muted-foreground ml-auto">
                    Hace {index + 1} min
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
        </TabsContent>

        <TabsContent value="analytics">
          <AnalyticsDashboard />
        </TabsContent>
      </Tabs>
    </div>
  );
}