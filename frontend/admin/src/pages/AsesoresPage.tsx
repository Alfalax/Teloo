import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { KPICard } from '@/components/dashboard/KPICard';
import { AsesoresTable } from '@/components/asesores/AsesoresTable';
import { AsesorForm } from '@/components/asesores/AsesorForm';
import { ExcelImportDialog } from '@/components/asesores/ExcelImportDialog';
import { AsesoresFilters } from '@/components/asesores/AsesoresFilters';
import { BulkActions } from '@/components/asesores/BulkActions';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Plus, Upload, Users, Building, MapPin, AlertTriangle } from 'lucide-react';
import { asesoresService } from '@/services/asesores';
import { Asesor, AsesorCreate, AsesorUpdate, AsesoresKPIs } from '@/types/asesores';

export function AsesoresPage() {
  const [asesores, setAsesores] = useState<Asesor[]>([]);
  const [kpis, setKpis] = useState<AsesoresKPIs | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingKPIs, setIsLoadingKPIs] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedAsesor, setSelectedAsesor] = useState<Asesor | null>(null);
  const [selectedAsesores, setSelectedAsesores] = useState<string[]>([]);
  const [asesorToDelete, setAsesorToDelete] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    search: '',
    estado: '',
    ciudad: '',
    departamento: '',
  });

  const loadAsesores = useCallback(async (page: number = 1) => {
    setIsLoading(true);
    try {
      const response = await asesoresService.getAsesores(
        page,
        50, // limit
        filters.search || undefined,
        filters.estado || undefined,
        filters.ciudad || undefined,
        filters.departamento || undefined
      );
      
      setAsesores(response.data);
      setTotalPages(Math.ceil(response.total / 50));
      setCurrentPage(page);
    } catch (error) {
      console.error('Error loading asesores:', error);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const loadKPIs = useCallback(async () => {
    setIsLoadingKPIs(true);
    try {
      const kpisData = await asesoresService.getAsesoresKPIs();
      setKpis(kpisData);
    } catch (error) {
      console.error('Error loading KPIs:', error);
    } finally {
      setIsLoadingKPIs(false);
    }
  }, []);

  useEffect(() => {
    loadAsesores(1);
  }, [loadAsesores]);

  useEffect(() => {
    loadKPIs();
  }, [loadKPIs]);

  const handleFiltersChange = (newFilters: typeof filters) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  const handleCreateAsesor = async (data: AsesorCreate | AsesorUpdate) => {
    setIsSubmitting(true);
    try {
      await asesoresService.createAsesor(data as AsesorCreate);
      await loadAsesores(currentPage);
      await loadKPIs();
      setShowCreateForm(false);
    } catch (error: any) {
      console.error('Error creating asesor:', error);
      throw new Error(error.response?.data?.detail || 'Error al crear el asesor');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditAsesor = async (data: AsesorCreate | AsesorUpdate) => {
    if (!selectedAsesor) return;
    
    setIsSubmitting(true);
    try {
      await asesoresService.updateAsesor(selectedAsesor.id, data as AsesorUpdate);
      await loadAsesores(currentPage);
      setShowEditForm(false);
      setSelectedAsesor(null);
    } catch (error: any) {
      console.error('Error updating asesor:', error);
      throw new Error(error.response?.data?.detail || 'Error al actualizar el asesor');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateEstado = async (id: string, estado: 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO') => {
    try {
      await asesoresService.updateAsesorEstado(id, estado);
      await loadAsesores(currentPage);
      await loadKPIs();
    } catch (error) {
      console.error('Error updating asesor estado:', error);
      alert('Error al actualizar el estado del asesor');
    }
  };

  const handleDeleteAsesor = async () => {
    if (!asesorToDelete) return;
    
    setIsDeleting(true);
    try {
      await asesoresService.deleteAsesor(asesorToDelete);
      await loadAsesores(currentPage);
      await loadKPIs();
      setShowDeleteDialog(false);
      setAsesorToDelete(null);
    } catch (error: any) {
      console.error('Error deleting asesor:', error);
      alert(error.response?.data?.detail || 'Error al eliminar el asesor');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleSelectAsesor = (id: string) => {
    setSelectedAsesores(prev => 
      prev.includes(id) 
        ? prev.filter(asesorId => asesorId !== id)
        : [...prev, id]
    );
  };

  const handleSelectAll = (selected: boolean) => {
    setSelectedAsesores(selected ? asesores.map(a => a.id) : []);
  };

  const handleBulkAction = async () => {
    await loadAsesores(currentPage);
    await loadKPIs();
    setSelectedAsesores([]);
  };

  const handleExport = async () => {
    try {
      const blob = await asesoresService.exportExcel(
        filters.search || undefined,
        filters.estado || undefined,
        filters.ciudad || undefined,
        filters.departamento || undefined
      );
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `asesores_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting asesores:', error);
      alert('Error al exportar los asesores');
    }
  };

  const handleImportComplete = async () => {
    await loadAsesores(currentPage);
    await loadKPIs();
  };

  const openEditForm = (asesor: Asesor) => {
    setSelectedAsesor(asesor);
    setShowEditForm(true);
  };

  const openDeleteDialog = (id: string) => {
    setAsesorToDelete(id);
    setShowDeleteDialog(true);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Gestión de Asesores</h1>
          <p className="text-muted-foreground">
            Administrar asesores y proveedores del marketplace
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => setShowImportDialog(true)}
            className="flex items-center gap-2"
          >
            <Upload className="h-4 w-4" />
            Importar Excel
          </Button>
          <Button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Nuevo Asesor
          </Button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid gap-4 md:grid-cols-3">
        <KPICard
          title="Total Asesores Habilitados"
          value={kpis?.total_asesores_habilitados.valor || 0}
          change={kpis?.total_asesores_habilitados.cambio_porcentual}
          trend={
            (kpis?.total_asesores_habilitados.cambio_porcentual || 0) > 0 
              ? 'up' 
              : (kpis?.total_asesores_habilitados.cambio_porcentual || 0) < 0 
                ? 'down' 
                : 'neutral'
          }
          description={kpis?.total_asesores_habilitados.periodo}
          icon={Users}
          isLoading={isLoadingKPIs}
        />
        <KPICard
          title="Total Puntos de Venta"
          value={kpis?.total_puntos_venta.valor || 0}
          change={kpis?.total_puntos_venta.cambio_porcentual}
          trend={
            (kpis?.total_puntos_venta.cambio_porcentual || 0) > 0 
              ? 'up' 
              : (kpis?.total_puntos_venta.cambio_porcentual || 0) < 0 
                ? 'down' 
                : 'neutral'
          }
          description={kpis?.total_puntos_venta.periodo}
          icon={Building}
          isLoading={isLoadingKPIs}
        />
        <KPICard
          title="Cobertura Nacional"
          value={`${kpis?.cobertura_nacional.valor || 0}%`}
          change={kpis?.cobertura_nacional.cambio_porcentual}
          trend={
            (kpis?.cobertura_nacional.cambio_porcentual || 0) > 0 
              ? 'up' 
              : (kpis?.cobertura_nacional.cambio_porcentual || 0) < 0 
                ? 'down' 
                : 'neutral'
          }
          description={kpis?.cobertura_nacional.periodo}
          icon={MapPin}
          isLoading={isLoadingKPIs}
        />
      </div>

      {/* Filters */}
      <AsesoresFilters
        onFiltersChange={handleFiltersChange}
        isLoading={isLoading}
      />

      {/* Bulk Actions */}
      <BulkActions
        selectedAsesores={selectedAsesores}
        onBulkAction={handleBulkAction}
        onExport={handleExport}
        isLoading={isLoading}
      />

      {/* Table */}
      <AsesoresTable
        asesores={asesores}
        isLoading={isLoading}
        onEdit={openEditForm}
        onUpdateEstado={handleUpdateEstado}
        onDelete={openDeleteDialog}
        selectedAsesores={selectedAsesores}
        onSelectAsesor={handleSelectAsesor}
        onSelectAll={handleSelectAll}
      />

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            onClick={() => loadAsesores(currentPage - 1)}
            disabled={currentPage === 1 || isLoading}
          >
            Anterior
          </Button>
          <span className="text-sm text-muted-foreground">
            Página {currentPage} de {totalPages}
          </span>
          <Button
            variant="outline"
            onClick={() => loadAsesores(currentPage + 1)}
            disabled={currentPage === totalPages || isLoading}
          >
            Siguiente
          </Button>
        </div>
      )}

      {/* Create Form Dialog */}
      <AsesorForm
        isOpen={showCreateForm}
        onClose={() => setShowCreateForm(false)}
        onSubmit={handleCreateAsesor}
        isLoading={isSubmitting}
      />

      {/* Edit Form Dialog */}
      <AsesorForm
        isOpen={showEditForm}
        onClose={() => {
          setShowEditForm(false);
          setSelectedAsesor(null);
        }}
        onSubmit={handleEditAsesor}
        asesor={selectedAsesor}
        isLoading={isSubmitting}
      />

      {/* Import Dialog */}
      <ExcelImportDialog
        isOpen={showImportDialog}
        onClose={() => setShowImportDialog(false)}
        onImportComplete={handleImportComplete}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Confirmar Eliminación
            </DialogTitle>
            <DialogDescription>
              ¿Estás seguro de que quieres eliminar este asesor? Esta acción no se puede deshacer.
              Se eliminarán también todos los datos relacionados.
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
              onClick={handleDeleteAsesor}
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