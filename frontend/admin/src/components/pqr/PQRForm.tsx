import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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
import { PQRCreate } from '@/types/pqr';

interface PQRFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: PQRCreate) => Promise<void>;
  isLoading?: boolean;
}

export function PQRForm({ isOpen, onClose, onSubmit, isLoading }: PQRFormProps) {
  const [formData, setFormData] = useState<PQRCreate>({
    cliente_id: '',
    tipo: 'PETICION',
    prioridad: 'MEDIA',
    resumen: '',
    detalle: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!isOpen) {
      // Reset form when dialog closes
      setFormData({
        cliente_id: '',
        tipo: 'PETICION',
        prioridad: 'MEDIA',
        resumen: '',
        detalle: '',
      });
      setErrors({});
    }
  }, [isOpen]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.cliente_id.trim()) {
      newErrors.cliente_id = 'El ID del cliente es requerido';
    }

    if (!formData.resumen.trim()) {
      newErrors.resumen = 'El resumen es requerido';
    } else if (formData.resumen.length < 10) {
      newErrors.resumen = 'El resumen debe tener al menos 10 caracteres';
    } else if (formData.resumen.length > 200) {
      newErrors.resumen = 'El resumen no puede exceder 200 caracteres';
    }

    if (!formData.detalle.trim()) {
      newErrors.detalle = 'El detalle es requerido';
    } else if (formData.detalle.length < 20) {
      newErrors.detalle = 'El detalle debe tener al menos 20 caracteres';
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
      await onSubmit(formData);
    } catch (error: any) {
      // Handle specific validation errors from server
      if (error.message.includes('Cliente no encontrado')) {
        setErrors({ cliente_id: 'Cliente no encontrado' });
      } else {
        setErrors({ general: error.message });
      }
    }
  };

  const handleInputChange = (field: keyof PQRCreate, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Nueva PQR</DialogTitle>
          <DialogDescription>
            Crear una nueva Petición, Queja o Reclamo
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.general && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {errors.general}
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            {/* Cliente ID */}
            <div className="space-y-2">
              <Label htmlFor="cliente_id">ID del Cliente *</Label>
              <Input
                id="cliente_id"
                value={formData.cliente_id}
                onChange={(e) => handleInputChange('cliente_id', e.target.value)}
                placeholder="UUID del cliente"
                disabled={isLoading}
              />
              {errors.cliente_id && (
                <p className="text-sm text-destructive">{errors.cliente_id}</p>
              )}
            </div>

            {/* Tipo */}
            <div className="space-y-2">
              <Label>Tipo *</Label>
              <Select
                value={formData.tipo}
                onValueChange={(value: 'PETICION' | 'QUEJA' | 'RECLAMO') => 
                  handleInputChange('tipo', value)
                }
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PETICION">Petición</SelectItem>
                  <SelectItem value="QUEJA">Queja</SelectItem>
                  <SelectItem value="RECLAMO">Reclamo</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Prioridad */}
          <div className="space-y-2">
            <Label>Prioridad *</Label>
            <Select
              value={formData.prioridad}
              onValueChange={(value: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA') => 
                handleInputChange('prioridad', value)
              }
              disabled={isLoading}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BAJA">Baja</SelectItem>
                <SelectItem value="MEDIA">Media</SelectItem>
                <SelectItem value="ALTA">Alta</SelectItem>
                <SelectItem value="CRITICA">Crítica</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Resumen */}
          <div className="space-y-2">
            <Label htmlFor="resumen">Resumen *</Label>
            <Input
              id="resumen"
              value={formData.resumen}
              onChange={(e) => handleInputChange('resumen', e.target.value)}
              placeholder="Resumen breve del problema (10-200 caracteres)"
              disabled={isLoading}
              maxLength={200}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{errors.resumen || ''}</span>
              <span>{formData.resumen.length}/200</span>
            </div>
          </div>

          {/* Detalle */}
          <div className="space-y-2">
            <Label htmlFor="detalle">Detalle *</Label>
            <Textarea
              id="detalle"
              value={formData.detalle}
              onChange={(e) => handleInputChange('detalle', e.target.value)}
              placeholder="Descripción detallada del problema (mínimo 20 caracteres)"
              disabled={isLoading}
              rows={4}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{errors.detalle || ''}</span>
              <span>{formData.detalle.length} caracteres</span>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Creando...' : 'Crear PQR'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}