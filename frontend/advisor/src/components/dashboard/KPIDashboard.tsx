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
      title: 'Ofertas Asignadas',
      value: kpis.ofertas_asignadas,
      icon: Package,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Monto Total Ganado',
      value: formatCurrency(kpis.monto_total_ganado),
      icon: DollarSign,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Solicitudes Abiertas',
      value: kpis.solicitudes_abiertas,
      icon: TrendingUp,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
    {
      title: 'Tasa de Conversión',
      value: `${kpis.tasa_conversion.toFixed(1)}%`,
      icon: Target,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ];

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
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
          <Card key={kpi.title}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">
                    {kpi.title}
                  </p>
                  <p className="text-2xl font-bold">{kpi.value}</p>
                </div>
                <div className={`${kpi.bgColor} p-3 rounded-full`}>
                  <Icon className={`h-6 w-6 ${kpi.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
