import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { UserCheck, UserX, Download } from 'lucide-react';
import { asesoresService } from '@/services/asesores';

interface BulkActionsProps {
  selectedAsesores: string[];
  onBulkAction: () => void;
  onExport: () => void;
  isLoading?: boolean;
}

export function BulkActions({
  selectedAsesores,
  onBulkAction,
  onExport,
  isLoading = false,
}: BulkActionsProps) {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [selectedAction, setSelectedAction] = useState<'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO' | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleBulkEstadoChange = (estado: 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO') => {
    setSelectedAction(estado);
    setShowConfirmDialog(true);
  };

  const confirmBulkAction = async () => {
    if (!selectedAction) return;

    setIsProcessing(true);
    try {
      await asesoresService.bulkUpdateEstado(selectedAsesores, selectedAction);
      onBulkAction();
      setShowConfirmDialog(false);
      setSelectedAction(null);
    } catch (error) {
      console.error('Error in bulk action:', error);
      alert('Error al actualizar los asesores seleccionados');
    } finally {
      setIsProcessing(false);
    }
  };

  const getActionText = (action: string) => {
    switch (action) {
      case 'ACTIVO':
        return 'activar';
      case 'INACTIVO':
        return 'desactivar';
      case 'SUSPENDIDO':
        return 'suspender';
      default:
        return 'actualizar';
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'ACTIVO':
        return <UserCheck className="h-4 w-4" />;
      case 'INACTIVO':
      case 'SUSPENDIDO':
        return <UserX className="h-4 w-4" />;
      default:
        return null;
    }
  };

  if (selectedAsesores.length === 0) {
    return (
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          Selecciona asesores para realizar acciones masivas
        </div>
        <Button
          variant="outline"
          onClick={onExport}
          disabled={isLoading}
          className="flex items-center gap-2"
        >
          <Download className="h-4 w-4" />
          Exportar Excel
        </Button>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center justify-between bg-muted/50 p-4 rounded-lg">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium">
            {selectedAsesores.length} asesor{selectedAsesores.length !== 1 ? 'es' : ''} seleccionado{selectedAsesores.length !== 1 ? 's' : ''}
          </span>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBulkEstadoChange('ACTIVO')}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              <UserCheck className="h-4 w-4" />
              Activar
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBulkEstadoChange('INACTIVO')}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              <UserX className="h-4 w-4" />
              Desactivar
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBulkEstadoChange('SUSPENDIDO')}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              <UserX className="h-4 w-4" />
              Suspender
            </Button>
          </div>
        </div>

        <Button
          variant="outline"
          onClick={onExport}
          disabled={isLoading}
          className="flex items-center gap-2"
        >
          <Download className="h-4 w-4" />
          Exportar Excel
        </Button>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedAction && getActionIcon(selectedAction)}
              Confirmar Acción Masiva
            </DialogTitle>
            <DialogDescription>
              ¿Estás seguro de que quieres {selectedAction && getActionText(selectedAction)} {selectedAsesores.length} asesor{selectedAsesores.length !== 1 ? 'es' : ''}?
              Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowConfirmDialog(false)}
              disabled={isProcessing}
            >
              Cancelar
            </Button>
            <Button
              onClick={confirmBulkAction}
              disabled={isProcessing}
              variant={selectedAction === 'SUSPENDIDO' ? 'destructive' : 'default'}
            >
              {isProcessing ? 'Procesando...' : `Confirmar ${selectedAction && getActionText(selectedAction)}`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}