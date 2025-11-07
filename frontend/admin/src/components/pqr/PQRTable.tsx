
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  MoreHorizontal, 
  Eye, 
  Trash2, 
  Clock,
  MessageSquare,
  User,
  Phone
} from 'lucide-react';
import { PQR } from '@/types/pqr';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

interface PQRTableProps {
  pqrs: PQR[];
  isLoading?: boolean;
  onView: (pqr: PQR) => void;
  onCambiarEstado: (id: string, estado: 'ABIERTA' | 'EN_PROCESO' | 'CERRADA') => void;
  onCambiarPrioridad: (id: string, prioridad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA') => void;
  onDelete: (id: string) => void;
}

export function PQRTable({ 
  pqrs, 
  isLoading, 
  onView, 
  onCambiarEstado, 
  onCambiarPrioridad, 
  onDelete 
}: PQRTableProps) {
  const getEstadoBadge = (estado: string) => {
    switch (estado) {
      case 'ABIERTA':
        return <Badge variant="destructive">Abierta</Badge>;
      case 'EN_PROCESO':
        return <Badge variant="secondary">En Proceso</Badge>;
      case 'CERRADA':
        return <Badge variant="default">Cerrada</Badge>;
      default:
        return <Badge variant="outline">{estado}</Badge>;
    }
  };

  const getPrioridadBadge = (prioridad: string) => {
    switch (prioridad) {
      case 'CRITICA':
        return <Badge variant="destructive" className="bg-red-600">Crítica</Badge>;
      case 'ALTA':
        return <Badge variant="destructive" className="bg-orange-600">Alta</Badge>;
      case 'MEDIA':
        return <Badge variant="secondary" className="bg-yellow-600">Media</Badge>;
      case 'BAJA':
        return <Badge variant="outline" className="bg-green-600 text-white">Baja</Badge>;
      default:
        return <Badge variant="outline">{prioridad}</Badge>;
    }
  };

  const getTipoBadge = (tipo: string) => {
    switch (tipo) {
      case 'PETICION':
        return <Badge variant="outline" className="bg-blue-100 text-blue-800">Petición</Badge>;
      case 'QUEJA':
        return <Badge variant="outline" className="bg-yellow-100 text-yellow-800">Queja</Badge>;
      case 'RECLAMO':
        return <Badge variant="outline" className="bg-red-100 text-red-800">Reclamo</Badge>;
      default:
        return <Badge variant="outline">{tipo}</Badge>;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { 
        addSuffix: true, 
        locale: es 
      });
    } catch {
      return 'Fecha inválida';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>PQRs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="text-muted-foreground">Cargando PQRs...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (pqrs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>PQRs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <MessageSquare className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No hay PQRs</h3>
            <p className="text-muted-foreground">
              No se encontraron PQRs con los filtros aplicados.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          PQRs ({pqrs.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cliente</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Prioridad</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Resumen</TableHead>
                <TableHead>Creada</TableHead>
                <TableHead>Tiempo Resolución</TableHead>
                <TableHead className="w-[50px]">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pqrs.map((pqr) => (
                <TableRow key={pqr.id} className="hover:bg-muted/50">
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{pqr.cliente.nombre_completo}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Phone className="h-3 w-3" />
                        <span>{pqr.cliente.telefono}</span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    {getTipoBadge(pqr.tipo)}
                  </TableCell>
                  <TableCell>
                    {getPrioridadBadge(pqr.prioridad)}
                  </TableCell>
                  <TableCell>
                    {getEstadoBadge(pqr.estado)}
                  </TableCell>
                  <TableCell>
                    <div className="max-w-xs">
                      <p className="truncate font-medium">{pqr.resumen}</p>
                      <p className="text-sm text-muted-foreground truncate">
                        {pqr.detalle}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2 text-sm">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <span>{formatTimeAgo(pqr.created_at)}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {pqr.tiempo_resolucion_horas ? (
                      <span className="text-sm">
                        {pqr.tiempo_resolucion_horas}h
                      </span>
                    ) : (
                      <span className="text-sm text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Acciones</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => onView(pqr)}>
                          <Eye className="mr-2 h-4 w-4" />
                          Ver Detalles
                        </DropdownMenuItem>
                        
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel>Cambiar Estado</DropdownMenuLabel>
                        {pqr.estado !== 'ABIERTA' && (
                          <DropdownMenuItem onClick={() => onCambiarEstado(pqr.id, 'ABIERTA')}>
                            Marcar como Abierta
                          </DropdownMenuItem>
                        )}
                        {pqr.estado !== 'EN_PROCESO' && (
                          <DropdownMenuItem onClick={() => onCambiarEstado(pqr.id, 'EN_PROCESO')}>
                            Marcar En Proceso
                          </DropdownMenuItem>
                        )}
                        {pqr.estado !== 'CERRADA' && (
                          <DropdownMenuItem onClick={() => onCambiarEstado(pqr.id, 'CERRADA')}>
                            Marcar como Cerrada
                          </DropdownMenuItem>
                        )}
                        
                        <DropdownMenuSeparator />
                        <DropdownMenuLabel>Cambiar Prioridad</DropdownMenuLabel>
                        {pqr.prioridad !== 'BAJA' && (
                          <DropdownMenuItem onClick={() => onCambiarPrioridad(pqr.id, 'BAJA')}>
                            Prioridad Baja
                          </DropdownMenuItem>
                        )}
                        {pqr.prioridad !== 'MEDIA' && (
                          <DropdownMenuItem onClick={() => onCambiarPrioridad(pqr.id, 'MEDIA')}>
                            Prioridad Media
                          </DropdownMenuItem>
                        )}
                        {pqr.prioridad !== 'ALTA' && (
                          <DropdownMenuItem onClick={() => onCambiarPrioridad(pqr.id, 'ALTA')}>
                            Prioridad Alta
                          </DropdownMenuItem>
                        )}
                        {pqr.prioridad !== 'CRITICA' && (
                          <DropdownMenuItem onClick={() => onCambiarPrioridad(pqr.id, 'CRITICA')}>
                            Prioridad Crítica
                          </DropdownMenuItem>
                        )}
                        
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          onClick={() => onDelete(pqr.id)}
                          className="text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Eliminar
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}