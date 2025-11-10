/**
 * Parámetros Generales Form Component
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Save, Info } from 'lucide-react';
import { useConfiguracion } from '@/hooks/useConfiguracion';
import type { ParametrosGenerales, CategoriaConfiguracion } from '@/types/configuracion';

interface Props {
  data: ParametrosGenerales;
  categoria: CategoriaConfiguracion;
}

export function ParametrosGeneralesForm({ data, categoria }: Props) {
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const { updateConfiguracion, metadata } = useConfiguracion();

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset
  } = useForm<ParametrosGenerales>({
    defaultValues: data
  });

  useEffect(() => {
    reset(data);
  }, [data, reset]);

  const onSubmit = async (formData: ParametrosGenerales) => {
    try {
      setSaving(true);
      setSaveError(null);
      setSaveSuccess(false);

      await updateConfiguracion(categoria, formData);
      setSaveSuccess(true);
      
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Error guardando configuración');
    } finally {
      setSaving(false);
    }
  };

  // Helper function to format label from key
  const formatLabel = (key: string): string => {
    const labels: Record<string, string> = {
      'ofertas_minimas_deseadas': 'Ofertas Mínimas Deseadas',
      'timeout_evaluacion_seg': 'Timeout de Evaluación',
      'timeout_evaluacion_segundos': 'Timeout de Evaluación',
      'vigencia_auditoria_dias': 'Vigencia de Auditoría',
      'periodo_actividad_dias': 'Período de Actividad',
      'periodo_actividad_reciente_dias': 'Período de Actividad',
      'periodo_desempeno_meses': 'Período de Desempeño',
      'periodo_desempeno_historico_meses': 'Período de Desempeño',
      'confianza_minima_operar': 'Confianza Mínima para Operar',
      'cobertura_minima_pct': 'Cobertura Mínima',
      'cobertura_minima_porcentaje': 'Cobertura Mínima',
      'timeout_ofertas_horas': 'Timeout de Ofertas',
      'notificacion_expiracion_horas_antes': 'Notificación de Expiración'
    };
    return labels[key] || key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  // Generate parametros dynamically from metadata
  const parametros = Object.entries(metadata)
    .filter(([key, meta]) => {
      // Only include parameters that have min/max (individual parameters, not categories)
      return meta && typeof meta === 'object' && ('min' in meta || 'max' in meta);
    })
    .map(([key, meta]) => ({
      key,
      label: formatLabel(key),
      description: meta.description || '',
      type: 'number' as const,
      min: meta.min ?? 0,
      max: meta.max ?? 100,
      step: (meta.min !== undefined && meta.min < 1) ? 0.1 : 1,
      default: meta.default ?? 0,
      unit: meta.unit || ''
    }))
    .sort((a, b) => a.label.localeCompare(b.label));

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 text-blue-800">
            <Info className="h-4 w-4" />
            Información sobre Parámetros Generales
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-700">
          <p>
            Estos parámetros controlan el comportamiento general del sistema, incluyendo timeouts,
            períodos de cálculo y umbrales operativos.
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {parametros.map((param) => (
          <Card key={param.key} className="relative">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">{param.label}</CardTitle>
              <p className="text-xs text-muted-foreground">{param.description}</p>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor={param.key}>
                  Valor ({param.unit})
                </Label>
                <Input
                  id={param.key}
                  type="number"
                  min={param.min}
                  max={param.max}
                  step={param.step || 1}
                  placeholder={param.default.toString()}
                  {...register(param.key as keyof ParametrosGenerales, { 
                    valueAsNumber: true,
                    required: 'Este campo es requerido',
                    min: { value: param.min, message: `Mínimo ${param.min}` },
                    max: { value: param.max, message: `Máximo ${param.max}` }
                  })}
                />
                {errors[param.key as keyof ParametrosGenerales] && (
                  <p className="text-sm text-red-600">
                    {errors[param.key as keyof ParametrosGenerales]?.message}
                  </p>
                )}
              </div>
              
              <div className="text-xs text-muted-foreground">
                <p>Recomendado: {param.default} {param.unit}</p>
                <p>Rango: {param.min} - {param.max} {param.unit}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {saveError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{saveError}</AlertDescription>
        </Alert>
      )}

      {saveSuccess && (
        <Alert className="border-green-200 bg-green-50">
          <AlertCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Configuración guardada exitosamente
          </AlertDescription>
        </Alert>
      )}

      <div className="flex justify-end">
        <Button
          type="submit"
          disabled={saving || !isDirty}
          className="min-w-[120px]"
        >
          {saving ? (
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Guardando...
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Save className="h-4 w-4" />
              Guardar
            </div>
          )}
        </Button>
      </div>
    </form>
  );
}