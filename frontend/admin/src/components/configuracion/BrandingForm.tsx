import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Upload, Check, Image as ImageIcon } from 'lucide-react';
import axios from '@/lib/axios';

const brandingSchema = z.object({
  nombre_empresa: z.string().min(1, 'El nombre es requerido'),
  color_primario: z.string().regex(/^#[0-9A-F]{6}$/i, 'Color inválido (formato: #RRGGBB)'),
  color_secundario: z.string().regex(/^#[0-9A-F]{6}$/i, 'Color inválido (formato: #RRGGBB)'),
});

type BrandingFormData = z.infer<typeof brandingSchema>;

interface BrandingConfig extends BrandingFormData {
  logo_url?: string;
}

export function BrandingForm() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [currentLogo, setCurrentLogo] = useState<string>('/logo.png');
  const [previewLogo, setPreviewLogo] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<BrandingFormData>({
    resolver: zodResolver(brandingSchema),
    defaultValues: {
      nombre_empresa: 'TeLOO',
      color_primario: '#3b82f6',
      color_secundario: '#1e40af',
    },
  });

  useEffect(() => {
    loadBranding();
  }, []);

  const loadBranding = async () => {
    try {
      const response = await axios.get('/v1/configuracion/branding');
      if (response.data.success && response.data.data) {
        const config: BrandingConfig = response.data.data;
        reset({
          nombre_empresa: config.nombre_empresa || 'TeLOO',
          color_primario: config.color_primario || '#3b82f6',
          color_secundario: config.color_secundario || '#1e40af',
        });
        if (config.logo_url) {
          const logoUrl = config.logo_url.startsWith('http')
            ? config.logo_url
            : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${config.logo_url}`;
          setCurrentLogo(logoUrl);
        }
      }
    } catch (error) {
      console.error('Error loading branding:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: BrandingFormData) => {
    setSaving(true);
    setMessage(null);

    try {
      await axios.put('/v1/configuracion/branding', data);
      setMessage({ type: 'success', text: 'Configuración actualizada exitosamente' });
      
      // Reload page after 1 second to apply changes
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Error al actualizar configuración',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml'].includes(file.type)) {
      setMessage({ type: 'error', text: 'Solo se permiten archivos PNG, JPG, JPEG o SVG' });
      return;
    }

    // Validate file size (2MB)
    if (file.size > 2 * 1024 * 1024) {
      setMessage({ type: 'error', text: 'El archivo no debe superar 2MB' });
      return;
    }

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreviewLogo(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    setUploading(true);
    setMessage(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('/v1/configuracion/branding/logo', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        const logoUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${response.data.data.logo_url}`;
        setCurrentLogo(logoUrl);
        setPreviewLogo(null);
        setMessage({ type: 'success', text: 'Logo actualizado exitosamente' });
        
        // Reload page after 1 second to apply changes
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      }
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Error al subir logo',
      });
      setPreviewLogo(null);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Personalización de Marca</CardTitle>
        <CardDescription>
          Configura el logo, nombre y colores de tu empresa
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {message && (
          <div
            className={`flex items-center gap-2 p-3 rounded-md ${
              message.type === 'success'
                ? 'bg-green-50 text-green-800 border border-green-200'
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            {message.type === 'success' ? (
              <Check className="h-4 w-4" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
            <span className="text-sm">{message.text}</span>
          </div>
        )}

        {/* Logo Upload Section */}
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Logo de la Empresa</label>
            <p className="text-sm text-muted-foreground">
              Formatos: PNG, JPG, SVG. Tamaño máximo: 2MB
            </p>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex-shrink-0">
              <div className="w-32 h-32 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50">
                {previewLogo || currentLogo ? (
                  <img
                    src={previewLogo || currentLogo}
                    alt="Logo preview"
                    className="max-w-full max-h-full object-contain p-2"
                  />
                ) : (
                  <ImageIcon className="h-12 w-12 text-gray-400" />
                )}
              </div>
            </div>

            <div className="flex-1">
              <input
                type="file"
                id="logo-upload"
                accept="image/png,image/jpeg,image/jpg,image/svg+xml"
                onChange={handleLogoUpload}
                className="hidden"
                disabled={uploading}
              />
              <label htmlFor="logo-upload">
                <Button
                  type="button"
                  variant="outline"
                  disabled={uploading}
                  onClick={() => document.getElementById('logo-upload')?.click()}
                  asChild
                >
                  <span>
                    <Upload className="h-4 w-4 mr-2" />
                    {uploading ? 'Subiendo...' : 'Subir Logo'}
                  </span>
                </Button>
              </label>
              <p className="text-xs text-muted-foreground mt-2">
                El logo se actualizará en todas las pantallas automáticamente
              </p>
            </div>
          </div>
        </div>

        {/* Branding Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="nombre_empresa" className="text-sm font-medium">
              Nombre de la Empresa
            </label>
            <Input
              id="nombre_empresa"
              {...register('nombre_empresa')}
              placeholder="TeLOO"
              className={errors.nombre_empresa ? 'border-destructive' : ''}
            />
            {errors.nombre_empresa && (
              <p className="text-sm text-destructive">{errors.nombre_empresa.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="color_primario" className="text-sm font-medium">
                Color Primario
              </label>
              <div className="flex gap-2">
                <Input
                  id="color_primario"
                  type="color"
                  {...register('color_primario')}
                  className="w-16 h-10 p-1 cursor-pointer"
                />
                <Input
                  {...register('color_primario')}
                  placeholder="#3b82f6"
                  className={errors.color_primario ? 'border-destructive' : ''}
                />
              </div>
              {errors.color_primario && (
                <p className="text-sm text-destructive">{errors.color_primario.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="color_secundario" className="text-sm font-medium">
                Color Secundario
              </label>
              <div className="flex gap-2">
                <Input
                  id="color_secundario"
                  type="color"
                  {...register('color_secundario')}
                  className="w-16 h-10 p-1 cursor-pointer"
                />
                <Input
                  {...register('color_secundario')}
                  placeholder="#1e40af"
                  className={errors.color_secundario ? 'border-destructive' : ''}
                />
              </div>
              {errors.color_secundario && (
                <p className="text-sm text-destructive">{errors.color_secundario.message}</p>
              )}
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <Button type="submit" disabled={saving}>
              {saving ? 'Guardando...' : 'Guardar Cambios'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
