import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { analyticsService } from '@/services/analytics';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Users, 
  DollarSign, 
  Clock, 
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Download
} from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple';
  loading?: boolean;
}

const KPICard: React.FC<KPICardProps> = ({ 
  title, 
  value, 
  change, 
  icon, 
  color = 'blue',
  loading = false 
}) => {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    green: 'text-green-600 bg-green-50',
    red: 'text-red-600 bg-red-50',
    yellow: 'text-yellow-600 bg-yellow-50',
    purple: 'text-purple-600 bg-purple-50'
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
            {loading ? (
              <div className="h-8 w-24 bg-gray-200 animate-pulse rounded"></div>
            ) : (
              <p className="text-2xl font-bold text-gray-900">{value}</p>
            )}
            {change !== undefined && !loading && (
              <div className="flex items-center mt-1">
                {change >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                )}
                <span className={`text-sm font-medium ${
                  change >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {change >= 0 ? '+' : ''}{change}%
                </span>
                <span className="text-sm text-gray-500 ml-1">vs período anterior</span>
              </div>
            )}
          </div>
          <div className={`p-3 rounded-full ${colorClasses[color]}`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

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

export const AnalyticsDashboard: React.FC = () => {
  const [refreshing, setRefreshing] = useState(false);

  // Queries para diferentes dashboards
  const { data: principalData, isLoading: principalLoading, refetch: refetchPrincipal } = useQuery({
    queryKey: ['dashboard-principal'],
    queryFn: () => analyticsService.getDashboardPrincipal(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const { data: embudoData, isLoading: embudoLoading } = useQuery({
    queryKey: ['embudo-operativo'],
    queryFn: () => analyticsService.getEmbudoOperativo(),
    refetchInterval: 60000, // Refetch every minute
  });

  const { data: saludData, isLoading: saludLoading } = useQuery({
    queryKey: ['salud-marketplace'],
    queryFn: () => analyticsService.getSaludMarketplace(),
    refetchInterval: 120000, // Refetch every 2 minutes
  });

  const { data: topSolicitudes, isLoading: topSolicitudesLoading } = useQuery({
    queryKey: ['top-solicitudes-abiertas'],
    queryFn: () => analyticsService.getTopSolicitudesAbiertas(10),
    refetchInterval: 60000,
  });

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refetchPrincipal(),
      ]);
    } finally {
      setRefreshing(false);
    }
  };

  const handleExportAll = () => {
    const allData = {
      principal: principalData,
      embudo: embudoData,
      salud: saludData,
      topSolicitudes: topSolicitudes,
      generado_en: new Date().toISOString()
    };

    analyticsService.exportToJSON(allData, `dashboard-completo-${new Date().toISOString().split('T')[0]}.json`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard Analytics</h1>
          <p className="text-gray-600 mt-1">Métricas y KPIs en tiempo real del marketplace</p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={handleRefresh} 
            variant="outline" 
            disabled={refreshing}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          <Button onClick={handleExportAll} className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Exportar Todo
          </Button>
        </div>
      </div>

      {/* KPIs Principales */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">KPIs Principales</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard
            title="Ofertas Totales Mes"
            value={principalData?.kpis?.ofertas_totales_asignadas?.valor?.toLocaleString() || '0'}
            change={principalData?.kpis?.ofertas_totales_asignadas?.cambio_porcentual}
            icon={<TrendingUp className="h-6 w-6" />}
            color="blue"
            loading={principalLoading}
          />
          <KPICard
            title="Monto Total Aceptado"
            value={`$${(principalData?.kpis?.monto_total_aceptado?.valor || 0).toLocaleString()}`}
            change={principalData?.kpis?.monto_total_aceptado?.cambio_porcentual}
            icon={<DollarSign className="h-6 w-6" />}
            color="green"
            loading={principalLoading}
          />
          <KPICard
            title="Solicitudes Abiertas"
            value={principalData?.kpis?.solicitudes_abiertas?.valor || '0'}
            change={principalData?.kpis?.solicitudes_abiertas?.cambio_porcentual}
            icon={<Activity className="h-6 w-6" />}
            color="yellow"
            loading={principalLoading}
          />
          <KPICard
            title="Tasa de Conversión"
            value={`${principalData?.kpis?.tasa_conversion?.valor || '0'}%`}
            change={principalData?.kpis?.tasa_conversion?.cambio_porcentual}
            icon={<Users className="h-6 w-6" />}
            color="purple"
            loading={principalLoading}
          />
        </div>
      </div>

      {/* Embudo Operativo y Salud del Sistema */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Embudo Operativo */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-blue-600" />
              Embudo Operativo
            </CardTitle>
          </CardHeader>
          <CardContent>
            {embudoLoading ? (
              <div className="space-y-3">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-4 bg-gray-200 animate-pulse rounded"></div>
                ))}
              </div>
            ) : (
              <div className="space-y-1">
                <MetricRow
                  label="Solicitudes Recibidas"
                  value={embudoData?.metricas?.solicitudes_recibidas || 0}
                  status="good"
                />
                <MetricRow
                  label="Solicitudes Procesadas"
                  value={embudoData?.metricas?.solicitudes_procesadas || 0}
                  status="good"
                />
                <MetricRow
                  label="Asesores Contactados"
                  value={embudoData?.metricas?.asesores_contactados || 0}
                />
                <MetricRow
                  label="Tasa Respuesta Asesores"
                  value={embudoData?.metricas?.tasa_respuesta_asesores || 0}
                  unit="%"
                  status={
                    (embudoData?.metricas?.tasa_respuesta_asesores || 0) > 70 ? 'good' :
                    (embudoData?.metricas?.tasa_respuesta_asesores || 0) > 50 ? 'warning' : 'critical'
                  }
                />
                <MetricRow
                  label="Ofertas Recibidas"
                  value={embudoData?.metricas?.ofertas_recibidas || 0}
                />
                <MetricRow
                  label="Solicitudes Cerradas"
                  value={embudoData?.metricas?.solicitudes_cerradas || 0}
                  status="good"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Salud del Sistema */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-green-600" />
              Salud del Sistema
            </CardTitle>
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

      {/* Top Solicitudes Abiertas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-orange-600" />
            Top Solicitudes Abiertas (Mayor Tiempo en Proceso)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {topSolicitudesLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-200 animate-pulse rounded"></div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {(topSolicitudes || []).slice(0, 10).map((solicitud: any) => (
                <div key={solicitud.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="font-mono">
                      {solicitud.codigo}
                    </Badge>
                    <div>
                      <p className="font-medium text-gray-900">{solicitud.vehiculo}</p>
                      <p className="text-sm text-gray-600">
                        {solicitud.cliente} • {solicitud.ciudad}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">
                      {Math.round(solicitud.tiempo_proceso_horas || 0)}h
                    </p>
                    <p className="text-sm text-gray-600">
                      {solicitud.repuestos_count} repuesto{solicitud.repuestos_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
              ))}
              {(!topSolicitudes || topSolicitudes.length === 0) && (
                <div className="text-center py-8 text-gray-500">
                  No hay solicitudes abiertas en este momento
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};