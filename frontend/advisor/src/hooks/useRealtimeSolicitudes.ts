import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getSocket, disconnectSocket } from '@/services/socket';
import { queryKeys } from '@/lib/queryKeys';

const EVENTS = [
  'solicitud_created',
  'solicitud_oleada',
  'solicitud_updated',
  'oferta_created',
  'oferta_updated',
  'oferta_accepted',
  'oferta_rejected',
];

export function useRealtimeSolicitudes() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    const invalidate = () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.solicitudes.all });
    };

    EVENTS.forEach(event => socket.on(event, invalidate));

    return () => {
      EVENTS.forEach(event => socket.off(event, invalidate));
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
