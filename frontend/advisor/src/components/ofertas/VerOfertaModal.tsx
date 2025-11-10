import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { SolicitudConOferta } from '@/types/solicitud';
import { 
  DollarSign, 
  Package, 
  Calendar, 
  Clock, 
  CheckCircle2, 
  XCircle,
  AlertCircle
} from 'lucide-react';

interface VerOfertaModalProps {
  open: boolean;
  onClose: () => void;
  solicitud: SolicitudConOferta | null;
  onActualizarOferta?: (solicitud: SolicitudConOferta) => void;
}

export default function VerOfertaModal({ open, onClose, solicitud, onActualizarOferta }: VerOfertaModalProps) {
  if (!solicitud || !solicitud.mi_oferta) return null;

  const { mi_oferta } = solicitud;
  const repuestos = solicitud.repuestos_solicitados || solicitud.repuestos || [];
  
  // Calcular monto total
  const montoTotal = mi_oferta.detalles?.reduce(
    (sum, detalle) => sum + (detalle.precio_unitario * detalle.cantidad), 
    0
  ) || 0;

  // Obtener badge de estado
  const getEstadoBadge = (estado: string) => {
    switch (estado) {
      case 'ENVIADA':
        return <Badge variant="default"><Clock className="h-3 w-3 mr-1" />Enviada</Badge>;
      case 'GANADORA':
        return <Badge variant="success"><CheckCircle2 className="h-3 w-3 mr-1" />Ganadora</Badge>;
      case 'ACEPTADA':
        return <Badge variant="success"><CheckCircle2 className="h-3 w-3 mr-1" />Aceptada</Badge>;
      case 'NO_SELECCIONADA':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />No Seleccionada</Badge>;
      default:
        return <Badge variant="outline">{estado}</Badge>;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto" aria-describedby="ver-oferta-description">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Detalle de Mi Oferta</span>
            {getEstadoBadge(mi_oferta.estado)}
          </DialogTitle>
          <DialogDescription id="ver-oferta-description" className="sr-only">
            Visualización del detalle de la oferta enviada
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Resumen General */}
          <div className="grid grid-cols-3 gap-4 p-4 bg-muted rounded-lg">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <DollarSign className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Monto Total</p>
                <p className="text-lg font-bold">${montoTotal.toLocaleString()}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Package className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Repuestos</p>
                <p className="text-lg font-bold">{mi_oferta.detalles?.length || 0}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Calendar className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Tiempo Entrega</p>
                <p className="text-lg font-bold">{mi_oferta.tiempo_entrega_dias} días</p>
              </div>
            </div>
          </div>

          {/* Observaciones */}
          {mi_oferta.observaciones && (
            <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm text-blue-900 dark:text-blue-100">Observaciones</p>
                  <p className="text-sm text-blue-800 dark:text-blue-200 mt-1">{mi_oferta.observaciones}</p>
                </div>
              </div>
            </div>
          )}

          {/* Comparación Detallada */}
          <div>
            <h3 className="font-semibold mb-3">Comparación: Solicitado vs Ofertado</h3>
            <div className="space-y-3">
              {repuestos.map((repuesto) => {
                const detalle = mi_oferta.detalles?.find(
                  d => d.repuesto_solicitado_id === repuesto.id
                );
                
                return (
                  <div 
                    key={repuesto.id} 
                    className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h4 className="font-medium">{repuesto.nombre}</h4>
                        {repuesto.codigo && (
                          <p className="text-xs text-muted-foreground">Código: {repuesto.codigo}</p>
                        )}
                      </div>
                      {detalle ? (
                        <Badge variant="success" className="ml-2">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Cotizado
                        </Badge>
                      ) : (
                        <Badge variant="destructive" className="ml-2">
                          <XCircle className="h-3 w-3 mr-1" />
                          No cotizado
                        </Badge>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {/* Columna Solicitado */}
                      <div className="space-y-2">
                        <p className="font-semibold text-muted-foreground">Solicitado</p>
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Cantidad:</span>
                            <span className="font-medium">{repuesto.cantidad}</span>
                          </div>
                          {repuesto.observaciones && (
                            <div className="text-xs text-muted-foreground mt-2">
                              <p className="font-medium">Observaciones:</p>
                              <p>{repuesto.observaciones}</p>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Columna Ofertado */}
                      <div className="space-y-2 border-l pl-4">
                        <p className="font-semibold text-primary">Mi Oferta</p>
                        {detalle ? (
                          <div className="space-y-1">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Precio Unit.:</span>
                              <span className="font-medium">${detalle.precio_unitario.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Cantidad:</span>
                              <span className="font-medium">{detalle.cantidad}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Subtotal:</span>
                              <span className="font-bold text-primary">
                                ${(detalle.precio_unitario * detalle.cantidad).toLocaleString()}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Garantía:</span>
                              <span className="font-medium">{detalle.garantia_meses} meses</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Entrega:</span>
                              <span className="font-medium">{detalle.tiempo_entrega_dias} días</span>
                            </div>
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground italic">
                            No se cotizó este repuesto
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Información de Fechas */}
          <div className="grid grid-cols-2 gap-4 p-4 bg-muted rounded-lg text-sm">
            <div>
              <p className="text-muted-foreground">Fecha de Envío</p>
              <p className="font-medium">
                {new Date(mi_oferta.created_at).toLocaleString('es-CO', {
                  dateStyle: 'medium',
                  timeStyle: 'short'
                })}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Última Actualización</p>
              <p className="font-medium">
                {new Date(mi_oferta.updated_at).toLocaleString('es-CO', {
                  dateStyle: 'medium',
                  timeStyle: 'short'
                })}
              </p>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Cerrar
          </Button>
          {onActualizarOferta && (
            <Button 
              onClick={() => {
                onClose();
                onActualizarOferta(solicitud);
              }}
            >
              Actualizar Oferta
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
