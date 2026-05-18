import { useNavigate } from 'react-router-dom';
import {
  Package, Users, BarChart3, Zap, Shield, ArrowRight,
  MessageCircle, Car, CheckCircle2, Clock, UserCheck,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useBranding } from '@/contexts/BrandingContext';

// Habilitar cuando se configure el número de WhatsApp
const WHATSAPP_ENABLED = false;
const WHATSAPP_COTIZAR_URL = `https://wa.me/TODO?text=${encodeURIComponent('Hola, quiero cotizar un repuesto con TeLOO')}`;
const WHATSAPP_ASESOR_URL = `https://wa.me/TODO?text=${encodeURIComponent('Hola, quiero registrarme como asesor TeLOO')}`;

const features = [
  {
    icon: Package,
    title: 'Marketplace de Repuestos',
    description: 'Conectamos compradores con proveedores especializados en tiempo real. Cotizaciones automáticas, precios competitivos.',
    color: '#00D248',
  },
  {
    icon: Users,
    title: 'Red de Asesores',
    description: 'Asesores certificados evalúan cada solicitud y ofrecen repuestos con garantía de calidad y respaldo.',
    color: '#00C2C0',
  },
  {
    icon: BarChart3,
    title: 'Analytics en Tiempo Real',
    description: 'Métricas detalladas, reportes de conversión y salud del marketplace para tomar decisiones con datos.',
    color: '#007BFF',
  },
  {
    icon: Zap,
    title: 'Asignación Inteligente',
    description: 'Algoritmo de escalamiento que distribuye solicitudes al asesor óptimo según disponibilidad y especialidad.',
    color: '#FFB800',
  },
  {
    icon: Shield,
    title: 'Garantía y Confianza',
    description: 'Cada transacción respaldada con trazabilidad completa, historial de ofertas y seguimiento de PQR.',
    color: '#F6888B',
  },
];

const HOW_IT_WORKS = [
  {
    step: '01',
    icon: MessageCircle,
    title: 'Escribinos por WhatsApp',
    desc: 'Indicá tu vehículo (marca, modelo, año) y el repuesto que necesitás.',
    color: '#00D248',
  },
  {
    step: '02',
    icon: Users,
    title: 'Un asesor certificado te toma',
    desc: 'Experto en tu marca recibe la solicitud y busca entre decenas de proveedores.',
    color: '#00C2C0',
  },
  {
    step: '03',
    icon: CheckCircle2,
    title: 'Cotización en minutos',
    desc: 'Recibís precio, garantía y disponibilidad. Comprás con respaldo total.',
    color: '#007BFF',
  },
];

const ADVISOR_REQUIREMENTS = [
  'Cédula de identidad vigente',
  'Conocimiento certificado en marca de vehículos',
  'Punto de venta activo',
];

const ADVISOR_BENEFITS = [
  'Acceso a la red de +500 proveedores verificados',
  'Panel propio de gestión de solicitudes',
  'Comisiones por cierre de cotizaciones',
  'Soporte y capacitación continua',
];

