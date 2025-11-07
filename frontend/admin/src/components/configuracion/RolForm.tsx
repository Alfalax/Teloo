/**
 * Role Form Component
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { AlertCircle, Shield } from 'lucide-react';
import type { Rol } from '@/types/configuracion';

const rolSchema = z.object({
  nombre: z.string().min(2, 'El nombre debe tener al menos 2 caracteres'),
  descripcion: z.string().min(10, 'La descripción debe tener al menos 10 caracteres'),
  activo: z.boolean()
});

type RolFormData = z.infer<typeof rolSchema>;

interface Props {
  initialData?: Rol;
  permisosDisponibles: string[];
  onSubmit: (data: RolFormData & { permisos: string[] }) => Promise<void>;
  onCancel: () => void;
  isEditing?: boolean;
}

export function RolForm({ 
  initialData, 
  permisosDisponibles, 
  onSubmit, 
  onCancel, 
  isEditing = false 
}: Props) {
  const [selectedPermisos, setSelectedPermisos] = useState<string[]>(
    initialData?.permisos || []
  );

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting }
  } = useForm<RolFormData>({
    resolver: zodResolver(rolSchema),
    defaultValues: initialData ? {
      nombre: initialData.nombre,
      descripcion: initialData.descripcion,
      activo: initialData.activo
    } : {
      activo: true
    }
  });

  const watchedActivo = watch('activo');

  const handleFormSubmit = async (data: RolFormData) => {
    try {
      await onSubmit({
        ...data,
        permisos: selectedPermisos
      });
    } catch (err) {
      // Error is handled by parent component
    }
  };

  const handlePermisoToggle = (permiso: string, checked: boolean) => {
    if (checked) {
      setSelectedPermisos(prev => [...prev, permiso]);
    } else {
      setSelectedPermisos(prev => prev.filter(p => p !== permiso));
    }
  };

  const toggleAllPermisos = () => {
    if (selectedPermisos.length === permisosDisponibles.length) {
      setSelectedPermisos([]);
    } else {
      setSelectedPermisos([...permisosDisponibles]);
    }
  };

  // Group permissions by category
  const groupedPermisos = permisosDisponibles.reduce((groups, permiso) => {
    const category = permiso.split(':')[0] || 'general';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(permiso);
    return groups;
  }, {} as Record<string, string[]>);

  const getCategoryTitle = (category: string) => {
    const titles: Record<string, string> = {
      'admin': 'Administración',
      'solicitudes': 'Solicitudes',
      'ofertas': 'Ofertas',
      'asesores': 'Asesores',
      'analytics': 'Analytics',
      'pqr': 'PQR',
      'configuracion': 'Configuración',
      'general': 'General'
    };
    return titles[category] || category;
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Basic Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="nombre">Nombre del Rol</Label>
          <Input
            id="nombre"
            placeholder="Ej: Supervisor de Ventas"
            {...register('nombre')}
          />
          {errors.nombre && (
            <p className="text-sm text-red-600">{errors.nombre.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="activo" className="flex items-center gap-2">
            Estado del Rol
          </Label>
          <div className="flex items-center space-x-2">
            <Switch
              id="activo"
              checked={watchedActivo}
              onCheckedChange={(checked) => setValue('activo', checked)}
            />
            <Label htmlFor="activo" className="text-sm">
              {watchedActivo ? 'Activo' : 'Inactivo'}
            </Label>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="descripcion">Descripción</Label>
        <Textarea
          id="descripcion"
          placeholder="Describe las responsabilidades y alcance de este rol..."
          rows={3}
          {...register('descripcion')}
        />
        {errors.descripcion && (
          <p className="text-sm text-red-600">{errors.descripcion.message}</p>
        )}
      </div>

      {/* Permissions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Permisos del Rol
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {selectedPermisos.length} de {permisosDisponibles.length} seleccionados
              </Badge>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={toggleAllPermisos}
              >
                {selectedPermisos.length === permisosDisponibles.length ? 'Deseleccionar Todo' : 'Seleccionar Todo'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {Object.keys(groupedPermisos).length === 0 ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No hay permisos disponibles para asignar
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-6">
              {Object.entries(groupedPermisos).map(([category, permisos]) => (
                <div key={category} className="space-y-3">
                  <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
                    {getCategoryTitle(category)}
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {permisos.map((permiso) => (
                      <div key={permiso} className="flex items-center space-x-2">
                        <Checkbox
                          id={permiso}
                          checked={selectedPermisos.includes(permiso)}
                          onCheckedChange={(checked) => 
                            handlePermisoToggle(permiso, checked as boolean)
                          }
                        />
                        <Label
                          htmlFor={permiso}
                          className="text-sm font-normal cursor-pointer"
                        >
                          {permiso.replace(/^[^:]+:/, '').replace(/_/g, ' ')}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Selected Permissions Summary */}
      {selectedPermisos.length > 0 && (
        <Card className="bg-muted/50">
          <CardHeader>
            <CardTitle className="text-sm">Permisos Seleccionados</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {selectedPermisos.map((permiso) => (
                <Badge key={permiso} variant="secondary" className="text-xs">
                  {permiso}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-end gap-2 pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancelar
        </Button>
        <Button
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              {isEditing ? 'Actualizando...' : 'Creando...'}
            </div>
          ) : (
            isEditing ? 'Actualizar Rol' : 'Crear Rol'
          )}
        </Button>
      </div>
    </form>
  );
}