/**
 * Pesos de Evaluación Form Component
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
import type { PesosEvaluacionOfertas, CategoriaConfiguracion } from '@/types/configuracion';

const pesosSchema = z.object({
  precio: z.number().min(0).max(1),
  tiempo_entrega: z.number().min(0).max(1),
  garantia: z.number().min(0).max(1)
});

interface Props {
  data: PesosEvaluacionOfertas;
  categoria: CategoriaConfiguracion;
}

export function PesosEvaluacionForm({ data, categoria }: Props) {
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
  } = useForm<PesosEvaluacionOfertas>({
    resolver: zodResolver(pesosSchema),
    defaultValues: data
  });

  const watchedValues = watch();
  const suma = Object.values(watchedValues).reduce((acc, val) => acc + (val || 0), 0);
  const sumaPercentage = (suma / 1.0) * 100;

  useEffect(() => {
    reset(data);
  }, [data, reset]);

  const onSubmit = async (formData: PesosEvaluacionOfertas) => {
    try {
      setSaving(true);
      setSaveError(null);
      setSaveSuccess(false);

      const validation = configuracionService.validatePesos(formData);
      if (!validation.valid) {
        setSaveError(validation.error || 'Validación fallida');
        return;
      }

      await updateConfiguracion(categoria, formData);
      setSaveSuccess(true);
      
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Error guardando configuración');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 text-blue-800">
            <Info className="h-4 w-4" />
            Información sobre Pesos de Evaluación
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-700">
          <p className="mb-2">
            Los pesos determinan la importancia relativa de cada factor en la evaluación de ofertas:
          </p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li><strong>Precio:</strong> Competitividad del precio ofrecido (recomendado: 50%)</li>
            <li><strong>Tiempo de Entrega:</strong> Rapidez de entrega prometida (recomendado: 35%)</li>
            <li><strong>Garantía:</strong> Duración de la garantía ofrecida (recomendado: 15%)</li>
          </ul>
        </CardContent>
      </Card>

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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="space-y-2">
          <Label htmlFor="precio">
            Precio
            <span className="text-xs text-muted-foreground ml-2">(Recomendado: 50%)</span>
          </Label>
          <Input
            id="precio"
            type="number"
            step="0.01"
            min="0"
            max="1"
            placeholder="0.50"
            {...register('precio', { valueAsNumber: true })}
          />
          {errors.precio && (
            <p className="text-sm text-red-600">{errors.precio.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Peso actual: {((watchedValues.precio || 0) * 100).toFixed(1)}%
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="tiempo_entrega">
            Tiempo de Entrega
            <span className="text-xs text-muted-foreground ml-2">(Recomendado: 35%)</span>
          </Label>
          <Input
            id="tiempo_entrega"
            type="number"
            step="0.01"
            min="0"
            max="1"
            placeholder="0.35"
            {...register('tiempo_entrega', { valueAsNumber: true })}
          />
          {errors.tiempo_entrega && (
            <p className="text-sm text-red-600">{errors.tiempo_entrega.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Peso actual: {((watchedValues.tiempo_entrega || 0) * 100).toFixed(1)}%
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="garantia">
            Garantía
            <span className="text-xs text-muted-foreground ml-2">(Recomendado: 15%)</span>
          </Label>
          <Input
            id="garantia"
            type="number"
            step="0.01"
            min="0"
            max="1"
            placeholder="0.15"
            {...register('garantia', { valueAsNumber: true })}
          />
          {errors.garantia && (
            <p className="text-sm text-red-600">{errors.garantia.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Peso actual: {((watchedValues.garantia || 0) * 100).toFixed(1)}%
          </p>
        </div>
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