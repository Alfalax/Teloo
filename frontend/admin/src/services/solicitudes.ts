/**
 * Service for Solicitudes API
 */

import apiClient from "@/lib/axios";
import type {
  Solicitud,
  CreateSolicitudData,
  SolicitudesFilters,
  SolicitudesPaginatedResponse,
  SolicitudesStats,
} from "../types/solicitudes";

export const solicitudesService = {
  /**
   * Get paginated solicitudes with filters
   */
  async getSolicitudes(
    page: number = 1,
    pageSize: number = 25,
    filters?: SolicitudesFilters
  ): Promise<SolicitudesPaginatedResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    if (filters?.estado) {
      params.append("estado", filters.estado);
    }
    if (filters?.search) {
      params.append("search", filters.search);
    }
    if (filters?.fecha_desde) {
      params.append("fecha_desde", filters.fecha_desde);
    }
    if (filters?.fecha_hasta) {
      params.append("fecha_hasta", filters.fecha_hasta);
    }
    if (filters?.ciudad) {
      params.append("ciudad", filters.ciudad);
    }
    if (filters?.departamento) {
      params.append("departamento", filters.departamento);
    }

    const response = await apiClient.get(`/v1/solicitudes?${params.toString()}`);
    return response.data;
  },

  /**
   * Get solicitud by ID with details
   */
  async getSolicitudById(id: string): Promise<Solicitud> {
    const response = await apiClient.get(`/v1/solicitudes/${id}`);
    return response.data;
  },

  /**
   * Create new solicitud
   */
  async createSolicitud(data: CreateSolicitudData): Promise<Solicitud> {
    const response = await apiClient.post("/v1/solicitudes", data);
    return response.data;
  },

  /**
   * Get statistics by estado
   */
  async getStats(): Promise<SolicitudesStats> {
    const response = await apiClient.get("/v1/solicitudes/stats");
    return response.data;
  },

  /**
   * Search cliente by phone number
   */
  async buscarClientePorTelefono(telefono: string): Promise<{
    found: boolean;
    cliente_id?: string;
    nombre?: string;
    email?: string;
    telefono?: string;
    ciudad?: string;
    departamento?: string;
  }> {
    const response = await apiClient.get("/v1/solicitudes/clientes/buscar", {
      params: { telefono },
    });
    return response.data;
  },

  /**
   * Parse Excel file for repuestos
   */
  parseExcelRepuestos(file: File): Promise<any[]> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = () => {
        try {
          // TODO: Implement Excel parsing with xlsx library
          // For now, return empty array
          resolve([]);
        } catch (error) {
          reject(error);
        }
      };

      reader.onerror = () => reject(new Error("Error reading file"));
      reader.readAsBinaryString(file);
    });
  },
};
