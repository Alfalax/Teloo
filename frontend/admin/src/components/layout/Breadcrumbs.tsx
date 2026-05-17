import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

const ROUTE_LABELS: Record<string, string> = {
  solicitudes: 'Solicitudes',
  asesores: 'Asesores',
  reportes: 'Reportes',
  pqr: 'PQR',
  configuracion: 'Configuración',
};

export function Breadcrumbs() {
  const { pathname } = useLocation();
  const segments = pathname.split('/').filter(Boolean);

  if (segments.length === 0) return null;

  const crumbs = segments.map((seg, i) => ({
    label: ROUTE_LABELS[seg] ?? seg,
    href: '/' + segments.slice(0, i + 1).join('/'),
    isLast: i === segments.length - 1,
  }));

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-muted-foreground px-6 py-2 bg-slate-50 border-b border-slate-200/70">
      <Link to="/" className="flex items-center gap-1 hover:text-foreground transition-colors">
        <Home className="h-3.5 w-3.5" />
        <span>Inicio</span>
      </Link>
      {crumbs.map(({ label, href, isLast }) => (
        <span key={href} className="flex items-center gap-1">
          <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
          {isLast ? (
            <span className="font-medium text-foreground" aria-current="page">{label}</span>
          ) : (
            <Link to={href} className="hover:text-foreground transition-colors">{label}</Link>
          )}
        </span>
      ))}
    </nav>
  );
}
