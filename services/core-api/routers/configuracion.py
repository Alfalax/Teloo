"""
Configuracion Router
Public configuration endpoints for all authenticated users
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from models.user import Usuario
from middleware.auth_middleware import get_current_active_user
from services.configuracion_service import ConfiguracionService

router = APIRouter(prefix="/v1/configuracion", tags=["configuracion"])


@router.get("/public", summary="Obtener configuración pública")
async def get_configuracion_public(
    claves: Optional[List[str]] = Query(None, description="Claves específicas de parámetros"),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene parámetros de configuración pública del sistema
    Disponible para todos los usuarios autenticados (advisors, admins, etc.)
    
    Si se proporcionan claves específicas, devuelve solo esos parámetros.
    Si no se proporcionan claves, devuelve todos los parámetros públicos.
    """
    from models.analytics import ParametroConfig
    
    try:
        if claves:
            # Get specific parameters by keys
            parametros = await ParametroConfig.filter(clave__in=claves).all()
        else:
            # Get all public parameters
            parametros = await ParametroConfig.all()
        
        # Format response
        result = []
        for param in parametros:
            # Extract valor from valor_json
            valor = param.valor_json
            if isinstance(valor, dict) and 'valor' in valor:
                valor_str = str(valor['valor'])
                tipo_dato = valor.get('tipo_dato', 'string')
            else:
                valor_str = str(valor)
                tipo_dato = 'string'
            
            result.append({
                "clave": param.clave,
                "valor": valor_str,
                "tipo_dato": tipo_dato,
                "descripcion": param.descripcion,
                "metadata": param.metadata_json
            })
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Error in get_configuracion_public: {str(e)}")
        print(traceback.format_exc())
        raise
