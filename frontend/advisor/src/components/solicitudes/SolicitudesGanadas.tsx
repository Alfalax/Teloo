import { useState, useEffect } from 'react';
import { Clock, MapPin, Car, Package, Trophy, Phone, User } from 'lucide-react';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { SolicitudConOferta } from '@/types/solicitud';
import { solicitudesService } from '@/services/solicitudes';
import { formatRelativeTime, formatCurrency } from '@/lib/utils';

export default function SolicitudesGanadas() {
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
      const data = await solicitudesService.getSolicitudesGanadas();
      setSolicitudes(data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail 
        ? (typeof err.response.data.detail === 'string' 
            ? err.response.data.detail 
            : JSON.stringify(err.response.data.detail))
        : 'Error al cargar solicitudes';
      setError(errorMessage);
      console.error('Error loading solicitudes ganadas:', err);
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
        <Trophy className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-lg font-medium mb-2">No hay ofertas ganadoras</p>
        <p className="text-sm text-muted-foreground">
          Tus ofertas ganadoras aparecerán aquí
        </p>
      </div>
    );
  }

  const getEstadoBadge = (estado: string) => {
    switch (estado) {
      case 'ACEPTADA':
        return <Badge variant="success">Aceptada por cliente</Badge>;
      case 'GANADORA':
        return <Badge variant="warning">Pendiente respuesta</Badge>;
      case 'RECHAZADA':
        return <Badge variant="destructive">Rechazada</Badge>;
      default:
        return <Badge variant="secondary">{estado}</Badge>;
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Ofertas Ganadoras</h3>
        <p className="text-sm text-muted-foreground">
          {solicitudes.length} oferta{solicitudes.length !== 1 ? 's' : ''} ganadora{solicitudes.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {solicitudes.map((solicitud) => {
          const oferta = solicitud.mi_oferta || solicitud.oferta_ganadora;
          const totalOferta = oferta?.detalles.reduce(
            (sum, d) => sum + d.precio_unitario * d.cantidad,
            0
          ) || 0;

          return (
            <Card key={solicitud.id} className="border-primary/50">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Trophy className="h-4 w-4 text-primary" />
                      <h3 className="font-semibold">Solicitud #{solicitud.id.slice(0, 8)}</h3>
                    </div>
                    {oferta && getEstadoBadge(oferta.estado)}
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        {solicitud.ciudad_origen}
                      </div>
                      <div className="flex items-center gap-1">
                        <Package className="h-4 w-4" />
                        {(solicitud.repuestos_solicitados || solicitud.repuestos || []).length} repuesto{(solicitud.repuestos_solicitados || solicitud.repuestos || []).length !== 1 ? 's' : ''}
                      </div>
                    </div>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-3">
                {((solicitud.repuestos_solicitados || solicitud.repuestos || []).length > 0) && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <Car className="h-4 w-4 text-primary" />
                      <span>
                        {(solicitud.repuestos_solicitados || solicitud.repuestos || [])[0]?.marca_vehiculo} {(solicitud.repuestos_solicitados || solicitud.repuestos || [])[0]?.linea_vehiculo} {(solicitud.repuestos_solicitados || solicitud.repuestos || [])[0]?.anio_vehiculo}
                      </span>
                    </div>
                    <div className="space-y-1">
                      {(solicitud.repuestos_solicitados || solicitud.repuestos || []).slice(0, 2).map((repuesto, index) => (
                        <div key={repuesto.id} className="text-sm">
                          {index + 1}. {repuesto.nombre}
                        </div>
                      ))}
                      {(solicitud.repuestos_solicitados || solicitud.repuestos || []).length > 2 && (
                        <div className="text-xs text-muted-foreground">
                          +{(solicitud.repuestos_solicitados || solicitud.repuestos || []).length - 2} más
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {oferta && (
                  <div className="pt-2 border-t space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Total oferta:</span>
                      <span className="text-lg font-bold text-primary">
                        {formatCurrency(totalOferta)}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Tiempo de entrega: {oferta.tiempo_entrega_dias} días
                    </div>
                    {oferta.detalles.length > 0 && (
                      <div className="text-sm text-muted-foreground">
                        Garantía: {oferta.detalles[0].garantia_meses} meses
                      </div>
                    )}
                  </div>
                )}

                {/* Cliente Contact Info - Only if accepted */}
                {oferta?.estado === 'ACEPTADA' && solicitud.cliente_contacto && (
                  <div className="pt-2 border-t bg-primary/5 -mx-6 px-6 py-3">
                    <p className="text-sm font-medium mb-2">Información del Cliente:</p>
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span>{solicitud.cliente_contacto.nombre}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 text-muted-foreground" />
                        <a
                          href={`tel:${solicitud.cliente_contacto.telefono}`}
                          className="text-primary hover:underline"
                        >
                          {solicitud.cliente_contacto.telefono}
                        </a>
                      </div>
                      <div className="flex items-center gap-2">
                        <MapPin className="h-4 w-4 text-muted-foreground" />
                        <span>{solicitud.cliente_contacto.ciudad}</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="text-xs text-muted-foreground pt-2 border-t flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Ganada {formatRelativeTime(solicitud.updated_at || solicitud.created_at || new Date().toISOString())}
                </div>
              </CardContent>

              {oferta?.estado === 'ACEPTADA' && solicitud.cliente_contacto && (
                <CardFooter className="pt-3">
                  <Button
                    className="w-full"
                    onClick={() => window.open(`https://wa.me/${solicitud.cliente_contacto?.telefono.replace(/\+/g, '')}`, '_blank')}
                  >
                    <Phone className="h-4 w-4 mr-2" />
                    Contactar por WhatsApp
                  </Button>
                </CardFooter>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
