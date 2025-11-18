import { useState, useEffect } from 'react';
import KPIDashboard from '@/components/dashboard/KPIDashboard';
import SolicitudesUnificadas from '@/components/solicitudes/SolicitudesUnificadas';
import OfertaIndividualModal from '@/components/ofertas/OfertaIndividualModal';
import VerOfertaModal from '@/components/ofertas/VerOfertaModal';
import { AsesorKPIs } from '@/types/kpi';
import { SolicitudConOferta } from '@/types/solicitud';

export default function DashboardPage() {
  const [kpis, setKpis] = useState<AsesorKPIs>({
    repuestos_adjudicados: 0,
    monto_total_ganado: 0,
    pendientes_por_oferta: 0,
    tasa_conversion: 0,
    tasa_oferta: 0,
  });
  const [isLoadingKPIs, setIsLoadingKPIs] = useState(true);
  const [selectedSolicitud, setSelectedSolicitud] = useState<SolicitudConOferta | null>(null);
  const [showOfertaModal, setShowOfertaModal] = useState(false);
  const [showVerOfertaModal, setShowVerOfertaModal] = useState(false);

  useEffect(() => {
    loadKPIs();
  }, []);

  const loadKPIs = async () => {
    try {
      setIsLoadingKPIs(true);
      const { solicitudesService } = await import('@/services/solicitudes');
      const data = await solicitudesService.getMetrics();
      setKpis(data);
    } catch (error) {
      console.error('Error loading KPIs:', error);
      // Fallback to zeros if error
      setKpis({
        repuestos_adjudicados: 0,
        monto_total_ganado: 0,
        pendientes_por_oferta: 0,
        tasa_conversion: 0,
        tasa_oferta: 0,
      });
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

      <KPIDashboard kpis={kpis} isLoading={isLoadingKPIs} />

      {/* Solicitudes Unificadas con filtros */}
      <SolicitudesUnificadas 
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
            // Refresh solicitudes list
            window.location.reload();
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
