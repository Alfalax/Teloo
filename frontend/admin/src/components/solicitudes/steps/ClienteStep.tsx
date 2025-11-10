/**
 * Cliente Step - First step of nueva solicitud wizard
 */

import { useState, useEffect } from "react";
import { User, Phone, Mail, Loader2, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { geografiaService } from "@/services/geografia";
import { solicitudesService } from "@/services/solicitudes";

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

export function ClienteStep({ data, onChange }: ClienteStepProps) {
  const [departamentos, setDepartamentos] = useState<string[]>([]);
  const [ciudades, setCiudades] = useState<string[]>([]);
  const [loadingDepartamentos, setLoadingDepartamentos] = useState(false);
  const [loadingCiudades, setLoadingCiudades] = useState(false);
  const [searchingCliente, setSearchingCliente] = useState(false);
  const [clienteFound, setClienteFound] = useState(false);

  // Load departamentos on mount
  useEffect(() => {
    loadDepartamentos();
  }, []);

  // Load ciudades when departamento changes
  useEffect(() => {
    if (data.departamento_origen) {
      loadCiudades(data.departamento_origen);
    } else {
      setCiudades([]);
    }
  }, [data.departamento_origen]);

  const loadDepartamentos = async () => {
    setLoadingDepartamentos(true);
    try {
      const deps = await geografiaService.getDepartamentos();
      setDepartamentos(deps);
    } catch (error) {
      console.error('Error loading departamentos:', error);
    } finally {
      setLoadingDepartamentos(false);
    }
  };

  const loadCiudades = async (departamento: string) => {
    setLoadingCiudades(true);
    try {
      const ciud = await geografiaService.getCiudadesByDepartamento(departamento);
      setCiudades(ciud);
    } catch (error) {
      console.error('Error loading ciudades:', error);
    } finally {
      setLoadingCiudades(false);
    }
  };

  const handleChange = (field: keyof ClienteData, value: string) => {
    const newData = { ...data, [field]: value };
    
    if (field === "departamento_origen") {
      newData.ciudad_origen = "";
    }
    
    // Reset cliente found flag when phone changes
    if (field === "telefono") {
      setClienteFound(false);
    }
    
    onChange(newData);
  };

  const buscarClientePorTelefono = async () => {
    if (!data.telefono || data.telefono.length < 10) {
      return;
    }

    setSearchingCliente(true);
    try {
      const result = await solicitudesService.buscarClientePorTelefono(data.telefono);
      
      if (result.found) {
        setClienteFound(true);
        onChange({
          nombre: result.nombre || data.nombre,
          telefono: result.telefono || data.telefono,
          email: result.email || data.email,
          ciudad_origen: result.ciudad || data.ciudad_origen,
          departamento_origen: result.departamento || data.departamento_origen,
        });
      } else {
        setClienteFound(false);
      }
    } catch (error) {
      console.error('Error buscando cliente:', error);
      setClienteFound(false);
    } finally {
      setSearchingCliente(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold">Información del Cliente</h3>
        <p className="text-muted-foreground">
          Ingresa los datos del cliente que solicita los repuestos
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="telefono">Teléfono *</Label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                id="telefono"
                placeholder="Ej: 3001234567"
                value={data.telefono}
                onChange={(e) => handleChange("telefono", e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={buscarClientePorTelefono}
              disabled={searchingCliente || !data.telefono || data.telefono.length < 10}
              title="Buscar cliente existente"
            >
              {searchingCliente ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
            </Button>
          </div>
          {clienteFound && (
            <p className="text-xs text-green-600">
              ✓ Cliente encontrado - datos autocompletados
            </p>
          )}
        </div>

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
            disabled={loadingDepartamentos}
          >
            <SelectTrigger>
              <SelectValue placeholder={loadingDepartamentos ? "Cargando..." : "Seleccionar departamento"} />
            </SelectTrigger>
            <SelectContent>
              {departamentos.map((dept) => (
                <SelectItem key={dept} value={dept}>
                  {dept}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {loadingDepartamentos && (
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              Cargando departamentos...
            </p>
          )}
        </div>

        <div className="space-y-2 md:col-span-2">
          <Label>Ciudad *</Label>
          <Select
            value={data.ciudad_origen}
            onValueChange={(value) => handleChange("ciudad_origen", value)}
            disabled={!data.departamento_origen || loadingCiudades}
          >
            <SelectTrigger>
              <SelectValue 
                placeholder={
                  !data.departamento_origen 
                    ? "Primero selecciona un departamento" 
                    : loadingCiudades 
                    ? "Cargando ciudades..." 
                    : "Seleccionar ciudad"
                } 
              />
            </SelectTrigger>
            <SelectContent>
              {ciudades.map((ciudad) => (
                <SelectItem key={ciudad} value={ciudad}>
                  {ciudad}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {loadingCiudades && (
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              Cargando ciudades del departamento...
            </p>
          )}
          {data.departamento_origen && ciudades.length === 0 && !loadingCiudades && (
            <p className="text-xs text-muted-foreground">
              No se encontraron ciudades para este departamento
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
