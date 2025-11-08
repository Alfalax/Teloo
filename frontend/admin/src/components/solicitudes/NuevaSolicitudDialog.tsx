/**
 * Nueva Solicitud Dialog - Multi-step wizard
 * Step 1: Cliente info
 * Step 2: Repuestos (manual + Excel)
 */

import { useState } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ClienteStep } from "./steps/ClienteStep";
import { RepuestosStep } from "./steps/RepuestosStep";
import { solicitudesService } from "@/services/solicitudes";
import type { CreateSolicitudData, RepuestoSolicitado } from "@/types/solicitudes";

interface NuevaSolicitudDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

interface ClienteData {
  nombre: string;
  telefono: string;
  email?: string;
  ciudad_origen: string;
  departamento_origen: string;
}

const initialClienteData: ClienteData = {
  nombre: "",
  telefono: "",
  email: "",
  ciudad_origen: "",
  departamento_origen: "",
};

export function NuevaSolicitudDialog({
  open,
  onOpenChange,
  onSuccess,
}: NuevaSolicitudDialogProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [clienteData, setClienteData] = useState<ClienteData>(initialClienteData);
  const [repuestos, setRepuestos] = useState<Omit<RepuestoSolicitado, "id">[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const steps = [
    { number: 1, title: "Cliente", description: "Información del cliente" },
    { number: 2, title: "Repuestos", description: "Repuestos solicitados" },
  ];

  const handleClose = () => {
    setCurrentStep(1);
    setClienteData(initialClienteData);
    setRepuestos([]);
    setError(null);
    onOpenChange(false);
  };

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    if (repuestos.length === 0) {
      setError("Debe agregar al menos un repuesto");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const data: CreateSolicitudData = {
        cliente: {
          nombre: clienteData.nombre,
          telefono: clienteData.telefono,
          email: clienteData.email,
        },
        ciudad_origen: clienteData.ciudad_origen,
        departamento_origen: clienteData.departamento_origen,
        repuestos,
      };

      await solicitudesService.createSolicitud(data);
      onSuccess();
      handleClose();
    } catch (err: any) {
      console.error("Error creating solicitud:", err);
      const errorMessage = err.response?.data?.detail || err.message || "Error al crear solicitud";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const isStep1Valid = () => {
    return (
      clienteData.nombre.trim() !== "" &&
      clienteData.telefono.trim() !== "" &&
      clienteData.ciudad_origen.trim() !== "" &&
      clienteData.departamento_origen.trim() !== ""
    );
  };

  const isStep2Valid = () => {
    return repuestos.length > 0;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Nueva Solicitud</DialogTitle>
          <DialogDescription>
            Completa los pasos para crear una nueva solicitud de repuestos
          </DialogDescription>
        </DialogHeader>

        {/* Steps Indicator */}
        <div className="flex items-center justify-center space-x-4 py-4">
          {steps.map((step, index) => (
            <div key={step.number} className="flex items-center">
              <div className="flex items-center space-x-2">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    step.number === currentStep
                      ? "bg-primary text-primary-foreground"
                      : step.number < currentStep
                      ? "bg-green-500 text-white"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {step.number}
                </div>
                <div className="text-sm">
                  <div className="font-medium">{step.title}</div>
                  <div className="text-muted-foreground">{step.description}</div>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div className="w-12 h-px bg-border mx-4" />
              )}
            </div>
          ))}
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {/* Step Content */}
        <div className="min-h-[400px]">
          {currentStep === 1 && (
            <ClienteStep
              data={clienteData}
              onChange={setClienteData}
              onNext={handleNext}
              isValid={isStep1Valid()}
            />
          )}
          {currentStep === 2 && (
            <RepuestosStep
              repuestos={repuestos}
              onChange={setRepuestos}
              onPrevious={handlePrevious}
              onSubmit={handleSubmit}
              isValid={isStep2Valid()}
              loading={loading}
            />
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between pt-4 border-t">
          <div className="flex items-center space-x-2">
            <Badge variant="outline">
              Paso {currentStep} de {steps.length}
            </Badge>
            {repuestos.length > 0 && (
              <Badge variant="secondary">
                {repuestos.length} repuesto{repuestos.length !== 1 ? "s" : ""}
              </Badge>
            )}
          </div>

          <div className="flex items-center space-x-2">
            {currentStep > 1 && (
              <Button variant="outline" onClick={handlePrevious}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Anterior
              </Button>
            )}
            {currentStep < steps.length ? (
              <Button onClick={handleNext} disabled={!isStep1Valid()}>
                Siguiente
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={!isStep2Valid() || loading}
              >
                {loading ? "Creando..." : "Crear Solicitud"}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
