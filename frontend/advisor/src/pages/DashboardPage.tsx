import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import KPIDashboard from '@/components/dashboard/KPIDashboard';
import SolicitudesUnificadas from '@/components/solicitudes/SolicitudesUnificadas';
import OfertaIndividualModal from '@/components/ofertas/OfertaIndividualModal';
import VerOfertaModal from '@/components/ofertas/VerOfertaModal';
import { SolicitudConOferta } from '@/types/solicitud';
import { solicitudesService } from '@/services/solicitudes';
import { queryKeys } from '@/lib/queryKeys';

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [selectedSolicitud, setSelectedSolicitud] = useState<SolicitudConOferta | null>(null);
  const [showOfertaModal, setShowOfertaModal] = useState(false);
  const [showVerOfertaModal, setShowVerOfertaModal] = useState(false);

  const {
    data: kpis = null,
    isLoading: isLoadingKPIs,
    isError: kpiError,
    refetch: retryKpis,
  } = useQuery({
    queryKey: queryKeys.solicitudes.metrics(),
    queryFn: () => solicitudesService.getMetrics(),
    staleTime: 2 * 60 * 1000,
  });

  const handleHacerOferta = (solicitud: SolicitudConOferta) => {
    setSelectedSolicitud(solicitud);
    setShowOfertaModal(true);
  };

  const handleVerOferta = (solicitud: SolicitudConOferta) => {
    setSelectedSolicitud(solicitud);
    setShowVerOfertaModal(true);
  };

  const handleOfertaSuccess = () => {
    setShowOfertaModal(false);
    setSelectedSolicitud(null);
    queryClient.invalidateQueries({ queryKey: queryKeys.solicitudes.mis() });
    queryClient.invalidateQueries({ queryKey: queryKeys.solicitudes.metrics() });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">Gestiona tus ofertas y solicitudes</p>
      </div>

      <KPIDashboard kpis={kpis} isLoading={isLoadingKPIs} hasError={kpiError} onRetry={retryKpis} />

      <SolicitudesUnificadas onHacerOferta={handleHacerOferta} onVerOferta={handleVerOferta} />

      {selectedSolicitud && (
        <OfertaIndividualModal
          solicitud={selectedSolicitud}
          open={showOfertaModal}
          onClose={() => {
            setShowOfertaModal(false);
            setSelectedSolicitud(null);
          }}
          onSuccess={handleOfertaSuccess}
        />
      )}

      <VerOfertaModal
        open={showVerOfertaModal}
        onClose={() => {
          setShowVerOfertaModal(false);
          setSelectedSolicitud(null);
        }}
        solicitud={selectedSolicitud}
        onActualizarOferta={handleHacerOferta}
      />
    </div>
  );
}
