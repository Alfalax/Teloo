import { useState } from 'react';
import { Car, AlertCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Solicitud, CreateOfertaRequest } from '@/types/solicitud';
import { ofertasService } from '@/services/ofertas';
import { formatCurrency } from '@/lib/utils';

interface OfertaIndividualModalProps {
  solicitud: Solicitud;
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface RepuestoOferta {
  repuesto_solicitado_id: string;
  incluir: boolean;
  precio_unitario: string;
  garantia_meses: string;
}

export default function OfertaIndividualModal({
  solicitud,
  open,
  onClose,
  onSuccess,
}: OfertaIndividualModalProps) {
  const [repuestos, setRepuestos] = useState<RepuestoOferta[]>(
    solicitud.repuestos.map((r) => ({
      repuesto_solicitado_id: r.id,
      incluir: true,
      precio_unitario: '',
      garantia_meses: '',
    }))
  );
  const [tiempoEntrega, setTiempoEntrega] = useState('');
  const [observaciones, setObservaciones] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    // Validate tiempo entrega
    const tiempo = parseInt(tiempoEntrega);
    if (!tiempoEntrega || isNaN(tiempo)) {
      errors.tiempo_entrega = 'El tiempo de entrega es requerido';
    } else if (tiempo < 0 || tiempo > 90) {
      errors.tiempo_entrega = 'El tiempo de entrega debe estar entre 0 y 90 días';
    }

    // Validate at least one repuesto is included
    const repuestosIncluidos = repuestos.filter((r) => r.incluir);
    if (repuestosIncluidos.length === 0) {
      errors.repuestos = 'Debe incluir al menos un repuesto en la oferta';
    }

    // Validate each included repuesto
    repuestos.forEach((repuesto, index) => {
      if (repuesto.incluir) {
        const precio = parseFloat(repuesto.precio_unitario);
        const garantia = parseInt(repuesto.garantia_meses);

        if (!repuesto.precio_unitario || isNaN(precio)) {
          errors[`precio_${index}`] = 'Precio requerido';
        } else if (precio < 1000 || precio > 50000000) {
          errors[`precio_${index}`] = 'Precio debe estar entre $1,000 y $50,000,000';
        }

        if (!repuesto.garantia_meses || isNaN(garantia)) {
          errors[`garantia_${index}`] = 'Garantía requerida';
        } else if (garantia < 1 || garantia > 60) {
          errors[`garantia_${index}`] = 'Garantía debe estar entre 1 y 60 meses';
        }
      }
    });

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const repuestosIncluidos = repuestos.filter((r) => r.incluir);

      const ofertaData: CreateOfertaRequest = {
        solicitud_id: solicitud.id,
        tiempo_entrega_dias: parseInt(tiempoEntrega),
        observaciones: observaciones || undefined,
        detalles: repuestosIncluidos.map((r) => {
          const solicitudRepuesto = solicitud.repuestos.find(
            (sr) => sr.id === r.repuesto_solicitado_id
          );
          return {
            repuesto_solicitado_id: r.repuesto_solicitado_id,
            precio_unitario: parseFloat(r.precio_unitario),
            cantidad: solicitudRepuesto?.cantidad || 1,
            garantia_meses: parseInt(r.garantia_meses),
          };
        }),
      };

      await ofertasService.createOferta(ofertaData);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear la oferta');
      console.error('Error creating oferta:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRepuestoChange = (index: number, field: keyof RepuestoOferta, value: any) => {
    const newRepuestos = [...repuestos];
    newRepuestos[index] = { ...newRepuestos[index], [field]: value };
    setRepuestos(newRepuestos);
    
    // Clear validation error for this field
    if (field === 'precio_unitario') {
      const newErrors = { ...validationErrors };
      delete newErrors[`precio_${index}`];
      setValidationErrors(newErrors);
    } else if (field === 'garantia_meses') {
      const newErrors = { ...validationErrors };
      delete newErrors[`garantia_${index}`];
      setValidationErrors(newErrors);
    }
  };

  const totalEstimado = repuestos
    .filter((r) => r.incluir && r.precio_unitario)
    .reduce((sum, r) => {
      const solicitudRepuesto = solicitud.repuestos.find(
        (sr) => sr.id === r.repuesto_solicitado_id
      );
      return sum + parseFloat(r.precio_unitario) * (solicitudRepuesto?.cantidad || 1);
    }, 0);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Crear Oferta - Solicitud #{solicitud.id.slice(0, 8)}</DialogTitle>
          <DialogDescription>
            Complete la información de su oferta para los repuestos seleccionados
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Vehicle Info */}
          {solicitud.repuestos.length > 0 && (
            <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
              <Car className="h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">
                  {solicitud.repuestos[0].marca_vehiculo} {solicitud.repuestos[0].linea_vehiculo} {solicitud.repuestos[0].anio_vehiculo}
                </p>
                <p className="text-sm text-muted-foreground">
                  {solicitud.ciudad_origen}, {solicitud.departamento_origen}
                </p>
              </div>
            </div>
          )}

