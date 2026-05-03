import { useState, useEffect } from 'react';
import KPIDashboard from '@/components/dashboard/KPIDashboard';
import SolicitudesUnificadas from '@/components/solicitudes/SolicitudesUnificadas';
import OfertaIndividualModal from '@/components/ofertas/OfertaIndividualModal';
import VerOfertaModal from '@/components/ofertas/VerOfertaModal';
import { AsesorKPIs } from '@/types/kpi';
import { SolicitudConOferta } from '@/types/solicitud';

export default function DashboardPage() {
  const [kpis, setKpis] = useState<AsesorKPIs | null>(null);
  const [isLoadingKPIs, setIsLoadingKPIs] = useState(true);
  const [kpiError, setKpiError] = useState(false);
  const [selectedSolicitud, setSelectedSolicitud] = useState<SolicitudConOferta | null>(null);
  const [showOfertaModal, setShowOfertaModal] = useState(false);
  const [showVerOfertaModal, setShowVerOfertaModal] = useState(false);
  const [solicitudesRefreshKey, setSolicitudesRefreshKey] = useState(0);

  useEffect(() => {
    loadKPIs();
  }, []);

  const loadKPIs = async () => {
    try {
      setIsLoadingKPIs(true);
      setKpiError(false);
      const { solicitudesService } = await import('@/services/solicitudes');
      const data = await solicitudesService.getMetrics();
      setKpis(data);
    } catch (error) {
      console.error('Error loading KPIs:', error);
      setKpiError(true);
    } finally {
      setIsLoadingKPIs(false);
    }
  };

  const handleHacerOferta = (solicitud: SolicitudConOferta) => {
    setSelectedSolicitud(solicitud);
    setShowOfertaModal(true);
  };

  const handleVerOferta = (solicitud: SolicitudConOferta) => {
    setSelectedSolicitud(solicitud);
    setShowVerOfertaModal(true);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Gestiona tus ofertas y solicitudes
        </p>
      </div>

      <KPIDashboard kpis={kpis} isLoading={isLoadingKPIs} hasError={kpiError} onRetry={loadKPIs} />

      {/* Solicitudes Unificadas con filtros */}
      <SolicitudesUnificadas
        key={solicitudesRefreshKey}
        onHacerOferta={handleHacerOferta}
        onVerOferta={handleVerOferta}
      />

      {/* Oferta Individual Modal */}
      {selectedSolicitud && (
        <OfertaIndividualModal
          solicitud={selectedSolicitud}
          open={showOfertaModal}
          onClose={() => {
            setShowOfertaModal(false);
            setSelectedSolicitud(null);
          }}
          onSuccess={() => {
            setShowOfertaModal(false);
            setSelectedSolicitud(null);
            loadKPIs();
            setSolicitudesRefreshKey((k) => k + 1);
          }}
        />
      )}

      {/* Ver Oferta Modal */}
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
