/**
 * Umbrales de Niveles Form Component
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Save, Info, TrendingDown } from 'lucide-react';
import { useConfiguracion } from '@/hooks/useConfiguracion';
import { configuracionService } from '@/services/configuracion';
import type { UmbralesNiveles, CategoriaConfiguracion } from '@/types/configuracion';

const umbralesSchema = z.object({
  nivel1_min: z.number().min(1).max(5),
  nivel2_min: z.number().min(1).max(5),
  nivel3_min: z.number().min(1).max(5),
  nivel4_min: z.number().min(1).max(5)
});

interface Props {
  data: UmbralesNiveles;
  categoria: CategoriaConfiguracion;
}

export function UmbralesNivelesForm({ data, categoria }: Props) {
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
  } = useForm<UmbralesNiveles>({
    resolver: zodResolver(umbralesSchema),
    defaultValues: data
  });

  const watchedValues = watch();

  useEffect(() => {
    reset(data);
  }, [data, reset]);

  const onSubmit = async (formData: UmbralesNiveles) => {
    try {
      setSaving(true);
      setSaveError(null);
      setSaveSuccess(false);

      // Validate thresholds are decreasing
      const validation = configuracionService.validateUmbrales(formData);
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

  const isValidOrder = () => {
    const { nivel1_min, nivel2_min, nivel3_min, nivel4_min } = watchedValues;
    return nivel1_min > nivel2_min && 
           nivel2_min > nivel3_min && 
           nivel3_min > nivel4_min;
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 text-blue-800">
            <Info className="h-4 w-4" />
            Información sobre Umbrales de Niveles
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-700">
          <p className="mb-2">
            Los umbrales determinan cómo se clasifican los asesores en niveles según su puntaje total:
          </p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li><strong>Nivel 1:</strong> Asesores premium (puntaje ≥ nivel1_min)</li>
            <li><strong>Nivel 2:</strong> Asesores de alta calidad (puntaje ≥ nivel2_min)</li>
            <li><strong>Nivel 3:</strong> Asesores estándar (puntaje ≥ nivel3_min)</li>
            <li><strong>Nivel 4:</strong> Asesores básicos (puntaje ≥ nivel4_min)</li>
            <li><strong>Nivel 5:</strong> Asesores de respaldo (puntaje &lt; nivel4_min)</li>
          </ul>
        </CardContent>
      </Card>

      {/* Validation Status */}
      <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
        <TrendingDown className={`h-4 w-4 ${isValidOrder() ? 'text-green-600' : 'text-red-600'}`} />
        <span className="text-sm">
          Orden de umbrales: {isValidOrder() ? 'Válido' : 'Inválido'}
        </span>
        {isValidOrder() && (
          <Badge variant="outline" className="text-green-600 border-green-600">
            Decreciente ✓
          </Badge>
        )}
      </div>

      {/* Form Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="nivel1_min" className="flex items-center gap-2">
            Umbral Nivel 1 (Premium)
            <Badge variant="secondary" className="bg-amber-100 text-amber-800">
              Más Alto
            </Badge>
          </Label>
          <Input
            id="nivel1_min"
            type="number"
            step="0.1"
            min="1"
            max="5"
            placeholder="4.5"
            {...register('nivel1_min', { valueAsNumber: true })}
          />
          {errors.nivel1_min && (
            <p className="text-sm text-red-600">{errors.nivel1_min.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Asesores con puntaje ≥ {watchedValues.nivel1_min || 0} serán Nivel 1
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="nivel2_min" className="flex items-center gap-2">
            Umbral Nivel 2 (Alta Calidad)
            <Badge variant="secondary" className="bg-green-100 text-green-800">
              Alto
            </Badge>
          </Label>
          <Input
            id="nivel2_min"
            type="number"
            step="0.1"
            min="1"
            max="5"
            placeholder="4.0"
            {...register('nivel2_min', { valueAsNumber: true })}
          />
          {errors.nivel2_min && (
            <p className="text-sm text-red-600">{errors.nivel2_min.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Asesores con puntaje ≥ {watchedValues.nivel2_min || 0} serán Nivel 2
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="nivel3_min" className="flex items-center gap-2">
            Umbral Nivel 3 (Estándar)
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              Medio
            </Badge>
          </Label>
          <Input
            id="nivel3_min"
            type="number"
            step="0.1"
            min="1"
            max="5"
            placeholder="3.5"
            {...register('nivel3_min', { valueAsNumber: true })}
          />
          {errors.nivel3_min && (
            <p className="text-sm text-red-600">{errors.nivel3_min.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Asesores con puntaje ≥ {watchedValues.nivel3_min || 0} serán Nivel 3
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="nivel4_min" className="flex items-center gap-2">
            Umbral Nivel 4 (Básico)
            <Badge variant="secondary" className="bg-orange-100 text-orange-800">
              Bajo
            </Badge>
          </Label>
          <Input
            id="nivel4_min"
            type="number"
            step="0.1"
            min="1"
            max="5"
            placeholder="3.0"
            {...register('nivel4_min', { valueAsNumber: true })}
          />
          {errors.nivel4_min && (
            <p className="text-sm text-red-600">{errors.nivel4_min.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Asesores con puntaje ≥ {watchedValues.nivel4_min || 0} serán Nivel 4
          </p>
        </div>
      </div>

      {/* Level 5 Info */}
      <Card className="bg-gray-50 border-gray-200">
        <CardContent className="pt-4">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="secondary" className="bg-gray-100 text-gray-800">
              Nivel 5 (Respaldo)
            </Badge>
            <span className="text-sm text-muted-foreground">Automático</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Los asesores con puntaje &lt; {watchedValues.nivel4_min || 0} serán clasificados automáticamente como Nivel 5
          </p>
        </CardContent>
      </Card>

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
          disabled={saving || !isDirty || !isValidOrder()}
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