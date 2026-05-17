import { TrendingUp, Package, DollarSign, Target, AlertCircle, RefreshCw } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AsesorKPIs } from '@/types/kpi';
import { formatCurrency } from '@/lib/utils';

interface KPIDashboardProps {
  kpis: AsesorKPIs | null;
  isLoading?: boolean;
  hasError?: boolean;
  onRetry?: () => void;
}

export default function KPIDashboard({ kpis, isLoading, hasError, onRetry }: KPIDashboardProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="bg-white border-0 shadow-sm">
            <CardContent className="p-6">
              <div className="animate-pulse space-y-3">
                <div className="h-4 bg-muted rounded w-1/2"></div>
                <div className="h-8 bg-muted rounded w-3/4"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (hasError || !kpis) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-lg border border-destructive/30 bg-destructive/5 text-destructive">
        <AlertCircle className="h-5 w-5 flex-shrink-0" />
        <span className="text-sm font-medium">No se pudieron cargar los indicadores</span>
        {onRetry && (
          <Button variant="ghost" size="sm" onClick={onRetry} className="ml-auto gap-1.5 text-destructive hover:text-destructive">
            <RefreshCw className="h-3.5 w-3.5" />
            Reintentar
          </Button>
        )}
      </div>
    );
  }

  const kpiCards = [
    {
      title: 'Repuestos Asignados',
      value: kpis.repuestos_adjudicados,
      icon: Package,
    },
    {
      title: 'Monto Total Ganado',
      value: formatCurrency(kpis.monto_total_ganado),
      icon: DollarSign,
    },
    {
      title: 'Pendientes por Oferta',
      value: kpis.pendientes_por_oferta,
      icon: TrendingUp,
    },
    {
      title: 'Tasa de Conversión',
      value: `${kpis.tasa_conversion.toFixed(1)}%`,
      icon: Target,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {kpiCards.map((kpi) => {
        const Icon = kpi.icon;
        return (
          <Card key={kpi.title} className="bg-white border-0 shadow-sm hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">{kpi.title}</p>
                  <p className="text-2xl font-bold tracking-tight">{kpi.value}</p>
                </div>
                <div className="p-3 rounded-xl bg-primary/10">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
