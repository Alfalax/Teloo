import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Upload, Download, FileSpreadsheet, AlertCircle, CheckCircle } from 'lucide-react';
import { asesoresService } from '@/services/asesores';
import { ExcelImportResult } from '@/types/asesores';

interface ExcelImportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onImportComplete: () => void;
}

export function ExcelImportDialog({
  isOpen,
  onClose,
  onImportComplete,
}: ExcelImportDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDownloadingTemplate, setIsDownloadingTemplate] = useState(false);
  const [importResult, setImportResult] = useState<ExcelImportResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
      }
    }
  };

  const validateFile = (file: File): boolean => {
    const validTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel'
    ];
    
    if (!validTypes.includes(file.type)) {
      alert('Por favor selecciona un archivo Excel válido (.xlsx o .xls)');
      return false;
    }

    if (file.size > 5 * 1024 * 1024) { // 5MB
      alert('El archivo no puede ser mayor a 5MB');
      return false;
    }

    return true;
  };

  const handleDownloadTemplate = async () => {
    setIsDownloadingTemplate(true);
    try {
      const blob = await asesoresService.downloadTemplate();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'plantilla_asesores.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading template:', error);
      alert('Error al descargar la plantilla');
    } finally {
      setIsDownloadingTemplate(false);
    }
  };

  const handleImport = async () => {
    if (!file) return;

    setIsUploading(true);
    try {
      const result = await asesoresService.importExcel(file);
      setImportResult(result);
      
      if (result.success && result.exitosos > 0) {
        onImportComplete();
      }
    } catch (error: any) {
      console.error('Error importing file:', error);
      setImportResult({
        success: false,
        message: error.response?.data?.detail || 'Error al importar el archivo',
        total_procesados: 0,
        exitosos: 0,
        errores: 0,
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setImportResult(null);
    onClose();
  };

  const resetForm = () => {
    setFile(null);
    setImportResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            Importar Asesores desde Excel
          </DialogTitle>
        </DialogHeader>
        <DialogDescription>
          Sube un archivo Excel con la información de los asesores para importar masivamente.
        </DialogDescription>

        <div className="space-y-4">
          {/* Download Template Button */}
          <div className="flex justify-center">
            <Button
              variant="outline"
              onClick={handleDownloadTemplate}
              disabled={isDownloadingTemplate}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              {isDownloadingTemplate ? 'Descargando...' : 'Descargar Plantilla'}
            </Button>
          </div>

          {/* File Upload Area */}
          {!importResult && (
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                dragActive
                  ? 'border-primary bg-primary/5'
                  : 'border-muted-foreground/25 hover:border-muted-foreground/50'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              {file ? (
                <div className="space-y-2">
                  <FileSpreadsheet className="h-8 w-8 mx-auto text-green-600" />
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={resetForm}
                  >
                    Cambiar archivo
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
                  <p className="text-sm">
                    Arrastra tu archivo Excel aquí o{' '}
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="text-primary hover:underline"
                    >
                      selecciona un archivo
                    </button>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Formatos soportados: .xlsx, .xls (máximo 5MB)
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Import Result */}
          {importResult && (
            <div className="space-y-4">
              <div className={`p-4 rounded-lg border ${
                importResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  {importResult.success ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-600" />
                  )}
                  <h4 className="font-medium">
                    {importResult.success ? 'Importación Completada' : 'Error en Importación'}
                  </h4>
                </div>
                
                <p className="text-sm mb-3">{importResult.message}</p>
                
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Total:</span> {importResult.total_procesados}
                  </div>
                  <div>
                    <span className="font-medium text-green-600">Exitosos:</span> {importResult.exitosos}
                  </div>
                  <div>
                    <span className="font-medium text-red-600">Errores:</span> {importResult.errores}
                  </div>
                </div>

                {importResult.detalles_errores && importResult.detalles_errores.length > 0 && (
                  <div className="mt-3">
                    <h5 className="font-medium text-sm mb-2">Detalles de errores:</h5>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {importResult.detalles_errores.map((error, index) => (
                        <div key={index} className="text-xs bg-white p-2 rounded border">
                          <span className="font-medium">Fila {error.fila}:</span>{' '}
                          {error.errores.join(', ')}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-center">
                <Button onClick={resetForm} variant="outline">
                  Importar otro archivo
                </Button>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            {importResult ? 'Cerrar' : 'Cancelar'}
          </Button>
          {!importResult && (
            <Button
              onClick={handleImport}
              disabled={!file || isUploading}
            >
              {isUploading ? 'Importando...' : 'Importar'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}