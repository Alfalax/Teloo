import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Clock, MapPin, User, Car } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

interface SolicitudAbierta {
  id: string;
  codigo: string;
  vehiculo: string;
  cliente: string;
  ciudad: string;
  tiempo_proceso_horas: number;
  created_at: string;
  repuestos_count?: number;
}

interface TopSolicitudesTableProps {
  solicitudes: SolicitudAbierta[];
  isLoading?: boolean;
}

export function TopSolicitudesTable({ solicitudes, isLoading = false }: TopSolicitudesTableProps) {
  const formatTiempo = (horas: number) => {
    if (horas < 1) {
      return `${Math.round(horas * 60)}m`;
    } else if (horas < 24) {
      return `${Math.round(horas)}h`;
    } else {
      const dias = Math.floor(horas / 24);
      const horasRestantes = Math.round(horas % 24);
      return `${dias}d ${horasRestantes}h`;
    }
  };

  const getTiempoColor = (horas: number) => {
    if (horas < 2) return 'bg-green-100 text-green-800';
    if (horas < 8) return 'bg-yellow-100 text-yellow-800';
    if (horas < 24) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  if (isLoading) {
    return (
      <Card className="col-span-3">
        <CardHeader>
          <CardTitle>Top 15 Solicitudes Abiertas</CardTitle>
          <CardDescription>
            Solicitudes con mayor tiempo en proceso
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="space-y-2 flex-1">
                  <div className="h-4 w-24 bg-muted animate-pulse rounded" />
                  <div className="h-3 w-40 bg-muted animate-pulse rounded" />
                </div>
                <div className="h-6 w-12 bg-muted animate-pulse rounded" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="col-span-3">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Top 15 Solicitudes Abiertas
        </CardTitle>
        <CardDescription>
          Solicitudes con mayor tiempo en proceso
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {solicitudes.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No hay solicitudes abiertas
            </div>
          ) : (
            solicitudes.slice(0, 15).map((solicitud, index) => (
              <div
                key={solicitud.id}
                className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
              >
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium leading-none">
                      #{index + 1} {solicitud.codigo}
                    </span>
                    <div
                      className={cn(
                        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
                        getTiempoColor(solicitud.tiempo_proceso_horas)
                      )}
                    >
                      {formatTiempo(solicitud.tiempo_proceso_horas)}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Car className="h-3 w-3" />
                      <span>{solicitud.vehiculo}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      <span>{solicitud.cliente}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      <span>{solicitud.ciudad}</span>
                    </div>
                  </div>
                  
                  {solicitud.repuestos_count && (
                    <div className="text-xs text-muted-foreground">
                      {solicitud.repuestos_count} repuesto{solicitud.repuestos_count !== 1 ? 's' : ''}
                    </div>
                  )}
                </div>
                
                <div className="text-right">
                  <div className="text-xs text-muted-foreground">
                    {formatDistanceToNow(parseISO(solicitud.created_at), {
                      addSuffix: true,
                      locale: es,
                    })}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}