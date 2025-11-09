import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { analyticsService } from '@/services/analytics';
import { Download, Filter, Calendar, TrendingUp, Users, DollarSign, Activity } from 'lucide-react';

interface DashboardFilters {
  fechaInicio: string;
  fechaFin: string;
  ciudad?: string;
}

export function ReportesPage() {
  const [filters, setFilters] = useState<DashboardFilters>({
    fechaInicio: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    fechaFin: new Date().toISOString().split('T')[0]
  });

  const [activeTab, setActiveTab] = useState<'embudo' | 'salud' | 'financiero' | 'asesores'>('embudo');

  // Queries para cada dashboard - se cargan solo cuando la pestaña está activa
  const { data: embudoData, isLoading: embudoLoading } = useQuery({
    queryKey: ['embudo-operativo', filters.fechaInicio, filters.fechaFin],
    queryFn: () => analyticsService.getEmbudoOperativo(filters.fechaInicio, filters.fechaFin),
    enabled: activeTab === 'embudo'
  });

  const { data: saludData, isLoading: saludLoading } = useQuery({
    queryKey: ['salud-marketplace', filters.fechaInicio, filters.fechaFin],
    queryFn: () => analyticsService.getSaludMarketplace(filters.fechaInicio, filters.fechaFin),
    enabled: activeTab === 'salud'
  });

  const { data: financieroData, isLoading: financieroLoading } = useQuery({
    queryKey: ['dashboard-financiero', filters.fechaInicio, filters.fechaFin],
    queryFn: () => analyticsService.getDashboardFinanciero(filters.fechaInicio, filters.fechaFin),
    enabled: activeTab === 'financiero'
  });

  const { data: asesoresData, isLoading: asesoresLoading } = useQuery({
    queryKey: ['analisis-asesores', filters.fechaInicio, filters.fechaFin, filters.ciudad],
    queryFn: () => analyticsService.getAnalisisAsesores(filters.fechaInicio, filters.fechaFin, filters.ciudad),
    enabled: activeTab === 'asesores'
  });

  const handleExportData = async (format: 'json' | 'csv' = 'json') => {
    try {
      let data;
      switch (activeTab) {
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
        const filename = `reporte-${activeTab}-${filters.fechaInicio}-${filters.fechaFin}.${format}`;
        
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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

            {activeTab === 'asesores' && (
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

      {/* Tabs con Dashboards */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as any)} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="embudo" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Embudo Operativo
          </TabsTrigger>
          <TabsTrigger value="salud" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Salud Marketplace
          </TabsTrigger>
          <TabsTrigger value="financiero" className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            Dashboard Financiero
          </TabsTrigger>
          <TabsTrigger value="asesores" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Análisis Asesores
          </TabsTrigger>
        </TabsList>

        <TabsContent value="embudo" className="mt-6">
          {embudoLoading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <EmbudoOperativoReport data={embudoData} />
          )}
        </TabsContent>

        <TabsContent value="salud" className="mt-6">
          {saludLoading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
            </div>
          ) : (
            <SaludMarketplaceReport data={saludData} />
          )}
        </TabsContent>

        <TabsContent value="financiero" className="mt-6">
          {financieroLoading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
            </div>
          ) : (
            <FinancieroReport data={financieroData} />
          )}
        </TabsContent>

        <TabsContent value="asesores" className="mt-6">
          {asesoresLoading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          ) : (
            <AsesoresReport data={asesoresData} />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Componente para Embudo Operativo - 11 KPIs
const EmbudoOperativoReport: React.FC<{ data: any }> = ({ data }) => {
  const metricas = data?.metricas || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-6 w-6 text-blue-600" />
        <h2 className="text-2xl font-bold">Embudo Operativo - 11 KPIs</h2>
      </div>

      {/* KPIs Principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Solicitudes Recibidas"
          value={metricas.solicitudes_recibidas || 0}
          icon={<Activity className="h-4 w-4" />}
        />
        <MetricCard
          title="Solicitudes Procesadas"
          value={metricas.solicitudes_procesadas || 0}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <MetricCard
          title="Asesores Contactados"
          value={metricas.asesores_contactados || 0}
          icon={<Users className="h-4 w-4" />}
        />
        <MetricCard
          title="Tasa Respuesta Asesores"
          value={`${(metricas.tasa_respuesta_asesores || 0).toFixed(1)}%`}
          icon={<TrendingUp className="h-4 w-4" />}
        />
      </div>

      {/* Ofertas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard
          title="Ofertas Recibidas"
          value={metricas.ofertas_recibidas || 0}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          title="Ofertas por Solicitud"
          value={(metricas.ofertas_por_solicitud || 0).toFixed(1)}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <MetricCard
          title="Solicitudes Evaluadas"
          value={metricas.solicitudes_evaluadas || 0}
          icon={<Activity className="h-4 w-4" />}
        />
      </div>

      {/* Cierre */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Tiempo Evaluación (min)"
          value={(metricas.tiempo_evaluacion || 0).toFixed(1)}
          icon={<Calendar className="h-4 w-4" />}
        />
        <MetricCard
          title="Ofertas Ganadoras"
          value={metricas.ofertas_ganadoras || 0}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <MetricCard
          title="Tasa Aceptación Cliente"
          value={`${(metricas.tasa_aceptacion_cliente || 0).toFixed(1)}%`}
          icon={<Users className="h-4 w-4" />}
        />
        <MetricCard
          title="Solicitudes Cerradas"
          value={metricas.solicitudes_cerradas || 0}
          icon={<Activity className="h-4 w-4" />}
        />
      </div>

      {/* Resumen en Tabla */}
      <Card>
        <CardHeader>
          <CardTitle>Resumen Completo del Embudo</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(metricas).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center py-2 border-b last:border-b-0">
                <span className="font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                <Badge variant="outline">{typeof value === 'number' ? value.toLocaleString() : String(value)}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Componente para Salud del Marketplace - 5 KPIs
const SaludMarketplaceReport: React.FC<{ data: any }> = ({ data }) => {
  const metricas = data?.metricas || {};

  const getStatusColor = (key: string, value: number) => {
    if (key === 'disponibilidad_sistema') {
      return value >= 99 ? 'text-green-600' : value >= 95 ? 'text-yellow-600' : 'text-red-600';
    }
    if (key === 'latencia_promedio') {
      return value < 200 ? 'text-green-600' : value < 500 ? 'text-yellow-600' : 'text-red-600';
    }
    if (key === 'tasa_error') {
      return value < 0.01 ? 'text-green-600' : value < 0.05 ? 'text-yellow-600' : 'text-red-600';
    }
    if (key === 'carga_sistema') {
      return value < 70 ? 'text-green-600' : value < 85 ? 'text-yellow-600' : 'text-red-600';
    }
    return 'text-gray-900';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="h-6 w-6 text-green-600" />
        <h2 className="text-2xl font-bold">Salud del Marketplace - 5 KPIs</h2>
      </div>

      {/* KPIs de Salud */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Disponibilidad Sistema</p>
                <p className={`text-2xl font-bold ${getStatusColor('disponibilidad_sistema', metricas.disponibilidad_sistema || 0)}`}>
                  {(metricas.disponibilidad_sistema || 0).toFixed(2)}%
                </p>
                <p className="text-xs text-gray-500 mt-1">Objetivo: &gt; 99%</p>
              </div>
              <Activity className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Latencia Promedio</p>
                <p className={`text-2xl font-bold ${getStatusColor('latencia_promedio', metricas.latencia_promedio || 0)}`}>
                  {(metricas.latencia_promedio || 0).toFixed(0)} ms
                </p>
                <p className="text-xs text-gray-500 mt-1">Objetivo: &lt; 200ms</p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tasa de Error</p>
                <p className={`text-2xl font-bold ${getStatusColor('tasa_error', metricas.tasa_error || 0)}`}>
                  {((metricas.tasa_error || 0) * 100).toFixed(2)}%
                </p>
                <p className="text-xs text-gray-500 mt-1">Objetivo: &lt; 1%</p>
              </div>
              <Activity className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Asesores Activos</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metricas.asesores_activos || 0}
                </p>
                <p className="text-xs text-gray-500 mt-1">Últimos 7 días</p>
              </div>
              <Users className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Carga del Sistema</p>
                <p className={`text-2xl font-bold ${getStatusColor('carga_sistema', metricas.carga_sistema || 0)}`}>
                  {(metricas.carga_sistema || 0).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 mt-1">Objetivo: &lt; 70%</p>
              </div>
              <Activity className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Estado General */}
      <Card>
        <CardHeader>
          <CardTitle>Estado General del Sistema</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(metricas).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center py-2 border-b last:border-b-0">
                <span className="font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                <Badge variant="outline" className={getStatusColor(key, typeof value === 'number' ? value : 0)}>
                  {typeof value === 'number' ? value.toLocaleString() : String(value)}
                </Badge>
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

// Componente para Análisis de Asesores - 13 KPIs
const AsesoresReport: React.FC<{ data: any }> = ({ data }) => {
  const metricas = data?.metricas || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Users className="h-6 w-6 text-purple-600" />
        <h2 className="text-2xl font-bold">Análisis de Asesores - 13 KPIs</h2>
      </div>

      {/* KPIs Principales de Asesores */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Asesores</p>
                <p className="text-2xl font-bold text-gray-900">{metricas.total_asesores || 0}</p>
                <p className="text-xs text-gray-500 mt-1">Registrados</p>
              </div>
              <Users className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Asesores Activos</p>
                <p className="text-2xl font-bold text-green-600">{metricas.asesores_activos || 0}</p>
                <p className="text-xs text-gray-500 mt-1">Último mes</p>
              </div>
              <Activity className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tasa Respuesta</p>
                <p className="text-2xl font-bold text-blue-600">{(metricas.tasa_respuesta_promedio || 0).toFixed(1)}%</p>
                <p className="text-xs text-gray-500 mt-1">Promedio</p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tiempo Respuesta</p>
                <p className="text-2xl font-bold text-orange-600">{(metricas.tiempo_respuesta_promedio || 0).toFixed(1)} min</p>
                <p className="text-xs text-gray-500 mt-1">Promedio</p>
              </div>
              <Calendar className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Métricas de Performance */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Ofertas por Asesor"
          value={(metricas.ofertas_por_asesor || 0).toFixed(1)}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          title="Tasa Adjudicación"
          value={`${(metricas.tasa_adjudicacion || 0).toFixed(1)}%`}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <MetricCard
          title="Nivel Confianza"
          value={(metricas.nivel_confianza_promedio || 0).toFixed(1)}
          icon={<Activity className="h-4 w-4" />}
        />
        <MetricCard
          title="Asesores Nuevos"
          value={metricas.asesores_nuevos || 0}
          icon={<Users className="h-4 w-4" />}
        />
      </div>

      {/* Retención y Satisfacción */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Retención de Asesores</p>
                <p className="text-2xl font-bold text-green-600">{(metricas.retension_asesores || 0).toFixed(1)}%</p>
                <p className="text-xs text-gray-500 mt-1">Últimos 3 meses</p>
              </div>
              <Users className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Satisfacción Cliente</p>
                <p className="text-2xl font-bold text-yellow-600">{(metricas.satisfaccion_cliente || 0).toFixed(1)}/5.0</p>
                <p className="text-xs text-gray-500 mt-1">Calificación promedio</p>
              </div>
              <Activity className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Ranking y Distribución */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Ranking Top 10 Asesores</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {(metricas.ranking_top_10 || []).length > 0 ? (
                (metricas.ranking_top_10 || []).map((asesor: any, index: number) => (
                  <div key={index} className="flex justify-between items-center py-2 border-b last:border-b-0">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="w-8 h-8 flex items-center justify-center">
                        {index + 1}
                      </Badge>
                      <span className="font-medium">{asesor.nombre || `Asesor ${index + 1}`}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">{asesor.ciudad || ''}</span>
                      <Badge variant="outline">{asesor.puntaje || 0}</Badge>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500 py-4">No hay datos disponibles</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Especialización y Distribución</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b">
                <span className="font-medium">Especialización por Repuesto</span>
                <Badge variant="outline">
                  {Object.keys(metricas.especializacion_por_repuesto || {}).length} categorías
                </Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="font-medium">Distribución Geográfica</span>
                <Badge variant="outline">
                  {Object.keys(metricas.distribucion_geografica || {}).length} ciudades
                </Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="font-medium">Ofertas por Asesor</span>
                <Badge variant="outline">{(metricas.ofertas_por_asesor || 0).toFixed(1)}</Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="font-medium">Tasa Adjudicación</span>
                <Badge variant="outline">{(metricas.tasa_adjudicacion || 0).toFixed(1)}%</Badge>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="font-medium">Nivel Confianza Promedio</span>
                <Badge variant="outline">{(metricas.nivel_confianza_promedio || 0).toFixed(1)}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Resumen Completo */}
      <Card>
        <CardHeader>
          <CardTitle>Resumen Completo - Todos los KPIs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2">
            {Object.entries(metricas).map(([key, value]) => {
              if (key === 'ranking_top_10' || key === 'especializacion_por_repuesto' || key === 'distribucion_geografica') {
                return null; // Skip complex objects
              }
              return (
                <div key={key} className="flex justify-between items-center py-2 border-b">
                  <span className="font-medium capitalize text-sm">{key.replace(/_/g, ' ')}</span>
                  <Badge variant="outline">
                    {typeof value === 'number' ? value.toLocaleString() : String(value)}
                  </Badge>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
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