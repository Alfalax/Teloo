export const queryKeys = {
  asesores: {
    all: ['asesores'] as const,
    list: (filters: Record<string, string>, page: number) =>
      [...queryKeys.asesores.all, 'list', filters, page] as const,
    kpis: () => [...queryKeys.asesores.all, 'kpis'] as const,
  },
} as const;
