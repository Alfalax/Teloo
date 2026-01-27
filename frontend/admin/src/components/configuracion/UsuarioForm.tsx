/**
 * User Form Component
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Store, MapPin } from 'lucide-react';
import type { Usuario } from '@/types/configuracion';
import { ROLES_DISPONIBLES, ESTADOS_USUARIO } from '@/types/configuracion';
import axios from '@/lib/axios';

const usuarioSchema = z.object({
  nombre_completo: z.string().min(2, 'El nombre debe tener al menos 2 caracteres'),
  email: z.string().email('Email inválido'),
  telefono: z.string().regex(/^\+57[0-9]{10}$/, 'Formato: +57XXXXXXXXXX (10 dígitos)'),
  rol: z.enum(['ADMIN', 'ADVISOR', 'ANALYST', 'SUPPORT', 'CLIENT']),
  estado: z.enum(['ACTIVO', 'INACTIVO', 'SUSPENDIDO']),
  // Campos condicionales para Asesor
  punto_venta: z.string().optional(),
  municipio_id: z.string().optional(),
  direccion_punto_venta: z.string().optional(),
}).superRefine((data, ctx) => {
  if (data.rol === 'ADVISOR') {
    if (!data.punto_venta || data.punto_venta.trim().length === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "El nombre del punto de venta es obligatorio",
        path: ["punto_venta"],
      });
    }
    if (!data.municipio_id) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Debe seleccionar una ciudad",
        path: ["municipio_id"],
      });
    }
    if (!data.direccion_punto_venta || data.direccion_punto_venta.trim().length === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "La dirección del punto de venta es obligatoria",
        path: ["direccion_punto_venta"],
      });
    }
  }
});

type UsuarioFormData = z.infer<typeof usuarioSchema>;

interface Municipio {
  id: string;
  municipio: string;
  departamento: string;
}

interface Props {
  initialData?: Usuario;
  onSubmit: (data: UsuarioFormData) => Promise<void>;
  onCancel: () => void;
  isEditing?: boolean;
}

export function UsuarioForm({ initialData, onSubmit, onCancel, isEditing = false }: Props) {
  const [municipios, setMunicipios] = useState<Municipio[]>([]);
  const [loadingMunicipios, setLoadingMunicipios] = useState(false);

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
      telefono: initialData.telefono || '',
      rol: initialData.rol,
      estado: initialData.estado
    } : {
      telefono: '+57',
      rol: 'CLIENT',
      estado: 'ACTIVO'
    }
  });

  const watchedRol = watch('rol');
  const watchedEstado = watch('estado');
  const watchedMunicipio = watch('municipio_id');

  useEffect(() => {
    const fetchMunicipios = async () => {
      setLoadingMunicipios(true);
      try {
        const response = await axios.get('/admin/geografia/municipios', {
          params: { limit: 200 } // Ajustar según sea necesario
        });
        if (response.data.success) {
          setMunicipios(response.data.municipios);
        }
      } catch (error) {
        console.error("Error cargando municipios:", error);
      } finally {
        setLoadingMunicipios(false);
      }
    };

    fetchMunicipios();
  }, []);

  const handleFormSubmit = async (data: UsuarioFormData) => {
    try {
      await onSubmit(data);
    } catch (err) {
      // Error is handled by parent component
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4 max-h-[70vh] overflow-y-auto px-1">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="nombre_completo">Nombre Completo</Label>
          <Input
            id="nombre_completo"
            placeholder="Ej: Juan Pérez García"
            {...register('nombre_completo')}
          />
          {errors.nombre_completo && (
            <p className="text-sm text-red-600 font-medium">{errors.nombre_completo.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="usuario@ejemplo.com"
            disabled={isEditing}
            {...register('email')}
          />
          {errors.email && (
            <p className="text-sm text-red-600 font-medium">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="telefono">Teléfono</Label>
          <Input
            id="telefono"
            type="tel"
            placeholder="+573001234567"
            {...register('telefono')}
          />
          {errors.telefono && (
            <p className="text-sm text-red-600 font-medium">{errors.telefono.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="rol">Rol del Usuario</Label>
          <Select
            value={watchedRol}
            onValueChange={(value) => setValue('rol', value as any)}
            disabled={isEditing}
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
            <p className="text-sm text-red-600 font-medium">{errors.rol.message}</p>
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
            <p className="text-sm text-red-600 font-medium">{errors.estado.message}</p>
          )}
        </div>
      </div>

      {/* Sección Condicional para Asesores */}
      {watchedRol === 'ADVISOR' && (
        <div className="mt-6 p-4 border rounded-lg bg-blue-50/50 space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
          <div className="flex items-center gap-2 text-blue-700 font-semibold mb-2">
            <Store className="h-5 w-5" />
            <h3>Información del Asesor / Punto de Venta</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="punto_venta">Nombre del Punto de Venta</Label>
              <Input
                id="punto_venta"
                placeholder="Ej: Repuestos El Sol"
                {...register('punto_venta')}
              />
              {errors.punto_venta && (
                <p className="text-sm text-red-600 font-medium">{errors.punto_venta.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="municipio_id">Ciudad / Municipio</Label>
              <Select
                value={watchedMunicipio}
                onValueChange={(value) => setValue('municipio_id', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder={loadingMunicipios ? "Cargando..." : "Seleccionar ciudad"} />
                </SelectTrigger>
                <SelectContent>
                  {municipios.map((m) => (
                    <SelectItem key={m.id} value={m.id}>
                      {m.municipio} ({m.departamento})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.municipio_id && (
                <p className="text-sm text-red-600 font-medium">{errors.municipio_id.message}</p>
              )}
            </div>

            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="direccion_punto_venta" className="flex items-center gap-1">
                <MapPin className="h-3 w-3" /> Dirección Física
              </Label>
              <Input
                id="direccion_punto_venta"
                placeholder="Ej: Calle 10 # 5-20, Barrio Centro"
                {...register('direccion_punto_venta')}
              />
              {errors.direccion_punto_venta && (
                <p className="text-sm text-red-600 font-medium">{errors.direccion_punto_venta.message}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Role Description */}
      {watchedRol && watchedRol !== 'ADVISOR' && (
        <Alert className="bg-slate-50">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {watchedRol === 'ADMIN' && 'Acceso completo al sistema, incluyendo configuración y gestión de usuarios.'}
            {watchedRol === 'ANALYST' && 'Acceso a reportes, analytics y métricas del sistema.'}
            {watchedRol === 'SUPPORT' && 'Acceso a PQR, soporte técnico y monitoreo del sistema.'}
            {watchedRol === 'CLIENT' && 'Acceso básico como cliente del marketplace.'}
          </AlertDescription>
        </Alert>
      )}

      <div className="flex justify-end gap-3 pt-6 border-t">
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
          className="bg-blue-600 hover:bg-blue-700"
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
