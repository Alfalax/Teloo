import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import KPIDashboard from '@/components/dashboard/KPIDashboard';
import SolicitudesAbiertas from '@/components/solicitudes/SolicitudesAbiertas';
import SolicitudesCerradas from '@/components/solicitudes/SolicitudesCerradas';
import SolicitudesGanadas from '@/components/solicitudes/SolicitudesGanadas';
import OfertaIndividualModal from '@/components/ofertas/OfertaIndividualModal';
import CargaMasivaModal from '@/components/ofertas/CargaMasivaModal';
import VerOfertaModal from '@/components/ofertas/VerOfertaModal';
import { AsesorKPIs } from '@/types/kpi';
import { SolicitudConOferta } from '@/types/solicitud';

export default function DashboardPage() {
  const [kpis, setKpis] = useState<AsesorKPIs>({
    ofertas_asignadas: 0,
    monto_total_ganado: 0,
    solicitudes_abiertas: 0,
    tasa_conversion: 0,
  });
  const [isLoadingKPIs, setIsLoadingKPIs] = useState(true);
  const [selectedSolicitud, setSelectedSolicitud] = useState<SolicitudConOferta | null>(null);
  const [showOfertaModal, setShowOfertaModal] = useState(false);
  const [showCargaMasivaModal, setShowCargaMasivaModal] = useState(false);
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
        ofertas_asignadas: 0,
        monto_total_ganado: 0,
        solicitudes_abiertas: 0,
        tasa_conversion: 0,
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

  const handleCargaMasiva = () => {
    setShowCargaMasivaModal(true);
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

      <Tabs defaultValue="abiertas" className="space-y-4">
        <TabsList>
          <TabsTrigger value="abiertas">Abiertas</TabsTrigger>
          <TabsTrigger value="cerradas">Cerradas</TabsTrigger>
          <TabsTrigger value="ganadas">Ganadas</TabsTrigger>
        </TabsList>

        <TabsContent value="abiertas" className="space-y-4">
          <SolicitudesAbiertas 
            onHacerOferta={handleHacerOferta}
            onCargaMasiva={handleCargaMasiva}
            onVerOferta={handleVerOferta}
          />
        </TabsContent>

        <TabsContent value="cerradas" className="space-y-4">
          <SolicitudesCerradas />
        </TabsContent>

        <TabsContent value="ganadas" className="space-y-4">
          <SolicitudesGanadas />
        </TabsContent>
      </Tabs>

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
      
      {/* Carga Masiva Modal */}
      <CargaMasivaModal
        open={showCargaMasivaModal}
        onClose={() => setShowCargaMasivaModal(false)}
        onSuccess={() => {
          // Refresh solicitudes list
          window.location.reload();
        }}
      />

      {/* Ver Oferta Modal */}
      <VerOfertaModal
        open={showVerOfertaModal}
        onClose={() => {
          setShowVerOfertaModal(false);
          setSelectedSolicitud(null);
        }}
        solicitud={selectedSolicitud}
      />
    </div>
  );
}
