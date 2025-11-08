import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Download, FileSpreadsheet, AlertCircle, CheckCircle, X } from 'lucide-react';
import * as XLSX from 'xlsx';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ofertasService } from '@/services/ofertas';

interface CargaMasivaModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface ExcelRow {
  solicitud_id: string;
  repuesto_nombre: string;
  precio_unitario: number;
  garantia_meses: number;
  tiempo_entrega_dias: number;
  observaciones?: string;
  error?: string;
}

export default function CargaMasivaModal({ open, onClose, onSuccess }: CargaMasivaModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<ExcelRow[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<{ success: boolean; message: string } | null>(
    null
  );

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setFile(file);
    setError(null);
    setUploadResult(null);
    processExcelFile(file);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024, // 5MB
  });

  const processExcelFile = async (file: File) => {
    setIsProcessing(true);
    setError(null);

    try {
      const data = await file.arrayBuffer();
      const workbook = XLSX.read(data);
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json<any>(worksheet);

      // Validate and transform data
      const rows: ExcelRow[] = jsonData.map((row) => {
        const errors: string[] = [];

        // Validate required fields
        if (!row.solicitud_id) errors.push('solicitud_id requerido');
        if (!row.repuesto_nombre) errors.push('repuesto_nombre requerido');
        if (!row.precio_unitario) errors.push('precio_unitario requerido');
        if (!row.garantia_meses) errors.push('garantia_meses requerido');
        if (!row.tiempo_entrega_dias) errors.push('tiempo_entrega_dias requerido');

        // Validate ranges
        const precio = parseFloat(row.precio_unitario);
        if (isNaN(precio) || precio < 1000 || precio > 50000000) {
          errors.push('precio debe estar entre 1,000 y 50,000,000');
        }

        const garantia = parseInt(row.garantia_meses);
        if (isNaN(garantia) || garantia < 1 || garantia > 60) {
          errors.push('garantía debe estar entre 1 y 60 meses');
        }

        const tiempo = parseInt(row.tiempo_entrega_dias);
        if (isNaN(tiempo) || tiempo < 0 || tiempo > 90) {
          errors.push('tiempo de entrega debe estar entre 0 y 90 días');
        }

        return {
          solicitud_id: row.solicitud_id,
          repuesto_nombre: row.repuesto_nombre,
          precio_unitario: precio,
          garantia_meses: garantia,
          tiempo_entrega_dias: tiempo,
          observaciones: row.observaciones,
          error: errors.length > 0 ? errors.join(', ') : undefined,
        };
      });

      setPreviewData(rows);
    } catch (err) {
      setError('Error al procesar el archivo Excel. Verifique el formato.');
      console.error('Error processing Excel:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadTemplate = () => {
    const template = [
      {
        solicitud_id: 'SOL-001',
        repuesto_nombre: 'Filtro de aceite',
        precio_unitario: 45000,
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

    const ws = XLSX.utils.json_to_sheet(template);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Ofertas');
    XLSX.writeFile(wb, 'template_ofertas.xlsx');
  };

  const handleUpload = async () => {
    if (!file) return;

    const hasErrors = previewData.some((row) => row.error);
    if (hasErrors) {
      setError('Corrija los errores antes de enviar');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      // Group by solicitud_id and upload
      const solicitudIds = [...new Set(previewData.map((row) => row.solicitud_id))];
      
      for (const solicitudId of solicitudIds) {
        await ofertasService.uploadOfertaExcel(solicitudId, file);
      }

      setUploadResult({
        success: true,
        message: `Ofertas cargadas exitosamente para ${solicitudIds.length} solicitud(es)`,
      });

      setTimeout(() => {
        onSuccess();
        onClose();
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar las ofertas');
      console.error('Error uploading ofertas:', err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setPreviewData([]);
    setError(null);
    setUploadResult(null);
    onClose();
  };

  const validRows = previewData.filter((row) => !row.error).length;
  const errorRows = previewData.filter((row) => row.error).length;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Carga Masiva de Ofertas</DialogTitle>
          <DialogDescription>
            Suba un archivo Excel con sus ofertas para múltiples solicitudes
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Download Template */}
          <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="h-8 w-8 text-primary" />
              <div>
                <p className="font-medium">Plantilla de Excel</p>
                <p className="text-sm text-muted-foreground">
                  Descargue la plantilla para ver el formato requerido
                </p>
              </div>
            </div>
            <Button variant="outline" onClick={downloadTemplate}>
              <Download className="h-4 w-4 mr-2" />
              Descargar Plantilla
            </Button>
          </div>

          {/* Upload Area */}
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25 hover:border-primary/50'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            {isDragActive ? (
              <p className="text-lg font-medium">Suelte el archivo aquí...</p>
            ) : (
              <>
                <p className="text-lg font-medium mb-2">
                  Arrastre un archivo Excel o haga clic para seleccionar
                </p>
                <p className="text-sm text-muted-foreground">
                  Formatos soportados: .xlsx, .xls (máximo 5MB)
                </p>
              </>
            )}
          </div>

          {/* File Info */}
          {file && (
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5 text-primary" />
                <span className="font-medium">{file.name}</span>
                <span className="text-sm text-muted-foreground">
                  ({(file.size / 1024).toFixed(1)} KB)
                </span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  setFile(null);
                  setPreviewData([]);
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Processing */}
          {isProcessing && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Procesando archivo...</p>
            </div>
          )}

          {/* Preview */}
          {previewData.length > 0 && !isProcessing && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold">Vista Previa</h4>
                <div className="flex gap-2">
                  <Badge variant="success">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    {validRows} válidas
                  </Badge>
                  {errorRows > 0 && (
                    <Badge variant="destructive">
                      <AlertCircle className="h-3 w-3 mr-1" />
                      {errorRows} con errores
                    </Badge>
                  )}
                </div>
              </div>

              <div className="border rounded-lg overflow-hidden">
                <div className="max-h-64 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-muted sticky top-0">
                      <tr>
                        <th className="text-left p-2">Solicitud</th>
                        <th className="text-left p-2">Repuesto</th>
                        <th className="text-right p-2">Precio</th>
                        <th className="text-right p-2">Garantía</th>
                        <th className="text-right p-2">Tiempo</th>
                        <th className="text-left p-2">Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.map((row, index) => (
                        <tr
                          key={index}
                          className={row.error ? 'bg-destructive/10' : 'hover:bg-muted/50'}
                        >
                          <td className="p-2">{row.solicitud_id}</td>
                          <td className="p-2">{row.repuesto_nombre}</td>
                          <td className="p-2 text-right">${row.precio_unitario?.toLocaleString()}</td>
                          <td className="p-2 text-right">{row.garantia_meses}m</td>
                          <td className="p-2 text-right">{row.tiempo_entrega_dias}d</td>
                          <td className="p-2">
                            {row.error ? (
                              <span className="text-xs text-destructive">{row.error}</span>
                            ) : (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md flex items-start gap-2">
              <AlertCircle className="h-4 w-4 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Success Message */}
          {uploadResult && uploadResult.success && (
            <div className="p-3 text-sm text-green-800 bg-green-100 rounded-md flex items-start gap-2">
              <CheckCircle className="h-4 w-4 mt-0.5" />
              <span>{uploadResult.message}</span>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isUploading}>
            Cancelar
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!file || previewData.length === 0 || errorRows > 0 || isUploading}
          >
            {isUploading ? 'Cargando...' : `Cargar ${validRows} Oferta(s)`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
