/**
 * Repuestos Step - Second step with manual entry and Excel upload
 */

import { useState } from "react";
import { Plus, Upload, Trash2, FileSpreadsheet } from "lucide-react";
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

    try {
      // TODO: Implement Excel parsing with xlsx library
      setExcelError("Funcionalidad de Excel en desarrollo. Use entrada manual por ahora.");
    } catch (error) {
      setExcelError("Error al procesar el archivo Excel");
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
            <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
            <div>
              <h4 className="font-medium">Cargar desde Excel</h4>
              <p className="text-sm text-muted-foreground">
                Sube un archivo Excel con los repuestos. Formato esperado:
              </p>
            </div>
            
            <div className="text-xs text-left bg-muted p-3 rounded">
              <strong>Columnas requeridas:</strong><br />
              Nombre | Marca Vehículo | Línea | Año | Cantidad | Observaciones
            </div>

            <Input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleExcelUpload}
              className="cursor-pointer"
            />

            {excelError && (
              <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <p className="text-sm text-yellow-800">{excelError}</p>
              </div>
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
