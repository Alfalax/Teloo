/**
 * User Form Component
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import type { Usuario } from '@/types/configuracion';
import { ROLES_DISPONIBLES, ESTADOS_USUARIO } from '@/types/configuracion';

const usuarioSchema = z.object({
  nombre_completo: z.string().min(2, 'El nombre debe tener al menos 2 caracteres'),
  email: z.string().email('Email inválido'),
  rol: z.enum(['ADMIN', 'ADVISOR', 'ANALYST', 'SUPPORT', 'CLIENT']),
  estado: z.enum(['ACTIVO', 'INACTIVO', 'SUSPENDIDO'])
});

type UsuarioFormData = z.infer<typeof usuarioSchema>;

interface Props {
  initialData?: Usuario;
  onSubmit: (data: UsuarioFormData) => Promise<void>;
  onCancel: () => void;
  isEditing?: boolean;
}

export function UsuarioForm({ initialData, onSubmit, onCancel, isEditing = false }: Props) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting }
  } = useForm<UsuarioFormData>({
    resolver: zodResolver(usuarioSchema),
    defaultValues: initialData ? {
      nombre_completo: initialData.nombre_completo,
      email: initialData.email,
      rol: initialData.rol,
      estado: initialData.estado
    } : {
      rol: 'CLIENT',
      estado: 'ACTIVO'
    }
  });

  const watchedRol = watch('rol');
  const watchedEstado = watch('estado');

  const handleFormSubmit = async (data: UsuarioFormData) => {
    try {
      await onSubmit(data);
    } catch (err) {
      // Error is handled by parent component
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="nombre_completo">Nombre Completo</Label>
        <Input
          id="nombre_completo"
          placeholder="Ej: Juan Pérez García"
          {...register('nombre_completo')}
        />
        {errors.nombre_completo && (
          <p className="text-sm text-red-600">{errors.nombre_completo.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="usuario@ejemplo.com"
          {...register('email')}
        />
        {errors.email && (
          <p className="text-sm text-red-600">{errors.email.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="rol">Rol</Label>
        <Select
          value={watchedRol}
          onValueChange={(value) => setValue('rol', value as any)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Seleccionar rol" />
          </SelectTrigger>
          <SelectContent>
            {ROLES_DISPONIBLES.map((rol) => (
              <SelectItem key={rol.value} value={rol.value}>
                {rol.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.rol && (
          <p className="text-sm text-red-600">{errors.rol.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="estado">Estado</Label>
        <Select
          value={watchedEstado}
          onValueChange={(value) => setValue('estado', value as any)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Seleccionar estado" />
          </SelectTrigger>
          <SelectContent>
            {ESTADOS_USUARIO.map((estado) => (
              <SelectItem key={estado.value} value={estado.value}>
                {estado.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.estado && (
          <p className="text-sm text-red-600">{errors.estado.message}</p>
        )}
      </div>

      {/* Role Description */}
      {watchedRol && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {watchedRol === 'ADMIN' && 'Acceso completo al sistema, incluyendo configuración y gestión de usuarios.'}
            {watchedRol === 'ADVISOR' && 'Acceso a solicitudes, ofertas y gestión de inventario.'}
            {watchedRol === 'ANALYST' && 'Acceso a reportes, analytics y métricas del sistema.'}
            {watchedRol === 'SUPPORT' && 'Acceso a PQR, soporte técnico y monitoreo del sistema.'}
            {watchedRol === 'CLIENT' && 'Acceso básico como cliente del marketplace.'}
          </AlertDescription>
        </Alert>
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
            isEditing ? 'Actualizar Usuario' : 'Crear Usuario'
          )}
        </Button>
      </div>
    </form>
  );
}