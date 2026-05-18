import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LandingPage } from '@/pages/LandingPage';
import { useBranding } from '@/contexts/BrandingContext';

vi.mock('@/contexts/BrandingContext', () => ({
  useBranding: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('LandingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useBranding).mockReturnValue({ logoUrl: null, nombreEmpresa: 'TeLOO' });
  });

  describe('REQ-1: Logo dinámico', () => {
    it('usa logoUrl del BrandingContext cuando está disponible', () => {
      vi.mocked(useBranding).mockReturnValue({ logoUrl: 'https://cdn.test/logo.png', nombreEmpresa: 'TeLOO' });

      render(<TestWrapper><LandingPage /></TestWrapper>);

      const logos = screen.getAllByAltText('TeLOO');
      expect(logos[0]).toHaveAttribute('src', 'https://cdn.test/logo.png');
    });

    it('usa /Logo.png como fallback cuando logoUrl es null', () => {
      vi.mocked(useBranding).mockReturnValue({ logoUrl: null, nombreEmpresa: 'TeLOO' });

      render(<TestWrapper><LandingPage /></TestWrapper>);

      const logos = screen.getAllByAltText('TeLOO');
      expect(logos[0]).toHaveAttribute('src', '/Logo.png');
    });
  });

  describe('REQ-2: Hero h1 legible', () => {
    it('el h1 contiene el texto principal de la landing', () => {
      render(<TestWrapper><LandingPage /></TestWrapper>);

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Repuestos listos en');
    });
  });

  describe('REQ-3: CTA Advisor semántico', () => {
    it('el CTA de asesores es un <a> con href y target="_blank"', () => {
      render(<TestWrapper><LandingPage /></TestWrapper>);

      const advisorLink = screen.getByRole('link', { name: /Portal de Asesores/i });
      expect(advisorLink).toHaveAttribute('href', 'https://advisor.teloo.cloud/');
      expect(advisorLink).toHaveAttribute('target', '_blank');
      expect(advisorLink).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  describe('REQ-4: Light mode forzado', () => {
    it('el wrapper raíz tiene la clase light', () => {
      const { container } = render(<TestWrapper><LandingPage /></TestWrapper>);

      expect(container.firstChild).toHaveClass('light');
    });
  });
});
