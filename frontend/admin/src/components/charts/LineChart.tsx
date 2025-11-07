import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

interface LineChartProps {
  data: any[];
  lines: {
    key: string;
    name: string;
    color: string;
  }[];
  xAxisKey: string;
  height?: number;
  showLegend?: boolean;
  formatXAxis?: (value: any) => string;
  formatTooltip?: (value: any, name: string) => [string, string];
}

export function LineChart({
  data,
  lines,
  xAxisKey,
  height = 300,
  showLegend = true,
  formatXAxis,
  formatTooltip,
}: LineChartProps) {
  const defaultFormatXAxis = (value: any) => {
    try {
      if (typeof value === 'string' && value.includes('-')) {
        return format(parseISO(value), 'dd/MM', { locale: es });
      }
      return value;
    } catch {
      return value;
    }
  };

  const defaultFormatTooltip = (value: any, name: string) => {
    return [value.toLocaleString(), name];
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsLineChart
        data={data}
        margin={{
          top: 5,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey={xAxisKey}
          tickFormatter={formatXAxis || defaultFormatXAxis}
          className="text-xs fill-muted-foreground"
        />
        <YAxis className="text-xs fill-muted-foreground" />
        <Tooltip
          formatter={formatTooltip || defaultFormatTooltip}
          labelFormatter={(label) => {
            try {
              if (typeof label === 'string' && label.includes('-')) {
                return format(parseISO(label), 'dd/MM/yyyy', { locale: es });
              }
              return label;
            } catch {
              return label;
            }
          }}
          contentStyle={{
            backgroundColor: 'hsl(var(--background))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '6px',
          }}
        />
        {showLegend && <Legend />}
        {lines.map((line) => (
          <Line
            key={line.key}
            type="monotone"
            dataKey={line.key}
            stroke={line.color}
            strokeWidth={2}
            dot={{ fill: line.color, strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: line.color, strokeWidth: 2 }}
            name={line.name}
          />
        ))}
      </RechartsLineChart>
    </ResponsiveContainer>
  );
}