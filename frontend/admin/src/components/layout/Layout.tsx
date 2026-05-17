import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Breadcrumbs } from './Breadcrumbs';
import { useRealtimeAdmin } from '@/hooks/useRealtimeAdmin';

export function Layout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  useRealtimeAdmin();

  return (
    <div className="min-h-screen flex">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <div className="flex-1 flex flex-col bg-slate-50 min-w-0">
        <Header sidebarCollapsed={sidebarCollapsed} />
        <Breadcrumbs />
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
