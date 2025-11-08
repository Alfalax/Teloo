/**
 * Cliente Step - First step of nueva solicitud wizard
 */

import { User, Phone, Mail, MapPin } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ClienteData {
  nombre: string;
  telefono: string;
  email?: string;
  ciudad_origen: string;
  departamento_origen: string;
}

interface ClienteStepProps {
  data: ClienteData;
  onChange: (data: ClienteData) => void;
  onNext: () => void;
  isValid: boolean;
}

const departamentos = [
  "Antioquia",
  "Bogotá D.C.",
  "Valle del Cauca",
  "Atlántico",
  "Santander",
  "Cundinamarca",
  "Bolívar",
  "Córdoba",
  "Norte de Santander",
  "Tolima",
];

const ciudadesPorDepartamento: Record<string, string[]> = {
  "Antioquia": ["Medellín", "Bello", "Itagüí", "Envigado"],
  "Bogotá D.C.": ["Bogotá"],
  "Valle del Cauca": ["Cali", "Palmira", "Buenaventura"],
  "Atlántico": ["Barranquilla", "Soledad"],
  "Santander": ["Bucaramanga", "Floridablanca", "Girón"],
};

export function ClienteStep({ data, onChange, onNext, isValid }: ClienteStepProps) {
  const handleChange = (field: keyof ClienteData, value: string) => {
    const newData = { ...data, [field]: value };
    
    if (field === "departamento_origen") {
      newData.ciudad_origen = "";
    }
    
    onChange(newData);
  };

  const ciudadesDisponibles = data.departamento_origen
    ? ciudadesPorDepartamento[data.departamento_origen] || []
    : [];

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold">Información del Cliente</h3>
        <p className="text-muted-foreground">
          Ingresa los datos del cliente que solicita los repuestos
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="nombre">Nombre Completo *</Label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              id="nombre"
              placeholder="Ej: Juan Pérez"
              value={data.nombre}
              onChange={(e) => handleChange("nombre", e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="telefono">Teléfono *</Label>
          <div className="relative">
            <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              id="telefono"
              placeholder="Ej: 3001234567"
              value={data.telefono}
              onChange={(e) => handleChange("telefono", e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email (Opcional)</Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              id="email"
              type="email"
              placeholder="Ej: juan@email.com"
              value={data.email || ""}
              onChange={(e) => handleChange("email", e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label>Departamento *</Label>
          <Select
            value={data.departamento_origen}
            onValueChange={(value) => handleChange("departamento_origen", value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar departamento" />
            </SelectTrigger>
            <SelectContent>
              {departamentos.map((dept) => (
                <SelectItem key={dept} value={dept}>
                  {dept}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2 md:col-span-2">
          <Label>Ciudad *</Label>
          {ciudadesDisponibles.length > 0 ? (
            <Select
              value={data.ciudad_origen}
              onValueChange={(value) => handleChange("ciudad_origen", value)}
              disabled={!data.departamento_origen}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleccionar ciudad" />
              </SelectTrigger>
              <SelectContent>
                {ciudadesDisponibles.map((ciudad) => (
                  <SelectItem key={ciudad} value={ciudad}>
                    {ciudad}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Ingresa la ciudad"
                value={data.ciudad_origen}
                onChange={(e) => handleChange("ciudad_origen", e.target.value)}
                className="pl-10"
                disabled={!data.departamento_origen}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
