"""
Asesores service for TeLOO V3
Handles business logic for asesor management including Excel import/export
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
from fastapi import HTTPException, UploadFile
from models.user import Usuario, Asesor
from models.enums import EstadoAsesor, EstadoUsuario, RolUsuario
from services.auth_service import AuthService


class AsesoresService:
    """Service class for asesor management operations"""
    
    @staticmethod
    async def import_asesores_excel(file: UploadFile) -> Dict[str, Any]:
        """
        Import asesores from Excel file
        
        Expected columns:
        - nombre, apellido, email, telefono
        - ciudad, departamento, punto_venta, direccion_punto_venta
        - password (optional, will generate if not provided)
        """
        try:
            # Read Excel file
            content = await file.read()
            # Force telefono column to be read as string to preserve + sign
            df = pd.read_excel(BytesIO(content), dtype={'telefono': str})
            
            # Validate required columns
            required_columns = [
                'nombre', 'apellido', 'email', 'telefono',
                'ciudad', 'departamento', 'punto_venta'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Columnas faltantes: {', '.join(missing_columns)}"
                )
            
            # Process each row
            total_procesados = len(df)
            exitosos = 0
            errores = 0
            detalles_errores = []
            
            for index, row in df.iterrows():
                try:
                    # Validate email format
                    email = str(row['email']).strip()
                    if not email or '@' not in email:
                        raise ValueError("Email inválido")
                    
                    # Check if email already exists
                    existing_user = await Usuario.get_or_none(email=email)
                    if existing_user:
                        raise ValueError("Email ya registrado")
                    
                    # Generate password if not provided
                    password = str(row.get('password', '')).strip()
                    if not password:
                        password = f"TeLOO{datetime.now().year}!"
                    
                    # Create user
                    password_hash = AuthService.get_password_hash(password)
                    
                    usuario = await Usuario.create(
                        email=email,
                        password_hash=password_hash,
                        nombre=str(row['nombre']).strip(),
                        apellido=str(row['apellido']).strip(),
                        telefono=str(row['telefono']).strip(),
                        rol=RolUsuario.ADVISOR,
                        estado=EstadoUsuario.ACTIVO
                    )
                    
                    # Create asesor
                    await Asesor.create(
                        usuario=usuario,
                        ciudad=str(row['ciudad']).strip(),
                        departamento=str(row['departamento']).strip(),
                        punto_venta=str(row['punto_venta']).strip(),
                        direccion_punto_venta=str(row.get('direccion_punto_venta', '')).strip() or None,
                        estado=EstadoAsesor.ACTIVO
                    )
                    
                    exitosos += 1
                    
                except Exception as e:
                    errores += 1
                    detalles_errores.append({
                        "fila": index + 2,  # +2 because pandas is 0-indexed and Excel has header
                        "errores": [str(e)]
                    })
            
            return {
                "success": True,
                "message": f"Importación completada: {exitosos} exitosos, {errores} errores",
                "total_procesados": total_procesados,
                "exitosos": exitosos,
                "errores": errores,
                "detalles_errores": detalles_errores[:10]  # Limit to first 10 errors
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")
    
    @staticmethod
    async def export_asesores_excel(
        search: Optional[str] = None,
        estado: Optional[EstadoAsesor] = None,
        ciudad: Optional[str] = None,
        departamento: Optional[str] = None
    ) -> BytesIO:
        """
        Export asesores to Excel file with filters
        """
        try:
            # Build query with same filters as get_asesores
            query = Asesor.all().prefetch_related('usuario')
            
            # Apply filters (same logic as in router)
            if search:
                from tortoise.expressions import Q
                query = query.filter(
                    Q(usuario__nombre__icontains=search) |
                    Q(usuario__apellido__icontains=search) |
                    Q(usuario__email__icontains=search) |
                    Q(punto_venta__icontains=search)
                )
            
            if estado:
                query = query.filter(estado=estado)
            
            if ciudad:
                query = query.filter(ciudad=ciudad)
            
            if departamento:
                query = query.filter(departamento=departamento)
            
            # Get all asesores
            asesores = await query.order_by('-created_at')
            
            # Prepare data for Excel
            data = []
            for asesor in asesores:
                tasa_adjudicacion = 0
                if asesor.total_ofertas > 0:
                    tasa_adjudicacion = (asesor.ofertas_ganadoras / asesor.total_ofertas) * 100
                
                data.append({
                    'nombre': asesor.usuario.nombre,
                    'apellido': asesor.usuario.apellido,
                    'email': asesor.usuario.email,
                    'telefono': asesor.usuario.telefono,
                    'ciudad': asesor.ciudad,
                    'departamento': asesor.departamento,
                    'punto_venta': asesor.punto_venta,
                    'direccion_punto_venta': asesor.direccion_punto_venta or '',
                    'estado': asesor.estado.value,
                    'confianza': float(asesor.confianza),
                    'nivel_actual': asesor.nivel_actual,
                    'actividad_reciente_pct': float(asesor.actividad_reciente_pct),
                    'desempeno_historico_pct': float(asesor.desempeno_historico_pct),
                    'total_ofertas': asesor.total_ofertas,
                    'ofertas_ganadoras': asesor.ofertas_ganadoras,
                    'monto_total_ventas': float(asesor.monto_total_ventas),
                    'tasa_adjudicacion': round(tasa_adjudicacion, 2),
                    'created_at': asesor.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Create Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Asesores', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Asesores']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            output.seek(0)
            return output
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error exportando asesores: {str(e)}")
    
    @staticmethod
    async def get_excel_template() -> BytesIO:
        """
        Generate Excel template for asesor import
        """
        try:
            # Create template data
            template_data = {
                'nombre': ['Juan', 'María'],
                'apellido': ['Pérez', 'González'],
                'email': ['juan.perez@ejemplo.com', 'maria.gonzalez@ejemplo.com'],
                'telefono': ['+573001234567', '+573007654321'],
                'ciudad': ['Bogotá', 'Medellín'],
                'departamento': ['Cundinamarca', 'Antioquia'],
                'punto_venta': ['Repuestos Pérez', 'Auto Partes González'],
                'direccion_punto_venta': ['Calle 123 #45-67', 'Carrera 89 #12-34'],
                'password': ['MiPassword123!', 'OtraPassword456!']
            }
            
            df = pd.DataFrame(template_data)
            
            # Create Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Plantilla_Asesores', index=False)
                
                # Add instructions sheet
                instructions = pd.DataFrame({
                    'Instrucciones': [
                        '1. Complete todos los campos obligatorios marcados con *',
                        '2. El email debe ser único en el sistema',
                        '3. El teléfono debe tener formato colombiano +57XXXXXXXXXX',
                        '4. Si no proporciona password, se generará automáticamente',
                        '5. Guarde el archivo y súbalo al sistema',
                        '',
                        'Campos obligatorios:',
                        '- nombre*',
                        '- apellido*', 
                        '- email*',
                        '- telefono*',
                        '- ciudad*',
                        '- departamento*',
                        '- punto_venta*',
                        '',
                        'Campos opcionales:',
                        '- direccion_punto_venta',
                        '- password (se genera automáticamente si no se proporciona)'
                    ]
                })
                instructions.to_excel(writer, sheet_name='Instrucciones', index=False)
            
            output.seek(0)
            return output
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generando plantilla: {str(e)}")