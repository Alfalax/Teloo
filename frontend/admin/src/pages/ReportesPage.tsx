import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { analyticsService } from '@/services/analytics';
import { Download, Filter, TrendingUp, Users, DollarSign, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, FunnelChart, Funnel, LabelList } from 'recharts';
import { AdvisorScorecardsTable } from '@/components/analytics/AdvisorScorecardsTable';
import { SegmentacionRFM } from '@/components/analytics/SegmentacionRFM';

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
  // Para embudo, cargamos AMBOS niveles
  const { data: embudoDataSolicitud, isLoading: embudoLoadingSolicitud } = useQuery({
    queryKey: ['embudo-operativo', 'solicitud', filters.fechaInicio, filters.fechaFin],
    queryFn: () => analyticsService.getEmbudoOperativo(filters.fechaInicio, filters.fechaFin, 'solicitud'),
    enabled: activeTab === 'embudo'
  });

  const { data: embudoDataRepuesto, isLoading: embudoLoadingRepuesto } = useQuery({
    queryKey: ['embudo-operativo', 'repuesto', filters.fechaInicio, filters.fechaFin],
    queryFn: () => analyticsService.getEmbudoOperativo(filters.fechaInicio, filters.fechaFin, 'repuesto'),
    enabled: activeTab === 'embudo'
  });

  const embudoLoading = embudoLoadingSolicitud || embudoLoadingRepuesto;

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
          // Para embudo, exportar ambos niveles
          data = {
            solicitud: embudoDataSolicitud,
            repuesto: embudoDataRepuesto
          };
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
            <EmbudoOperativoReport 
              dataSolicitud={embudoDataSolicitud} 
              dataRepuesto={embudoDataRepuesto} 
            />
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

