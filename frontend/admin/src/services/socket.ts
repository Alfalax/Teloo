import { io, Socket } from 'socket.io-client';

const REALTIME_URL = import.meta.env.VITE_REALTIME_URL || 'http://localhost:8003';
const REALTIME_ENABLED = import.meta.env.VITE_REALTIME_ENABLED === 'true';

let socket: Socket | null = null;

export function getSocket(): Socket | null {
  if (!REALTIME_ENABLED) return null;

  if (!socket) {
    const token = localStorage.getItem('access_token');
    socket = io(REALTIME_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 3,
      reconnectionDelay: 3000,
      timeout: 5000,
    });

    socket.on('reconnect_failed', () => {
      socket?.disconnect();
      socket = null;
    });
  }
  return socket;
}

export function disconnectSocket(): void {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}

export function updateSocketToken(): void {
  if (socket) {
    const token = localStorage.getItem('access_token');
    socket.auth = { token };
    socket.disconnect().connect();
  }
}
