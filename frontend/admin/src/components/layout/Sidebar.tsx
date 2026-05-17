import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils.ts';
import {
  Home,
  Users,
  BarChart3,
  MessageSquare,
  Settings,
  FileText,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import axios from '@/lib/axios';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navigation = [
  { name: 'Inicio',        href: '/app',                icon: Home },
  { name: 'Solicitudes',   href: '/app/solicitudes',    icon: FileText },
  { name: 'Asesores',      href: '/app/asesores',       icon: Users },
  { name: 'Reportes',      href: '/app/reportes',       icon: BarChart3 },
  { name: 'PQR',           href: '/app/pqr',            icon: MessageSquare },
  { name: 'Configuración', href: '/app/configuracion',  icon: Settings },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    axios.get('/v1/configuracion/branding')
      .then((res) => {
        const url = res.data?.data?.logo_url;
        if (url) setLogoUrl(url.startsWith('http') ? url : `${API_BASE}${url}`);
      })
      .catch(() => {});
  }, []);

  return (
    <div
      className={cn(
        'relative flex flex-col bg-white border-r border-slate-200 transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo + toggle */}
      <div className={cn(
        'flex items-center px-4 py-5',
        collapsed ? 'justify-center' : 'justify-between'
      )}>
        {!collapsed && (
          <div className="min-w-0 flex-1">
            {logoUrl ? (
              <img
                src={logoUrl}
                alt="Logo"
                style={{ width: '160px', height: 'auto', display: 'block' }}
              />
            ) : (
              <span className="font-bold text-lg text-white">TeLOO</span>
            )}
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-md text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-colors flex-shrink-0"
          aria-label={collapsed ? 'Expandir menú' : 'Colapsar menú'}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 pb-4 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            end={item.href === '/app'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                collapsed && 'justify-center',
                isActive
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              )
            }
            title={collapsed ? item.name : undefined}
          >
            <item.icon className="h-4 w-4 flex-shrink-0" />
            {!collapsed && <span>{item.name}</span>}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
