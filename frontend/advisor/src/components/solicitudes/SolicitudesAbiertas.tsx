import { useState, useEffect } from 'react';
import { Upload, Package, LayoutGrid, Table as TableIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import SolicitudCard from './SolicitudCard';
import { SolicitudConOferta } from '@/types/solicitud';
import { solicitudesService } from '@/services/solicitudes';

interface SolicitudesAbiertasProps {
  onHacerOferta: (solicitud: SolicitudConOferta) => void;
  onCargaMasiva: () => void;
  onVerOferta?: (solicitud: SolicitudConOferta) => void;
}

export default function SolicitudesAbiertas({ onHacerOferta, onCargaMasiva, onVerOferta }: SolicitudesAbiertasProps) {
  const [solicitudes, setSolicitudes] = useState<SolicitudConOferta[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');

  useEffect(() => {
    loadSolicitudes();
  }, []);

  const loadSolicitudes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await solicitudesService.getSolicitudesAbiertas();
      setSolicitudes(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar solicitudes');
      console.error('Error loading solicitudes:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <div className="h-8 w-48 bg-muted animate-pulse rounded"></div>
          <div className="h-10 w-40 bg-muted animate-pulse rounded"></div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-64 bg-muted animate-pulse rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-8 text-center">
        <p className="text-destructive font-medium mb-2">Error al cargar solicitudes</p>
        <p className="text-sm text-muted-foreground mb-4">{error}</p>
        <Button onClick={loadSolicitudes} variant="outline">
          Reintentar
        </Button>
      </div>
    );
  }

  const getEstadoBadge = (estado: string) => {
    const variants: Record<string, 'default' | 'success' | 'warning' | 'destructive'> = {
      'ABIERTA': 'success',
      'EVALUADA': 'warning',
      'ACEPTADA': 'default',
      'RECHAZADA': 'destructive',
      'EXPIRADA': 'destructive',
    };
    return <Badge variant={variants[estado] || 'default'}>{estado}</Badge>;
  };

  const getNivelBadge = (nivel: number) => {
    const colors: Record<number, string> = {
      1: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      2: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      3: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      4: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      5: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };
    return (
      <Badge className={colors[nivel] || colors[5]}>
        Nivel {nivel}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Solicitudes Disponibles</h3>
          <p className="text-sm text-muted-foreground">
            {solicitudes.length} solicitud{solicitudes.length !== 1 ? 'es' : ''} disponible{solicitudes.length !== 1 ? 's' : ''} para ofertar
          </p>
        </div>
        <div className="flex gap-2">
          <div className="flex border rounded-lg">
            <Button
              variant={viewMode === 'cards' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('cards')}
              className="rounded-r-none"
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'table' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('table')}
              className="rounded-l-none"
            >
              <TableIcon className="h-4 w-4" />
            </Button>
          </div>
          <Button onClick={onCargaMasiva} variant="outline">
            <Upload className="h-4 w-4 mr-2" />
            Carga Masiva Excel
          </Button>
        </div>
      </div>

      {solicitudes.length === 0 ? (
        <div className="rounded-lg border bg-card p-12 text-center">
          <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-lg font-medium mb-2">No hay solicitudes disponibles</p>
          <p className="text-sm text-muted-foreground">
            Las nuevas solicitudes aparecerán aquí cuando estén disponibles
          </p>
        </div>
      ) : viewMode === 'cards' ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {solicitudes.map((solicitud) => (
            <SolicitudCard
              key={solicitud.id}
              solicitud={solicitud}
              onHacerOferta={onHacerOferta}
              onVerOferta={onVerOferta}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead>Ciudad</TableHead>
                <TableHead>Repuestos</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Nivel</TableHead>
                <TableHead>Tiempo</TableHead>
                <TableHead>Mi Oferta</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {solicitudes.map((solicitud) => {
                const tiempoRestante = solicitud.tiempo_restante_horas || 0;
                const tieneOferta = !!solicitud.mi_oferta;
                const repuestos = solicitud.repuestos_solicitados || solicitud.repuestos || [];
                
                return (
                  <TableRow key={solicitud.id}>
                    <TableCell className="font-mono text-xs">
                      #{solicitud.id.slice(0, 8)}
                    </TableCell>
                    <TableCell>{solicitud.cliente_nombre}</TableCell>
                    <TableCell>
                      {solicitud.ciudad_origen}, {solicitud.departamento_origen}
                    </TableCell>
                    <TableCell>{repuestos.length}</TableCell>
                    <TableCell>{getEstadoBadge(solicitud.estado)}</TableCell>
                    <TableCell>{getNivelBadge(solicitud.nivel_actual)}</TableCell>
                    <TableCell>
                      <Badge variant={tiempoRestante < 4 ? 'destructive' : 'warning'}>
                        {tiempoRestante}h
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {tieneOferta ? (
                        <Badge variant="success">Enviada</Badge>
                      ) : (
                        <Badge variant="destructive">Sin oferta</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {tieneOferta ? (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onVerOferta?.(solicitud)}
                        >
                          Ver Oferta
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          onClick={() => onHacerOferta(solicitud)}
                        >
                          Hacer Oferta
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
