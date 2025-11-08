import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import CargaMasivaModal from '../ofertas/CargaMasivaModal';
import { ofertasService } from '@/services/ofertas';
import * as XLSX from 'xlsx';

// Mock the ofertas service
vi.mock('@/services/ofertas', () => ({
  ofertasService: {
    uploadOfertaExcel: vi.fn(),
  },
}));

// Mock XLSX
vi.mock('xlsx', () => ({
  default: {
    read: vi.fn(),
    utils: {
      sheet_to_json: vi.fn(),
      json_to_sheet: vi.fn(),
      book_new: vi.fn(),
      book_append_sheet: vi.fn(),
    },
    writeFile: vi.fn(),
  },
}));

describe('CargaMasivaModal', () => {
  const mockOnClose = vi.fn();
  const mockOnSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders modal with upload area', () => {
    render(
      <CargaMasivaModal
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    expect(screen.getByText(/Carga Masiva de Ofertas/i)).toBeInTheDocument();
    expect(screen.getByText(/Arrastre un archivo Excel/i)).toBeInTheDocument();
    expect(screen.getByText(/Descargar Plantilla/i)).toBeInTheDocument();
  });

  it('downloads template when button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <CargaMasivaModal
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const downloadButton = screen.getByRole('button', { name: /Descargar Plantilla/i });
    await user.click(downloadButton);

    expect(XLSX.utils.json_to_sheet).toHaveBeenCalled();
    expect(XLSX.writeFile).toHaveBeenCalled();
  });

  it('processes valid Excel file and shows preview', async () => {
    const mockExcelData = [
      {
        solicitud_id: 'SOL-001',
        repuesto_nombre: 'Filtro de aceite',
        precio_unitario: 50000,
        garantia_meses: 12,
        tiempo_entrega_dias: 3,
        observaciones: 'Original',
      },
      {
        solicitud_id: 'SOL-001',
        repuesto_nombre: 'Pastillas de freno',
        precio_unitario: 120000,
        garantia_meses: 24,
        tiempo_entrega_dias: 3,
        observaciones: '',
      },
    ];

    vi.mocked(XLSX.read).mockReturnValue({
      SheetNames: ['Ofertas'],
      Sheets: { Ofertas: {} },
    } as any);

    vi.mocked(XLSX.utils.sheet_to_json).mockReturnValue(mockExcelData);

    render(
      <CargaMasivaModal
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Create a mock file
    const file = new File([''], 'ofertas.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const input = screen.getByRole('button', { name: /Arrastre un archivo Excel/i }).querySelector('input');
    
    if (input) {
      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });
      fireEvent.change(input);
    }

    await waitFor(() => {
      expect(screen.getByText(/Vista Previa/i)).toBeInTheDocument();
      expect(screen.getByText(/2 válidas/i)).toBeInTheDocument();
      expect(screen.getByText(/Filtro de aceite/i)).toBeInTheDocument();
      expect(screen.getByText(/Pastillas de freno/i)).toBeInTheDocument();
    });
  });

  it('validates Excel data and shows errors', async () => {
    const mockExcelData = [
      {
        solicitud_id: 'SOL-001',
        repuesto_nombre: 'Filtro de aceite',
        precio_unitario: 500, // Invalid: too low
        garantia_meses: 12,
        tiempo_entrega_dias: 3,
      },
      {
        solicitud_id: 'SOL-001',
        repuesto_nombre: 'Pastillas de freno',
        precio_unitario: 120000,
        garantia_meses: 70, // Invalid: too high
        tiempo_entrega_dias: 3,
      },
    ];

    vi.mocked(XLSX.read).mockReturnValue({
      SheetNames: ['Ofertas'],
      Sheets: { Ofertas: {} },
    } as any);

    vi.mocked(XLSX.utils.sheet_to_json).mockReturnValue(mockExcelData);

    render(
      <CargaMasivaModal
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const file = new File([''], 'ofertas.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const input = screen.getByRole('button', { name: /Arrastre un archivo Excel/i }).querySelector('input');
    
    if (input) {
      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });
      fireEvent.change(input);
    }

    await waitFor(() => {
      expect(screen.getByText(/2 con errores/i)).toBeInTheDocument();
      expect(screen.getByText(/precio debe estar entre/i)).toBeInTheDocument();
      expect(screen.getByText(/garantía debe estar entre/i)).toBeInTheDocument();
    });
  });

  it('validates required fields in Excel data', async () => {
    const mockExcelData = [
      {
        solicitud_id: '',
        repuesto_nombre: 'Filtro de aceite',
        precio_unitario: 50000,
        garantia_meses: 12,
        tiempo_entrega_dias: 3,
      },
    ];

    vi.mocked(XLSX.read).mockReturnValue({
      SheetNames: ['Ofertas'],
      Sheets: { Ofertas: {} },
    } as any);

    vi.mocked(XLSX.utils.sheet_to_json).mockReturnValue(mockExcelData);

    render(
      <CargaMasivaModal
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const file = new File([''], 'ofertas.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const input = screen.getByRole('button', { name: /Arrastre un archivo Excel/i }).querySelector('input');
    
    if (input) {
      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });
      fireEvent.change(input);
    }

    await waitFor(() => {
      expect(screen.getByText(/solicitud_id requerido/i)).toBeInTheDocument();
    });
  });

  it('uploads valid Excel file successfully', async () => {
    const user = userEvent.setup();
    const mockExcelData = [
      {
        solicitud_id: 'SOL-001',
        repuesto_nombre: 'Filtro de aceite',
        precio_unitario: 50000,
        garantia_meses: 12,
        tiempo_entrega_dias: 3,
      },
    ];

    vi.mocked(XLSX.read).mockReturnValue({
      SheetNames: ['Ofertas'],
      Sheets: { Ofertas: {} },
    } as any);

    vi.mocked(XLSX.utils.sheet_to_json).mockReturnValue(mockExcelData);
    vi.mocked(ofertasService.uploadOfertaExcel).mockResolvedValue({} as any);

    render(
      <CargaMasivaModal
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const file = new File([''], 'ofertas.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const input = screen.getByRole('button', { name: /Arrastre un archivo Excel/i }).querySelector('input');
    
    if (input) {
      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });
      fireEvent.change(input);
    }

    await waitFor(() => {
      expect(screen.getByText(/1 válidas/i)).toBeInTheDocument();
    });

    const uploadButton = screen.getByRole('button', { name: /Cargar 1 Oferta/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(ofertasService.uploadOfertaExcel).toHaveBeenCalledWith('SOL-001', file);
      expect(screen.getByText(/Ofertas cargadas exitosamente/i)).toBeInTheDocument();
    });

    // Wait for auto-close
    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    }, { timeout: 3000 });
  });

  it('prevents upload when there are validation errors', async () => {
    const user = userEvent.setup();
    const mockExcelData = [
      {
        solicitud_id: 'SOL-001',
        repuesto_nombre: 'Filtro de aceite',
        precio_unitario: 500, // Invalid
        garantia_meses: 12,
        tiempo_entrega_dias: 3,
      },
    ];

    vi.mocked(XLSX.read).mockReturnValue({
      SheetNames: ['Ofertas'],
      Sheets: { Ofertas: {} },
    } as any);

    vi.mocked(XLSX.utils.sheet_to_json).mockReturnValue(mockExcelData);

    render(
      <CargaMasivaModal
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const file = new File([''], 'ofertas.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const input = screen.getByRole('button', { name: /Arrastre un archivo Excel/i }).querySelector('input');
    
    if (input) {
      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });
      fireEvent.change(input);
    }

    await waitFor(() => {
      expect(screen.getByText(/1 con errores/i)).toBeInTheDocument();
    });

    const uploadButton = screen.getByRole('button', { name: /Cargar 0 Oferta/i });
    expect(uploadButton).toBeDisabled();
  });

  it('displays error message on upload failure', async () => {
    const user = userEvent.setup();
    const errorMessage = 'Error al cargar las ofertas';
    const mockExcelData = [
      {
        solicitud_id: 'SOL-001',
        repuesto_nombre: 'Filtro de aceite',
        precio_unitario: 50000,
        garantia_meses: 12,
        tiempo_entrega_dias: 3,
      },
    ];

    vi.mocked(XLSX.read).mockReturnValue({
      SheetNames: ['Ofertas'],
      Sheets: { Ofertas: {} },
    } as any);

    vi.mocked(XLSX.utils.sheet_to_json).mockReturnValue(mockExcelData);
    vi.mocked(ofertasService.uploadOfertaExcel).mockRejectedValue({
      response: { data: { detail: errorMessage } },
    });

    render(
      <CargaMasivaModal
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const file = new File([''], 'ofertas.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const input = screen.getByRole('button', { name: /Arrastre un archivo Excel/i }).querySelector('input');
    
    if (input) {
      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });
      fireEvent.change(input);
    }

    await waitFor(() => {
      expect(screen.getByText(/1 válidas/i)).toBeInTheDocument();
    });

    const uploadButton = screen.getByRole('button', { name: /Cargar 1 Oferta/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('allows removing uploaded file', async () => {
    const user = userEvent.setup();
    const mockExcelData = [
      {
        solicitud_id: 'SOL-001',
        repuesto_nombre: 'Filtro de aceite',
        precio_unitario: 50000,
        garantia_meses: 12,
        tiempo_entrega_dias: 3,
      },
    ];

    vi.mocked(XLSX.read).mockReturnValue({
      SheetNames: ['Ofertas'],
      Sheets: { Ofertas: {} },
    } as any);

    vi.mocked(XLSX.utils.sheet_to_json).mockReturnValue(mockExcelData);

    render(
      <CargaMasivaModal
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const file = new File([''], 'ofertas.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const input = screen.getByRole('button', { name: /Arrastre un archivo Excel/i }).querySelector('input');
    
    if (input) {
      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false,
      });
      fireEvent.change(input);
    }

    await waitFor(() => {
      expect(screen.getByText(/ofertas.xlsx/i)).toBeInTheDocument();
    });

    // Find and click the remove button (X icon)
    const removeButtons = screen.getAllByRole('button');
    const removeButton = removeButtons.find(btn => btn.querySelector('svg'));
    if (removeButton) {
      await user.click(removeButton);
    }

    await waitFor(() => {
      expect(screen.queryByText(/ofertas.xlsx/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Vista Previa/i)).not.toBeInTheDocument();
    });
  });
});
