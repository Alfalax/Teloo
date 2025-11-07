/**
 * Pesos de Escalamiento Form Component
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Save, Info } from 'lucide-react';
import { useConfiguracion } from '@/hooks/useConfiguracion';
import { configuracionService } from '@/services/configuracion';
import type { PesosEscalamiento, CategoriaConfiguracion } from '@/types/configuracion';

const pesosSchema = z.object({
  proximidad: z.number().min(0).max(1),
  actividad: z.number().min(0).max(1),
  desempeno: z.number().min(0).max(1),
  confianza: z.number().min(0).max(1)
});

interface Props {
  data: PesosEscalamiento;
  categoria: CategoriaConfiguracion;
}

export function PesosEscalamientoForm({ data, categoria }: Props) {
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const { updateConfiguracion } = useConfiguracion();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isDirty },
    reset
  } = useForm<PesosEscalamiento>({
    resolver: zodResolver(pesosSchema),
    defaultValues: data
  });

  const watchedValues = watch();
  const suma = Object.values(watchedValues).reduce((acc, val) => acc + (val || 0), 0);
  const sumaPercentage = (suma / 1.0) * 100;

  useEffect(() => {
    reset(data);
  }, [data, reset]);

  const onSubmit = async (formData: PesosEscalamiento) => {
    try {
      setSaving(true);
      setSaveError(null);
      setSaveSuccess(false);

      // Validate weights sum to 1.0
      const validation = configuracionService.validatePesos(formData);
      if (!validation.valid) {
        setSaveError(validation.error || 'Validación fallida');
        return;
      }

      await updateConfiguracion(categoria, formData);
      setSaveSuccess(true);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Error guardando configuración');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 text-blue-800">
            <Info className="h-4 w-4" />
            Información sobre Pesos de Escalamiento
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-700">
          <p className="mb-2">
            Los pesos determinan la importancia relativa de cada variable en el cálculo del puntaje total de escalamiento:
          </p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li><strong>Proximidad:</strong> Cercanía geográfica (ciudad, área metropolitana, hub logístico)</li>
            <li><strong>Actividad:</strong> Porcentaje de respuesta a solicitudes en los últimos 30 días</li>
            <li><strong>Desempeño:</strong> Tasa de adjudicación, cumplimiento y eficiencia de respuesta</li>
            <li><strong>Confianza:</strong> Nivel de confianza basado en auditorías de tienda</li>
          </ul>
        </CardContent>
      </Card>

      {/* Suma Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="text-sm font-medium">Suma Total de Pesos</Label>
          <span className={`text-sm font-mono ${Math.abs(suma - 1.0) <= 1e-6 ? 'text-green-600' : 'text-red-600'}`}>
            {suma.toFixed(6)}
          </span>
        </div>
        <Progress 
          value={sumaPercentage} 
          className={`h-2 ${Math.abs(suma - 1.0) <= 1e-6 ? '' : 'bg-red-100'}`}
        />
        <p className="text-xs text-muted-foreground">
          Los pesos deben sumar exactamente 1.0 para ser válidos
        </p>
      </div>

      {/* Form Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="proximidad">
            Proximidad Geográfica
            <span className="text-xs text-muted-foreground ml-2">(Recomendado: 40%)</span>
          </Label>
          <Input
            id="proximidad"
            type="number"
            step="0.01"
            min="0"
            max="1"
            placeholder="0.40"
            {...register('proximidad', { valueAsNumber: true })}
          />
          {errors.proximidad && (
            <p className="text-sm text-red-600">{errors.proximidad.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Peso actual: {((watchedValues.proximidad || 0) * 100).toFixed(1)}%
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="actividad">
            Actividad Reciente
            <span className="text-xs text-muted-foreground ml-2">(Recomendado: 25%)</span>
          </Label>
          <Input
            id="actividad"
            type="number"
            step="0.01"
            min="0"
            max="1"
            placeholder="0.25"
            {...register('actividad', { valueAsNumber: true })}
          />
          {errors.actividad && (
            <p className="text-sm text-red-600">{errors.actividad.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Peso actual: {((watchedValues.actividad || 0) * 100).toFixed(1)}%
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="desempeno">
            Desempeño Histórico
            <span className="text-xs text-muted-foreground ml-2">(Recomendado: 20%)</span>
          </Label>
          <Input
            id="desempeno"
            type="number"
            step="0.01"
            min="0"
            max="1"
            placeholder="0.20"
            {...register('desempeno', { valueAsNumber: true })}
          />
          {errors.desempeno && (
            <p className="text-sm text-red-600">{errors.desempeno.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Peso actual: {((watchedValues.desempeno || 0) * 100).toFixed(1)}%
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="confianza">
            Nivel de Confianza
            <span className="text-xs text-muted-foreground ml-2">(Recomendado: 15%)</span>
          </Label>
          <Input
            id="confianza"
            type="number"
            step="0.01"
            min="0"
            max="1"
            placeholder="0.15"
            {...register('confianza', { valueAsNumber: true })}
          />
          {errors.confianza && (
            <p className="text-sm text-red-600">{errors.confianza.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Peso actual: {((watchedValues.confianza || 0) * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Validation Errors */}


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

      {/* Submit Button */}
      <div className="flex justify-end">
        <Button
          type="submit"
          disabled={saving || !isDirty || Math.abs(suma - 1.0) > 1e-6}
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