// Componente para Embudo Operativo - 15 KPIs (11 base + 4 detalle)
const EmbudoOperativoReport: React.FC<{ dataSolicitud: any; dataRepuesto: any }> = ({ dataSolicitud, dataRepuesto }) => {
  const metricasSolicitud = dataSolicitud?.metricas || {};
  const metricasRepuesto = dataRepuesto?.metricas || {};
  
  const conversionesSolicitud = metricasSolicitud.conversiones || {};
  const conversionesRepuesto = metricasRepuesto.conversiones || {};
  
  const tiempos = metricasSolicitud.tiempos || {};
  const fallos = metricasSolicitud.fallos || {};
  const tasa_entrada = metricasSolicitud.tasa_entrada || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-6 w-6 text-blue-600" />
        <h2 className="text-2xl font-bold">Embudo Operativo - 15 KPIs</h2>
      </div>

      {/* 1. Tasa de Entrada de Solicitudes */}
      <Card>
        <CardHeader>
          <CardTitle>1. Tasa de Entrada de Solicitudes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Por Día</p>
              <p className="text-2xl font-bold">{tasa_entrada.por_dia?.length || 0} días</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Por Semana</p>
              <p className="text-2xl font-bold">{tasa_entrada.por_semana?.length || 0} semanas</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Por Hora</p>
              <p className="text-2xl font-bold">{tasa_entrada.por_hora?.length || 0} horas</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 2-14. Layout Reorganizado: Los 4 gráficos en una sola línea */}
      <div>
        <h3 className="text-lg font-semibold mb-3">2-14. Análisis Completo del Embudo Operativo</h3>
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* 2-5. Por Solicitud */}
          <Card className="w-full">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between text-base">
                <span>Por Solicitud</span>
                <Badge variant="outline">
                  {(conversionesSolicitud.conversion_general || 0).toFixed(1)}%
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="pb-4">
              <ResponsiveContainer width="100%" height={300}>
                <FunnelChart>
                  <Tooltip 
                    formatter={(value: number) => `${value.toFixed(1)}%`}
                    contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '4px' }}
                  />
                  <Funnel
                    dataKey="value"
                    data={[
                      { name: 'Ofertas', value: conversionesSolicitud.abierta_a_evaluacion || 0, fill: '#3b82f6' },
                      { name: 'Ganador', value: conversionesSolicitud.evaluacion_a_adjudicada || 0, fill: '#10b981' },
                      { name: 'Aceptada', value: conversionesSolicitud.adjudicada_a_aceptada || 0, fill: '#8b5cf6' }
                    ]}
                    isAnimationActive
                  >
                    <LabelList 
                      position="center" 
                      fill="#fff" 
                      stroke="none" 
                      content={(props: any) => {
                        const { x, y, width, height, value, name } = props;
                        return (
                          <g>
                            <text 
                              x={x + width / 2} 
                              y={y + height / 2 - 8} 
                              fill="#fff" 
                              textAnchor="middle" 
                              dominantBaseline="middle"
                              style={{ fontSize: '10px' }}
                            >
                              {name}
                            </text>
                            <text 
                              x={x + width / 2} 
                              y={y + height / 2 + 8} 
                              fill="#fff" 
                              textAnchor="middle" 
                              dominantBaseline="middle"
                              style={{ fontSize: '16px', fontWeight: 'bold' }}
                            >
                              {value.toFixed(1)}%
                            </text>
                          </g>
                        );
                      }}
                    />
                  </Funnel>
                </FunnelChart>
              </ResponsiveContainer>
              <div className="mt-2 p-2 bg-orange-50 rounded border border-orange-200">
                <p className="text-xs text-gray-600 text-center">General</p>
                <p className="text-xl font-bold text-orange-600 text-center">{(conversionesSolicitud.conversion_general || 0).toFixed(1)}%</p>
              </div>
            </CardContent>
          </Card>

          {/* 6-9. Por Repuesto */}
          <Card className="w-full">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between text-base">
                <span>Por Repuesto</span>
                <Badge variant="outline">
                  {(conversionesRepuesto.conversion_general || 0).toFixed(1)}%
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="pb-4">
              <ResponsiveContainer width="100%" height={300}>
                <FunnelChart>
                  <Tooltip 
                    formatter={(value: number) => `${value.toFixed(1)}%`}
                    contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '4px' }}
                  />
                  <Funnel
                    dataKey="value"
                    data={[
                      { name: 'Ofertas', value: conversionesRepuesto.abierta_a_evaluacion || 0, fill: '#60a5fa' },
                      { name: 'Ganador', value: conversionesRepuesto.evaluacion_a_adjudicada || 0, fill: '#34d399' },
                      { name: 'Aceptada', value: conversionesRepuesto.adjudicada_a_aceptada || 0, fill: '#a78bfa' }
                    ]}
                    isAnimationActive
                  >
                    <LabelList 
                      position="center" 
                      fill="#fff" 
                      stroke="none" 
                      content={(props: any) => {
                        const { x, y, width, height, value, name } = props;
                        return (
                          <g>
                            <text 
                              x={x + width / 2} 
                              y={y + height / 2 - 8} 
                              fill="#fff" 
                              textAnchor="middle" 
                              dominantBaseline="middle"
                              style={{ fontSize: '10px' }}
                            >
                              {name}
                            </text>
                            <text 
                              x={x + width / 2} 
                              y={y + height / 2 + 8} 
                              fill="#fff" 
                              textAnchor="middle" 
                              dominantBaseline="middle"
                              style={{ fontSize: '16px', fontWeight: 'bold' }}
                            >
                              {value.toFixed(1)}%
                            </text>
                          </g>
                        );
                      }}
                    />
                  </Funnel>
                </FunnelChart>
              </ResponsiveContainer>
              <div className="mt-2 p-2 bg-orange-50 rounded border border-orange-200">
                <p className="text-xs text-gray-600 text-center">General</p>
                <p className="text-xl font-bold text-orange-600 text-center">{(conversionesRepuesto.conversion_general || 0).toFixed(1)}%</p>
              </div>
            </CardContent>
          </Card>

          {/* 13. Tasa de Escalamiento */}
          <Card className="w-full">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between text-base">
                <span>Escalamiento</span>
                <Badge variant="outline">
                  {(fallos.tasa_escalamiento?.tasa_general || 0).toFixed(1)}%
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="pb-4">
              <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={[
                      { nivel: 'Nivel 1 → 2', porcentaje: fallos.tasa_escalamiento?.por_nivel?.['1_a_2'] || 0, color: '#3b82f6' },
                      { nivel: 'Nivel 2 → 3', porcentaje: fallos.tasa_escalamiento?.por_nivel?.['2_a_3'] || 0, color: '#eab308' },
                      { nivel: 'Nivel 3 → 4', porcentaje: fallos.tasa_escalamiento?.por_nivel?.['3_a_4'] || 0, color: '#f97316' },
                      { nivel: 'Nivel 4 → 5', porcentaje: fallos.tasa_escalamiento?.por_nivel?.['4_a_5'] || 0, color: '#ef4444' }
                    ]}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="nivel" />
                    <YAxis label={{ value: '% Solicitudes', angle: -90, position: 'insideLeft' }} domain={[0, 100]} />
                    <Tooltip 
                      formatter={(value: number) => `${value.toFixed(1)}%`}
                      contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '4px' }}
                    />
                    <Bar dataKey="porcentaje" radius={[8, 8, 0, 0]}>
                      {[
                        { nivel: 'Nivel 1 → 2', porcentaje: fallos.tasa_escalamiento?.por_nivel?.['1_a_2'] || 0, color: '#3b82f6' },
                        { nivel: 'Nivel 2 → 3', porcentaje: fallos.tasa_escalamiento?.por_nivel?.['2_a_3'] || 0, color: '#eab308' },
                        { nivel: 'Nivel 3 → 4', porcentaje: fallos.tasa_escalamiento?.por_nivel?.['3_a_4'] || 0, color: '#f97316' },
                        { nivel: 'Nivel 4 → 5', porcentaje: fallos.tasa_escalamiento?.por_nivel?.['4_a_5'] || 0, color: '#ef4444' }
                      ].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>

              <p className="text-xs text-gray-500 mt-2 text-center">
                Total: {fallos.tasa_escalamiento?.total_solicitudes || 0} solicitudes
              </p>
            </CardContent>
          </Card>

          {/* 14. Tasa de Fallo por Nivel */}
          <Card className="w-full">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between text-base">
                <span>Tasa de Fallo</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pb-4">
              {fallos.fallo_por_nivel?.detalles && fallos.fallo_por_nivel.detalles.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={300}>
                      <BarChart
                        data={fallos.fallo_por_nivel.detalles.map((d: any) => ({
                          nivel: `Nivel ${d.nivel}`,
                          porcentaje: d.tasa,
                          color: d.nivel === 1 ? '#10b981' : d.nivel === 2 ? '#3b82f6' : d.nivel === 3 ? '#eab308' : d.nivel === 4 ? '#f97316' : '#ef4444'
                        }))}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="nivel" />
                        <YAxis label={{ value: '% Sin Ofertas', angle: -90, position: 'insideLeft' }} domain={[0, 100]} />
                        <Tooltip 
                          formatter={(value: number) => `${value.toFixed(1)}%`}
                          contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '4px' }}
                        />
                        <Bar dataKey="porcentaje" radius={[8, 8, 0, 0]}>
                          {fallos.fallo_por_nivel.detalles.map((d: any, index: number) => (
                            <Cell 
                              key={`cell-${index}`} 
                              fill={d.nivel === 1 ? '#10b981' : d.nivel === 2 ? '#3b82f6' : d.nivel === 3 ? '#eab308' : d.nivel === 4 ? '#f97316' : '#ef4444'} 
                            />
                          ))}
                        </Bar>
                      </BarChart>
                  </ResponsiveContainer>

                  <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mt-3">
                    {fallos.fallo_por_nivel.detalles.map((d: any) => (
                      <div key={d.nivel} className="text-center p-2 bg-gray-50 rounded">
                        <p className="text-xs text-gray-600">Nivel {d.nivel}</p>
                        <p className="text-sm font-bold">{d.sin_ofertas}/{d.total_solicitudes}</p>
                        <p className="text-xs text-gray-500">{d.tasa.toFixed(1)}%</p>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-sm text-gray-400 text-center py-8">Sin datos</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 10-12. Tiempos */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Tiempos del Proceso</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-6">
              <p className="text-sm font-medium text-gray-600">10. Tiempo hasta Primera Oferta (TTFO)</p>
              <p className="text-3xl font-bold text-blue-600">{(tiempos.ttfo?.mediana_minutos || 0).toFixed(1)}m</p>
              <p className="text-xs text-gray-500 mt-1">Mediana: {(tiempos.ttfo?.mediana_minutos || 0).toFixed(1)}m | Promedio: {(tiempos.ttfo?.promedio_minutos || 0).toFixed(1)}m</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <p className="text-sm font-medium text-gray-600">11. Tiempo hasta Adjudicación (TTA)</p>
              <p className="text-3xl font-bold text-green-600">{(tiempos.tta?.mediana_minutos || 0).toFixed(1)}m</p>
              <p className="text-xs text-gray-500 mt-1">Mediana: {(tiempos.tta?.mediana_minutos || 0).toFixed(1)}m | Promedio: {(tiempos.tta?.promedio_minutos || 0).toFixed(1)}m</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <p className="text-sm font-medium text-gray-600">12. Tiempo hasta Decisión Cliente (TTCD)</p>
              <p className="text-3xl font-bold text-purple-600">{(tiempos.ttcd?.mediana_minutos || 0).toFixed(1)}m</p>
              <p className="text-xs text-gray-500 mt-1">Mediana: {(tiempos.ttcd?.mediana_minutos || 0).toFixed(1)}m | Promedio: {(tiempos.ttcd?.promedio_minutos || 0).toFixed(1)}m</p>
            </CardContent>
          </Card>
        </div>
      </div>


    </div>
  );
};

// Componente para Salud del Marketplace - 5 KPIs
const SaludMarketplaceReport: React.FC<{ data: any }> = ({ data }) => {
  const metricas = data?.metricas || {};
  const ratio = metricas.ratio_oferta_demanda || {};
  const densidad = metricas.densidad_ofertas || {};
  const participacion = metricas.tasa_participacion_asesores || {};
  const adjudicacion = metricas.tasa_adjudicacion_promedio || {};
  const aceptacion = metricas.tasa_aceptacion_cliente || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="h-6 w-6 text-green-600" />
        <h2 className="text-2xl font-bold">Salud del Marketplace - 5 KPIs</h2>
      </div>

      {/* 1. Ratio Oferta/Demanda */}
      <Card>
        <CardContent className="p-6">
          <p className="text-sm font-medium text-gray-600">1. Ratio Oferta/Demanda</p>
          <p className="text-3xl font-bold text-blue-600">{(ratio.ratio || 0).toFixed(1)}</p>
          <p className="text-xs text-gray-500 mt-1">
            {ratio.asesores_activos || 0} asesores / {(ratio.solicitudes_diarias_promedio || 0).toFixed(2)} solicitudes diarias
          </p>
          <p className="text-xs text-gray-400 mt-1">Óptimo: 15-25</p>
        </CardContent>
      </Card>

      {/* 2-5. Otros KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-600">2. Densidad de Ofertas</p>
            <p className="text-3xl font-bold text-green-600">{(densidad.densidad_promedio || 0).toFixed(2)}</p>
            <p className="text-xs text-gray-500 mt-1">Ofertas por solicitud llenada</p>
            <div className="mt-2 text-xs text-gray-600">
              <span>Min: {densidad.min_ofertas || 0} | Max: {densidad.max_ofertas || 0}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-600">3. Tasa de Participación de Asesores</p>
            <p className="text-3xl font-bold text-purple-600">{(participacion.tasa_participacion || 0).toFixed(1)}%</p>
            <p className="text-xs text-gray-500 mt-1">Asesores que enviaron ofertas</p>
            <div className="mt-2 text-xs text-gray-600">
              <span>{participacion.total_participantes || 0} de {participacion.total_habilitados || 0} habilitados</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-600">4. Tasa de Adjudicación Promedio</p>
            <p className="text-3xl font-bold text-orange-600">{(adjudicacion.tasa_promedio || 0).toFixed(1)}%</p>
            <p className="text-xs text-gray-500 mt-1">% ofertas ganadoras por asesor</p>
            <div className="mt-2 text-xs text-gray-600">
              <span>Mediana: {(adjudicacion.mediana || 0).toFixed(1)}%</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-600">5. Tasa de Aceptación del Cliente</p>
            <p className="text-3xl font-bold text-teal-600">{(aceptacion.tasa_aceptacion || 0).toFixed(1)}%</p>
            <p className="text-xs text-gray-500 mt-1">Ofertas adjudicadas aceptadas</p>
            <div className="mt-2 text-xs text-gray-600">
              <span>{aceptacion.aceptadas || 0} de {aceptacion.total_adjudicadas || 0} adjudicadas</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const AsesoresReport: React.FC<{ data: any }> = ({ data }) => {
  // Nueva estructura: advisor_scorecards y segmentacion_rfm
  const advisorScorecardsData = data?.datos?.advisor_scorecards;
  const segmentacionRFMData = data?.datos?.segmentacion_rfm;
  const resumenEjecutivo = data?.datos?.resumen_ejecutivo;

  // Si no hay datos, mostrar mensaje
  if (!advisorScorecardsData || !segmentacionRFMData) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <Users className="h-12 w-12 text-gray-400 mb-4" />
        <p className="text-lg text-gray-600">No hay datos disponibles</p>
        <p className="text-sm text-gray-500">Selecciona un rango de fechas diferente</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Resumen Ejecutivo */}
      {resumenEjecutivo && (
        <Card className="bg-gradient-to-r from-purple-50 to-blue-50">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Resumen Ejecutivo</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Análisis de {resumenEjecutivo.total_asesores_analizados} asesores
                </p>
              </div>
              <Badge variant="secondary" className="text-lg px-4 py-2">
                {resumenEjecutivo.total_asesores_analizados} Asesores
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Advisor Scorecards Table */}
      <AdvisorScorecardsTable data={advisorScorecardsData} />

      {/* Segmentación RFM */}
      <SegmentacionRFM data={segmentacionRFMData} />
    </div>
  );
};


// Componente para Dashboard Financiero - 6 KPIs
const FinancieroReport: React.FC<{ data: any }> = ({ data }) => {
  const metricas = data?.metricas || {};
  const gov = metricas.valor_bruto_ofertado || {};
  const gav_adj = metricas.valor_bruto_adjudicado || {};
  const gav_acc = metricas.valor_bruto_aceptado || {};
  const promedio_sol = metricas.valor_promedio_solicitud || {};
  const fuga = metricas.tasa_fuga_valor || {};
  const resumen = metricas.resumen_financiero || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <DollarSign className="h-6 w-6 text-green-600" />
        <h2 className="text-2xl font-bold">Dashboard Financiero - 6 KPIs</h2>
      </div>

      {/* KPIs 1-3: Valores Brutos */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-600">1. Valor Bruto Ofertado (GOV)</p>
            <p className="text-3xl font-bold text-blue-600">${(gov.valor_total || 0).toLocaleString()}</p>
            <p className="text-xs text-gray-500 mt-1">{gov.total_ofertas || 0} ofertas | Promedio: ${(gov.valor_promedio || 0).toLocaleString()}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-600">2. Valor Bruto Adjudicado (GAV_adj)</p>
            <p className="text-3xl font-bold text-green-600">${(gav_adj.valor_total || 0).toLocaleString()}</p>
            <p className="text-xs text-gray-500 mt-1">{gav_adj.total_adjudicadas || 0} adjudicadas | Promedio: ${(gav_adj.valor_promedio || 0).toLocaleString()}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-600">3. Valor Bruto Aceptado (GAV_acc)</p>
            <p className="text-3xl font-bold text-emerald-600">${(gav_acc.valor_total || 0).toLocaleString()}</p>
            <p className="text-xs text-gray-500 mt-1">{gav_acc.total_aceptadas || 0} aceptadas | Promedio: ${(gav_acc.valor_promedio || 0).toLocaleString()}</p>
          </CardContent>
        </Card>
      </div>

      {/* KPIs 4-5: Promedio y Fuga */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-600">4. Valor Promedio por Solicitud</p>
            <p className="text-3xl font-bold text-purple-600">${(promedio_sol.valor_promedio_por_solicitud || 0).toLocaleString()}</p>
            <p className="text-xs text-gray-500 mt-1">{promedio_sol.solicitudes_aceptadas || 0} solicitudes aceptadas</p>
            <p className="text-xs text-gray-500">Total: ${(promedio_sol.valor_total_aceptado || 0).toLocaleString()}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-600">5. Tasa de Fuga de Valor</p>
            <p className="text-3xl font-bold text-red-600">{(fuga.tasa_fuga_porcentaje || 0).toFixed(1)}%</p>
            <p className="text-xs text-gray-500 mt-1">Valor fugado: ${(fuga.valor_fugado || 0).toLocaleString()}</p>
            <p className="text-xs text-gray-500">Adjudicado: ${(fuga.valor_adjudicado || 0).toLocaleString()} | Aceptado: ${(fuga.valor_aceptado || 0).toLocaleString()}</p>
          </CardContent>
        </Card>
      </div>

      {/* KPI 6: Resumen Financiero */}
      <Card>
        <CardHeader>
          <CardTitle>6. Resumen Financiero</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">Conversión Oferta → Adjudicación</p>
              <p className="text-2xl font-bold text-blue-600">{(resumen.conversion_oferta_adjudicacion || 0).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Conversión Adjudicación → Aceptación</p>
              <p className="text-2xl font-bold text-green-600">{(resumen.conversion_adjudicacion_aceptacion || 0).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Conversión General Financiera</p>
              <p className="text-2xl font-bold text-purple-600">{(resumen.conversion_general_financiera || 0).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Ticket Promedio Marketplace</p>
              <p className="text-2xl font-bold text-orange-600">${(resumen.ticket_promedio_marketplace || 0).toLocaleString()}</p>
            </div>
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
