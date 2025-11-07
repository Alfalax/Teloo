/**
 * Canales de Notificación Form Component
 */

import { useState, useEffect } from 'react';

import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, Save, Info, MessageSquare } from 'lucide-react';
import { useConfiguracion } from '@/hooks/useConfiguracion';
import type { CanalesPorNivel, CategoriaConfiguracion } from '@/types/configuracion';
import { CANALES_DISPONIBLES } from '@/types/configuracion';

interface Props {
  data: CanalesPorNivel;
  categoria: CategoriaConfiguracion;
}

export function CanalesNotificacionForm({ data, categoria }: Props) {
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [formData, setFormData] = useState<CanalesPorNivel>(data);
  const { updateConfiguracion } = useConfiguracion();

  useEffect(() => {
    setFormData(data);
  }, [data]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
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

  const handleChannelChange = (nivel: number, canal: string) => {
    setFormData(prev => ({
      ...prev,
      [nivel as keyof CanalesPorNivel]: canal as 'WHATSAPP' | 'PUSH' | 'EMAIL' | 'SMS'
    }));
  };

  const isDirty = JSON.stringify(formData) !== JSON.stringify(data);

  const niveles = [
    { key: 1, label: 'Nivel 1 (Premium)', color: 'bg-amber-100 text-amber-800', recommended: 'WHATSAPP' },
    { key: 2, label: 'Nivel 2 (Alta Calidad)', color: 'bg-green-100 text-green-800', recommended: 'WHATSAPP' },
    { key: 3, label: 'Nivel 3 (Estándar)', color: 'bg-blue-100 text-blue-800', recommended: 'PUSH' },
    { key: 4, label: 'Nivel 4 (Básico)', color: 'bg-orange-100 text-orange-800', recommended: 'PUSH' },
    { key: 5, label: 'Nivel 5 (Respaldo)', color: 'bg-gray-100 text-gray-800', recommended: 'PUSH' }
  ];

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 text-blue-800">
            <Info className="h-4 w-4" />
            Información sobre Canales de Notificación
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-700">
          <p className="mb-2">
            Los canales determinan cómo se notifica a los asesores sobre nuevas solicitudes:
          </p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li><strong>WhatsApp:</strong> Notificación directa, alta visibilidad (recomendado para niveles 1-2)</li>
            <li><strong>Push:</strong> Notificación en la aplicación (recomendado para niveles 3-5)</li>
            <li><strong>Email:</strong> Notificación por correo electrónico</li>
            <li><strong>SMS:</strong> Mensaje de texto</li>
          </ul>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {niveles.map((nivel) => (
          <Card key={nivel.key} className="relative">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                <Badge variant="secondary" className={nivel.color}>
                  {nivel.label}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor={`canal_${nivel.key}`}>
                  Canal de notificación
                </Label>
                <Select
                  value={formData[nivel.key as keyof CanalesPorNivel] || nivel.recommended}
                  onValueChange={(value) => handleChannelChange(nivel.key, value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar canal" />
                  </SelectTrigger>
                  <SelectContent>
                    {CANALES_DISPONIBLES.map((canal) => (
                      <SelectItem key={canal.value} value={canal.value}>
                        {canal.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="text-xs text-muted-foreground">
                <p>Canal actual: {formData[nivel.key as keyof CanalesPorNivel] || 'No configurado'}</p>
                <p>Recomendado: {nivel.recommended}</p>
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