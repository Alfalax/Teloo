import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SegmentacionRFMData, SegmentoRFM } from "@/types/advisor-scorecards";
import { UsersIcon, TrendingUpIcon, AlertTriangleIcon, StarIcon, SparklesIcon, ZapIcon } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

interface SegmentacionRFMProps {
  data: SegmentacionRFMData;
}

const SEGMENT_CONFIG = {
  ASESORES_ESTRELLA: {
    icon: StarIcon,
    color: "text-yellow-500",
    bgColor: "bg-yellow-50",
    borderColor: "border-yellow-200",
    label: "Asesores Estrella",
    description: "Alto rendimiento en todas las dimensiones"
  },
  ESTRELLAS_ASCENSO: {
    icon: TrendingUpIcon,
    color: "text-blue-500",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    label: "Estrellas en Ascenso",
    description: "Alta actividad, necesitan mejorar competitividad"
  },
  GIGANTES_DORMIDOS: {
    icon: ZapIcon,
    color: "text-purple-500",
    bgColor: "bg-purple-50",
    borderColor: "border-purple-200",
    label: "Gigantes Dormidos",
    description: "Alto valor histórico, baja actividad reciente"
  },
  ASESORES_RIESGO: {
    icon: AlertTriangleIcon,
    color: "text-red-500",
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
    label: "Asesores en Riesgo",
    description: "Frecuencia y valor en declive"
  },
  NUEVOS_ASESORES: {
    icon: SparklesIcon,
    color: "text-green-500",
    bgColor: "bg-green-50",
    borderColor: "border-green-200",
    label: "Nuevos Asesores",
    description: "Menos de 30 días en la plataforma"
  }
};

export function SegmentacionRFM({ data }: SegmentacionRFMProps) {
  const { segmentos, acciones_recomendadas, definiciones } = data;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UsersIcon className="h-5 w-5" />
          Segmentación Dinámica RFM
        </CardTitle>
        <CardDescription>
          Clasificación de asesores basada en Recencia, Frecuencia y Valor Monetario
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Definiciones RFM */}
        <div className="mb-6 p-4 bg-muted rounded-lg">
          <p className="font-semibold mb-2">Dimensiones RFM:</p>
          <ul className="space-y-1 text-sm">
            <li>• <strong>Recencia:</strong> {definiciones.recencia}</li>
            <li>• <strong>Frecuencia:</strong> {definiciones.frecuencia}</li>
            <li>• <strong>Valor:</strong> {definiciones.valor}</li>
          </ul>
        </div>

        {/* Segmentos */}
        <div className="space-y-4">
          {segmentos.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No hay datos de segmentación disponibles
            </p>
          ) : (
            segmentos.map((segmento) => {
              const config = SEGMENT_CONFIG[segmento.segmento as keyof typeof SEGMENT_CONFIG];
              if (!config) return null;

              const Icon = config.icon;
              const acciones = acciones_recomendadas[segmento.segmento] || [];

              return (
                <Card key={segmento.segmento} className={`border-2 ${config.borderColor}`}>
                  <CardHeader className={config.bgColor}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Icon className={`h-6 w-6 ${config.color}`} />
                        <div>
                          <CardTitle className="text-lg">{config.label}</CardTitle>
                          <CardDescription>{config.description}</CardDescription>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-lg px-4 py-2">
                        {segmento.cantidad_asesores} asesores
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-4">
                    {/* Métricas promedio */}
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="text-center">
                        <p className="text-sm text-muted-foreground">Recencia Promedio</p>
                        <p className="text-2xl font-bold">{segmento.recencia_promedio.toFixed(1)}</p>
                        <p className="text-xs text-muted-foreground">días</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-muted-foreground">Frecuencia Promedio</p>
                        <p className="text-2xl font-bold">{segmento.frecuencia_promedio.toFixed(1)}</p>
                        <p className="text-xs text-muted-foreground">ofertas</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-muted-foreground">Valor Promedio</p>
                        <p className="text-2xl font-bold">{formatCurrency(segmento.valor_promedio)}</p>
                        <p className="text-xs text-muted-foreground">GAV_acc</p>
                      </div>
                    </div>

                    {/* Acciones recomendadas */}
                    {acciones.length > 0 && (
                      <Accordion type="single" collapsible className="w-full">
                        <AccordionItem value="acciones">
                          <AccordionTrigger className="text-sm font-semibold">
                            Acciones Recomendadas ({acciones.length})
                          </AccordionTrigger>
                          <AccordionContent>
                            <ul className="space-y-2 text-sm">
                              {acciones.map((accion, index) => (
                                <li key={index} className="flex items-start gap-2">
                                  <span className="text-primary mt-1">•</span>
                                  <span>{accion}</span>
                                </li>
                              ))}
                            </ul>
                          </AccordionContent>
                        </AccordionItem>
                      </Accordion>
                    )}
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
}
