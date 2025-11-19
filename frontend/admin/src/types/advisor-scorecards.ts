/**
 * Tipos para Advisor Scorecards y Segmentación RFM
 */

export interface AsesorScorecard {
  asesor_id: string;
  nombre: string;
  ciudad: string;
  solicitudes_asignadas: number;
  solicitudes_respondidas: number;
  total_ofertas: number;
  ofertas_adjudicadas: number;
  ofertas_aceptadas: number;
  indice_competitividad: number;
  mediana_tiempo_respuesta_seg: number;
  tasa_presentacion_ofertas: number;
  tasa_adjudicacion_personal: number;
  tasa_aceptacion_adjudicaciones: number;
}

export interface AdvisorScorecardsData {
  asesores: AsesorScorecard[];
  metricas_definicion: {
    tasa_presentacion_ofertas: string;
    tasa_adjudicacion_personal: string;
    tasa_aceptacion_adjudicaciones: string;
    indice_competitividad: string;
    mediana_tiempo_respuesta_seg: string;
  };
}

export interface AsesorDetalle {
  asesor_id: string;
  nombre: string;
  ciudad: string;
  recencia_dias: number;
  frecuencia_ofertas: number;
  valor_monetario: number;
}

export interface SegmentoRFM {
  segmento: string;
  cantidad_asesores: number;
  recencia_promedio: number;
  frecuencia_promedio: number;
  valor_promedio: number;
  asesores_detalle: AsesorDetalle[];
}

export interface SegmentacionRFMData {
  segmentos: SegmentoRFM[];
  acciones_recomendadas: {
    [key: string]: string[];
  };
  definiciones: {
    recencia: string;
    frecuencia: string;
    valor: string;
  };
}

export interface AdvisorAnalyticsResponse {
  dashboard: string;
  periodo: {
    inicio: string;
    fin: string;
  };
  filtros: {
    ciudad: string | null;
  };
  datos: {
    advisor_scorecards: AdvisorScorecardsData;
    segmentacion_rfm: SegmentacionRFMData;
    resumen_ejecutivo: {
      total_asesores_analizados: number;
      periodo_analisis: {
        inicio: string;
        fin: string;
      };
      filtro_ciudad: string | null;
    };
  };
  generado_en: string;
}
