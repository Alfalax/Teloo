import { useState, useEffect } from 'react';
import { Upload, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';
import SolicitudCard from './SolicitudCard';
import { Solicitud } from '@/types/solicitud';
import { solicitudesService } from '@/services/solicitudes';

interface SolicitudesAbiertasProps {
  onHacerOferta: (solicitud: Solicitud) => void;
  onCargaMasiva: () => void;
}

export default function SolicitudesAbiertas({ onHacerOferta, onCargaMasiva }: SolicitudesAbiertasProps) {
  const [solicitudes, setSolicitudes] = useState<Solicitud[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSolicitudes();
  }, []);

  const loadSolicitudes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await solicitudesService.getSolicitudesAbiertas();
      setSolicitudes(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar solicitudes');
      console.error('Error loading solicitudes:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <div className="h-8 w-48 bg-muted animate-pulse rounded"></div>
          <div className="h-10 w-40 bg-muted animate-pulse rounded"></div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-64 bg-muted animate-pulse rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-8 text-center">
        <p className="text-destructive font-medium mb-2">Error al cargar solicitudes</p>
        <p className="text-sm text-muted-foreground mb-4">{error}</p>
        <Button onClick={loadSolicitudes} variant="outline">
          Reintentar
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Solicitudes Disponibles</h3>
          <p className="text-sm text-muted-foreground">
            {solicitudes.length} solicitud{solicitudes.length !== 1 ? 'es' : ''} disponible{solicitudes.length !== 1 ? 's' : ''} para ofertar
          </p>
        </div>
        <Button onClick={onCargaMasiva} variant="outline">
          <Upload className="h-4 w-4 mr-2" />
          Carga Masiva Excel
        </Button>
      </div>

      {solicitudes.length === 0 ? (
        <div className="rounded-lg border bg-card p-12 text-center">
          <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-lg font-medium mb-2">No hay solicitudes disponibles</p>
          <p className="text-sm text-muted-foreground">
            Las nuevas solicitudes aparecerán aquí cuando estén disponibles
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {solicitudes.map((solicitud) => (
            <SolicitudCard
              key={solicitud.id}
              solicitud={solicitud}
              onHacerOferta={onHacerOferta}
            />
          ))}
        </div>
      )}
    </div>
  );
}
