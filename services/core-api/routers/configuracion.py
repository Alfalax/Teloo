"""
Configuracion Router
Public configuration endpoints for all authenticated users
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import uuid
from models.user import Usuario
from middleware.auth_middleware import get_current_active_user, require_role
from models.enums import RolUsuario

router = APIRouter(prefix="/v1/configuracion", tags=["configuracion"])

_BRANDING_KEY = "branding"
_BRANDING_DEFAULTS: dict = {
    "nombre_empresa": "TeLOO",
    "color_primario": "#3b82f6",
    "color_secundario": "#1e40af",
    "logo_url": None,
}
_LOGO_UPLOADS_DIR = Path("uploads/branding")
_ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/svg+xml"}
_MAX_LOGO_SIZE = 2 * 1024 * 1024  # 2 MB


class BrandingUpdate(BaseModel):
    nombre_empresa: str
    color_primario: str
    color_secundario: str


async def _get_branding() -> dict:
    from models.analytics import ParametroConfig
    param = await ParametroConfig.filter(clave=_BRANDING_KEY).first()
    if param and isinstance(param.valor_json, dict):
        return {**_BRANDING_DEFAULTS, **param.valor_json}
    return dict(_BRANDING_DEFAULTS)


async def _save_branding(data: dict, usuario: Usuario) -> None:
    from models.analytics import ParametroConfig
    param, created = await ParametroConfig.get_or_create(
        clave=_BRANDING_KEY,
        defaults={
            "valor_json": data,
            "descripcion": "Configuración de branding y personalización",
            "categoria": "branding",
        },
    )
    if not created:
        param.valor_json = data
        param.descripcion = "Configuración de branding y personalización"
        param.categoria = "branding"
        await param.save()


# ── Public (no auth) ──────────────────────────────────────────────────────────

@router.get("/branding/public", summary="Obtener branding público (sin autenticación)")
async def get_branding_public():
    """Devuelve logo y nombre de empresa sin requerir token. Usado por el login."""
    data = await _get_branding()
    return {
        "success": True,
        "data": {
            "nombre_empresa": data.get("nombre_empresa", "TeLOO"),
            "logo_url": data.get("logo_url"),
        },
    }


# ── Authenticated ─────────────────────────────────────────────────────────────

@router.get("/branding", summary="Obtener configuración de branding")
async def get_branding(
    current_user: Usuario = Depends(get_current_active_user),
):
    data = await _get_branding()
    return {"success": True, "data": data}


@router.put("/branding", summary="Actualizar configuración de branding")
async def update_branding(
    payload: BrandingUpdate,
    current_user: Usuario = Depends(require_role([RolUsuario.ADMIN])),
):
    current = await _get_branding()
    current.update(payload.model_dump())
    await _save_branding(current, current_user)
    return {"success": True, "data": current}


@router.post("/branding/logo", summary="Subir logo de la empresa")
async def upload_branding_logo(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(require_role([RolUsuario.ADMIN])),
):
    if file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Formato no permitido. Use PNG, JPG o SVG.")

    content = await file.read()
    if len(content) > _MAX_LOGO_SIZE:
        raise HTTPException(status_code=400, detail="El archivo supera el límite de 2 MB.")

    _LOGO_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower() if file.filename else ".png"
    filename = f"logo_{uuid.uuid4().hex[:8]}{ext}"
    dest = _LOGO_UPLOADS_DIR / filename
    dest.write_bytes(content)

    logo_url = f"/uploads/branding/{filename}"

    current = await _get_branding()

    # Remove previous logo file
    old_url = current.get("logo_url")
    if old_url:
        old_path = Path(old_url.lstrip("/"))
        if old_path.exists():
            old_path.unlink(missing_ok=True)

    current["logo_url"] = logo_url
    await _save_branding(current, current_user)

    return {"success": True, "data": {"logo_url": logo_url}}


# ── Existing endpoint ─────────────────────────────────────────────────────────

@router.get("/public", summary="Obtener configuración pública")
async def get_configuracion_public(
    claves: Optional[List[str]] = Query(None, description="Claves específicas de parámetros"),
    current_user: Usuario = Depends(get_current_active_user),
):
    """
    Obtiene parámetros de configuración pública del sistema.
    Si se proporcionan claves, devuelve solo esos parámetros; de lo contrario devuelve todos.
    """
    from models.analytics import ParametroConfig

    try:
        if claves:
            parametros = await ParametroConfig.filter(clave__in=claves).all()
        else:
            parametros = await ParametroConfig.all()

        result = []
        for param in parametros:
            valor = param.valor_json
            if isinstance(valor, dict) and "valor" in valor:
                valor_str = str(valor["valor"])
                tipo_dato = valor.get("tipo_dato", "string")
            else:
                valor_str = str(valor)
                tipo_dato = "string"

            result.append({
                "clave": param.clave,
                "valor": valor_str,
                "tipo_dato": tipo_dato,
                "descripcion": param.descripcion,
                "metadata": param.metadata_json,
            })

        return result

    except Exception as e:
        import traceback
        print(f"Error in get_configuracion_public: {str(e)}")
        print(traceback.format_exc())
        raise
