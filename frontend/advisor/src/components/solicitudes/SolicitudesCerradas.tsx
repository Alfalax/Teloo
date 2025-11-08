import { useState, useEffect } from 'react';
import { Clock, MapPin, Car, Package, XCircle } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SolicitudConOferta } from '@/types/solicitud';
import { solicitudesService } from '@/services/solicitudes';
import { formatRelativeTime, formatCurrency } from '@/lib/utils';

export default function SolicitudesCerradas() {
  const [solicitudes, setSolicitudes] = useState<SolicitudConOferta[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSolicitudes();
  }, []);

  const loadSolicitudes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await solicitudesService.getSolicitudesCerradas();
      setSolicitudes(data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail 
        ? (typeof err.response.data.detail === 'string' 
            ? err.response.data.detail 
            : JSON.stringify(err.response.data.detail))
        : 'Error al cargar solicitudes';
      setError(errorMessage);
      console.error('Error loading solicitudes cerradas:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-64 bg-muted animate-pulse rounded-lg"></div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-8 text-center">
        <p className="text-destructive font-medium mb-2">Error al cargar solicitudes</p>
        <p className="text-sm text-muted-foreground">{error}</p>
      </div>
    );
  }

  if (solicitudes.length === 0) {
    return (
      <div className="rounded-lg border bg-card p-12 text-center">
        <XCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-lg font-medium mb-2">No hay solicitudes cerradas</p>
        <p className="text-sm text-muted-foreground">
          Las solicitudes en las que no ganaste aparecerán aquí
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Solicitudes Cerradas</h3>
        <p className="text-sm text-muted-foreground">
          {solicitudes.length} solicitud{solicitudes.length !== 1 ? 'es' : ''} no adjudicada{solicitudes.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {solicitudes.map((solicitud) => (
          <Card key={solicitud.id} className="opacity-75">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">Solicitud #{solicitud.id.slice(0, 8)}</h3>
                    <Badge variant="secondary">
                      {solicitud.estado === 'CERRADA_SIN_OFERTAS' ? 'Sin ofertas' : 'No seleccionada'}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {solicitud.ciudad_origen}
                    </div>
                    <div className="flex items-center gap-1">
                      <Package className="h-4 w-4" />
                      {solicitud.repuestos.length} repuesto{solicitud.repuestos.length !== 1 ? 's' : ''}
                    </div>
                  </div>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-3">
              {solicitud.repuestos.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Car className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">
                      {solicitud.repuestos[0].marca_vehiculo} {solicitud.repuestos[0].linea_vehiculo} {solicitud.repuestos[0].anio_vehiculo}
                    </span>
                  </div>
                  <div className="space-y-1">
                    {solicitud.repuestos.slice(0, 2).map((repuesto, index) => (
                      <div key={repuesto.id} className="text-sm text-muted-foreground">
                        {index + 1}. {repuesto.nombre}
                      </div>
                    ))}
                    {solicitud.repuestos.length > 2 && (
                      <div className="text-xs text-muted-foreground">
                        +{solicitud.repuestos.length - 2} más
                      </div>
                    )}
                  </div>
                </div>
              )}

              {solicitud.mi_oferta && (
                <div className="pt-2 border-t">
                  <p className="text-sm font-medium mb-1">Tu oferta:</p>
                  <div className="text-sm text-muted-foreground space-y-1">
                    <div>Precio total: {formatCurrency(
                      solicitud.mi_oferta.detalles.reduce(
                        (sum, d) => sum + d.precio_unitario * d.cantidad,
                        0
                      )
                    )}</div>
                    <div>Tiempo: {solicitud.mi_oferta.tiempo_entrega_dias} días</div>
                  </div>
                </div>
              )}

              {solicitud.oferta_ganadora && (
                <div className="pt-2 border-t">
                  <p className="text-sm font-medium mb-1 text-amber-600">Oferta ganadora:</p>
                  <div className="text-sm text-muted-foreground space-y-1">
                    <div>Precio: {formatCurrency(
                      solicitud.oferta_ganadora.detalles.reduce(
                        (sum, d) => sum + d.precio_unitario * d.cantidad,
                        0
                      )
                    )}</div>
                    <div>Tiempo: {solicitud.oferta_ganadora.tiempo_entrega_dias} días</div>
                  </div>
                </div>
              )}

              <div className="text-xs text-muted-foreground pt-2 border-t flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Cerrada {formatRelativeTime(solicitud.updated_at)}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
