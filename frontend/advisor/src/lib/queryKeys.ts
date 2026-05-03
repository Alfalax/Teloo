export const queryKeys = {
  solicitudes: {
    all: ['solicitudes'] as const,
    mis: () => [...queryKeys.solicitudes.all, 'mis'] as const,
    metrics: () => [...queryKeys.solicitudes.all, 'metrics'] as const,
  },
} as const;
