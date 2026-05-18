import { useNavigate } from 'react-router-dom';
import { Package, Users, BarChart3, Zap, Shield, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useBranding } from '@/contexts/BrandingContext';

const features = [
  {
    icon: Package,
    title: 'Marketplace de Repuestos',
    description: 'Conectamos compradores con proveedores especializados en tiempo real. Cotizaciones automáticas, precios competitivos.',
  },
  {
    icon: Users,
    title: 'Red de Asesores',
    description: 'Asesores certificados evalúan cada solicitud y ofrecen repuestos con garantía de calidad y respaldo.',
  },
  {
    icon: BarChart3,
    title: 'Analytics en Tiempo Real',
    description: 'Métricas detalladas, reportes de conversión y salud del marketplace para tomar decisiones con datos.',
  },
  {
    icon: Zap,
    title: 'Asignación Inteligente',
    description: 'Algoritmo de escalamiento que distribuye solicitudes al asesor óptimo según disponibilidad y especialidad.',
  },
  {
    icon: Shield,
    title: 'Garantía y Confianza',
    description: 'Cada transacción respaldada con trazabilidad completa, historial de ofertas y seguimiento de PQR.',
  },
];

export function LandingPage() {
  const navigate = useNavigate();
  const { logoUrl } = useBranding();
  const logo = logoUrl || '/Logo.png';

  return (
    <div className="light min-h-screen flex flex-col">

      {/* Nav */}
      <nav className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-8 py-5">
        <img src={logo} alt="TeLOO" className="h-12 w-auto brightness-0 invert" />
        <Button
          variant="ghost"
          className="text-white/80 hover:text-white hover:bg-white/10"
          onClick={() => navigate('/login')}
        >
          Iniciar sesión
        </Button>
      </nav>

      {/* Hero */}
      <section className="relative flex flex-col items-center justify-center min-h-[90vh] px-6 text-center bg-gradient-to-r from-accent to-secondary overflow-hidden">

        {/* background glow */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-white/10 via-transparent to-transparent pointer-events-none" />

        <div className="relative max-w-3xl mx-auto space-y-8">
          <img
            src={logo}
            alt="TeLOO"
            className="w-full max-w-[520px] h-auto mx-auto brightness-0 invert drop-shadow-2xl"
          />

          <div className="space-y-4">
            <h1 className="text-4xl md:text-6xl font-bold text-white tracking-tight leading-tight">
              El Marketplace Inteligente<br />
              <span className="text-white/90">
                de Repuestos
              </span>
            </h1>
            <p className="text-lg md:text-xl text-white/60 max-w-xl mx-auto">
              Conectamos compradores, asesores y proveedores en una sola plataforma.
              Cotizaciones en minutos, decisiones con datos.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Button
              size="lg"
              className="text-base px-8 gap-2 bg-white text-accent hover:bg-white/90"
              onClick={() => navigate('/login')}
            >
              Panel Administrativo
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="text-base px-8 gap-2 border-white/30 text-white bg-white/10 hover:bg-white/20 hover:text-white"
              asChild
            >
              <a href="https://advisor.teloo.cloud/" target="_blank" rel="noopener noreferrer">
                Portal de Asesores
                <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
          </div>
        </div>

        {/* scroll hint */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-white/30 text-xs">
          <div className="w-px h-10 bg-gradient-to-b from-white/20 to-transparent" />
          Descubrí más
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6 bg-slate-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16 space-y-3">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900">
              Todo lo que necesitás, en un solo lugar
            </h2>
            <p className="text-slate-500 max-w-xl mx-auto">
              TeLOO centraliza el proceso completo de gestión de repuestos,
              desde la solicitud hasta la entrega.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.title}
                  className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow border border-slate-100 space-y-4"
                >
                  <div className="h-11 w-11 rounded-xl bg-primary/10 flex items-center justify-center">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <div className="space-y-1.5">
                    <h3 className="font-semibold text-slate-900">{f.title}</h3>
                    <p className="text-sm text-slate-500 leading-relaxed">{f.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA bottom */}
      <section className="py-20 px-6 bg-slate-900 text-center">
        <div className="max-w-2xl mx-auto space-y-6">
          <h2 className="text-3xl font-bold text-white">¿Listo para empezar?</h2>
          <p className="text-white/50">Accedé al panel que corresponde a tu rol.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              size="lg"
              className="text-base px-8 gap-2"
              onClick={() => navigate('/login')}
            >
              Acceso Administrador
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="text-base px-8 gap-2 border-white/20 text-white bg-white/5 hover:bg-white/10 hover:text-white"
              asChild
            >
              <a href="https://advisor.teloo.cloud/" target="_blank" rel="noopener noreferrer">
                Acceso Asesor
                <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-950 py-6 px-8 flex items-center justify-between text-white/30 text-sm">
        <img src={logo} alt="TeLOO" className="h-7 w-auto opacity-40 brightness-0 invert" />
        <span>© {new Date().getFullYear()} TeLOO. Todos los derechos reservados.</span>
      </footer>

    </div>
  );
}
