import { Clock, MapPin, Package, CheckCircle2, DollarSign, Calendar, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { SolicitudConOferta } from '@/types/solicitud';
import { formatRelativeTime } from '@/lib/utils';

interface SolicitudCardProps {
  solicitud: SolicitudConOferta;
  onHacerOferta: (solicitud: SolicitudConOferta) => void;
  onVerOferta?: (solicitud: SolicitudConOferta) => void;
}

export default function SolicitudCard({ solicitud, onHacerOferta, onVerOferta }: SolicitudCardProps) {
  const tiempoRestanteMinutos = solicitud.tiempo_restante_minutos || 0;
  const tiempoTotalNivelMinutos = solicitud.tiempo_total_nivel_minutos || 1440; // Tiempo total configurado para el nivel (default 24h = 1440min)
  const repuestos = solicitud.repuestos_solicitados || solicitud.repuestos || [];
  const tieneOferta = !!solicitud.mi_oferta;
  const estadoSolicitud = solicitud.estado;
  const solicitudActiva = ['ABIERTA', 'EVALUADA'].includes(estadoSolicitud);
  
  // Calcular porcentaje de tiempo restante
  const porcentajeTiempo = (tiempoRestanteMinutos / tiempoTotalNivelMinutos) * 100;
  
  // Determinar color según porcentaje
  // 70-100%: verde, 40-70%: amarillo, 0-40%: rojo
  const getColorBadge = () => {
    if (porcentajeTiempo >= 70) return 'default'; // Verde
    if (porcentajeTiempo >= 40) return 'warning'; // Amarillo
    return 'destructive'; // Rojo
  };
  
  // Formatear tiempo para mostrar (convertir minutos a formato legible)
  const formatTiempo = (minutos: number) => {
    if (minutos >= 60) {
      const horas = Math.floor(minutos / 60);
      const mins = minutos % 60;
      return mins > 0 ? `${horas}h ${mins}m` : `${horas}h`;
    }
    return `${minutos}m`;
  };
  
  // Calcular monto total de la oferta desde los detalles
  const montoTotal = solicitud.mi_oferta?.detalles?.reduce(
    (sum, detalle) => sum + (detalle.precio_unitario * detalle.cantidad), 
    0
  ) || 0;
  
  const cantidadRepuestos = solicitud.mi_oferta?.detalles?.length || 0;

  return (
    <Card className={`hover:shadow-md transition-shadow ${tieneOferta ? 'border-green-200 dark:border-green-800' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-lg">Solicitud #{solicitud.id.slice(0, 8)}</h3>
              {solicitudActiva && tiempoRestanteMinutos > 0 && (
                <Badge variant={getColorBadge()}>
                  <Clock className="h-3 w-3 mr-1" />
                  {formatTiempo(tiempoRestanteMinutos)}
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
        {/* Sección SIN OFERTA - Solo cuando no tiene oferta */}
        {!tieneOferta && (
          <div className="p-3 bg-red-50 dark:bg-red-950 rounded-lg border border-red-200 dark:border-red-800 min-h-[88px] flex items-center justify-center">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
              <p className="font-semibold text-red-900 dark:text-red-100">SIN OFERTA</p>
            </div>
          </div>
        )}

        {/* Sección de Mi Oferta - Solo cuando tiene oferta */}
        {tieneOferta && solicitud.mi_oferta && (
          <div className="p-3 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200 dark:border-green-800">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-green-900 dark:text-green-100">Mi Oferta</h4>
              <Badge 
                variant={solicitud.mi_oferta.estado === 'GANADORA' ? 'success' : 'outline'} 
                className="text-xs"
              >
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
                  <p className="font-semibold">{cantidadRepuestos}</p>
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

      <CardFooter className="pt-3">
        {tieneOferta ? (
          <Button 
            className="w-full" 
            onClick={() => onVerOferta?.(solicitud)}
          >
            Ver Oferta
          </Button>
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
