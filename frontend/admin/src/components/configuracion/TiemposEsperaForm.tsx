/**
 * Tiempos de Espera Form Component
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Save, Info, Clock } from 'lucide-react';
import { useConfiguracion } from '@/hooks/useConfiguracion';
import type { TiemposEsperaNivel, CategoriaConfiguracion } from '@/types/configuracion';

interface Props {
  data: TiemposEsperaNivel;
  categoria: CategoriaConfiguracion;
}

export function TiemposEsperaForm({ data, categoria }: Props) {
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
  } = useForm<any>({
    defaultValues: data
  });

  const watchedValues = watch();

  useEffect(() => {
    reset(data);
  }, [data, reset]);

  const onSubmit = async (formData: any) => {
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

  const niveles = [
    { key: 1, label: 'Nivel 1 (Premium)', color: 'bg-amber-100 text-amber-800', default: 15 },
    { key: 2, label: 'Nivel 2 (Alta Calidad)', color: 'bg-green-100 text-green-800', default: 20 },
    { key: 3, label: 'Nivel 3 (Estándar)', color: 'bg-blue-100 text-blue-800', default: 25 },
    { key: 4, label: 'Nivel 4 (Básico)', color: 'bg-orange-100 text-orange-800', default: 30 },
    { key: 5, label: 'Nivel 5 (Respaldo)', color: 'bg-gray-100 text-gray-800', default: 35 }
  ];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 text-blue-800">
            <Info className="h-4 w-4" />
            Información sobre Tiempos de Espera
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-700">
          <p>
            Los tiempos de espera determinan cuánto tiempo se espera en cada nivel antes de escalar al siguiente.
            Tiempos más cortos para niveles premium aseguran respuesta rápida de los mejores asesores.
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {niveles.map((nivel) => (
          <Card key={nivel.key} className="relative">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                <Badge variant="secondary" className={nivel.color}>
                  {nivel.label}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor={`nivel_${nivel.key}`}>
                  Tiempo de espera (minutos)
                </Label>
                <Input
                  id={`nivel_${nivel.key}`}
                  type="number"
                  min="1"
                  max="120"
                  placeholder={nivel.default.toString()}
                  {...register(nivel.key.toString(), { 
                    valueAsNumber: true,
                    required: 'Este campo es requerido',
                    min: { value: 1, message: 'Mínimo 1 minuto' },
                    max: { value: 120, message: 'Máximo 120 minutos' }
                  })}
                />
                {(errors as any)[nivel.key.toString()] && (
                  <p className="text-sm text-red-600">{(errors as any)[nivel.key.toString()]?.message}</p>
                )}
              </div>
              
              <div className="text-xs text-muted-foreground">
                <p>Valor actual: {(watchedValues as any)[nivel.key.toString()] || 0} min</p>
                <p>Recomendado: {nivel.default} min</p>
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