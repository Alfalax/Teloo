/**
 * Roles Management Component
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  Plus, 
  Search, 
  MoreHorizontal, 
  Edit, 
  Trash2, 
  Shield, 
  ShieldCheck, 
  ShieldX,
  AlertCircle
} from 'lucide-react';
import { RolForm } from './RolForm';
import { useRoles } from '@/hooks/useConfiguracion';
import type { Rol } from '@/types/configuracion';

export function GestionRoles() {
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingRol, setEditingRol] = useState<Rol | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

  const { roles, permisosDisponibles, loading, error, createRol, updateRol, deleteRol } = useRoles();

  const filteredRoles = roles.filter(rol => 
    rol.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
    rol.descripcion.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreateRol = async (rolData: Omit<Rol, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      await createRol(rolData);
      setIsCreateDialogOpen(false);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const handleUpdateRol = async (rolData: Partial<Rol>) => {
    if (!editingRol) return;
    
    try {
      await updateRol(editingRol.id, rolData);
      setIsEditDialogOpen(false);
      setEditingRol(null);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const handleDeleteRol = async (rol: Rol) => {
    if (confirm(`¿Está seguro de que desea eliminar el rol "${rol.nombre}"?`)) {
      try {
        await deleteRol(rol.id);
      } catch (err) {
        // Error is handled by the hook
      }
    }
  };

  const handleToggleActivo = async (rol: Rol) => {
    try {
      await updateRol(rol.id, { activo: !rol.activo });
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const getActivoBadge = (activo: boolean) => {
    return activo ? (
      <Badge className="bg-green-100 text-green-800">Activo</Badge>
    ) : (
      <Badge variant="secondary">Inactivo</Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Cargando roles...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Header with Stats */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {filteredRoles.length} de {roles.length} roles
            </span>
          </div>
          
          <div className="flex gap-2">
            <Badge variant="outline" className="text-xs">
              Activos: {roles.filter(r => r.activo).length}
            </Badge>
            <Badge variant="outline" className="text-xs">
              Inactivos: {roles.filter(r => !r.activo).length}
            </Badge>
          </div>
        </div>

        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Nuevo Rol
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Crear Nuevo Rol</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              Defina un nuevo rol del sistema con sus permisos correspondientes
            </DialogDescription>
            <RolForm
              permisosDisponibles={permisosDisponibles}
              onSubmit={handleCreateRol}
              onCancel={() => setIsCreateDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar por nombre o descripción..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Roles Table */}
      <Card>
        <CardHeader>
          <CardTitle>Roles del Sistema</CardTitle>
          <CardDescription>
            Gestión de roles y asignación de permisos
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rol</TableHead>
                  <TableHead>Descripción</TableHead>
                  <TableHead>Permisos</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Creado</TableHead>
                  <TableHead className="w-[70px]">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRoles.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      No se encontraron roles
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredRoles.map((rol) => (
                    <TableRow key={rol.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <Shield className="h-4 w-4 text-muted-foreground" />
                          {rol.nombre}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-xs">
                        <p className="text-sm text-muted-foreground truncate">
                          {rol.descripcion}
                        </p>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {rol.permisos.slice(0, 3).map((permiso) => (
                            <Badge key={permiso} variant="outline" className="text-xs">
                              {permiso}
                            </Badge>
                          ))}
                          {rol.permisos.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{rol.permisos.length - 3} más
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{getActivoBadge(rol.activo)}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(rol.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() => {
                                setEditingRol(rol);
                                setIsEditDialogOpen(true);
                              }}
                            >
                              <Edit className="h-4 w-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleToggleActivo(rol)}
                            >
                              {rol.activo ? (
                                <>
                                  <ShieldX className="h-4 w-4 mr-2" />
                                  Desactivar
                                </>
                              ) : (
                                <>
                                  <ShieldCheck className="h-4 w-4 mr-2" />
                                  Activar
                                </>
                              )}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDeleteRol(rol)}
                              className="text-destructive"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Eliminar
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Editar Rol</DialogTitle>
          </DialogHeader>
          <DialogDescription>
            Modifique la información y permisos del rol
          </DialogDescription>
          {editingRol && (
            <RolForm
              initialData={editingRol}
              permisosDisponibles={permisosDisponibles}
              onSubmit={handleUpdateRol}
              onCancel={() => {
                setIsEditDialogOpen(false);
                setEditingRol(null);
              }}
              isEditing
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}