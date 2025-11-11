/**
 * Types for Configuration Module
 */

export interface PesosEscalamiento {
  proximidad: number;
  actividad: number;
  desempeno: number;
  confianza: number;
}

export interface UmbralesNiveles {
  nivel1_min: number;
  nivel2_min: number;
  nivel3_min: number;
  nivel4_min: number;
}

export interface TiemposEsperaNivel {
  1: number;
  2: number;
  3: number;
  4: number;
  5: number;
}

export interface CanalesPorNivel {
  1: 'WHATSAPP' | 'PUSH' | 'EMAIL' | 'SMS';
  2: 'WHATSAPP' | 'PUSH' | 'EMAIL' | 'SMS';
  3: 'WHATSAPP' | 'PUSH' | 'EMAIL' | 'SMS';
  4: 'WHATSAPP' | 'PUSH' | 'EMAIL' | 'SMS';
  5: 'WHATSAPP' | 'PUSH' | 'EMAIL' | 'SMS';
}

export interface PesosEvaluacionOfertas {
  precio: number;
  tiempo_entrega: number;
  garantia: number;
}

export interface ParametrosGenerales {
  ofertas_minimas_deseadas: number;
  precio_minimo_oferta: number;
  precio_maximo_oferta: number;
  garantia_minima_meses: number;
  garantia_maxima_meses: number;
  tiempo_entrega_minimo_dias: number;
  tiempo_entrega_maximo_dias: number;
  cobertura_minima_porcentaje: number;
  timeout_evaluacion_segundos: number;
  vigencia_auditoria_dias: number;
  timeout_ofertas_horas: number;
  notificacion_expiracion_horas_antes: number;
  confianza_minima_operar: number;
  periodo_actividad_reciente_dias: number;
  periodo_desempeno_historico_meses: number;
  fallback_actividad_asesores_nuevos: number;
  fallback_desempeno_asesores_nuevos: number;
  puntaje_defecto_asesores_nuevos: number;
}

export interface ParametroMetadata {
  min?: number;
  max?: number;
  default?: number;
  unit?: string;
  description?: string;
}

export interface ConfiguracionCompleta {
  pesos_escalamiento: PesosEscalamiento;
  umbrales_niveles: UmbralesNiveles;
  tiempos_espera_nivel: TiemposEsperaNivel;
  canales_por_nivel: CanalesPorNivel;
  pesos_evaluacion_ofertas: PesosEvaluacionOfertas;
  parametros_generales: ParametrosGenerales;
}

export interface ConfiguracionConMetadata {
  configuracion_completa: ConfiguracionCompleta;
  metadata: Record<string, ParametroMetadata>;
}

export interface ConfiguracionSummary {
  configuracion_actual: ConfiguracionCompleta;
  estadisticas: {
    total_categorias: number;
    total_parametros: number;
    ultima_modificacion: string | null;
    modificado_por: string | null;
  };
  validaciones_activas: {
    pesos_suman_1: boolean;
    umbrales_decrecientes: boolean;
    rangos_validos: boolean;
  };
}

export interface Usuario {
  id: string;
  nombre_completo: string;
  email: string;
  rol: 'ADMIN' | 'ADVISOR' | 'ANALYST' | 'SUPPORT' | 'CLIENT';
  estado: 'ACTIVO' | 'INACTIVO' | 'SUSPENDIDO';
  created_at: string;
  updated_at: string;
}

export interface Rol {
  id: string;
  nombre: string;
  descripcion: string;
  permisos: string[];
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export type CategoriaConfiguracion = 
  | 'pesos_escalamiento'
  | 'umbrales_niveles'
  | 'tiempos_espera_nivel'
  | 'canales_por_nivel'
  | 'pesos_evaluacion_ofertas'
  | 'parametros_generales';

export interface ConfiguracionFormData {
  categoria: CategoriaConfiguracion;
  valores: any;
}

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export interface ConfiguracionCategory {
  key: CategoriaConfiguracion;
  title: string;
  description: string;
  icon: string;
}

export const CATEGORIAS_CONFIG: ConfiguracionCategory[] = [
  {
    key: 'pesos_escalamiento',
    title: 'Pesos de Escalamiento',
    description: 'Pesos del algoritmo de escalamiento de asesores',
    icon: 'Scale'
  },
  {
    key: 'umbrales_niveles',
    title: 'Umbrales de Niveles',
    description: 'Umbrales para clasificación de asesores por niveles',
    icon: 'BarChart3'
  },
  {
    key: 'tiempos_espera_nivel',
    title: 'Tiempos de Espera',
    description: 'Tiempos de espera por nivel de asesor',
    icon: 'Clock'
  },
  {
    key: 'canales_por_nivel',
    title: 'Canales de Notificación',
    description: 'Canales de notificación por nivel de asesor',
    icon: 'MessageSquare'
  },
  {
    key: 'pesos_evaluacion_ofertas',
    title: 'Pesos de Evaluación',
    description: 'Pesos para evaluación de ofertas',
    icon: 'Calculator'
  },
  {
    key: 'parametros_generales',
    title: 'Parámetros Generales',
    description: 'Parámetros generales del sistema',
    icon: 'Settings'
  }
];

export const CANALES_DISPONIBLES = [
  { value: 'WHATSAPP', label: 'WhatsApp' },
  { value: 'PUSH', label: 'Push Notification' },
  { value: 'EMAIL', label: 'Email' },
  { value: 'SMS', label: 'SMS' }
] as const;

export const ROLES_DISPONIBLES = [
  { value: 'ADMIN', label: 'Administrador' },
  { value: 'ADVISOR', label: 'Asesor' },
  { value: 'ANALYST', label: 'Analista' },
  { value: 'SUPPORT', label: 'Soporte' },
  { value: 'CLIENT', label: 'Cliente' }
] as const;

export const ESTADOS_USUARIO = [
  { value: 'ACTIVO', label: 'Activo' },
  { value: 'INACTIVO', label: 'Inactivo' },
  { value: 'SUSPENDIDO', label: 'Suspendido' }
] as const;