/**
 * Utilidades para manejo de fechas y horas
 * Backend envía fechas en UTC (ISO 8601)
 * Frontend las convierte a hora local del navegador
 */

/**
 * Formatea una fecha ISO a formato legible en español
 * @param isoString - Fecha en formato ISO 8601 (UTC)
 * @param includeTime - Si incluir la hora
 * @returns Fecha formateada
 */
export function formatDate(isoString: string, includeTime: boolean = true): string {
  const date = new Date(isoString);
  
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...(includeTime && {
      hour: '2-digit',
      minute: '2-digit',
    }),
    timeZone: 'America/Bogota', // Hora de Colombia
  };
  
  return new Intl.DateTimeFormat('es-CO', options).format(date);
}

/**
 * Formatea una fecha a formato relativo (hace X minutos/horas/días)
 * @param isoString - Fecha en formato ISO 8601 (UTC)
 * @returns Texto relativo
 */
export function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'hace un momento';
  if (diffMins < 60) return `hace ${diffMins} min`;
  if (diffHours < 24) return `hace ${diffHours}h`;
  if (diffDays < 7) return `hace ${diffDays}d`;
  
  return formatDate(isoString, false);
}

/**
 * Formatea solo la hora
 * @param isoString - Fecha en formato ISO 8601 (UTC)
 * @returns Hora formateada (HH:MM)
 */
export function formatTime(isoString: string): string {
  const date = new Date(isoString);
  
  return new Intl.DateTimeFormat('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'America/Bogota',
  }).format(date);
}

/**
 * Formatea solo la fecha (sin hora)
 * @param isoString - Fecha en formato ISO 8601 (UTC)
 * @returns Fecha formateada (DD/MM/YYYY)
 */
export function formatDateOnly(isoString: string): string {
  const date = new Date(isoString);
  
  return new Intl.DateTimeFormat('es-CO', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: 'America/Bogota',
  }).format(date);
}

/**
 * Calcula minutos restantes desde ahora hasta una fecha
 * @param isoString - Fecha en formato ISO 8601 (UTC)
 * @returns Minutos restantes (negativo si ya pasó)
 */
export function minutesUntil(isoString: string): number {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  return Math.floor(diffMs / 60000);
}

/**
 * Calcula horas restantes desde ahora hasta una fecha
 * @param isoString - Fecha en formato ISO 8601 (UTC)
 * @returns Horas restantes (negativo si ya pasó)
 */
export function hoursUntil(isoString: string): number {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  return Math.floor(diffMs / 3600000);
}

/**
 * Verifica si una fecha ya pasó
 * @param isoString - Fecha en formato ISO 8601 (UTC)
 * @returns true si ya pasó
 */
export function isPast(isoString: string): boolean {
  const date = new Date(isoString);
  const now = new Date();
  return date < now;
}

/**
 * Formatea duración en minutos a texto legible
 * @param minutes - Minutos
 * @returns Texto formateado (ej: "2h 30min", "45min")
 */
export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}min`;
  
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  
  if (mins === 0) return `${hours}h`;
  return `${hours}h ${mins}min`;
}
