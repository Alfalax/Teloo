import { Clock, MapPin, Car, Package } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Solicitud } from '@/types/solicitud';
import { formatRelativeTime } from '@/lib/utils';

interface SolicitudCardProps {
  solicitud: Solicitud;
  onHacerOferta: (solicitud: Solicitud) => void;
}

export default function SolicitudCard({ solicitud, onHacerOferta }: SolicitudCardProps) {
  const tiempoRestante = solicitud.tiempo_restante_horas || 0;
  const isUrgente = tiempoRestante < 4;
  const repuestos = solicitud.repuestos_solicitados || solicitud.repuestos || [];

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-lg">Solicitud #{solicitud.id.slice(0, 8)}</h3>
              <Badge variant={isUrgente ? 'destructive' : 'warning'}>
                <Clock className="h-3 w-3 mr-1" />
                {tiempoRestante}h restantes
              </Badge>
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
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
              {repuestos.map((repuesto, index) => (
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
            </div>
          </div>
        )}

        <div className="text-xs text-muted-foreground pt-2 border-t">
          Creada {formatRelativeTime(solicitud.fecha_creacion || solicitud.created_at || new Date().toISOString())}
        </div>
      </CardContent>

      <CardFooter className="pt-3">
        <Button 
          className="w-full" 
          onClick={() => onHacerOferta(solicitud)}
        >
          Hacer Oferta
        </Button>
      </CardFooter>
    </Card>
  );
}
