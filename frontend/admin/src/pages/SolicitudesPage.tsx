/**
 * Solicitudes Page - Admin view for managing solicitudes
 * Features: Tabs by estado, filters, pagination, create new solicitud
 */

import { useState, useEffect } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { NuevaSolicitudDialog } from "@/components/solicitudes/NuevaSolicitudDialog";
import { SolicitudesTable } from "@/components/solicitudes/SolicitudesTable";
import { SolicitudesFilters as SolicitudesFiltersComponent } from "@/components/solicitudes/SolicitudesFilters";
import { SolicitudDetailDialog } from "@/components/solicitudes/SolicitudDetailDialog";
import { Pagination } from "@/components/solicitudes/Pagination";
import { solicitudesService } from "@/services/solicitudes";
import type {
  Solicitud,
  EstadoSolicitud,
  SolicitudesFilters,
  SolicitudesStats,
} from "@/types/solicitudes";

export default function SolicitudesPage() {
  const [solicitudes, setSolicitudes] = useState<Solicitud[]>([]);
  const [stats, setStats] = useState<SolicitudesStats>({
    total: 0,
    abiertas: 0,
    evaluadas: 0,
    aceptadas: 0,
    rechazadas_expiradas: 0,
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<EstadoSolicitud | "all">("all");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState<SolicitudesFilters>({});
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedSolicitud, setSelectedSolicitud] = useState<Solicitud | null>(
    null
  );
  const [showDetailDialog, setShowDetailDialog] = useState(false);

  // Load solicitudes
  const loadSolicitudes = async () => {
    try {
      setLoading(true);
      const filterWithTab =
        activeTab === "all" ? filters : { ...filters, estado: activeTab };

      const response = await solicitudesService.getSolicitudes(
        page,
        pageSize,
        filterWithTab
      );

      setSolicitudes(response.items);
      setTotalPages(response.total_pages);
    } catch (error) {
      console.error("Error loading solicitudes:", error);
    } finally {
      setLoading(false);
    }
  };

  // Load stats - Calculate from loaded solicitudes
  const calculateStats = (allSolicitudes: Solicitud[]) => {
    const newStats = {
      total: allSolicitudes.length,
      abiertas: allSolicitudes.filter((s) => s.estado === "ABIERTA").length,
      evaluadas: allSolicitudes.filter((s) => s.estado === "EVALUADA").length,
      aceptadas: 0, // Estado ACEPTADA no existe para solicitudes
      rechazadas_expiradas: allSolicitudes.filter(
        (s) => s.estado === "CERRADA_SIN_OFERTAS"
      ).length,
    };
    setStats(newStats);
  };

  useEffect(() => {
    loadSolicitudes();
  }, [page, activeTab, filters]);

  useEffect(() => {
    // Calculate stats from current solicitudes
    calculateStats(solicitudes);
  }, [solicitudes]);

  const handleViewDetails = (solicitud: Solicitud) => {
    setSelectedSolicitud(solicitud);
    setShowDetailDialog(true);
  };

  const handleFiltersChange = (newFilters: SolicitudesFilters) => {
    setFilters(newFilters);
    setPage(1); // Reset to first page when filters change
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Solicitudes</h1>
          <p className="text-muted-foreground">
            Gestión y seguimiento de solicitudes de repuestos
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nueva Solicitud
        </Button>
      </div>

      {/* Tabs with counters */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
        <TabsList>
          <TabsTrigger value="all">
            Todas
            <Badge variant="secondary" className="ml-2">
              {stats.total}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="ABIERTA">
            Abiertas
            <Badge variant="default" className="ml-2 bg-green-500">
              {stats.abiertas}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="EVALUADA">
            Evaluadas
            <Badge variant="default" className="ml-2 bg-yellow-500">
              {stats.evaluadas}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="CERRADA_SIN_OFERTAS">
            Cerradas sin Ofertas
            <Badge variant="default" className="ml-2 bg-red-500">
              {stats.rechazadas_expiradas}
            </Badge>
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          {/* Filters */}
          <SolicitudesFiltersComponent
            filters={filters}
            onFiltersChange={handleFiltersChange}
          />

          {/* Table */}
          <SolicitudesTable
            solicitudes={solicitudes}
            loading={loading}
            onViewDetails={handleViewDetails}
          />

          {/* Pagination */}
          {!loading && totalPages > 1 && (
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          )}
        </TabsContent>
      </Tabs>

      {/* Create Dialog */}
      <NuevaSolicitudDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSuccess={loadSolicitudes}
      />

      {/* Detail Dialog */}
      <SolicitudDetailDialog
        solicitud={selectedSolicitud}
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
      />
    </div>
  );
}
