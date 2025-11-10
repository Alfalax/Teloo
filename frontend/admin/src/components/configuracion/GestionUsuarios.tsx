/**
 * User Management Component
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
  UserCheck, 
  UserX, 
  AlertCircle,
  Users
} from 'lucide-react';
import { UsuarioForm } from './UsuarioForm';
import { useUsuarios } from '@/hooks/useConfiguracion';
import type { Usuario } from '@/types/configuracion';
import { ROLES_DISPONIBLES, ESTADOS_USUARIO } from '@/types/configuracion';

export function GestionUsuarios() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRol, setSelectedRol] = useState<string>('');
  const [selectedEstado, setSelectedEstado] = useState<string>('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingUsuario, setEditingUsuario] = useState<Usuario | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

  const { usuarios, loading, error, createUsuario, updateUsuario, deleteUsuario } = useUsuarios();

  const filteredUsuarios = usuarios.filter(usuario => {
    const matchesSearch = usuario.nombre_completo.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         usuario.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRol = !selectedRol || usuario.rol === selectedRol;
    const matchesEstado = !selectedEstado || usuario.estado === selectedEstado;
    
    return matchesSearch && matchesRol && matchesEstado;
  });

  const handleCreateUsuario = async (usuarioData: Omit<Usuario, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      await createUsuario(usuarioData);
      setIsCreateDialogOpen(false);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const handleUpdateUsuario = async (usuarioData: Partial<Usuario>) => {
    if (!editingUsuario) return;
    
    try {
      await updateUsuario(editingUsuario.id, usuarioData);
      setIsEditDialogOpen(false);
      setEditingUsuario(null);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const handleDeleteUsuario = async (usuario: Usuario) => {
    if (confirm(`¿Está seguro de que desea eliminar al usuario "${usuario.nombre_completo}"?`)) {
      try {
        await deleteUsuario(usuario.id);
      } catch (err) {
        // Error is handled by the hook
      }
    }
  };

  const handleToggleEstado = async (usuario: Usuario) => {
    const nuevoEstado = usuario.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO';
    try {
      await updateUsuario(usuario.id, { estado: nuevoEstado });
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const getEstadoBadge = (estado: string) => {
    switch (estado) {
      case 'ACTIVO':
        return <Badge className="bg-green-100 text-green-800">Activo</Badge>;
      case 'INACTIVO':
        return <Badge variant="secondary">Inactivo</Badge>;
      case 'SUSPENDIDO':
        return <Badge variant="destructive">Suspendido</Badge>;
      default:
        return <Badge variant="outline">{estado}</Badge>;
    }
  };

  const getRolBadge = (rol: string) => {
    const colors = {
      ADMIN: 'bg-purple-100 text-purple-800',
      ADVISOR: 'bg-blue-100 text-blue-800',
      ANALYST: 'bg-orange-100 text-orange-800',
      SUPPORT: 'bg-gray-100 text-gray-800',
      CLIENT: 'bg-green-100 text-green-800'
    };
    
    return (
      <Badge className={colors[rol as keyof typeof colors] || 'bg-gray-100 text-gray-800'}>
        {ROLES_DISPONIBLES.find(r => r.value === rol)?.label || rol}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Cargando usuarios...</p>
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
            <Users className="h-5 w-5 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {filteredUsuarios.length} de {usuarios.length} usuarios
            </span>
          </div>
          
          <div className="flex gap-2">
            {ESTADOS_USUARIO.map(estado => {
              const count = usuarios.filter(u => u.estado === estado.value).length;
              return (
                <Badge key={estado.value} variant="outline" className="text-xs">
                  {estado.label}: {count}
                </Badge>
              );
            })}
          </div>
        </div>

        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Nuevo Usuario
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Crear Nuevo Usuario</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              Complete la información del nuevo usuario del sistema
            </DialogDescription>
            <UsuarioForm
              onSubmit={handleCreateUsuario}
              onCancel={() => setIsCreateDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar por nombre o email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <select
              value={selectedRol}
              onChange={(e) => setSelectedRol(e.target.value)}
              className="px-3 py-2 border border-input bg-background rounded-md text-sm"
            >
              <option value="">Todos los roles</option>
              {ROLES_DISPONIBLES.map(rol => (
                <option key={rol.value} value={rol.value}>{rol.label}</option>
              ))}
            </select>
            
            <select
              value={selectedEstado}
              onChange={(e) => setSelectedEstado(e.target.value)}
              className="px-3 py-2 border border-input bg-background rounded-md text-sm"
            >
              <option value="">Todos los estados</option>
              {ESTADOS_USUARIO.map(estado => (
                <option key={estado.value} value={estado.value}>{estado.label}</option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>Usuarios del Sistema</CardTitle>
          <CardDescription>
            Gestión de usuarios y sus permisos de acceso
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Usuario</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Rol</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Creado</TableHead>
                  <TableHead className="w-[70px]">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsuarios.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      No se encontraron usuarios
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredUsuarios.map((usuario) => (
                    <TableRow key={usuario.id}>
                      <TableCell className="font-medium">
                        {usuario.nombre_completo}
                      </TableCell>
                      <TableCell>{usuario.email}</TableCell>
                      <TableCell>{getRolBadge(usuario.rol)}</TableCell>
                      <TableCell>{getEstadoBadge(usuario.estado)}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(usuario.created_at).toLocaleDateString()}
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
                                setEditingUsuario(usuario);
                                setIsEditDialogOpen(true);
                              }}
                            >
                              <Edit className="h-4 w-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleToggleEstado(usuario)}
                            >
                              {usuario.estado === 'ACTIVO' ? (
                                <>
                                  <UserX className="h-4 w-4 mr-2" />
                                  Desactivar
                                </>
                              ) : (
                                <>
                                  <UserCheck className="h-4 w-4 mr-2" />
                                  Activar
                                </>
                              )}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDeleteUsuario(usuario)}
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
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Editar Usuario</DialogTitle>
          </DialogHeader>
          <DialogDescription>
            Modifique la información del usuario
          </DialogDescription>
          {editingUsuario && (
            <UsuarioForm
              initialData={editingUsuario}
              onSubmit={handleUpdateUsuario}
              onCancel={() => {
                setIsEditDialogOpen(false);
                setEditingUsuario(null);
              }}
              isEditing
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}