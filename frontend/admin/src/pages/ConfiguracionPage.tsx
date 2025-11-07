import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertCircle, Settings, Users, Shield, RotateCcw } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ConfiguracionSistema } from '@/components/configuracion/ConfiguracionSistema';
import { GestionUsuarios } from '@/components/configuracion/GestionUsuarios';
import { GestionRoles } from '@/components/configuracion/GestionRoles';
import { useConfiguracion } from '@/hooks/useConfiguracion';

export function ConfiguracionPage() {
  const [activeTab, setActiveTab] = useState('sistema');
  const { summary, error, resetConfiguracion } = useConfiguracion();

  const handleResetCompleto = async () => {
    if (confirm('¿Está seguro de que desea resetear toda la configuración a valores por defecto? Esta acción no se puede deshacer.')) {
      await resetConfiguracion();
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Configuración</h1>
          <p className="text-muted-foreground">
            Gestión de parámetros del sistema, usuarios y permisos
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {summary && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Badge variant="outline">
                {summary.estadisticas.total_categorias} categorías
              </Badge>
              <Badge variant="outline">
                {summary.estadisticas.total_parametros} parámetros
              </Badge>
            </div>
          )}
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleResetCompleto}
            className="text-destructive hover:text-destructive"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset Completo
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {summary && summary.estadisticas.ultima_modificacion && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                Última modificación: {new Date(summary.estadisticas.ultima_modificacion).toLocaleString()}
              </span>
              {summary.estadisticas.modificado_por && (
                <span className="text-muted-foreground">
                  por {summary.estadisticas.modificado_por}
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="sistema" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Parámetros del Sistema
          </TabsTrigger>
          <TabsTrigger value="usuarios" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Gestión de Usuarios
          </TabsTrigger>
          <TabsTrigger value="roles" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Roles y Permisos
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sistema" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Parámetros del Sistema</CardTitle>
              <CardDescription>
                Configuración de algoritmos de escalamiento, evaluación y parámetros operativos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ConfiguracionSistema />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usuarios" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Gestión de Usuarios</CardTitle>
              <CardDescription>
                Administración de usuarios del sistema y sus permisos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <GestionUsuarios />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="roles" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Roles y Permisos</CardTitle>
              <CardDescription>
                Configuración de roles del sistema y asignación de permisos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <GestionRoles />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}