          {/* Repuestos */}
          <div className="space-y-4">
            <Label className="text-base font-semibold">Repuestos Solicitados</Label>
            {solicitud.repuestos.map((repuesto, index) => (
              <div
                key={repuesto.id}
                className={`p-4 border rounded-lg space-y-3 ${
                  !repuestos[index].incluir ? 'opacity-50 bg-muted/50' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <Checkbox
                    checked={repuestos[index].incluir}
                    onCheckedChange={(checked) =>
                      handleRepuestoChange(index, 'incluir', checked)
                    }
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <p className="font-medium">{repuesto.nombre}</p>
                    {repuesto.codigo && (
                      <p className="text-sm text-muted-foreground">Código: {repuesto.codigo}</p>
                    )}
                    <p className="text-sm text-muted-foreground">Cantidad: {repuesto.cantidad}</p>
                  </div>
                </div>

                {repuestos[index].incluir && (
                  <div className="grid grid-cols-2 gap-3 ml-7">
                    <div className="space-y-2">
                      <Label htmlFor={`precio-${index}`}>
                        Precio Unitario (COP) *
                      </Label>
                      <Input
                        id={`precio-${index}`}
                        type="number"
                        placeholder="1000 - 50000000"
                        value={repuestos[index].precio_unitario}
                        onChange={(e) =>
                          handleRepuestoChange(index, 'precio_unitario', e.target.value)
                        }
                        min="1000"
                        max="50000000"
                      />
                      {validationErrors[`precio_${index}`] && (
                        <p className="text-xs text-destructive">
                          {validationErrors[`precio_${index}`]}
                        </p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`garantia-${index}`}>
                        Garantía (meses) *
                      </Label>
                      <Input
                        id={`garantia-${index}`}
                        type="number"
                        placeholder="1 - 60"
                        value={repuestos[index].garantia_meses}
                        onChange={(e) =>
                          handleRepuestoChange(index, 'garantia_meses', e.target.value)
                        }
                        min="1"
                        max="60"
                      />
                      {validationErrors[`garantia_${index}`] && (
                        <p className="text-xs text-destructive">
                          {validationErrors[`garantia_${index}`]}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {validationErrors.repuestos && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {validationErrors.repuestos}
              </p>
            )}
          </div>

          {/* Tiempo de Entrega */}
          <div className="space-y-2">
            <Label htmlFor="tiempo-entrega">Tiempo de Entrega Total (días) *</Label>
            <Input
              id="tiempo-entrega"
              type="number"
              placeholder="0 - 90"
              value={tiempoEntrega}
              onChange={(e) => {
                setTiempoEntrega(e.target.value);
                const newErrors = { ...validationErrors };
                delete newErrors.tiempo_entrega;
                setValidationErrors(newErrors);
              }}
              min="0"
              max="90"
            />
            {validationErrors.tiempo_entrega && (
              <p className="text-xs text-destructive">{validationErrors.tiempo_entrega}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Tiempo estimado para entregar todos los repuestos
            </p>
          </div>

          {/* Observaciones */}
          <div className="space-y-2">
            <Label htmlFor="observaciones">Observaciones (opcional)</Label>
            <Textarea
              id="observaciones"
              placeholder="Información adicional sobre su oferta..."
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              rows={3}
            />
          </div>

          {/* Total Estimado */}
          {totalEstimado > 0 && (
            <div className="p-4 bg-primary/10 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="font-medium">Total Estimado:</span>
                <span className="text-2xl font-bold text-primary">
                  {formatCurrency(totalEstimado)}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Incluye {repuestos.filter((r) => r.incluir).length} repuesto(s)
              </p>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md flex items-start gap-2">
              <AlertCircle className="h-4 w-4 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Enviando...' : 'Enviar Oferta'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
