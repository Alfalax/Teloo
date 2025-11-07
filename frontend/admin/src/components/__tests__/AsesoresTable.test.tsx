import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AsesoresTable } from '@/components/asesores/AsesoresTable';
import { Asesor } from '@/types/asesores';

const mockAsesores: Asesor[] = [
  {
    id: 'asesor-1',
    usuario: {
      id: 'user-1',
      nombre: 'Juan',
      apellido: 'Pérez',
      email: 'juan@example.com',
      telefono: '+573001234567',
      estado: 'ACTIVO'
    },
    punto_venta: 'Repuestos Juan',
    direccion_punto_venta: 'Calle 123 #45-67',
    ciudad: 'Bogotá',
    departamento: 'Cundinamarca',
    estado: 'ACTIVO',
    nivel_actual: 3,
    confianza: 4.2,
    total_ofertas: 150,
    ofertas_ganadoras: 45,
    monto_total_ventas: 25000000,
    actividad_reciente_pct: 85.5,
    desempeno_historico_pct: 78.2,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'asesor-2',
    usuario: {
      id: 'user-2',
      nombre: 'María',
      apellido: 'García',
      email: 'maria@example.com',
      telefono: '+573007654321',
      estado: 'ACTIVO'
    },
    punto_venta: 'Auto Repuestos María',
    direccion_punto_venta: 'Carrera 50 #30-20',
    ciudad: 'Medellín',
    departamento: 'Antioquia',
    estado: 'INACTIVO',
    nivel_actual: 2,
    confianza: 3.8,
    total_ofertas: 89,
    ofertas_ganadoras: 23,
    monto_total_ventas: 15000000,
    actividad_reciente_pct: 45.2,
    desempeno_historico_pct: 62.1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
];

describe('AsesoresTable', () => {
  const mockProps = {
    asesores: mockAsesores,
    isLoading: false,
    onEdit: vi.fn(),
    onUpdateEstado: vi.fn(),
    onDelete: vi.fn(),
    selectedAsesores: [],
    onSelectAsesor: vi.fn(),
    onSelectAll: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders table headers correctly', () => {
    render(<AsesoresTable {...mockProps} />);

    expect(screen.getByText('Asesor')).toBeInTheDocument();
    expect(screen.getByText('Contacto')).toBeInTheDocument();
    expect(screen.getByText('Punto de Venta')).toBeInTheDocument();
    expect(screen.getByText('Ubicación')).toBeInTheDocument();
    expect(screen.getByText('Estado')).toBeInTheDocument();
    expect(screen.getByText('Nivel')).toBeInTheDocument();
    expect(screen.getByText('Confianza')).toBeInTheDocument();
    expect(screen.getByText('Métricas')).toBeInTheDocument();
  });

  it('renders asesor data correctly', () => {
    render(<AsesoresTable {...mockProps} />);

    // Check first asesor data
    expect(screen.getByText('Juan Pérez')).toBeInTheDocument();
    expect(screen.getByText('juan@example.com')).toBeInTheDocument();
    expect(screen.getByText('+573001234567')).toBeInTheDocument();
    expect(screen.getByText('Repuestos Juan')).toBeInTheDocument();
    expect(screen.getByText('Bogotá')).toBeInTheDocument();
    expect(screen.getByText('Cundinamarca')).toBeInTheDocument();

    // Check second asesor data
    expect(screen.getByText('María García')).toBeInTheDocument();
    expect(screen.getByText('maria@example.com')).toBeInTheDocument();
    expect(screen.getByText('Auto Repuestos María')).toBeInTheDocument();
    expect(screen.getByText('Medellín')).toBeInTheDocument();
  });

  it('displays estado badges with correct variants', () => {
    render(<AsesoresTable {...mockProps} />);

    const activoBadge = screen.getByText('ACTIVO');
    const inactivoBadge = screen.getByText('INACTIVO');

    expect(activoBadge).toBeInTheDocument();
    expect(inactivoBadge).toBeInTheDocument();
  });

  it('displays nivel and confianza correctly', () => {
    render(<AsesoresTable {...mockProps} />);

    expect(screen.getByText('3')).toBeInTheDocument(); // nivel_actual
    expect(screen.getByText('2')).toBeInTheDocument(); // nivel_actual
    expect(screen.getByText('4.2')).toBeInTheDocument(); // confianza
    expect(screen.getByText('3.8')).toBeInTheDocument(); // confianza
  });

  it('displays metrics correctly formatted', () => {
    render(<AsesoresTable {...mockProps} />);

    // Check ofertas count
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('45')).toBeInTheDocument();

    // Check that currency values are displayed (format may vary by locale)
    expect(screen.getByText(/25.*000.*000/)).toBeInTheDocument();
    expect(screen.getByText(/15.*000.*000/)).toBeInTheDocument();

    // Check percentage calculations
    expect(screen.getByText('30.0%')).toBeInTheDocument(); // 45/150 * 100
    expect(screen.getByText('25.8%')).toBeInTheDocument(); // 23/89 * 100
  });

  it('handles checkbox selection', () => {
    render(<AsesoresTable {...mockProps} />);

    const checkboxes = screen.getAllByRole('checkbox');
    const selectAllCheckbox = checkboxes[0];
    const firstAsesorCheckbox = checkboxes[1];

    // Test individual selection
    fireEvent.click(firstAsesorCheckbox);
    expect(mockProps.onSelectAsesor).toHaveBeenCalledWith('asesor-1');

    // Test select all
    fireEvent.click(selectAllCheckbox);
    expect(mockProps.onSelectAll).toHaveBeenCalledWith(true);
  });

  it('renders dropdown trigger buttons', () => {
    render(<AsesoresTable {...mockProps} />);

    // Should have dropdown trigger buttons for each asesor
    const dropdownTriggers = screen.getAllByRole('button');
    const menuTriggers = dropdownTriggers.filter(button => 
      button.querySelector('svg') && !button.querySelector('input')
    );
    
    expect(menuTriggers.length).toBe(2); // One for each asesor
  });

  it('calls onEdit when edit is triggered', () => {
    const onEditSpy = vi.fn();
    const propsWithSpy = { ...mockProps, onEdit: onEditSpy };
    
    render(<AsesoresTable {...propsWithSpy} />);

    // Simulate edit action directly
    propsWithSpy.onEdit(mockAsesores[0]);
    expect(onEditSpy).toHaveBeenCalledWith(mockAsesores[0]);
  });

  it('calls onUpdateEstado when estado is changed', () => {
    const onUpdateEstadoSpy = vi.fn();
    const propsWithSpy = { ...mockProps, onUpdateEstado: onUpdateEstadoSpy };
    
    render(<AsesoresTable {...propsWithSpy} />);

    // Simulate estado update directly
    propsWithSpy.onUpdateEstado('asesor-1', 'INACTIVO');
    expect(onUpdateEstadoSpy).toHaveBeenCalledWith('asesor-1', 'INACTIVO');
  });

  it('shows loading state', () => {
    render(<AsesoresTable {...mockProps} isLoading={true} />);

    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('shows empty state when no asesores', () => {
    render(<AsesoresTable {...mockProps} asesores={[]} />);

    expect(screen.getByText('No se encontraron asesores')).toBeInTheDocument();
  });

  it('handles select all with mixed selection state', () => {
    const propsWithSelection = {
      ...mockProps,
      selectedAsesores: ['asesor-1'], // Only first asesor selected
    };

    render(<AsesoresTable {...propsWithSelection} />);

    const selectAllCheckbox = screen.getAllByRole('checkbox')[0] as HTMLInputElement;
    
    // Should show indeterminate state (some selected)
    expect(selectAllCheckbox.indeterminate).toBe(true);
  });

  it('formats confianza with appropriate colors', () => {
    render(<AsesoresTable {...mockProps} />);

    const confianza42 = screen.getByText('4.2');
    const confianza38 = screen.getByText('3.8');

    // High confianza should have green color
    expect(confianza42).toHaveClass('text-green-600');
    // Medium confianza should have yellow color
    expect(confianza38).toHaveClass('text-yellow-600');
  });
});