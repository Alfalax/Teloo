import { Clock, MapPin, Car, Package, CheckCircle2, DollarSign, Calendar } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { SolicitudConOferta } from '@/types/solicitud';
import { formatRelativeTime } from '@/lib/utils';
import { useState } from 'react';

interface SolicitudCardProps {
  solicitud: SolicitudConOferta;
  onHacerOferta: (solicitud: SolicitudConOferta) => void;
  onVerOferta?: (solicitud: SolicitudConOferta) => void;
}

export default function SolicitudCard({ solicitud, onHacerOferta, onVerOferta }: SolicitudCardProps) {
  const [showOfertaDetails, setShowOfertaDetails] = useState(false);
  const tiempoRestante = solicitud.tiempo_restante_horas || 0;
  const isUrgente = tiempoRestante < 4;
  const repuestos = solicitud.repuestos_solicitados || solicitud.repuestos || [];
  const tieneOferta = !!solicitud.mi_oferta;
  
  // Calcular monto total de la oferta
  const montoTotal = solicitud.mi_oferta?.detalles?.reduce(
    (sum, detalle) => sum + (detalle.precio_unitario * detalle.cantidad), 
    0
  ) || 0;

  return (
    <Card className={`hover:shadow-md transition-shadow ${tieneOferta ? 'border-green-200 dark:border-green-800' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-lg">Solicitud #{solicitud.id.slice(0, 8)}</h3>
              <Badge variant={isUrgente ? 'destructive' : 'warning'}>
                <Clock className="h-3 w-3 mr-1" />
                {tiempoRestante}h restantes
              </Badge>
              {tieneOferta && (
                <Badge variant="success" className="gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  Oferta enviada
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
              <div className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                {solicitud.ciudad_origen}, {solicitud.departamento_origen}
              </div>
              <div className="flex items-center gap-1">
                <Package className="h-4 w-4" />
                {repuestos.length} repuesto{repuestos.length !== 1 ? 's' : ''}
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {repuestos.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Car className="h-4 w-4 text-primary" />
              <span>
                {repuestos[0].marca_vehiculo} {repuestos[0].linea_vehiculo} {repuestos[0].anio_vehiculo}
              </span>
            </div>
            <div className="space-y-1.5">
              {repuestos.slice(0, showOfertaDetails ? repuestos.length : 3).map((repuesto, index) => (
                <div key={repuesto.id} className="flex items-start gap-2 text-sm">
                  <span className="text-muted-foreground">{index + 1}.</span>
                  <div className="flex-1">
                    <p className="font-medium">{repuesto.nombre}</p>
                    {repuesto.codigo && (
                      <p className="text-xs text-muted-foreground">Código: {repuesto.codigo}</p>
                    )}
                    <p className="text-xs text-muted-foreground">Cantidad: {repuesto.cantidad}</p>
                  </div>
                </div>
              ))}
              {repuestos.length > 3 && !showOfertaDetails && (
                <button
                  onClick={() => setShowOfertaDetails(true)}
                  className="text-xs text-primary hover:underline"
                >
                  Ver {repuestos.length - 3} más...
                </button>
              )}
            </div>
          </div>
        )}

        {/* Sección de Mi Oferta */}
        {tieneOferta && solicitud.mi_oferta && (
          <div className="mt-3 p-3 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200 dark:border-green-800">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-green-900 dark:text-green-100">Mi Oferta</h4>
              <Badge variant="outline" className="text-xs">
                {solicitud.mi_oferta.estado}
              </Badge>
            </div>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="flex items-center gap-1">
                <DollarSign className="h-4 w-4 text-green-600" />
                <div>
                  <p className="text-xs text-muted-foreground">Monto</p>
                  <p className="font-semibold">${montoTotal.toLocaleString()}</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Package className="h-4 w-4 text-green-600" />
                <div>
                  <p className="text-xs text-muted-foreground">Repuestos</p>
                  <p className="font-semibold">{solicitud.mi_oferta.detalles?.length || 0}</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4 text-green-600" />
                <div>
                  <p className="text-xs text-muted-foreground">Entrega</p>
                  <p className="font-semibold">{solicitud.mi_oferta.tiempo_entrega_dias}d</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="text-xs text-muted-foreground pt-2 border-t">
          Creada {formatRelativeTime(solicitud.fecha_creacion || solicitud.created_at || new Date().toISOString())}
        </div>
      </CardContent>

      <CardFooter className="pt-3 gap-2">
        {tieneOferta ? (
          <>
            <Button 
              variant="outline"
              className="flex-1" 
              onClick={() => onVerOferta?.(solicitud)}
            >
              Ver Oferta
            </Button>
            <Button 
              className="flex-1" 
              onClick={() => onHacerOferta(solicitud)}
            >
              Actualizar Oferta
            </Button>
          </>
        ) : (
          <Button 
            className="w-full" 
            onClick={() => onHacerOferta(solicitud)}
          >
            Hacer Oferta
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
