/**
 * SolicitudesFilters - Advanced filters for solicitudes
 */

import { useState } from "react";
import { Search, Filter, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import type { SolicitudesFilters } from "@/types/solicitudes";

interface SolicitudesFiltersProps {
  filters: SolicitudesFilters;
  onFiltersChange: (filters: SolicitudesFilters) => void;
}

export function SolicitudesFilters({
  filters,
  onFiltersChange,
}: SolicitudesFiltersProps) {
  const [localFilters, setLocalFilters] = useState<SolicitudesFilters>(filters);
  const [isOpen, setIsOpen] = useState(false);

  const handleApplyFilters = () => {
    onFiltersChange(localFilters);
    setIsOpen(false);
  };

  const handleClearFilters = () => {
    const emptyFilters: SolicitudesFilters = {};
    setLocalFilters(emptyFilters);
    onFiltersChange(emptyFilters);
    setIsOpen(false);
  };

  const activeFiltersCount = Object.keys(filters).filter(
    (key) => filters[key as keyof SolicitudesFilters]
  ).length;

  return (
    <div className="flex gap-2">
      {/* Search Input */}
      <div className="flex-1 relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar por cliente, teléfono o ciudad..."
          value={localFilters.search || ""}
          onChange={(e) =>
            setLocalFilters({ ...localFilters, search: e.target.value })
          }
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleApplyFilters();
            }
          }}
          className="pl-9"
        />
      </div>

      {/* Advanced Filters Popover */}
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="relative">
            <Filter className="h-4 w-4 mr-2" />
            Filtros
            {activeFiltersCount > 0 && (
              <Badge
                variant="default"
                className="ml-2 h-5 w-5 p-0 flex items-center justify-center"
              >
                {activeFiltersCount}
              </Badge>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="end">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-medium">Filtros Avanzados</h4>
              {activeFiltersCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearFilters}
                  className="h-8 px-2"
                >
                  <X className="h-4 w-4 mr-1" />
                  Limpiar
                </Button>
              )}
            </div>

            {/* Date Range */}
            <div className="space-y-2">
              <Label>Rango de Fechas</Label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Input
                    type="date"
                    value={localFilters.fecha_desde || ""}
                    onChange={(e) =>
                      setLocalFilters({
                        ...localFilters,
                        fecha_desde: e.target.value,
                      })
                    }
                    placeholder="Desde"
                  />
                </div>
                <div>
                  <Input
                    type="date"
                    value={localFilters.fecha_hasta || ""}
                    onChange={(e) =>
                      setLocalFilters({
                        ...localFilters,
                        fecha_hasta: e.target.value,
                      })
                    }
                    placeholder="Hasta"
                  />
                </div>
              </div>
            </div>

            {/* City Filter */}
            <div className="space-y-2">
              <Label>Ciudad</Label>
              <Input
                placeholder="Ej: Bogotá"
                value={localFilters.ciudad || ""}
                onChange={(e) =>
                  setLocalFilters({ ...localFilters, ciudad: e.target.value })
                }
              />
            </div>

            {/* Department Filter */}
            <div className="space-y-2">
              <Label>Departamento</Label>
              <Select
                value={localFilters.departamento || ""}
                onValueChange={(value) =>
                  setLocalFilters({ ...localFilters, departamento: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar departamento" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Todos</SelectItem>
                  <SelectItem value="Cundinamarca">Cundinamarca</SelectItem>
                  <SelectItem value="Antioquia">Antioquia</SelectItem>
                  <SelectItem value="Valle del Cauca">
                    Valle del Cauca
                  </SelectItem>
                  <SelectItem value="Atlántico">Atlántico</SelectItem>
                  <SelectItem value="Santander">Santander</SelectItem>
                  <SelectItem value="Bolívar">Bolívar</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Apply Button */}
            <Button onClick={handleApplyFilters} className="w-full">
              Aplicar Filtros
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
