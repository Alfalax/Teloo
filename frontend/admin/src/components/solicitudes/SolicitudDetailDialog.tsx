/**
 * SolicitudDetailDialog - Modal to view solicitud details
 */

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { Solicitud } from "@/types/solicitudes";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import {
  MapPin,
  User,
  Phone,
  Calendar,
  Package,
  DollarSign,
  Clock,
} from "lucide-react";

interface SolicitudDetailDialogProps {
  solicitud: Solicitud | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const estadoBadgeColor = (estado: string) => {
  switch (estado) {
    case "ABIERTA":
      return "bg-green-500";
    case "EVALUADA":
      return "bg-yellow-500";
    case "CERRADA_SIN_OFERTAS":
      return "bg-red-500";
    default:
      return "bg-gray-500";
  }
};

export function SolicitudDetailDialog({
  solicitud,
  open,
  onOpenChange,
}: SolicitudDetailDialogProps) {
  if (!solicitud) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>Detalle de Solicitud</DialogTitle>
            <Badge className={estadoBadgeColor(solicitud.estado)}>
              {solicitud.estado}
            </Badge>
          </div>
        </DialogHeader>
        <DialogDescription className="text-sm text-muted-foreground font-mono">
          ID: {solicitud.id}
        </DialogDescription>

        <div className="space-y-6">
          {/* Cliente Info */}
          <div>
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <User className="h-4 w-4" />
              Información del Cliente
            </h3>
            <div className="grid grid-cols-2 gap-4 p-4 bg-muted rounded-lg">
              <div>
                <p className="text-sm text-muted-foreground">Nombre</p>
                <p className="font-medium">{solicitud.cliente_nombre}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground flex items-center gap-1">
                  <Phone className="h-3 w-3" />
                  Teléfono
                </p>
                <p className="font-medium">{solicitud.cliente_telefono}</p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Location Info */}
          <div>
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              Ubicación
            </h3>
            <div className="grid grid-cols-2 gap-4 p-4 bg-muted rounded-lg">
              <div>
                <p className="text-sm text-muted-foreground">Ciudad</p>
                <p className="font-medium">{solicitud.ciudad_origen}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Departamento</p>
                <p className="font-medium">{solicitud.departamento_origen}</p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Dates Info */}
          <div>
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Fechas
            </h3>
            <div className="grid grid-cols-2 gap-4 p-4 bg-muted rounded-lg">
              <div>
                <p className="text-sm text-muted-foreground">Creación</p>
                <p className="font-medium">
                  {format(new Date(solicitud.fecha_creacion), "PPp", {
                    locale: es,
                  })}
                </p>
              </div>
              {solicitud.fecha_evaluacion && (
                <div>
                  <p className="text-sm text-muted-foreground">Evaluación</p>
                  <p className="font-medium">
                    {format(new Date(solicitud.fecha_evaluacion), "PPp", {
                      locale: es,
                    })}
                  </p>
                </div>
              )}
              {solicitud.fecha_expiracion && (
                <div>
                  <p className="text-sm text-muted-foreground">Expiración</p>
                  <p className="font-medium">
                    {format(new Date(solicitud.fecha_expiracion), "PPp", {
                      locale: es,
                    })}
                  </p>
                </div>
              )}
            </div>
          </div>

          <Separator />

          {/* Repuestos */}
          <div>
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Package className="h-4 w-4" />
              Repuestos Solicitados ({solicitud.total_repuestos})
            </h3>
            <div className="space-y-3">
              {solicitud.repuestos_solicitados?.map((repuesto, index) => (
                <div
                  key={repuesto.id || index}
                  className="p-4 border rounded-lg space-y-2"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium">{repuesto.nombre}</p>
                      {repuesto.codigo && (
                        <p className="text-sm text-muted-foreground">
                          Código: {repuesto.codigo}
                        </p>
                      )}
                    </div>
                    <Badge variant="outline">x{repuesto.cantidad}</Badge>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <p className="text-muted-foreground">Vehículo</p>
                      <p className="font-medium">
                        {repuesto.marca_vehiculo} {repuesto.linea_vehiculo}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Año</p>
                      <p className="font-medium">{repuesto.anio_vehiculo}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Urgente</p>
                      <p className="font-medium">
                        {repuesto.es_urgente ? "Sí" : "No"}
                      </p>
                    </div>
                  </div>

                  {repuesto.descripcion && (
                    <div>
                      <p className="text-sm text-muted-foreground">
                        Descripción
                      </p>
                      <p className="text-sm">{repuesto.descripcion}</p>
                    </div>
                  )}

                  {repuesto.observaciones && (
                    <div>
                      <p className="text-sm text-muted-foreground">
                        Observaciones
                      </p>
                      <p className="text-sm">{repuesto.observaciones}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <Separator />

          {/* Additional Info */}
          <div>
            <h3 className="font-semibold mb-3">Información Adicional</h3>
            <div className="grid grid-cols-3 gap-4 p-4 bg-muted rounded-lg">
              <div>
                <p className="text-sm text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Nivel Actual
                </p>
                <p className="font-medium">Nivel {solicitud.nivel_actual}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">
                  Ofertas Mínimas
                </p>
                <p className="font-medium">
                  {solicitud.ofertas_minimas_deseadas}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground flex items-center gap-1">
                  <DollarSign className="h-3 w-3" />
                  Monto Adjudicado
                </p>
                <p className="font-medium">
                  {solicitud.monto_total_adjudicado > 0
                    ? `$${solicitud.monto_total_adjudicado.toLocaleString()}`
                    : "-"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
