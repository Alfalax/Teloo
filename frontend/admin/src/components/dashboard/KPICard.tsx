import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils.ts';

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
  isLoading?: boolean;
}

export function KPICard({
  title,
  value,
  change,
  trend,
  description,
  icon: Icon,
  isLoading = false,
}: KPICardProps) {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-3 w-3" />;
      case 'down':
        return <TrendingDown className="h-3 w-3" />;
      default:
        return <Minus className="h-3 w-3" />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-muted-foreground';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            <div className="h-4 w-32 bg-muted animate-pulse rounded" />
          </CardTitle>
          <div className="h-4 w-4 bg-muted animate-pulse rounded" />
        </CardHeader>
        <CardContent>
          <div className="h-8 w-24 bg-muted animate-pulse rounded mb-2" />
          <div className="h-3 w-40 bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {Icon && (
          <div className="p-2 rounded-xl bg-secondary">
            <Icon className="h-4 w-4 text-secondary-foreground" />
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold">{value}</div>
        {(change !== undefined || description) && (
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            {change !== undefined && (
              <>
                <span className={cn('flex items-center gap-1', getTrendColor())}>
                  {getTrendIcon()}
                  {change > 0 ? '+' : ''}
                  {change.toFixed(1)}%
                </span>
                {description && <span className="ml-1">{description}</span>}
              </>
            )}
            {change === undefined && description && <span>{description}</span>}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
