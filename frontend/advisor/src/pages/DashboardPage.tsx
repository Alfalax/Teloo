import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import KPIDashboard from '@/components/dashboard/KPIDashboard';
import SolicitudesUnificadas from '@/components/solicitudes/SolicitudesUnificadas';
import OfertaIndividualModal from '@/components/ofertas/OfertaIndividualModal';
import VerOfertaModal from '@/components/ofertas/VerOfertaModal';
import { SolicitudConOferta } from '@/types/solicitud';
import { solicitudesService } from '@/services/solicitudes';
import { queryKeys } from '@/lib/queryKeys';
import { useRealtimeSolicitudes } from '@/hooks/useRealtimeSolicitudes';

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [selectedSolicitud, setSelectedSolicitud] = useState<SolicitudConOferta | null>(null);
  useRealtimeSolicitudes();
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
      <p className="text-sm text-muted-foreground">Gestiona tus ofertas y solicitudes</p>

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
