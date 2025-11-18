
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
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Edit, UserX, UserCheck, Trash2 } from 'lucide-react';
import { Asesor } from '@/types/asesores';
import { cn } from '@/lib/utils';

interface AsesoresTableProps {
  asesores: Asesor[];
  isLoading?: boolean;
  onEdit: (asesor: Asesor) => void;
  onUpdateEstado: (id: string, estado: 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO') => void;
  onDelete: (id: string) => void;
  selectedAsesores: string[];
  onSelectAsesor: (id: string) => void;
  onSelectAll: (selected: boolean) => void;
}

export function AsesoresTable({
  asesores,
  isLoading = false,
  onEdit,
  onUpdateEstado,
  onDelete,
  selectedAsesores,
  onSelectAsesor,
  onSelectAll,
}: AsesoresTableProps) {
  const getEstadoBadgeVariant = (estado: string) => {
    switch (estado) {
      case 'ACTIVO':
        return 'default';
      case 'INACTIVO':
        return 'secondary';
      case 'SUSPENDIDO':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const getConfianzaColor = (confianza: number) => {
    if (confianza >= 4.0) return 'text-green-600';
    if (confianza >= 3.0) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  if (isLoading) {
    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">
                <div className="h-4 w-4 bg-muted animate-pulse rounded" />
              </TableHead>
              <TableHead>
                <div className="h-4 w-32 bg-muted animate-pulse rounded" />
              </TableHead>
              <TableHead>
                <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              </TableHead>
              <TableHead>
                <div className="h-4 w-40 bg-muted animate-pulse rounded" />
              </TableHead>
              <TableHead>
                <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              </TableHead>
              <TableHead>
                <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              </TableHead>
              <TableHead>
                <div className="h-4 w-16 bg-muted animate-pulse rounded" />
              </TableHead>
              <TableHead>
                <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              </TableHead>
              <TableHead className="w-12">
                <div className="h-4 w-4 bg-muted animate-pulse rounded" />
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, index) => (
              <TableRow key={index}>
                <TableCell>
                  <div className="h-4 w-4 bg-muted animate-pulse rounded" />
                </TableCell>
                <TableCell>
                  <div className="space-y-2">
                    <div className="h-4 w-32 bg-muted animate-pulse rounded" />
                    <div className="h-3 w-24 bg-muted animate-pulse rounded" />
                  </div>
                </TableCell>
                <TableCell>
                  <div className="h-4 w-20 bg-muted animate-pulse rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-4 w-36 bg-muted animate-pulse rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-4 w-20 bg-muted animate-pulse rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-6 w-16 bg-muted animate-pulse rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-4 w-8 bg-muted animate-pulse rounded" />
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <div className="h-3 w-12 bg-muted animate-pulse rounded" />
                    <div className="h-3 w-16 bg-muted animate-pulse rounded" />
                  </div>
                </TableCell>
                <TableCell>
                  <div className="h-8 w-8 bg-muted animate-pulse rounded" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  const allSelected = asesores.length > 0 && selectedAsesores.length === asesores.length;
  const someSelected = selectedAsesores.length > 0 && selectedAsesores.length < asesores.length;

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <input
                type="checkbox"
                checked={allSelected}
                ref={(el) => {
                  if (el) el.indeterminate = someSelected;
                }}
                onChange={(e) => onSelectAll(e.target.checked)}
                className="rounded border-gray-300"
              />
            </TableHead>
            <TableHead>Asesor</TableHead>
            <TableHead>Contacto</TableHead>
            <TableHead>Punto de Venta</TableHead>
            <TableHead>Ubicación</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Confianza</TableHead>
            <TableHead>Métricas</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {asesores.length === 0 ? (
            <TableRow>
              <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                No se encontraron asesores
              </TableCell>
            </TableRow>
          ) : (
            asesores.map((asesor) => (
              <TableRow key={asesor.id}>
                <TableCell>
                  <input
                    type="checkbox"
                    checked={selectedAsesores.includes(asesor.id)}
                    onChange={() => onSelectAsesor(asesor.id)}
                    className="rounded border-gray-300"
                  />
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <div className="font-medium">
                      {asesor.usuario.nombre} {asesor.usuario.apellido}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      ID: {asesor.id.slice(0, 8)}...
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <div className="text-sm">{asesor.usuario.email}</div>
                    <div className="text-sm text-muted-foreground">
                      {asesor.usuario.telefono}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <div className="font-medium text-sm">{asesor.punto_venta}</div>
                    {asesor.direccion_punto_venta && (
                      <div className="text-xs text-muted-foreground">
                        {asesor.direccion_punto_venta}
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <div className="text-sm">{asesor.ciudad}</div>
                    <div className="text-xs text-muted-foreground">
                      {asesor.departamento}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant={getEstadoBadgeVariant(asesor.estado)}>
                    {asesor.estado}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className={cn("font-medium", getConfianzaColor(asesor.confianza))}>
                    {asesor.confianza.toFixed(1)}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="space-y-1 text-xs">
                    <div>
                      <span className="text-muted-foreground">Ofertas:</span> {asesor.total_ofertas}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Ganadas:</span> {asesor.ofertas_ganadoras}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Tasa:</span>{' '}
                      {asesor.total_ofertas > 0 
                        ? formatPercentage((asesor.ofertas_ganadoras / asesor.total_ofertas) * 100)
                        : '0%'
                      }
                    </div>
                    <div>
                      <span className="text-muted-foreground">Ventas:</span>{' '}
                      {formatCurrency(asesor.monto_total_ventas)}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onEdit(asesor)}>
                        <Edit className="mr-2 h-4 w-4" />
                        Editar
                      </DropdownMenuItem>
                      {asesor.estado === 'ACTIVO' ? (
                        <>
                          <DropdownMenuItem 
                            onClick={() => onUpdateEstado(asesor.id, 'INACTIVO')}
                          >
                            <UserX className="mr-2 h-4 w-4" />
                            Desactivar
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => onUpdateEstado(asesor.id, 'SUSPENDIDO')}
                          >
                            <UserX className="mr-2 h-4 w-4" />
                            Suspender
                          </DropdownMenuItem>
                        </>
                      ) : (
                        <DropdownMenuItem 
                          onClick={() => onUpdateEstado(asesor.id, 'ACTIVO')}
                        >
                          <UserCheck className="mr-2 h-4 w-4" />
                          Activar
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuItem 
                        onClick={() => onDelete(asesor.id)}
                        className="text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Eliminar
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}