/**
 * System Configuration Component
 * Handles all system parameter categories
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Settings, 
  Scale, 
  BarChart3, 
  Clock, 
  MessageSquare, 
  Calculator,
  AlertCircle,
  CheckCircle,
  RotateCcw
} from 'lucide-react';
import { PesosEscalamientoForm } from './PesosEscalamientoForm';
import { UmbralesNivelesForm } from './UmbralesNivelesForm';
import { TiemposEsperaForm } from './TiemposEsperaForm';
import { CanalesNotificacionForm } from './CanalesNotificacionForm';
import { PesosEvaluacionForm } from './PesosEvaluacionForm';
import { ParametrosGeneralesForm } from './ParametrosGeneralesForm';
import { useConfiguracion } from '@/hooks/useConfiguracion';
import type { CategoriaConfiguracion } from '@/types/configuracion';

const CATEGORIAS = [
  {
    key: 'pesos_escalamiento' as CategoriaConfiguracion,
    title: 'Pesos de Escalamiento',
    description: 'Pesos del algoritmo de escalamiento de asesores',
    icon: Scale,
    component: PesosEscalamientoForm
  },
  {
    key: 'umbrales_niveles' as CategoriaConfiguracion,
    title: 'Umbrales de Niveles',
    description: 'Umbrales para clasificación de asesores por niveles',
    icon: BarChart3,
    component: UmbralesNivelesForm
  },
  {
    key: 'tiempos_espera_nivel' as CategoriaConfiguracion,
    title: 'Tiempos de Espera',
    description: 'Tiempos de espera por nivel de asesor',
    icon: Clock,
    component: TiemposEsperaForm
  },
  {
    key: 'canales_por_nivel' as CategoriaConfiguracion,
    title: 'Canales de Notificación',
    description: 'Canales de notificación por nivel de asesor',
    icon: MessageSquare,
    component: CanalesNotificacionForm
  },
  {
    key: 'pesos_evaluacion_ofertas' as CategoriaConfiguracion,
    title: 'Pesos de Evaluación',
    description: 'Pesos para evaluación de ofertas',
    icon: Calculator,
    component: PesosEvaluacionForm
  },
  {
    key: 'parametros_generales' as CategoriaConfiguracion,
    title: 'Parámetros Generales',
    description: 'Parámetros generales del sistema',
    icon: Settings,
    component: ParametrosGeneralesForm
  }
];

const renderComponent = (categoria: any, configuracion: any) => {
  const Component = categoria.component;
  const data = configuracion[categoria.key];
  
  // Use JSON.stringify as key to force re-render when data changes
  const dataKey = JSON.stringify(data);
  
  return (
    <Component 
      key={dataKey}
      data={data} 
      categoria={categoria.key}
    />
  );
};

export function ConfiguracionSistema() {
  const [activeCategory, setActiveCategory] = useState<CategoriaConfiguracion>('pesos_escalamiento');
  const { configuracion, summary, loading, error, resetConfiguracion, loadConfiguracion } = useConfiguracion();

  // Reload configuration when component mounts
  useEffect(() => {
    loadConfiguracion();
  }, [loadConfiguracion]);

  // Reload configuration when switching tabs
  useEffect(() => {
    loadConfiguracion();
  }, [activeCategory, loadConfiguracion]);

  const handleResetCategoria = async (categoria: CategoriaConfiguracion) => {
    if (confirm(`¿Está seguro de que desea resetear la configuración de "${CATEGORIAS.find(c => c.key === categoria)?.title}" a valores por defecto?`)) {
      try {
        await resetConfiguracion(categoria);
      } catch (err) {
        // Error is handled by the hook
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Cargando configuración...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!configuracion) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>No se pudo cargar la configuración</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Validation Status */}
      {summary && (
        <div className="flex items-center gap-4 p-4 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            {summary.validaciones_activas.pesos_suman_1 ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600" />
            )}
            <span className="text-sm">Pesos válidos</span>
          </div>
          
          <div className="flex items-center gap-2">
            {summary.validaciones_activas.umbrales_decrecientes ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600" />
            )}
            <span className="text-sm">Umbrales válidos</span>
          </div>
          
          <div className="flex items-center gap-2">
            {summary.validaciones_activas.rangos_validos ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600" />
            )}
            <span className="text-sm">Rangos válidos</span>
          </div>
        </div>
      )}

      <Tabs value={activeCategory} onValueChange={(value) => setActiveCategory(value as CategoriaConfiguracion)}>
        <TabsList className="grid w-full grid-cols-3 lg:grid-cols-6">
          {CATEGORIAS.map((categoria) => {
            const Icon = categoria.icon;
            return (
              <TabsTrigger
                key={categoria.key}
                value={categoria.key}
                className="flex items-center gap-1 text-xs"
              >
                <Icon className="h-3 w-3" />
                <span className="hidden sm:inline">{categoria.title.split(' ')[0]}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        {CATEGORIAS.map((categoria) => {
          const Icon = categoria.icon;
          
          return (
            <TabsContent key={categoria.key} value={categoria.key} className="space-y-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <Icon className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{categoria.title}</CardTitle>
                      <CardDescription>{categoria.description}</CardDescription>
                    </div>
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleResetCategoria(categoria.key)}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Reset
                  </Button>
                </CardHeader>
                
                <CardContent>
                  {renderComponent(categoria, configuracion)}
                </CardContent>
              </Card>
            </TabsContent>
          );
        })}
      </Tabs>
    </div>
  );
}