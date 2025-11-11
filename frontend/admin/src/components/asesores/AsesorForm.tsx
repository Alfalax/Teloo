import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Asesor, AsesorCreate, AsesorUpdate } from '@/types/asesores';
import { asesoresService } from '@/services/asesores';

interface AsesorFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: AsesorCreate | AsesorUpdate) => Promise<void>;
  asesor?: Asesor | null;
  isLoading?: boolean;
}

export function AsesorForm({
  isOpen,
  onClose,
  onSubmit,
  asesor,
  isLoading = false,
}: AsesorFormProps) {
  const [formData, setFormData] = useState<AsesorCreate>({
    nombre: '',
    apellido: '',
    email: '',
    telefono: '',
    ciudad: '',
    departamento: '',
    punto_venta: '',
    direccion_punto_venta: '',
    password: '',
  });

  const [ciudades, setCiudades] = useState<string[]>([]);
  const [departamentos, setDepartamentos] = useState<string[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState<string>('');
  const [loadingData, setLoadingData] = useState(false);
  const [loadingCiudades, setLoadingCiudades] = useState(false);

  const isEditing = !!asesor;

  useEffect(() => {
    if (isOpen) {
      loadFormData();
      setServerError(''); // Clear server error when opening form
      setErrors({}); // Clear validation errors
    }
  }, [isOpen]);

  useEffect(() => {
    if (asesor) {
      setFormData({
        nombre: asesor.usuario.nombre,
        apellido: asesor.usuario.apellido,
        email: asesor.usuario.email,
        telefono: asesor.usuario.telefono,
        ciudad: asesor.ciudad,
        departamento: asesor.departamento,
        punto_venta: asesor.punto_venta,
        direccion_punto_venta: asesor.direccion_punto_venta || '',
        password: '', // Password is not required for editing
      });
    } else {
      setFormData({
        nombre: '',
        apellido: '',
        email: '',
        telefono: '',
        ciudad: '',
        departamento: '',
        punto_venta: '',
        direccion_punto_venta: '',
        password: '',
      });
    }
    setErrors({});
  }, [asesor]);

  const loadFormData = async () => {
    setLoadingData(true);
    try {
      const departamentosData = await asesoresService.getDepartamentos();
      setDepartamentos(departamentosData);
      
      // If editing and has departamento, load ciudades for that departamento
      if (asesor?.departamento) {
        await loadCiudadesByDepartamento(asesor.departamento);
      }
    } catch (error) {
      console.error('Error loading form data:', error);
    } finally {
      setLoadingData(false);
    }
  };

  const loadCiudadesByDepartamento = async (departamento: string) => {
    if (!departamento) {
      setCiudades([]);
      return;
    }
    
    setLoadingCiudades(true);
    try {
      // Import geografia service
      const { geografiaService } = await import('@/services/geografia');
      const ciudadesData = await geografiaService.getCiudadesByDepartamento(departamento);
      setCiudades(ciudadesData);
    } catch (error) {
      console.error('Error loading ciudades:', error);
      // Fallback to all ciudades if departamento filter fails
      try {
        const ciudadesData = await asesoresService.getCiudades();
        setCiudades(ciudadesData);
      } catch (fallbackError) {
        console.error('Error loading all ciudades:', fallbackError);
      }
    } finally {
      setLoadingCiudades(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.nombre.trim()) {
      newErrors.nombre = 'El nombre es requerido';
    }

    if (!formData.apellido.trim()) {
      newErrors.apellido = 'El apellido es requerido';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'El email es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'El email debe tener un formato válido';
    }

    if (!formData.telefono.trim()) {
      newErrors.telefono = 'El teléfono es requerido';
    } else if (!/^\+57[0-9]{10}$/.test(formData.telefono)) {
      newErrors.telefono = 'El teléfono debe tener formato colombiano +57XXXXXXXXXX';
    }

    if (!formData.ciudad.trim()) {
      newErrors.ciudad = 'La ciudad es requerida';
    }

    if (!formData.departamento.trim()) {
      newErrors.departamento = 'El departamento es requerido';
    }

    if (!formData.punto_venta.trim()) {
      newErrors.punto_venta = 'El punto de venta es requerido';
    }

    if (!isEditing && !formData.password.trim()) {
      newErrors.password = 'La contraseña es requerida';
    } else if (!isEditing && formData.password.length < 8) {
      newErrors.password = 'La contraseña debe tener al menos 8 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      if (isEditing) {
        // For editing, exclude password if empty
        const updateData: AsesorUpdate = {
          nombre: formData.nombre,
          apellido: formData.apellido,
          email: formData.email,
          telefono: formData.telefono,
          ciudad: formData.ciudad,
          departamento: formData.departamento,
          punto_venta: formData.punto_venta,
          direccion_punto_venta: formData.direccion_punto_venta || undefined,
        };
        await onSubmit(updateData);
      } else {
        await onSubmit(formData);
      }
      setServerError('');
      onClose();
    } catch (error: any) {
      console.error('Error submitting form:', error);
      const errorMessage = error.message || error.response?.data?.detail || 'Error al guardar el asesor';
      setServerError(errorMessage);
    }
  };

  const handleInputChange = (field: keyof AsesorCreate, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
    
    // Load ciudades when departamento changes
    if (field === 'departamento') {
      setFormData(prev => ({ ...prev, ciudad: '' })); // Reset ciudad
      loadCiudadesByDepartamento(value);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Editar Asesor' : 'Crear Nuevo Asesor'}
          </DialogTitle>
        </DialogHeader>
        <DialogDescription>
          {isEditing 
            ? 'Modifica la información del asesor'
            : 'Completa la información para crear un nuevo asesor'
          }
        </DialogDescription>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="nombre">Nombre *</Label>
              <Input
                id="nombre"
                value={formData.nombre}
                onChange={(e) => handleInputChange('nombre', e.target.value)}
                placeholder="Nombre del asesor"
                disabled={loadingData || isLoading}
              />
              {errors.nombre && (
                <p className="text-sm text-destructive">{errors.nombre}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="apellido">Apellido *</Label>
              <Input
                id="apellido"
                value={formData.apellido}
                onChange={(e) => handleInputChange('apellido', e.target.value)}
                placeholder="Apellido del asesor"
                disabled={loadingData || isLoading}
              />
              {errors.apellido && (
                <p className="text-sm text-destructive">{errors.apellido}</p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email *</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="email@ejemplo.com"
              disabled={loadingData || isLoading}
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="telefono">Teléfono *</Label>
            <Input
              id="telefono"
              value={formData.telefono}
              onChange={(e) => handleInputChange('telefono', e.target.value)}
              placeholder="+57XXXXXXXXXX"
              disabled={loadingData || isLoading}
            />
            {errors.telefono && (
              <p className="text-sm text-destructive">{errors.telefono}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="departamento">Departamento *</Label>
              <Select
                value={formData.departamento}
                onValueChange={(value) => handleInputChange('departamento', value)}
                disabled={loadingData || isLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar departamento" />
                </SelectTrigger>
                <SelectContent>
                  {departamentos.map((dept) => (
                    <SelectItem key={dept} value={dept}>
                      {dept}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.departamento && (
                <p className="text-sm text-destructive">{errors.departamento}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="ciudad">Ciudad *</Label>
              <Select
                value={formData.ciudad}
                onValueChange={(value) => handleInputChange('ciudad', value)}
                disabled={loadingData || isLoading || loadingCiudades || !formData.departamento}
              >
                <SelectTrigger>
                  <SelectValue 
                    placeholder={
                      !formData.departamento 
                        ? "Primero selecciona un departamento" 
                        : loadingCiudades 
                        ? "Cargando ciudades..." 
                        : "Seleccionar ciudad"
                    } 
                  />
                </SelectTrigger>
                <SelectContent>
                  {ciudades.map((ciudad) => (
                    <SelectItem key={ciudad} value={ciudad}>
                      {ciudad}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.ciudad && (
                <p className="text-sm text-destructive">{errors.ciudad}</p>
              )}
              {loadingCiudades && (
                <p className="text-xs text-muted-foreground">Cargando ciudades...</p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="punto_venta">Punto de Venta *</Label>
            <Input
              id="punto_venta"
              value={formData.punto_venta}
              onChange={(e) => handleInputChange('punto_venta', e.target.value)}
              placeholder="Nombre del punto de venta"
              disabled={loadingData || isLoading}
            />
            {errors.punto_venta && (
              <p className="text-sm text-destructive">{errors.punto_venta}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="direccion_punto_venta">Dirección del Punto de Venta</Label>
            <Input
              id="direccion_punto_venta"
              value={formData.direccion_punto_venta}
              onChange={(e) => handleInputChange('direccion_punto_venta', e.target.value)}
              placeholder="Dirección completa (opcional)"
              disabled={loadingData || isLoading}
            />
          </div>

          {!isEditing && (
            <div className="space-y-2">
              <Label htmlFor="password">Contraseña *</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                placeholder="Mínimo 8 caracteres"
                disabled={loadingData || isLoading}
              />
              {errors.password && (
                <p className="text-sm text-destructive">{errors.password}</p>
              )}
            </div>
          )}

          {serverError && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3 mt-4">
              <p className="text-sm text-red-800">{serverError}</p>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={isLoading || loadingData}
            >
              {isLoading ? 'Guardando...' : (isEditing ? 'Actualizar' : 'Crear')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}