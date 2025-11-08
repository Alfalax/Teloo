/**
 * Repuestos Step - Second step with manual entry and Excel upload
 */

import { useState } from "react";
import { Plus, Upload, Trash2, FileSpreadsheet, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import * as XLSX from 'xlsx';
import type { RepuestoSolicitado } from "@/types/solicitudes";

interface RepuestosStepProps {
  repuestos: Omit<RepuestoSolicitado, "id">[];
  onChange: (repuestos: Omit<RepuestoSolicitado, "id">[]) => void;
  onPrevious: () => void;
  onSubmit: () => void;
  isValid: boolean;
  loading: boolean;
}

const initialRepuesto: Omit<RepuestoSolicitado, "id"> = {
  nombre: "",
  codigo: "",
  descripcion: "",
  cantidad: 1,
  marca_vehiculo: "",
  linea_vehiculo: "",
  anio_vehiculo: new Date().getFullYear(),
  observaciones: "",
  es_urgente: false,
};

export function RepuestosStep({
  repuestos,
  onChange,
  onPrevious,
  onSubmit,
  isValid,
  loading,
}: RepuestosStepProps) {
  const [currentRepuesto, setCurrentRepuesto] = useState<Omit<RepuestoSolicitado, "id">>(initialRepuesto);
  const [activeTab, setActiveTab] = useState("manual");
  const [excelError, setExcelError] = useState<string | null>(null);
  const [excelSuccess, setExcelSuccess] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleAddRepuesto = () => {
    if (!currentRepuesto.nombre.trim() || !currentRepuesto.marca_vehiculo.trim()) {
      return;
    }

    onChange([...repuestos, { ...currentRepuesto }]);
    setCurrentRepuesto(initialRepuesto);
  };

  const handleRemoveRepuesto = (index: number) => {
    const newRepuestos = repuestos.filter((_, i) => i !== index);
    onChange(newRepuestos);
  };

  const handleExcelUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setExcelError(null);
    setExcelSuccess(null);
    setIsProcessing(true);

    try {
      const data = await file.arrayBuffer();
      const workbook = XLSX.read(data);
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      if (jsonData.length === 0) {
        setExcelError("El archivo Excel está vacío");
        setIsProcessing(false);
        return;
      }

      const parsedRepuestos: Omit<RepuestoSolicitado, "id">[] = [];
      const errors: string[] = [];

      jsonData.forEach((row: any, index: number) => {
        const rowNum = index + 2; // +2 porque Excel empieza en 1 y tiene header

        // Validar campos requeridos
        if (!row.Nombre && !row.nombre) {
          errors.push(`Fila ${rowNum}: Falta el nombre del repuesto`);
          return;
        }

        if (!row["Marca Vehiculo"] && !row["Marca Vehículo"] && !row.marca_vehiculo) {
          errors.push(`Fila ${rowNum}: Falta la marca del vehículo`);
          return;
        }

        // Extraer y validar datos
        const nombre = (row.Nombre || row.nombre || "").toString().trim();
        const codigo = (row.Codigo || row.Código || row.codigo || "").toString().trim();
        const marcaVehiculo = (row["Marca Vehiculo"] || row["Marca Vehículo"] || row.marca_vehiculo || "").toString().trim();
        const lineaVehiculo = (row.Linea || row.Línea || row.linea || row.linea_vehiculo || "").toString().trim();
        const anioVehiculo = parseInt(row.Año || row.Anio || row.año || row.anio || row.anio_vehiculo || new Date().getFullYear());
        const cantidad = parseInt(row.Cantidad || row.cantidad || "1");
        const observaciones = (row.Observaciones || row.observaciones || "").toString().trim();
        const esUrgente = row.Urgente === "SI" || row.Urgente === "Sí" || row.urgente === "SI" || row.es_urgente === true;

        // Validar año
        if (anioVehiculo < 1980 || anioVehiculo > new Date().getFullYear() + 1) {
          errors.push(`Fila ${rowNum}: Año inválido (${anioVehiculo}). Debe estar entre 1980 y ${new Date().getFullYear() + 1}`);
          return;
        }

        // Validar cantidad
        if (isNaN(cantidad) || cantidad < 1) {
          errors.push(`Fila ${rowNum}: Cantidad inválida. Debe ser mayor a 0`);
          return;
        }

        parsedRepuestos.push({
          nombre,
          codigo: codigo || undefined,
          descripcion: observaciones || undefined,
          cantidad,
          marca_vehiculo: marcaVehiculo,
          linea_vehiculo: lineaVehiculo || undefined,
          anio_vehiculo: anioVehiculo,
          observaciones: observaciones || undefined,
          es_urgente: esUrgente,
        });
      });

      if (errors.length > 0) {
        setExcelError(`Se encontraron ${errors.length} errores:\n${errors.slice(0, 5).join("\n")}${errors.length > 5 ? `\n... y ${errors.length - 5} más` : ""}`);
        setIsProcessing(false);
        return;
      }

      if (parsedRepuestos.length === 0) {
        setExcelError("No se pudieron extraer repuestos válidos del archivo");
        setIsProcessing(false);
        return;
      }

      // Agregar los repuestos parseados a la lista existente
      onChange([...repuestos, ...parsedRepuestos]);
      setExcelSuccess(`✓ Se importaron ${parsedRepuestos.length} repuesto(s) exitosamente`);
      
      // Limpiar el input file
      event.target.value = "";
      
      // Cambiar a tab manual para ver los resultados
      setTimeout(() => {
        setActiveTab("manual");
      }, 1500);

    } catch (error) {
      console.error("Error al procesar Excel:", error);
      setExcelError("Error al procesar el archivo Excel. Verifique que el formato sea correcto.");
    } finally {
      setIsProcessing(false);
    }
  };

  const isCurrentRepuestoValid = () => {
    return (
      currentRepuesto.nombre.trim() !== "" &&
      currentRepuesto.marca_vehiculo.trim() !== "" &&
      currentRepuesto.cantidad > 0 &&
      currentRepuesto.anio_vehiculo >= 1980 &&
      currentRepuesto.anio_vehiculo <= new Date().getFullYear() + 1
    );
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold">Repuestos Solicitados</h3>
        <p className="text-muted-foreground">
          Agrega los repuestos manualmente o carga un archivo Excel
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="manual">
            <Plus className="h-4 w-4 mr-2" />
            Manual
          </TabsTrigger>
          <TabsTrigger value="excel">
            <FileSpreadsheet className="h-4 w-4 mr-2" />
            Excel
          </TabsTrigger>
        </TabsList>

        {/* Manual Entry Tab */}
        <TabsContent value="manual" className="space-y-4">
          <div className="border rounded-lg p-4 space-y-4">
            <h4 className="font-medium">Agregar Repuesto</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="nombre">Nombre del Repuesto *</Label>
                <Input
                  id="nombre"
                  placeholder="Ej: Pastillas de freno"
                  value={currentRepuesto.nombre}
                  onChange={(e) => setCurrentRepuesto({ ...currentRepuesto, nombre: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="codigo">Código (Opcional)</Label>
                <Input
                  id="codigo"
                  placeholder="Ej: BR-001"
                  value={currentRepuesto.codigo || ""}
                  onChange={(e) => setCurrentRepuesto({ ...currentRepuesto, codigo: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="cantidad">Cantidad *</Label>
                <Input
                  id="cantidad"
                  type="number"
                  min="1"
                  value={currentRepuesto.cantidad}
                  onChange={(e) => setCurrentRepuesto({ ...currentRepuesto, cantidad: parseInt(e.target.value) || 1 })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="marca">Marca Vehículo *</Label>
                <Input
                  id="marca"
                  placeholder="Ej: Toyota"
                  value={currentRepuesto.marca_vehiculo}
                  onChange={(e) => setCurrentRepuesto({ ...currentRepuesto, marca_vehiculo: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="linea">Línea Vehículo</Label>
                <Input
                  id="linea"
                  placeholder="Ej: Corolla"
                  value={currentRepuesto.linea_vehiculo}
                  onChange={(e) => setCurrentRepuesto({ ...currentRepuesto, linea_vehiculo: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="anio">Año Vehículo</Label>
                <Input
                  id="anio"
                  type="number"
                  min="1980"
                  max={new Date().getFullYear() + 1}
                  value={currentRepuesto.anio_vehiculo}
                  onChange={(e) => setCurrentRepuesto({ ...currentRepuesto, anio_vehiculo: parseInt(e.target.value) || new Date().getFullYear() })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="observaciones">Observaciones</Label>
              <Textarea
                id="observaciones"
                placeholder="Información adicional sobre el repuesto..."
                value={currentRepuesto.observaciones || ""}
                onChange={(e) => setCurrentRepuesto({ ...currentRepuesto, observaciones: e.target.value })}
                rows={2}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="urgente"
                checked={currentRepuesto.es_urgente}
                onCheckedChange={(checked) => setCurrentRepuesto({ ...currentRepuesto, es_urgente: !!checked })}
              />
              <Label htmlFor="urgente">Es urgente</Label>
            </div>

            <Button
              onClick={handleAddRepuesto}
              disabled={!isCurrentRepuestoValid()}
              className="w-full"
            >
              <Plus className="h-4 w-4 mr-2" />
              Agregar Repuesto
            </Button>
          </div>
        </TabsContent>

        {/* Excel Upload Tab */}
        <TabsContent value="excel" className="space-y-4">
          <div className="border rounded-lg p-6 text-center space-y-4">
            {!isProcessing && !excelSuccess && (
              <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
            )}
            {isProcessing && (
              <div className="h-12 w-12 mx-auto border-4 border-primary border-t-transparent rounded-full animate-spin" />
            )}
            {excelSuccess && (
              <CheckCircle2 className="h-12 w-12 mx-auto text-green-500" />
            )}
            
            <div>
              <h4 className="font-medium">Cargar desde Excel</h4>
              <p className="text-sm text-muted-foreground">
                Sube un archivo Excel (.xlsx o .xls) con los repuestos
              </p>
            </div>
            
            <div className="text-xs text-left bg-muted p-4 rounded space-y-2">
              <strong>Columnas esperadas (pueden variar en mayúsculas/minúsculas):</strong>
              <ul className="list-disc list-inside space-y-1 mt-2">
                <li><strong>Nombre</strong> (requerido): Nombre del repuesto</li>
                <li><strong>Marca Vehiculo</strong> (requerido): Marca del vehículo</li>
                <li><strong>Linea</strong> (opcional): Línea del vehículo</li>
                <li><strong>Año</strong> (opcional): Año del vehículo (1980-{new Date().getFullYear() + 1})</li>
                <li><strong>Cantidad</strong> (opcional): Cantidad solicitada (default: 1)</li>
                <li><strong>Codigo</strong> (opcional): Código del repuesto</li>
                <li><strong>Observaciones</strong> (opcional): Notas adicionales</li>
                <li><strong>Urgente</strong> (opcional): "SI" o "NO"</li>
              </ul>
            </div>

            <div className="space-y-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => {
                  // Crear un Excel de ejemplo programáticamente
                  const wb = XLSX.utils.book_new();
                  const wsData = [
                    ["Nombre", "Marca Vehiculo", "Linea", "Año", "Cantidad", "Codigo", "Observaciones", "Urgente"],
                    ["Pastillas de freno delanteras", "Toyota", "Corolla", "2015", "2", "BR-001", "Cerámicas", "NO"],
                    ["Filtro de aceite", "Honda", "Civic", "2018", "1", "FO-123", "Original", "SI"],
                    ["Amortiguadores traseros", "Chevrolet", "Spark", "2020", "2", "", "Par completo", "NO"],
                  ];
                  const ws = XLSX.utils.aoa_to_sheet(wsData);
                  XLSX.utils.book_append_sheet(wb, ws, "Repuestos");
                  XLSX.writeFile(wb, "template-repuestos.xlsx");
                }}
              >
                <FileSpreadsheet className="h-4 w-4 mr-2" />
                Descargar Template Excel
              </Button>
              
              <Input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleExcelUpload}
                className="cursor-pointer"
                disabled={isProcessing}
              />
            </div>

            {excelError && (
              <div className="bg-red-50 border border-red-200 rounded p-3 text-left">
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-800">Error al procesar el archivo</p>
                    <p className="text-xs text-red-700 mt-1 whitespace-pre-line">{excelError}</p>
                  </div>
                </div>
              </div>
            )}

            {excelSuccess && (
              <div className="bg-green-50 border border-green-200 rounded p-3">
                <div className="flex items-center gap-2 justify-center">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  <p className="text-sm font-medium text-green-800">{excelSuccess}</p>
                </div>
              </div>
            )}

            {isProcessing && (
              <p className="text-sm text-muted-foreground">
                Procesando archivo Excel...
              </p>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Repuestos List */}
      {repuestos.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium">Repuestos Agregados ({repuestos.length})</h4>
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nombre</TableHead>
                  <TableHead>Marca/Línea</TableHead>
                  <TableHead>Año</TableHead>
                  <TableHead>Cant.</TableHead>
                  <TableHead>Urgente</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {repuestos.map((repuesto, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{repuesto.nombre}</div>
                        {repuesto.codigo && (
                          <div className="text-sm text-muted-foreground">
                            Código: {repuesto.codigo}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div>{repuesto.marca_vehiculo}</div>
                        {repuesto.linea_vehiculo && (
                          <div className="text-sm text-muted-foreground">
                            {repuesto.linea_vehiculo}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{repuesto.anio_vehiculo}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{repuesto.cantidad}</Badge>
                    </TableCell>
                    <TableCell>
                      {repuesto.es_urgente && (
                        <Badge variant="destructive">Urgente</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveRepuesto(index)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between pt-4 border-t">
        <Button variant="outline" onClick={onPrevious}>
          Anterior
        </Button>
        <Button
          onClick={onSubmit}
          disabled={!isValid || loading}
        >
          {loading ? "Creando..." : "Crear Solicitud"}
        </Button>
      </div>
    </div>
  );
}
