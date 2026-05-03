import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getSocket, disconnectSocket } from '@/services/socket';
import { queryKeys } from '@/lib/queryKeys';

const SOLICITUD_EVENTS = [
  'solicitud_created',
  'solicitud_oleada',
  'solicitud_updated',
];

const OFERTA_EVENTS = [
  'oferta_created',
  'oferta_updated',
  'oferta_accepted',
  'oferta_rejected',
];

export function useRealtimeSolicitudes() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const socket = getSocket();

    const invalidate = () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.solicitudes.all });
    };

    [...SOLICITUD_EVENTS, ...OFERTA_EVENTS].forEach(event => {
      socket.on(event, invalidate);
    });

    return () => {
      [...SOLICITUD_EVENTS, ...OFERTA_EVENTS].forEach(event => {
        socket.off(event, invalidate);
      });
    };
  }, [queryClient]);
}

export function useSocketDisconnect() {
  useEffect(() => {
    return () => {
      disconnectSocket();
    };
  }, []);
}
