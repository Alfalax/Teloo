import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Search, Filter, X } from 'lucide-react';
import { asesoresService } from '@/services/asesores';

interface AsesoresFiltersProps {
  onFiltersChange: (filters: {
    search: string;
    estado: string;
    ciudad: string;
    departamento: string;
  }) => void;
  isLoading?: boolean;
}

export function AsesoresFilters({ onFiltersChange, isLoading = false }: AsesoresFiltersProps) {
  const [search, setSearch] = useState('');
  const [estado, setEstado] = useState('');
  const [ciudad, setCiudad] = useState('');
  const [departamento, setDepartamento] = useState('');
  const [ciudades, setCiudades] = useState<string[]>([]);
  const [departamentos, setDepartamentos] = useState<string[]>([]);
  const [loadingOptions, setLoadingOptions] = useState(false);

  useEffect(() => {
    loadFilterOptions();
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      onFiltersChange({ search, estado, ciudad, departamento });
    }, 300); // Debounce search

    return () => clearTimeout(timeoutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, estado, ciudad, departamento]);

  const loadFilterOptions = async () => {
    setLoadingOptions(true);
    try {
      const [ciudadesData, departamentosData] = await Promise.all([
        asesoresService.getCiudades(),
        asesoresService.getDepartamentos(),
      ]);
      setCiudades(ciudadesData);
      setDepartamentos(departamentosData);
    } catch (error) {
      console.error('Error loading filter options:', error);
    } finally {
      setLoadingOptions(false);
    }
  };

  const clearFilters = () => {
    setSearch('');
    setEstado('');
    setCiudad('');
    setDepartamento('');
  };

  const hasActiveFilters = search || estado || ciudad || departamento;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 flex-wrap">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por nombre, email o punto de venta..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
            disabled={isLoading}
          />
        </div>

        {/* Estado Filter */}
        <Select value={estado || "all"} onValueChange={(val) => setEstado(val === "all" ? "" : val)} disabled={isLoading}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos los estados</SelectItem>
            <SelectItem value="ACTIVO">Activo</SelectItem>
            <SelectItem value="INACTIVO">Inactivo</SelectItem>
            <SelectItem value="SUSPENDIDO">Suspendido</SelectItem>
          </SelectContent>
        </Select>

        {/* Departamento Filter */}
        <Select 
          value={departamento || "all"} 
          onValueChange={(val) => setDepartamento(val === "all" ? "" : val)} 
          disabled={isLoading || loadingOptions}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Departamento" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos los departamentos</SelectItem>
            {departamentos.map((dept) => (
              <SelectItem key={dept} value={dept}>
                {dept}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Ciudad Filter */}
        <Select 
          value={ciudad || "all"} 
          onValueChange={(val) => setCiudad(val === "all" ? "" : val)} 
          disabled={isLoading || loadingOptions}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Ciudad" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas las ciudades</SelectItem>
            {ciudades.map((city) => (
              <SelectItem key={city} value={city}>
                {city}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <Button
            variant="outline"
            size="sm"
            onClick={clearFilters}
            className="flex items-center gap-2"
            disabled={isLoading}
          >
            <X className="h-4 w-4" />
            Limpiar
          </Button>
        )}
      </div>

      {/* Active Filters Summary */}
      {hasActiveFilters && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Filter className="h-4 w-4" />
          <span>Filtros activos:</span>
          {search && (
            <span className="bg-primary/10 text-primary px-2 py-1 rounded-md">
              Búsqueda: "{search}"
            </span>
          )}
          {estado && (
            <span className="bg-primary/10 text-primary px-2 py-1 rounded-md">
              Estado: {estado}
            </span>
          )}
          {departamento && (
            <span className="bg-primary/10 text-primary px-2 py-1 rounded-md">
              Departamento: {departamento}
            </span>
          )}
          {ciudad && (
            <span className="bg-primary/10 text-primary px-2 py-1 rounded-md">
              Ciudad: {ciudad}
            </span>
          )}
        </div>
      )}
    </div>
  );
}