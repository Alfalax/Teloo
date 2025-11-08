/**
 * SolicitudesTable - Table component for displaying solicitudes
 */

import { Eye, Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Solicitud } from "@/types/solicitudes";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";

interface SolicitudesTableProps {
  solicitudes: Solicitud[];
  loading?: boolean;
  onViewDetails: (solicitud: Solicitud) => void;
}

const estadoBadgeVariant = (estado: string) => {
  switch (estado) {
    case "ABIERTA":
      return "default";
    case "EVALUADA":
      return "secondary";
    case "ACEPTADA":
      return "default";
    case "RECHAZADA":
    case "EXPIRADA":
    case "CERRADA_SIN_OFERTAS":
      return "destructive";
    default:
      return "outline";
  }
};

const estadoBadgeColor = (estado: string) => {
  switch (estado) {
    case "ABIERTA":
      return "bg-green-500 hover:bg-green-600";
    case "EVALUADA":
      return "bg-yellow-500 hover:bg-yellow-600";
    case "ACEPTADA":
      return "bg-blue-500 hover:bg-blue-600";
    case "RECHAZADA":
    case "EXPIRADA":
    case "CERRADA_SIN_OFERTAS":
      return "bg-red-500 hover:bg-red-600";
    default:
      return "";
  }
};

export function SolicitudesTable({
  solicitudes,
  loading,
  onViewDetails,
}: SolicitudesTableProps) {
  if (loading) {
    return (
      <div className="rounded-md border">
        <div className="p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-sm text-muted-foreground">
            Cargando solicitudes...
          </p>
        </div>
      </div>
    );
  }

  if (solicitudes.length === 0) {
    return (
      <div className="rounded-md border">
        <div className="p-12 text-center">
          <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-lg font-medium mb-2">No hay solicitudes</p>
          <p className="text-sm text-muted-foreground">
            No se encontraron solicitudes con los filtros aplicados
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Cliente</TableHead>
            <TableHead>Ubicación</TableHead>
            <TableHead>Repuestos</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Fecha</TableHead>
            <TableHead>Monto</TableHead>
            <TableHead className="text-right">Acciones</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {solicitudes.map((solicitud) => (
            <TableRow key={solicitud.id}>
              <TableCell className="font-mono text-xs">
                {solicitud.id.slice(0, 8)}
              </TableCell>
              <TableCell>
                <div>
                  <p className="font-medium">{solicitud.cliente_nombre}</p>
                  <p className="text-sm text-muted-foreground">
                    {solicitud.cliente_telefono}
                  </p>
                </div>
              </TableCell>
              <TableCell>
                <div>
                  <p className="text-sm">{solicitud.ciudad_origen}</p>
                  <p className="text-xs text-muted-foreground">
                    {solicitud.departamento_origen}
                  </p>
                </div>
              </TableCell>
              <TableCell>
                <Badge variant="outline">{solicitud.total_repuestos}</Badge>
              </TableCell>
              <TableCell>
                <Badge
                  variant={estadoBadgeVariant(solicitud.estado)}
                  className={estadoBadgeColor(solicitud.estado)}
                >
                  {solicitud.estado}
                </Badge>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatDistanceToNow(new Date(solicitud.fecha_creacion), {
                  addSuffix: true,
                  locale: es,
                })}
              </TableCell>
              <TableCell>
                {solicitud.monto_total_adjudicado > 0 ? (
                  <span className="font-medium">
                    ${solicitud.monto_total_adjudicado.toLocaleString()}
                  </span>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </TableCell>
              <TableCell className="text-right">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onViewDetails(solicitud)}
                >
                  <Eye className="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
