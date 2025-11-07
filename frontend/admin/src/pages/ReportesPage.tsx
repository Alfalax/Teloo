import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { analyticsService } from '@/services/analytics';
import { Download, Filter, Calendar, TrendingUp, Users, DollarSign, Activity } from 'lucide-react';

interface DashboardFilters {
  fechaInicio: string;
  fechaFin: string;
  ciudad?: string;
  dashboard: 'embudo' | 'salud' | 'financiero' | 'asesores';
}

export function ReportesPage() {
  const [filters, setFilters] = useState<DashboardFilters>({
    fechaInicio: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    fechaFin: new Date().toISOString().split('T')[0],
    dashboard: 'embudo'
  });

  // Queries para cada dashboard
  const { data: embudoData, isLoading: embudoLoading } = useQuery({
    queryKey: ['embudo-operativo', filters.fechaInicio, filters.fechaFin],
    queryFn: () => analyticsService.getEmbudoOperativo(filters.fechaInicio, filters.fechaFin),
    enabled: filters.dashboard === 'embudo'
  });

  const { data: saludData, isLoading: saludLoading } = useQuery({
    queryKey: ['salud-marketplace', filters.fechaInicio, filters.fechaFin],
    queryFn: () => analyticsService.getSaludMarketplace(filters.fechaInicio, filters.fechaFin),
    enabled: filters.dashboard === 'salud'
  });

  const { data: financieroData, isLoading: financieroLoading } = useQuery({
    queryKey: ['dashboard-financiero', filters.fechaInicio, filters.fechaFin],
    queryFn: () => analyticsService.getDashboardFinanciero(filters.fechaInicio, filters.fechaFin),
    enabled: filters.dashboard === 'financiero'
  });

  const { data: asesoresData, isLoading: asesoresLoading } = useQuery({
    queryKey: ['analisis-asesores', filters.fechaInicio, filters.fechaFin, filters.ciudad],
    queryFn: () => analyticsService.getAnalisisAsesores(filters.fechaInicio, filters.fechaFin, filters.ciudad),
    enabled: filters.dashboard === 'asesores'
  });

  const handleExportData = async (format: 'json' | 'csv' = 'json') => {
    try {
      let data;
      switch (filters.dashboard) {
        case 'embudo':
          data = embudoData;
          break;
        case 'salud':
          data = saludData;
          break;
        case 'financiero':
          data = financieroData;
          break;
        case 'asesores':
          data = asesoresData;
          break;
      }

      if (data) {
        const filename = `reporte-${filters.dashboard}-${filters.fechaInicio}-${filters.fechaFin}.${format}`;
        
        if (format === 'csv') {
          analyticsService.exportToCSV(data, filename);
        } else {
          analyticsService.exportToJSON(data, filename);
        }
      }
    } catch (error) {
      console.error('Error exportando datos:', error);
    }
  };

  const isLoading = embudoLoading || saludLoading || financieroLoading || asesoresLoading;

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Reportes y Analytics</h1>
        <div className="flex gap-2">
          <Button onClick={() => handleExportData('csv')} variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Exportar CSV
          </Button>
          <Button onClick={() => handleExportData('json')} className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Exportar JSON
          </Button>
        </div>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtros de Reporte
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Dashboard</label>
              <Select
                value={filters.dashboard}
                onValueChange={(value: 'embudo' | 'salud' | 'financiero' | 'asesores') =>
                  setFilters(prev => ({ ...prev, dashboard: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="embudo">Embudo Operativo</SelectItem>
                  <SelectItem value="salud">Salud del Marketplace</SelectItem>
                  <SelectItem value="financiero">Dashboard Financiero</SelectItem>
                  <SelectItem value="asesores">Análisis de Asesores</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Fecha Inicio</label>
              <Input
                type="date"
                value={filters.fechaInicio}
                onChange={(e) => setFilters(prev => ({ ...prev, fechaInicio: e.target.value }))}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Fecha Fin</label>
              <Input
                type="date"
                value={filters.fechaFin}
                onChange={(e) => setFilters(prev => ({ ...prev, fechaFin: e.target.value }))}
              />
            </div>

            {filters.dashboard === 'asesores' && (
              <div>
                <label className="text-sm font-medium mb-2 block">Ciudad (Opcional)</label>
                <Input
                  placeholder="Ej: BOGOTA"
                  value={filters.ciudad || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, ciudad: e.target.value }))}
                />
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Dashboard Content */}
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          {filters.dashboard === 'embudo' && <EmbudoOperativoReport data={embudoData} />}
          {filters.dashboard === 'salud' && <SaludMarketplaceReport data={saludData} />}
          {filters.dashboard === 'financiero' && <FinancieroReport data={financieroData} />}
          {filters.dashboard === 'asesores' && <AsesoresReport data={asesoresData} />}
        </>
      )}
    </div>
  );
}

