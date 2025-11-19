import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { AsesorScorecard, AdvisorScorecardsData } from "@/types/advisor-scorecards";
import { ArrowUpIcon, ArrowDownIcon, TrendingUpIcon, ClockIcon, AwardIcon } from "lucide-react";

interface AdvisorScorecardsTableProps {
  data: AdvisorScorecardsData;
}

export function AdvisorScorecardsTable({ data }: AdvisorScorecardsTableProps) {
  const { asesores, metricas_definicion } = data;

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  const getBadgeVariant = (value: number, threshold: number): "default" | "secondary" | "destructive" => {
    if (value >= threshold) return "default";
    if (value >= threshold * 0.5) return "secondary";
    return "destructive";
  };

  // Mostrar top 10 asesores
  const topAsesores = asesores.slice(0, 10);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AwardIcon className="h-5 w-5" />
          Cuadros de Mando de Rendimiento del Asesor
        </CardTitle>
        <CardDescription>
          Top 10 asesores ordenados por tasa de adjudicación personal
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">#</TableHead>
                <TableHead>Asesor</TableHead>
                <TableHead>Ciudad</TableHead>
                <TableHead className="text-center">
                  <div className="flex flex-col items-center">
                    <TrendingUpIcon className="h-4 w-4 mb-1" />
                    <span className="text-xs">Presentación</span>
                  </div>
                </TableHead>
                <TableHead className="text-center">
                  <div className="flex flex-col items-center">
                    <AwardIcon className="h-4 w-4 mb-1" />
                    <span className="text-xs">Adjudicación</span>
                  </div>
                </TableHead>
                <TableHead className="text-center">
                  <div className="flex flex-col items-center">
                    <ArrowUpIcon className="h-4 w-4 mb-1" />
                    <span className="text-xs">Aceptación</span>
                  </div>
                </TableHead>
                <TableHead className="text-center">
                  <div className="flex flex-col items-center">
                    <span className="text-xs">Competitividad</span>
                  </div>
                </TableHead>
                <TableHead className="text-center">
                  <div className="flex flex-col items-center">
                    <ClockIcon className="h-4 w-4 mb-1" />
                    <span className="text-xs">Tiempo Resp.</span>
                  </div>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {topAsesores.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-muted-foreground">
                    No hay datos disponibles
                  </TableCell>
                </TableRow>
              ) : (
                topAsesores.map((asesor, index) => (
                  <TableRow key={asesor.asesor_id}>
                    <TableCell className="font-medium">{index + 1}</TableCell>
                    <TableCell className="font-medium">{asesor.nombre}</TableCell>
                    <TableCell>{asesor.ciudad}</TableCell>
                    <TableCell className="text-center">
                      <Badge variant={getBadgeVariant(asesor.tasa_presentacion_ofertas, 70)}>
                        {formatPercentage(asesor.tasa_presentacion_ofertas)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant={getBadgeVariant(asesor.tasa_adjudicacion_personal, 50)}>
                        {formatPercentage(asesor.tasa_adjudicacion_personal)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant={getBadgeVariant(asesor.tasa_aceptacion_adjudicaciones, 80)}>
                        {formatPercentage(asesor.tasa_aceptacion_adjudicaciones)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      {asesor.indice_competitividad.toFixed(1)}
                    </TableCell>
                    <TableCell className="text-center text-sm text-muted-foreground">
                      {formatTime(asesor.mediana_tiempo_respuesta_seg)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Definiciones de métricas */}
        <div className="mt-4 space-y-2 text-sm text-muted-foreground">
          <p className="font-semibold">Definiciones:</p>
          <ul className="space-y-1 ml-4">
            <li>• <strong>Presentación:</strong> {metricas_definicion.tasa_presentacion_ofertas}</li>
            <li>• <strong>Adjudicación:</strong> {metricas_definicion.tasa_adjudicacion_personal}</li>
            <li>• <strong>Aceptación:</strong> {metricas_definicion.tasa_aceptacion_adjudicaciones}</li>
            <li>• <strong>Competitividad:</strong> {metricas_definicion.indice_competitividad}</li>
            <li>• <strong>Tiempo Resp.:</strong> {metricas_definicion.mediana_tiempo_respuesta_seg}</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
