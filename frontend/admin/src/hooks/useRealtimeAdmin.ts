import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getSocket } from '@/services/socket';
import { queryKeys } from '@/lib/queryKeys';

const SOLICITUD_EVENTS = [
  'solicitud_created',
  'solicitud_oleada',
  'solicitud_updated',
];

const ASESOR_EVENTS = [
  'oferta_created',
  'oferta_updated',
  'oferta_accepted',
  'oferta_rejected',
];

export function useRealtimeAdmin() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    const invalidateSolicitudes = () => {
      queryClient.invalidateQueries({ queryKey: ['solicitudes'] });
    };

    const invalidateAsesores = () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.asesores.all });
    };

    SOLICITUD_EVENTS.forEach(event => socket.on(event, invalidateSolicitudes));
    ASESOR_EVENTS.forEach(event => socket.on(event, invalidateAsesores));

    return () => {
      SOLICITUD_EVENTS.forEach(event => socket.off(event, invalidateSolicitudes));
      ASESOR_EVENTS.forEach(event => socket.off(event, invalidateAsesores));
    };
  }, [queryClient]);
}