// Componente para Embudo Operativo
const EmbudoOperativoReport: React.FC<{ data: any }> = ({ data }) => {
  const metricas = data?.metricas || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-6 w-6 text-blue-600" />
        <h2 className="text-2xl font-bold">Embudo Operativo</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Solicitudes Creadas Hoy"
          value={metricas.solicitudes_creadas_hoy || 0}
          icon={<Activity className="h-4 w-4" />}
          trend={metricas.solicitudes_creadas_hoy_cambio}
        />
        <MetricCard
          title="Ofertas Recibidas Hoy"
          value={metricas.ofertas_recibidas_hoy || 0}
          icon={<TrendingUp className="h-4 w-4" />}
          trend={metricas.ofertas_recibidas_hoy_cambio}
        />
        <MetricCard
          title="Evaluaciones Completadas"
          value={metricas.evaluaciones_completadas || 0}
          icon={<Activity className="h-4 w-4" />}
          trend={metricas.evaluaciones_completadas_cambio}
        />
        <MetricCard
          title="Tiempo Promedio Evaluación"
          value={`${metricas.tiempo_promedio_evaluacion || 0} min`}
          icon={<Calendar className="h-4 w-4" />}
          trend={metricas.tiempo_promedio_evaluacion_cambio}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Métricas Detalladas del Embudo</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(metricas).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center py-2 border-b">
                <span className="font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                <Badge variant="outline">{String(value)}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Componente para Salud del Marketplace
const SaludMarketplaceReport: React.FC<{ data: any }> = ({ data }) => {
  const metricas = data?.metricas || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="h-6 w-6 text-green-600" />
        <h2 className="text-2xl font-bold">Salud del Marketplace</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard
          title="Tiempo Respuesta Asesores"
          value={`${metricas.tiempo_respuesta_asesores || 0} min`}
          icon={<Calendar className="h-4 w-4" />}
          trend={metricas.tiempo_respuesta_asesores_cambio}
        />
        <MetricCard
          title="Tasa Participación"
          value={`${metricas.tasa_participacion || 0}%`}
          icon={<Users className="h-4 w-4" />}
          trend={metricas.tasa_participacion_cambio}
        />
        <MetricCard
          title="Asesores Activos"
          value={metricas.asesores_activos || 0}
          icon={<Users className="h-4 w-4" />}
          trend={metricas.asesores_activos_cambio}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Indicadores de Salud del Sistema</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(metricas).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center py-2 border-b">
                <span className="font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                <Badge variant="outline">{String(value)}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Componente para Dashboard Financiero
const FinancieroReport: React.FC<{ data: any }> = ({ data }) => {
  const metricas = data?.metricas || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <DollarSign className="h-6 w-6 text-green-600" />
        <h2 className="text-2xl font-bold">Dashboard Financiero</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard
          title="Ingresos Totales"
          value={`$${(metricas.ingresos_totales || 0).toLocaleString()}`}
          icon={<DollarSign className="h-4 w-4" />}
          trend={metricas.ingresos_totales_cambio}
        />
        <MetricCard
          title="Comisiones Generadas"
          value={`$${(metricas.comisiones_generadas || 0).toLocaleString()}`}
          icon={<DollarSign className="h-4 w-4" />}
          trend={metricas.comisiones_generadas_cambio}
        />
        <MetricCard
          title="Valor Promedio Transacción"
          value={`$${(metricas.valor_promedio_transaccion || 0).toLocaleString()}`}
          icon={<TrendingUp className="h-4 w-4" />}
          trend={metricas.valor_promedio_transaccion_cambio}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Métricas Financieras Detalladas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(metricas).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center py-2 border-b">
                <span className="font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                <Badge variant="outline">{String(value)}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Componente para Análisis de Asesores
const AsesoresReport: React.FC<{ data: any }> = ({ data }) => {
  const metricas = data?.metricas || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Users className="h-6 w-6 text-purple-600" />
        <h2 className="text-2xl font-bold">Análisis de Asesores</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Asesores"
          value={metricas.total_asesores || 0}
          icon={<Users className="h-4 w-4" />}
          trend={metricas.total_asesores_cambio}
        />
        <MetricCard
          title="Asesores Activos"
          value={metricas.asesores_activos || 0}
          icon={<Activity className="h-4 w-4" />}
          trend={metricas.asesores_activos_cambio}
        />
        <MetricCard
          title="Tasa Respuesta Promedio"
          value={`${metricas.tasa_respuesta_promedio || 0}%`}
          icon={<TrendingUp className="h-4 w-4" />}
          trend={metricas.tasa_respuesta_promedio_cambio}
        />
        <MetricCard
          title="Tiempo Respuesta Promedio"
          value={`${metricas.tiempo_respuesta_promedio || 0} min`}
          icon={<Calendar className="h-4 w-4" />}
          trend={metricas.tiempo_respuesta_promedio_cambio}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Ranking Top 10 Asesores</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {(metricas.ranking_top_10 || []).map((asesor: any, index: number) => (
                <div key={index} className="flex justify-between items-center py-2 border-b">
                  <span className="font-medium">{asesor.nombre || `Asesor ${index + 1}`}</span>
                  <Badge variant="outline">{asesor.puntaje || 0}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Métricas de Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b">
                <span className="font-medium">Ofertas por Asesor</span>
                <Badge variant="outline">{metricas.ofertas_por_asesor || 0}</Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="font-medium">Tasa Adjudicación</span>
                <Badge variant="outline">{metricas.tasa_adjudicacion || 0}%</Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="font-medium">Nivel Confianza Promedio</span>
                <Badge variant="outline">{metricas.nivel_confianza_promedio || 0}</Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="font-medium">Retención Asesores</span>
                <Badge variant="outline">{metricas.retension_asesores || 0}%</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Componente reutilizable para métricas
const MetricCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: number;
}> = ({ title, value, icon, trend }) => {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {trend !== undefined && (
              <p className={`text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {trend >= 0 ? '+' : ''}{trend}% vs período anterior
              </p>
            )}
          </div>
          <div className="text-gray-400">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};