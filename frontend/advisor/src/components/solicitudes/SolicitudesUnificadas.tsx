// Componente unificado de solicitudes
import { useState, useEffect, useMemo } from 'react';
import { Upload, Package, LayoutGrid, Table as TableIcon, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import SolicitudCard from './SolicitudCard';
import { SolicitudConOferta, EstadoOfertaAsesor } from '@/types/solicitud';
import { solicitudesService } from '@/services/solicitudes';

type FiltroTipo = 'todas' | 'activas' | 'finalizadas';
type VistaTipo = 'cards' | 'table';

interface Props {
  onHacerOferta: (solicitud: SolicitudConOferta) => void;
  onCargaMasiva: () => void;
  onVerOferta?: (solicitud: SolicitudConOferta) => void;
}

function determinarEstadoOfertaAsesor(solicitud: SolicitudConOferta): EstadoOfertaAsesor {
  if (solicitud.estado_oferta_asesor) {
    return solicitud.estado_oferta_asesor;
  }

  // Si tiene oferta, el estado depende del estado de la oferta y la solicitud
  if (solicitud.mi_oferta) {
    if (solicitud.estado === 'ABIERTA') {
      return 'ENVIADA';
    }
    if (solicitud.estado === 'EVALUADA') {
      return solicitud.mi_oferta.estado === 'GANADORA' ? 'GANADORA' : 'NO_SELECCIONADA';
    }
    if (solicitud.estado === 'CERRADA_SIN_OFERTAS') return 'EXPIRADA';
    return 'ENVIADA';
  }
  
  // Si NO tiene oferta
  if (solicitud.estado === 'ABIERTA') {
    return 'ABIERTA';
  }
  
  // Si no tiene oferta y la solicitud ya cerró, no debería mostrarse
  return 'EXPIRADA';
}

function obtenerPrioridadEstado(estado: EstadoOfertaAsesor): number {
  const prioridades: Record<EstadoOfertaAsesor, number> = {
    'ABIERTA': 1,
    'ENVIADA': 2,
    'GANADORA': 3,
    'NO_SELECCIONADA': 4,
    'ACEPTADA': 5,
    'RECHAZADA': 6,
    'EXPIRADA': 7
  };
  return prioridades[estado] || 999;
}

function obtenerConfigBadge(estado: EstadoOfertaAsesor) {
  const configs: Record<EstadoOfertaAsesor, { text: string; className: string }> = {
    'ABIERTA': { 
      text: 'Abierta', 
      className: 'bg-blue-100 text-blue-800 border-blue-200' 
    },
    'ENVIADA': { 
      text: 'Enviada', 
      className: 'bg-yellow-100 text-yellow-800 border-yellow-200' 
    },
    'GANADORA': { 
      text: 'Ganadora', 
      className: 'bg-green-100 text-green-800 border-green-200' 
    },
    'NO_SELECCIONADA': { 
      text: 'No Seleccionada', 
      className: 'bg-gray-100 text-gray-800 border-gray-200' 
    },
    'ACEPTADA': { 
      text: 'Aceptada', 
      className: 'bg-emerald-100 text-emerald-800 border-emerald-200' 
    },
    'RECHAZADA': { 
      text: 'Rechazada', 
      className: 'bg-red-100 text-red-800 border-red-200' 
    },
    'EXPIRADA': { 
      text: 'Expirada', 
      className: 'bg-orange-100 text-orange-800 border-orange-200' 
    }
  };
  return configs[estado] || configs['ABIERTA'];
}

export default function SolicitudesUnificadas({ onHacerOferta, onCargaMasiva, onVerOferta }: Props) {
  const [solicitudes, setSolicitudes] = useState<SolicitudConOferta[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtroActivo, setFiltroActivo] = useState<FiltroTipo>('todas');
  const [vistaActiva, setVistaActiva] = useState<VistaTipo>('cards');

  useEffect(() => {
    loadSolicitudes();
  }, []);

  const loadSolicitudes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await solicitudesService.getMisSolicitudes();
      console.log('📊 Solicitudes recibidas del backend:', data.length);
      console.log('📋 Datos:', data);
      setSolicitudes(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar solicitudes');
      console.error('❌ Error loading solicitudes:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const solicitudesProcesadas = useMemo(() => {
    return solicitudes
      .map(solicitud => ({
        ...solicitud,
        estado_oferta_asesor: determinarEstadoOfertaAsesor(solicitud)
      }))
      .filter(solicitud => {
        // Ocultar solicitudes finalizadas donde el asesor NO hizo oferta
        if (!solicitud.mi_oferta && 
            ['EVALUADA', 'CERRADA_SIN_OFERTAS'].includes(solicitud.estado)) {
          return false;
        }
        return true;
      })
      .sort((a, b) => {
        const prioridadA = obtenerPrioridadEstado(a.estado_oferta_asesor!);
        const prioridadB = obtenerPrioridadEstado(b.estado_oferta_asesor!);
        if (prioridadA !== prioridadB) {
          return prioridadA - prioridadB;
        }
        const fechaA = a.fecha_creacion || a.created_at || new Date().toISOString();
        const fechaB = b.fecha_creacion || b.created_at || new Date().toISOString();
        return new Date(fechaB).getTime() - new Date(fechaA).getTime();
      });
  }, [solicitudes]);

  const solicitudesFiltradas = useMemo(() => {
    if (filtroActivo === 'todas') return solicitudesProcesadas;
    if (filtroActivo === 'activas') {
      return solicitudesProcesadas.filter(s => 
        ['ABIERTA', 'ENVIADA'].includes(s.estado_oferta_asesor!)
      );
    }
    if (filtroActivo === 'finalizadas') {
      return solicitudesProcesadas.filter(s => 
        ['GANADORA', 'NO_SELECCIONADA', 'ACEPTADA', 'RECHAZADA', 'EXPIRADA'].includes(s.estado_oferta_asesor!)
      );
    }
    return solicitudesProcesadas;
  }, [solicitudesProcesadas, filtroActivo]);

  const contadores = useMemo(() => {
    const activas = solicitudesProcesadas.filter(s => 
      ['ABIERTA', 'ENVIADA'].includes(s.estado_oferta_asesor!)
    ).length;
    const finalizadas = solicitudesProcesadas.filter(s => 
      ['GANADORA', 'NO_SELECCIONADA', 'ACEPTADA', 'RECHAZADA', 'EXPIRADA'].includes(s.estado_oferta_asesor!)
    ).length;
    return {
      todas: solicitudesProcesadas.length,
      activas,
      finalizadas
    };
  }, [solicitudesProcesadas]);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-8 text-center">
            <p className="text-destructive font-medium mb-2">Error al cargar solicitudes</p>
            <p className="text-sm text-muted-foreground mb-4">{error}</p>
            <Button onClick={loadSolicitudes} variant="outline">Reintentar</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <CardTitle className="text-xl font-semibold">Mis Solicitudes</CardTitle>
            <div className="flex flex-wrap items-center gap-2">
              <Button onClick={onCargaMasiva} variant="outline" size="sm" className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Carga Masiva
              </Button>
              <div className="flex border rounded-lg p-1">
                <Button
                  variant={vistaActiva === 'cards' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setVistaActiva('cards')}
                  className="px-3 py-1"
                >
                  <LayoutGrid className="h-4 w-4" />
                </Button>
                <Button
                  variant={vistaActiva === 'table' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setVistaActiva('table')}
                  className="px-3 py-1"
                >
                  <TableIcon className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 pt-4">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <Button
              variant={filtroActivo === 'todas' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFiltroActivo('todas')}
            >
              Todas <Badge variant="secondary" className="ml-1">{contadores.todas}</Badge>
            </Button>
            <Button
              variant={filtroActivo === 'activas' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFiltroActivo('activas')}
            >
              Activas <Badge variant="secondary" className="ml-1">{contadores.activas}</Badge>
            </Button>
            <Button
              variant={filtroActivo === 'finalizadas' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFiltroActivo('finalizadas')}
            >
              Finalizadas <Badge variant="secondary" className="ml-1">{contadores.finalizadas}</Badge>
            </Button>
          </div>
        </CardHeader>
      </Card>

      {solicitudesFiltradas.length === 0 ? (
        <Card>
          <CardContent className="p-6">
            <div className="text-center py-8">
              <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                {filtroActivo === 'todas' 
                  ? 'No tienes solicitudes asignadas'
                  : `No tienes solicitudes ${filtroActivo}`}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : vistaActiva === 'cards' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {solicitudesFiltradas.map((solicitud) => {
            const configBadge = obtenerConfigBadge(solicitud.estado_oferta_asesor!);
            return (
              <div key={solicitud.id} className="relative">
                <div className="absolute top-2 right-2 z-10">
                  <Badge className={configBadge.className}>{configBadge.text}</Badge>
                </div>
                <SolicitudCard
                  solicitud={solicitud}
                  onHacerOferta={onHacerOferta}
                  onVerOferta={onVerOferta}
                />
              </div>
            );
          })}
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
                <TableHead>Estado Oferta</TableHead>
                <TableHead>Nivel</TableHead>
                <TableHead>Tiempo</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {solicitudesFiltradas.map((solicitud) => {
                const tiempoRestante = solicitud.tiempo_restante_horas || 0;
                const repuestos = solicitud.repuestos_solicitados || solicitud.repuestos || [];
                const configBadge = obtenerConfigBadge(solicitud.estado_oferta_asesor!);
                const tieneOferta = !!solicitud.mi_oferta;
                return (
                  <TableRow key={solicitud.id}>
                    <TableCell className="font-mono text-xs">#{solicitud.id.slice(0, 8)}</TableCell>
                    <TableCell>{solicitud.cliente_nombre}</TableCell>
                    <TableCell>{solicitud.ciudad_origen}, {solicitud.departamento_origen}</TableCell>
                    <TableCell>{repuestos.length}</TableCell>
                    <TableCell>
                      <Badge className={configBadge.className}>{configBadge.text}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">Nivel {solicitud.nivel_actual}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={tiempoRestante < 4 ? 'destructive' : 'warning'}>{tiempoRestante}h</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {tieneOferta ? (
                        <Button size="sm" variant="outline" onClick={() => onVerOferta?.(solicitud)}>
                          Ver Oferta
                        </Button>
                      ) : (
                        <Button size="sm" onClick={() => onHacerOferta(solicitud)}>
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
