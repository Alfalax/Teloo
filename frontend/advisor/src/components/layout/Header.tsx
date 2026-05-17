import { useState, useEffect } from 'react';
import { Bell, LogOut, User, Search, Moon, Sun } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

import axios from '@/lib/axios';

export default function Header() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    axios.get('/v1/configuracion/branding')
      .then((res) => {
        const url = res.data?.data?.logo_url;
        if (url) {
          setLogoUrl(url.startsWith('http') ? url : `${API_BASE}${url}`);
        }
      })
      .catch(() => {});
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Error al cerrar sesión:', error);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-gradient-to-r from-accent to-secondary">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-3">
          {logoUrl ? (
            <img
              src={logoUrl}
              alt="Logo"
              style={{ height: '36px', width: 'auto', display: 'block' }}
            />
          ) : (
            <div className="h-9 w-9 rounded-xl bg-primary flex items-center justify-center shadow-sm">
              <span className="text-lg font-bold text-primary-foreground">T</span>
            </div>
          )}
          <div>
            <h1 className="text-lg font-semibold text-white">TeLOO Asesor</h1>
            <p className="text-xs text-white/80">Portal de Asesores</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 bg-white/90 rounded-md px-2 py-1 shadow-sm">
            <Search className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <Input
              placeholder="Buscar..."
              className="h-8 w-56 border-0 bg-transparent focus-visible:ring-0"
              aria-label="Buscar"
            />
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="text-white"
            aria-label={theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
          >
            {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </Button>

          <Button variant="ghost" size="icon" className="relative text-white" aria-label="Notificaciones">
            <Bell className="h-5 w-5" aria-hidden="true" />
            <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-primary"></span>
          </Button>

          <div className="flex items-center gap-3 border-l border-white/20 pl-4">
            <div className="text-right">
              <p className="text-sm font-medium text-white">{user?.nombre}</p>
              <p className="text-xs text-white/80">{user?.email}</p>
            </div>
            <div className="h-9 w-9 rounded-full bg-white/20 flex items-center justify-center">
              <User className="h-5 w-5 text-white" />
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              title="Cerrar sesión"
              className="text-white"
              aria-label="Cerrar sesión"
            >
              <LogOut className="h-5 w-5" aria-hidden="true" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