export function LandingPage() {
  const navigate = useNavigate();
  const { logoUrl } = useBranding();
  const logo = logoUrl || '/Logo.png';

  return (
    <div className="light bg-white text-[#4A4A4A] min-h-screen flex flex-col antialiased overflow-x-hidden">

      {/* ── NAV ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-b border-[#8E8E8E]/10 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src={logo} alt="TeLOO" className="h-12 w-auto object-contain" />
            <span className="hidden md:inline-block px-2.5 py-0.5 text-xs font-semibold bg-[#E2FBE9] text-[#00D248] rounded-full border border-[#00D248]/20">
              Ecosistema Activo
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              className="text-[#333333] hover:text-[#007BFF] font-medium"
              onClick={() => navigate('/login')}
            >
              Iniciar sesión
            </Button>
            <Button
              className="bg-[#00D248] text-white hover:bg-[#00D248]/90 font-semibold px-5 rounded-xl shadow-[0_4px_14px_rgba(0,210,72,0.3)]"
              onClick={() => navigate('/login')}
            >
              Acceso Staff
            </Button>
          </div>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section className="relative pt-32 pb-24 md:pt-40 md:pb-32 px-6 overflow-hidden bg-gradient-to-b from-[#F5F5F5]/50 to-white">
        <div className="absolute top-20 left-1/4 w-[250px] h-[250px] bg-[#00C2C0]/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute top-40 right-1/4 w-[300px] h-[300px] bg-[#007BFF]/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#8E8E8E_1px,transparent_1px),linear-gradient(to_bottom,#8E8E8E_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-[0.03] pointer-events-none" />

        <div className="relative max-w-7xl mx-auto grid lg:grid-cols-12 gap-12 items-center">

          {/* Left: copy */}
          <div className="lg:col-span-7 space-y-8 text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-[#8E8E8E]/15 shadow-sm">
              <span className="flex h-2 w-2 rounded-full bg-[#00D248] animate-pulse" />
              <span className="text-xs font-bold text-[#333333] uppercase tracking-wider">Marketplace Inteligente Autorizado</span>
            </div>

            <img
              src={logo}
              alt="TeLOO"
              className="max-w-[520px] w-full h-auto"
            />

            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-[#333333] tracking-tight leading-[1.1]">
                Repuestos listos en{' '}
                <span className="bg-gradient-to-r from-[#007BFF] via-[#00C2C0] to-[#00D248] bg-clip-text text-transparent">
                  Tiempo Récord
                </span>
              </h1>
              <p className="text-lg md:text-xl text-[#4A4A4A] max-w-2xl leading-relaxed">
                Conectamos flotas, aseguradoras y talleres con asesores certificados y proveedores en minutos.
                Cotizaciones precisas respaldadas con garantía real.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <Button
                size="lg"
                className="bg-[#00D248] text-white hover:bg-[#00D248]/90 text-base px-8 py-6 gap-3 rounded-2xl shadow-[0_8px_20px_-4px_rgba(0,210,72,0.4)] font-bold"
                onClick={() => navigate('/login')}
              >
                Panel Administrativo
                <ArrowRight className="h-5 w-5" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-[#007BFF] text-[#007BFF] hover:bg-[#007BFF]/5 text-base px-8 py-6 gap-3 rounded-2xl font-bold"
                asChild
              >
                <a href="https://advisor.teloo.cloud/" target="_blank" rel="noopener noreferrer">
                  Portal de Asesores
                  <ArrowRight className="h-5 w-5" />
                </a>
              </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-6 pt-8 border-t border-[#8E8E8E]/15">
              <div>
                <p className="text-3xl font-extrabold text-[#007BFF]">&lt; 5 min</p>
                <p className="text-xs text-[#8E8E8E] font-medium mt-1 uppercase tracking-wider">Tiempo de Cotización</p>
              </div>
              <div>
                <p className="text-3xl font-extrabold text-[#00D248]">+500</p>
                <p className="text-xs text-[#8E8E8E] font-medium mt-1 uppercase tracking-wider">Proveedores Activos</p>
              </div>
              <div>
                <p className="text-3xl font-extrabold text-[#F6888B]">99.4%</p>
                <p className="text-xs text-[#8E8E8E] font-medium mt-1 uppercase tracking-wider">Asignación Exitosa</p>
              </div>
            </div>
          </div>

          {/* Right: mockup card */}
          <div className="lg:col-span-5 relative">
            <div className="absolute inset-0 bg-gradient-to-tr from-[#007BFF]/10 to-[#00D248]/10 rounded-3xl blur-2xl -z-10" />
            <div className="bg-white rounded-3xl p-6 shadow-2xl border border-[#8E8E8E]/10 space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-[#F5F5F5]">
                <span className="font-bold text-[#333333] text-sm tracking-tight">Ecosistema TeLOO</span>
                <span className="px-2 py-0.5 text-[10px] font-bold bg-[#E2FBE9] text-[#00D248] rounded-full">SISTEMA EN VIVO</span>
              </div>

              <div className="space-y-4">
                <div className="bg-[#F5F5F5] rounded-2xl p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[#007BFF]/10 rounded-xl">
                      <Car className="h-5 w-5 text-[#007BFF]" />
                    </div>
                    <div>
                      <p className="text-xs text-[#8E8E8E] font-semibold">Último Pedido Recibido</p>
                      <p className="text-sm font-bold text-[#333333]">Amortiguadores Hilux 2023</p>
                    </div>
                  </div>
                  <span className="text-[11px] bg-[#E2FBE9] text-[#00D248] px-2 py-0.5 rounded-md font-semibold">12s atrás</span>
                </div>

                <div className="bg-[#F5F5F5] rounded-2xl p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[#00C2C0]/10 rounded-xl">
                      <Users className="h-5 w-5 text-[#00C2C0]" />
                    </div>
                    <div>
                      <p className="text-xs text-[#8E8E8E] font-semibold">Asesor Asignado</p>
                      <p className="text-sm font-bold text-[#333333]">Diego R. (Especialista Suspensión)</p>
                    </div>
                  </div>
                  <span className="text-[11px] bg-[#007BFF]/10 text-[#007BFF] px-2 py-0.5 rounded-md font-semibold">Conectado</span>
                </div>

                <div className="bg-[#FFFDF0] border border-[#FFB800]/30 rounded-2xl p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-4 w-4 rounded-full bg-[#FFB800] flex items-center justify-center text-white text-[10px] font-bold">!</div>
                    <div>
                      <p className="text-xs text-[#FFB800] font-bold uppercase tracking-wider">¡Nueva Oferta!</p>
                      <p className="text-sm font-extrabold text-[#333333]">$145.000 COP <span className="text-xs text-[#8E8E8E] font-normal">Sugerido</span></p>
                    </div>
                  </div>
                  <span className="text-[11px] bg-[#FFB800]/10 text-[#FFB800] px-2 py-0.5 rounded-md font-bold">Garantizado</span>
                </div>
              </div>

              <button className="w-full bg-[#00D248] hover:bg-[#00D248]/90 text-white font-bold py-3.5 px-4 rounded-2xl transition-all shadow-[0_4px_12px_rgba(0,210,72,0.25)] flex items-center justify-center gap-2 group text-sm">
                <span>Comprar Ahora</span>
                <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── CÓMO FUNCIONA / WHATSAPP ── */}
      <section className="py-20 px-6 bg-[#F5F5F5] border-y border-[#8E8E8E]/10">
        <div className="max-w-4xl mx-auto text-center space-y-4 mb-12">
          <span className="inline-flex items-center gap-2 px-3 py-1 bg-[#00D248]/10 text-[#00D248] text-xs font-bold rounded-full uppercase tracking-wider">
            <MessageCircle className="h-3 w-3" />
            Cotizá en minutos
          </span>
          <h2 className="text-3xl font-extrabold text-[#333333] tracking-tight">
            ¿Necesitás un repuesto? Así funciona
          </h2>
          <p className="text-[#4A4A4A] max-w-xl mx-auto text-sm">
            Sin formularios complicados. Un asesor certificado te atiende por WhatsApp y cotiza en tiempo real.
          </p>
        </div>

        <div className="max-w-3xl mx-auto grid md:grid-cols-3 gap-6 mb-12">
          {HOW_IT_WORKS.map((s) => {
            const Icon = s.icon;
            return (
              <div key={s.step} className="bg-white rounded-2xl p-6 shadow-sm border border-[#8E8E8E]/10 text-center space-y-3">
                <div className="mx-auto h-12 w-12 rounded-2xl flex items-center justify-center" style={{ backgroundColor: `${s.color}15` }}>
                  <Icon className="h-6 w-6" style={{ color: s.color }} />
                </div>
                <p className="text-[10px] font-black text-[#8E8E8E] uppercase tracking-widest">{s.step}</p>
                <h3 className="font-bold text-[#333333] text-sm">{s.title}</h3>
                <p className="text-xs text-[#4A4A4A] leading-relaxed">{s.desc}</p>
              </div>
            );
          })}
        </div>

        <div className="flex flex-col items-center gap-3">
          {WHATSAPP_ENABLED ? (
            <Button size="lg" className="bg-[#25D366] hover:bg-[#25D366]/90 text-white font-bold px-10 py-6 rounded-2xl gap-3 text-base shadow-[0_8px_20px_-4px_rgba(37,211,102,0.4)]" asChild>
              <a href={WHATSAPP_COTIZAR_URL} target="_blank" rel="noopener noreferrer">
                <MessageCircle className="h-5 w-5" />
                Cotizá por WhatsApp
              </a>
            </Button>
          ) : (
            <Button size="lg" disabled className="bg-[#25D366] text-white font-bold px-10 py-6 rounded-2xl gap-3 text-base opacity-50 cursor-not-allowed">
              <MessageCircle className="h-5 w-5" />
              Cotizá por WhatsApp
            </Button>
          )}
          {!WHATSAPP_ENABLED && (
            <p className="text-xs text-[#8E8E8E]">Canal de atención próximamente disponible</p>
          )}
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section className="py-24 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-20 space-y-4">
            <span className="text-xs font-bold text-[#007BFF] uppercase tracking-widest bg-[#007BFF]/10 px-3 py-1.5 rounded-full">
              Características del Ecosistema
            </span>
            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[#333333]">
              Todo lo que tu operación necesita, simplificado
            </h2>
            <p className="text-[#8E8E8E] max-w-xl mx-auto text-base">
              TeLOO unifica la comunicación, cotizaciones y seguimiento de repuestos en un solo panel central.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((f) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.title}
                  className="group relative bg-white rounded-3xl p-8 shadow-sm hover:shadow-xl transition-all duration-300 border border-[#8E8E8E]/10 hover:-translate-y-1 overflow-hidden"
                >
                  <div className="absolute top-0 left-0 right-0 h-1.5 opacity-40 transition-opacity group-hover:opacity-100" style={{ backgroundColor: f.color }} />
                  <div className="h-12 w-12 rounded-2xl flex items-center justify-center mb-6" style={{ backgroundColor: `${f.color}15` }}>
                    <Icon className="h-6 w-6" style={{ color: f.color }} />
                  </div>
                  <div className="space-y-3">
                    <h3 className="font-bold text-lg text-[#333333]">{f.title}</h3>
                    <p className="text-sm text-[#4A4A4A] leading-relaxed">{f.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── ECOSISTEMA ── */}
      <section className="py-20 px-6 bg-white border-t border-[#8E8E8E]/10">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16 space-y-2">
            <h2 className="text-2xl md:text-3xl font-extrabold text-[#333333]">¿Quiénes forman parte de TeLOO?</h2>
            <p className="text-[#8E8E8E] text-sm">
              Conectamos las tres aristas del mercado para eliminar la desconfianza y los sobreprecios.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-[#F5F5F5] p-6 rounded-2xl space-y-4">
              <div className="text-xs font-bold text-[#007BFF] uppercase">1. Compradores</div>
              <h4 className="font-bold text-base text-[#333333]">Flotas, Aseguradoras y Talleres</h4>
              <p className="text-xs text-[#4A4A4A] leading-relaxed">
                Ingresan sus solicitudes de repuestos y obtienen transparencia absoluta en precios con garantía real.
              </p>
            </div>
            <div className="bg-[#F5F5F5] p-6 rounded-2xl space-y-4 border-t-4 border-[#00C2C0]">
              <div className="text-xs font-bold text-[#00C2C0] uppercase">2. Asesores TeLOO</div>
              <h4 className="font-bold text-base text-[#333333]">Expertos de Marca</h4>
              <p className="text-xs text-[#4A4A4A] leading-relaxed">
                Validan la solicitud, buscan la mejor combinación de precio y entrega entre decenas de proveedores autorizados.
              </p>
            </div>
            <div className="bg-[#F5F5F5] p-6 rounded-2xl space-y-4">
              <div className="text-xs font-bold text-[#00D248] uppercase">3. Proveedores</div>
              <h4 className="font-bold text-base text-[#333333]">Importadores y Distribuidores</h4>
              <p className="text-xs text-[#4A4A4A] leading-relaxed">
                Reciben solicitudes pre-calificadas listas para comprar, sin esfuerzo comercial adicional.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── REGISTRO DE ASESORES ── */}
      <section className="py-20 px-6 bg-gradient-to-b from-[#F0F9FF] to-white border-t border-[#007BFF]/10">
        <div className="max-w-5xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#007BFF]/10 text-[#007BFF] text-xs font-bold rounded-full uppercase tracking-wider">
              <UserCheck className="h-3 w-3" />
              Oportunidad profesional
            </div>
            <h2 className="text-3xl font-extrabold text-[#333333] tracking-tight">
              ¿Querés ser asesor TeLOO?
            </h2>
            <p className="text-[#4A4A4A] leading-relaxed">
              Los asesores TeLOO son expertos certificados en marcas de vehículos que conectan compradores
              con proveedores. Trabajá desde tu punto de venta y generá comisiones por cada cotización cerrada.
            </p>
            <ul className="space-y-3">
              {ADVISOR_BENEFITS.map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-[#4A4A4A]">
                  <CheckCircle2 className="h-4 w-4 text-[#00D248] mt-0.5 shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-white rounded-3xl p-8 shadow-xl border border-[#8E8E8E]/10 space-y-6">
            <div className="space-y-2">
              <h3 className="font-bold text-[#333333] text-lg">Registrate como asesor</h3>
              <p className="text-xs text-[#8E8E8E]">
                El proceso de onboarding es gestionado por el equipo TeLOO.
                Contactanos para iniciar tu registro.
              </p>
            </div>

            <div className="bg-[#F5F5F5] rounded-2xl p-4 space-y-3">
              <p className="text-xs font-bold text-[#333333] uppercase tracking-wider">Lo que necesitás tener</p>
              {ADVISOR_REQUIREMENTS.map((req) => (
                <div key={req} className="flex items-center gap-2 text-xs text-[#4A4A4A]">
                  <div className="h-1.5 w-1.5 rounded-full bg-[#00C2C0] shrink-0" />
                  {req}
                </div>
              ))}
            </div>

            <div className="space-y-3">
              {WHATSAPP_ENABLED ? (
                <Button size="lg" className="w-full bg-[#007BFF] hover:bg-[#007BFF]/90 text-white font-bold py-6 rounded-2xl gap-2" asChild>
                  <a href={WHATSAPP_ASESOR_URL} target="_blank" rel="noopener noreferrer">
                    <MessageCircle className="h-4 w-4" />
                    Quiero ser asesor
                  </a>
                </Button>
              ) : (
                <Button size="lg" disabled className="w-full bg-[#007BFF] text-white font-bold py-6 rounded-2xl gap-2 opacity-50 cursor-not-allowed">
                  <MessageCircle className="h-4 w-4" />
                  Quiero ser asesor
                </Button>
              )}
              {!WHATSAPP_ENABLED && (
                <p className="text-xs text-[#8E8E8E] text-center">Canal de contacto próximamente disponible</p>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA BOTTOM ── */}
      <section className="relative py-24 px-6 bg-[#333333] text-center overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-[#00C2C0]/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="relative max-w-3xl mx-auto space-y-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 text-[#00C2C0] text-xs font-bold rounded-full">
            <Clock className="h-3 w-3" />
            Empieza hoy mismo
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight">
            ¿Listo para transformar tu gestión de repuestos?
          </h2>
          <p className="text-white/70 max-w-xl mx-auto text-base">
            Accedé al panel operativo asignado a tu rol.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-2">
            <Button
              size="lg"
              className="bg-[#00D248] text-white hover:bg-[#00D248]/95 text-base px-8 py-6 gap-2 rounded-2xl font-bold shadow-[0_8px_20px_rgba(0,210,72,0.3)]"
              onClick={() => navigate('/login')}
            >
              Acceso Administrador
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="border-white/20 text-white bg-white/5 hover:bg-white/10 hover:text-white text-base px-8 py-6 gap-2 rounded-2xl font-bold"
              asChild
            >
              <a href="https://advisor.teloo.cloud/" target="_blank" rel="noopener noreferrer">
                Acceso Asesor Certificado
                <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="bg-[#1E1E1E] border-t border-white/5 py-12 px-8 text-white/50 text-xs">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <img src={logo} alt="TeLOO" className="h-7 w-auto opacity-80 brightness-0 invert" />
            <span className="text-white/20 border-l border-white/10 pl-3">Marketplace de Repuestos</span>
          </div>
          <div className="flex gap-6 text-white/60">
            <a href="#" className="hover:text-white transition-colors">Términos de Servicio</a>
            <a href="#" className="hover:text-white transition-colors">Política de Privacidad</a>
            <a href="#" className="hover:text-white transition-colors">Soporte PQR</a>
          </div>
          <span>© {new Date().getFullYear()} TeLOO. Todos los derechos reservados.</span>
        </div>
      </footer>

    </div>
  );
}
