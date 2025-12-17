import { TrendingUp, Package, DollarSign, Target } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { AsesorKPIs } from '@/types/kpi';
import { formatCurrency } from '@/lib/utils';

interface KPIDashboardProps {
  kpis: AsesorKPIs;
  isLoading?: boolean;
}

export default function KPIDashboard({ kpis, isLoading }: KPIDashboardProps) {
  const kpiCards = [
    {
      title: 'Repuestos Asignados',
      value: kpis.repuestos_adjudicados,
      icon: Package,
      bg: 'bg-secondary',
      fg: 'text-secondary-foreground',
    },
    {
      title: 'Monto Total Ganado',
      value: formatCurrency(kpis.monto_total_ganado),
      icon: DollarSign,
      bg: 'bg-primary',
      fg: 'text-primary-foreground',
    },
    {
      title: 'Pendientes por Oferta',
      value: kpis.pendientes_por_oferta,
      icon: TrendingUp,
      bg: 'bg-accent',
      fg: 'text-accent-foreground',
    },
    {
      title: 'Tasa de Conversión',
      value: `${kpis.tasa_conversion.toFixed(1)}%`,
      icon: Target,
      bg: 'bg-secondary',
      fg: 'text-secondary-foreground',
    },
  ];

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {[1, 2, 3, 4, 5].map((i) => (
          <Card key={i}>
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

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {kpiCards.map((kpi) => {
        const Icon = kpi.icon;
        return (
          <Card key={kpi.title} className="shadow-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">{kpi.title}</p>
                  <p className="text-3xl font-bold">{kpi.value}</p>
                </div>
                <div className={`p-3 rounded-xl ${kpi.bg}`}>
                  <Icon className={`h-6 w-6 ${kpi.fg}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
