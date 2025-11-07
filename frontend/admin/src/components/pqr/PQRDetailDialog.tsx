import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Phone, 
  Mail, 
  Calendar, 
  Clock, 
  MessageSquare,
  CheckCircle
} from 'lucide-react';
import { PQR } from '@/types/pqr';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

interface PQRDetailDialogProps {
  isOpen: boolean;
  onClose: () => void;
  pqr: PQR | null;
  onResponder: (id: string, respuesta: string) => Promise<void>;
  onCambiarEstado: (id: string, estado: 'ABIERTA' | 'EN_PROCESO' | 'CERRADA') => void;
  onCambiarPrioridad: (id: string, prioridad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA') => void;
}

export function PQRDetailDialog({ 
  isOpen, 
  onClose, 
  pqr, 
  onResponder, 
  onCambiarEstado, 
  onCambiarPrioridad 
}: PQRDetailDialogProps) {
  const [respuesta, setRespuesta] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showResponseForm, setShowResponseForm] = useState(false);

  if (!pqr) return null;

  const handleResponder = async () => {
    if (!respuesta.trim()) return;
    
    setIsSubmitting(true);
    try {
      await onResponder(pqr.id, respuesta);
      setRespuesta('');
      setShowResponseForm(false);
    } catch (error) {
      console.error('Error responding to PQR:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

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

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), "dd 'de' MMMM 'de' yyyy 'a las' HH:mm", { locale: es });
    } catch {
      return 'Fecha inválida';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Detalle de PQR
          </DialogTitle>
          <DialogDescription>
            Información completa y gestión de la PQR
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Información básica */}
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Tipo</Label>
              <div>{getTipoBadge(pqr.tipo)}</div>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Prioridad</Label>
              <div className="flex items-center gap-2">
                {getPrioridadBadge(pqr.prioridad)}
                <Select
                  value={pqr.prioridad}
                  onValueChange={(value: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA') => 
                    onCambiarPrioridad(pqr.id, value)
                  }
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BAJA">Baja</SelectItem>
                    <SelectItem value="MEDIA">Media</SelectItem>
                    <SelectItem value="ALTA">Alta</SelectItem>
                    <SelectItem value="CRITICA">Crítica</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Estado</Label>
              <div className="flex items-center gap-2">
                {getEstadoBadge(pqr.estado)}
                <Select
                  value={pqr.estado}
                  onValueChange={(value: 'ABIERTA' | 'EN_PROCESO' | 'CERRADA') => 
                    onCambiarEstado(pqr.id, value)
                  }
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ABIERTA">Abierta</SelectItem>
                    <SelectItem value="EN_PROCESO">En Proceso</SelectItem>
                    <SelectItem value="CERRADA">Cerrada</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <Separator />

          {/* Información del cliente */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Información del Cliente</Label>
            <div className="bg-muted/50 p-4 rounded-lg space-y-2">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">{pqr.cliente.nombre_completo}</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <span>{pqr.cliente.telefono}</span>
              </div>
              {pqr.cliente.email && (
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <span>{pqr.cliente.email}</span>
                </div>
              )}
            </div>
          </div>

          <Separator />

          {/* Contenido de la PQR */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Resumen</Label>
            <p className="text-sm bg-muted/50 p-3 rounded-lg">{pqr.resumen}</p>
          </div>

          <div className="space-y-3">
            <Label className="text-sm font-medium">Detalle</Label>
            <p className="text-sm bg-muted/50 p-3 rounded-lg whitespace-pre-wrap">{pqr.detalle}</p>
          </div>

          <Separator />

          {/* Información de fechas */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Fecha de Creación</Label>
              <div className="flex items-center gap-2 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span>{formatDate(pqr.created_at)}</span>
              </div>
            </div>
            {pqr.tiempo_resolucion_horas && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Tiempo de Resolución</Label>
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span>{pqr.tiempo_resolucion_horas} horas</span>
                </div>
              </div>
            )}
          </div>

          {/* Respuesta existente */}
          {pqr.respuesta && (
            <>
              <Separator />
              <div className="space-y-3">
                <Label className="text-sm font-medium">Respuesta</Label>
                <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
                  <p className="text-sm whitespace-pre-wrap">{pqr.respuesta}</p>
                  {pqr.respondido_por && pqr.fecha_respuesta && (
                    <div className="mt-3 pt-3 border-t border-green-200 text-xs text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-3 w-3" />
                        <span>
                          Respondido por {pqr.respondido_por.nombre_completo} el {formatDate(pqr.fecha_respuesta)}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Formulario de respuesta */}
          {showResponseForm && (
            <>
              <Separator />
              <div className="space-y-3">
                <Label htmlFor="respuesta">Nueva Respuesta</Label>
                <Textarea
                  id="respuesta"
                  value={respuesta}
                  onChange={(e) => setRespuesta(e.target.value)}
                  placeholder="Escriba su respuesta aquí..."
                  rows={4}
                  disabled={isSubmitting}
                />
                <div className="flex gap-2">
                  <Button
                    onClick={handleResponder}
                    disabled={!respuesta.trim() || isSubmitting}
                    size="sm"
                  >
                    {isSubmitting ? 'Enviando...' : 'Enviar Respuesta'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowResponseForm(false);
                      setRespuesta('');
                    }}
                    size="sm"
                    disabled={isSubmitting}
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          {!showResponseForm && pqr.estado !== 'CERRADA' && (
            <Button
              onClick={() => setShowResponseForm(true)}
              className="flex items-center gap-2"
            >
              <MessageSquare className="h-4 w-4" />
              Responder
            </Button>
          )}
          <Button variant="outline" onClick={onClose}>
            Cerrar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}