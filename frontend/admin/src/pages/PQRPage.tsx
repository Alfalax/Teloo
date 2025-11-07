import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { KPICard } from '@/components/dashboard/KPICard';
import { PQRTable } from '@/components/pqr/PQRTable';
import { PQRFilters } from '@/components/pqr/PQRFilters';
import { PQRForm } from '@/components/pqr/PQRForm';
import { PQRDetailDialog } from '@/components/pqr/PQRDetailDialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  Plus, 
  MessageSquare, 
  Clock, 
  CheckCircle, 
  AlertTriangle,
  AlertCircle
} from 'lucide-react';
import { pqrService } from '@/services/pqr';
import { PQR, PQRCreate, PQRMetrics, PQRFilters as PQRFiltersType } from '@/types/pqr';

export function PQRPage() {
  const [pqrs, setPqrs] = useState<PQR[]>([]);
  const [metrics, setMetrics] = useState<PQRMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedPQR, setSelectedPQR] = useState<PQR | null>(null);
  const [pqrToDelete, setPqrToDelete] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState<PQRFiltersType>({
    search: '',
    estado: undefined,
    tipo: undefined,
    prioridad: undefined,
  });

  const loadPQRs = useCallback(async (page: number = 1) => {
    setIsLoading(true);
    try {
      const response = await pqrService.getPQRs(page, 50, filters);
      setPqrs(response.data);
      setTotalPages(response.total_pages);
      setCurrentPage(page);
    } catch (error) {
      console.error('Error loading PQRs:', error);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const loadMetrics = useCallback(async () => {
    setIsLoadingMetrics(true);
    try {
      const metricsData = await pqrService.getPQRMetrics();
      setMetrics(metricsData);
    } catch (error) {
      console.error('Error loading metrics:', error);
    } finally {
      setIsLoadingMetrics(false);
    }
  }, []);

  useEffect(() => {
    loadPQRs(1);
  }, [loadPQRs]);

  useEffect(() => {
    loadMetrics();
  }, [loadMetrics]);

  const handleFiltersChange = (newFilters: PQRFiltersType) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  const handleCreatePQR = async (data: PQRCreate) => {
    setIsSubmitting(true);
    try {
      await pqrService.createPQR(data);
      await loadPQRs(currentPage);
      await loadMetrics();
      setShowCreateForm(false);
    } catch (error: any) {
      console.error('Error creating PQR:', error);
      throw new Error(error.response?.data?.detail || 'Error al crear la PQR');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResponderPQR = async (id: string, respuesta: string) => {
    try {
      await pqrService.responderPQR(id, respuesta);
      await loadPQRs(currentPage);
      await loadMetrics();
      setShowDetailDialog(false);
      setSelectedPQR(null);
    } catch (error: any) {
      console.error('Error responding to PQR:', error);
      throw new Error(error.response?.data?.detail || 'Error al responder la PQR');
    }
  };

  const handleCambiarEstado = async (id: string, nuevoEstado: 'ABIERTA' | 'EN_PROCESO' | 'CERRADA') => {
    try {
      await pqrService.cambiarEstado(id, nuevoEstado);
      await loadPQRs(currentPage);
      await loadMetrics();
    } catch (error) {
      console.error('Error changing PQR status:', error);
      alert('Error al cambiar el estado de la PQR');
    }
  };

  const handleCambiarPrioridad = async (id: string, nuevaPrioridad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA') => {
    try {
      await pqrService.cambiarPrioridad(id, nuevaPrioridad);
      await loadPQRs(currentPage);
      await loadMetrics();
    } catch (error) {
      console.error('Error changing PQR priority:', error);
      alert('Error al cambiar la prioridad de la PQR');
    }
  };

  const handleDeletePQR = async () => {
    if (!pqrToDelete) return;
    
    setIsDeleting(true);
    try {
      await pqrService.deletePQR(pqrToDelete);
      await loadPQRs(currentPage);
      await loadMetrics();
      setShowDeleteDialog(false);
      setPqrToDelete(null);
    } catch (error: any) {
      console.error('Error deleting PQR:', error);
      alert(error.response?.data?.detail || 'Error al eliminar la PQR');
    } finally {
      setIsDeleting(false);
    }
  };

  const openDetailDialog = (pqr: PQR) => {
    setSelectedPQR(pqr);
    setShowDetailDialog(true);
  };

  const openDeleteDialog = (id: string) => {
    setPqrToDelete(id);
    setShowDeleteDialog(true);
  };



  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">PQR - Atención al Cliente</h1>
          <p className="text-muted-foreground">
            Gestión de Peticiones, Quejas y Reclamos
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Nueva PQR
          </Button>
        </div>
      </div>

      {/* Métricas */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="PQRs Abiertas"
          value={metrics?.total_abiertas || 0}
          description="Pendientes de atención"
          icon={MessageSquare}
          isLoading={isLoadingMetrics}
        />
        <KPICard
          title="En Proceso"
          value={metrics?.total_en_proceso || 0}
          description="Siendo atendidas"
          icon={Clock}
          isLoading={isLoadingMetrics}
        />
        <KPICard
          title="Cerradas"
          value={metrics?.total_cerradas || 0}
          description="Resueltas"
          icon={CheckCircle}
          isLoading={isLoadingMetrics}
        />
        <KPICard
          title="Tiempo Promedio"
          value={`${metrics?.tiempo_promedio_resolucion_horas?.toFixed(1) || 0}h`}
          description="Resolución promedio"
          icon={Clock}
          isLoading={isLoadingMetrics}
        />
      </div>

      {/* Métricas adicionales */}
      <div className="grid gap-4 md:grid-cols-3">
        <KPICard
          title="Alta Prioridad"
          value={metrics?.pqrs_alta_prioridad || 0}
          description="Requieren atención urgente"
          icon={AlertTriangle}

          isLoading={isLoadingMetrics}
        />
        <KPICard
          title="Críticas"
          value={metrics?.pqrs_criticas || 0}
          description="Atención inmediata"
          icon={AlertCircle}

          isLoading={isLoadingMetrics}
        />
        <KPICard
          title="Resolución 24h"
          value={`${metrics?.tasa_resolucion_24h?.toFixed(1) || 0}%`}
          description="Resueltas en menos de 24h"
          icon={CheckCircle}
          isLoading={isLoadingMetrics}
        />
      </div>

      {/* Filtros */}
      <PQRFilters
        onFiltersChange={handleFiltersChange}
        isLoading={isLoading}
      />

      {/* Tabla */}
      <PQRTable
        pqrs={pqrs}
        isLoading={isLoading}
        onView={openDetailDialog}
        onCambiarEstado={handleCambiarEstado}
        onCambiarPrioridad={handleCambiarPrioridad}
        onDelete={openDeleteDialog}
      />

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            onClick={() => loadPQRs(currentPage - 1)}
            disabled={currentPage === 1 || isLoading}
          >
            Anterior
          </Button>
          <span className="text-sm text-muted-foreground">
            Página {currentPage} de {totalPages}
          </span>
          <Button
            variant="outline"
            onClick={() => loadPQRs(currentPage + 1)}
            disabled={currentPage === totalPages || isLoading}
          >
            Siguiente
          </Button>
        </div>
      )}

      {/* Formulario de creación */}
      <PQRForm
        isOpen={showCreateForm}
        onClose={() => setShowCreateForm(false)}
        onSubmit={handleCreatePQR}
        isLoading={isSubmitting}
      />

      {/* Diálogo de detalle */}
      <PQRDetailDialog
        isOpen={showDetailDialog}
        onClose={() => {
          setShowDetailDialog(false);
          setSelectedPQR(null);
        }}
        pqr={selectedPQR}
        onResponder={handleResponderPQR}
        onCambiarEstado={handleCambiarEstado}
        onCambiarPrioridad={handleCambiarPrioridad}
      />

      {/* Diálogo de confirmación de eliminación */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Confirmar Eliminación
            </DialogTitle>
            <DialogDescription>
              ¿Estás seguro de que quieres eliminar esta PQR? Esta acción no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={isDeleting}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeletePQR}
              disabled={isDeleting}
            >
              {isDeleting ? 'Eliminando...' : 'Eliminar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}