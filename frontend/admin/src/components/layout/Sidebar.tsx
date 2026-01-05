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

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navigation = [
  {
    name: 'Inicio',
    href: '/',
    icon: Home,
    description: 'Dashboard principal',
  },
  {
    name: 'Solicitudes',
    href: '/solicitudes',
    icon: FileText,
    description: 'Gestión de solicitudes',
  },
  {
    name: 'Asesores',
    href: '/asesores',
    icon: Users,
    description: 'Gestión de asesores',
  },
  {
    name: 'Reportes',
    href: '/reportes',
    icon: BarChart3,
    description: 'Analytics y métricas',
  },
  {
    name: 'PQR',
    href: '/pqr',
    icon: MessageSquare,
    description: 'Atención al cliente',
  },
  {
    name: 'Configuración',
    href: '/configuracion',
    icon: Settings,
    description: 'Parámetros del sistema',
  },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <div
      className={cn(
        'relative flex flex-col bg-card border-r border-border transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-primary flex items-center justify-center shadow-sm">
              <span className="text-sm font-bold text-primary-foreground">T</span>
            </div>
            <span className="font-bold text-lg">TeLOO</span>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                'hover:bg-accent hover:text-accent-foreground',
                isActive
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground'
              )
            }
            title={collapsed ? item.name : undefined}
          >
            <div className="h-8 w-8 rounded-xl bg-primary/10 flex items-center justify-center">
              <item.icon className="h-4 w-4 text-primary" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span>{item.name}</span>
                <span className="text-xs opacity-70">{item.description}</span>
              </div>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        {!collapsed && (
          <div className="text-xs text-muted-foreground">
            <p>TeLOO V3</p>
            <p>Marketplace Inteligente</p>
          </div>
        )}
      </div>
    </div>
  );
}
