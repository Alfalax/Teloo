"""
Shared solicitud creation flow for Telegram and WhatsApp bots.

Both processors call run_solicitud_flow() passing a send_fn callback.
This keeps the conversation logic in one place and platform differences
(Telegram commands, WhatsApp audio, etc.) in each processor.
"""

import logging
import json
import re
import httpx
from typing import Any, Callable, Awaitable, Dict, List, Optional

from app.core.redis import redis_manager
from app.services.solicitud_service import limpiar_ciudad
from app.services.bot_prompts import (
    INTENT_SYSTEM_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    ERR_PROCESS_MSG,
)

logger = logging.getLogger(__name__)

DRAFT_TTL = 86400  # 24 hours — long enough for WhatsApp users who take breaks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def format_repuestos_list(repuestos: list, max_items: int = 7) -> str:
    if not repuestos:
        return "🔧 Repuestos: Ninguno\n"
    n = len(repuestos)
    if n > max_items:
        return f"🔧 Repuestos: {n} items en total\n"
    result = "🔧 Repuestos:\n"
    for rep in repuestos:
        result += f"• {rep.get('cantidad', 1)}x {rep['nombre']}\n"
    return result


def _is_phone_only(message: str, existing_draft: Optional[dict]) -> bool:
    if not existing_draft:
        return False
    if existing_draft.get("_status") == "correcting":
        return False
    digits = re.sub(r'\D', '', message)
    return len(message.strip()) <= 30 and len(digits) == 10 and digits.startswith("3")


def _normalize_phone(raw: str) -> str:
    phone = raw.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not phone.startswith("+57"):
        if phone.startswith("57"):
            phone = "+" + phone
        else:
            phone = "+57" + phone
    return phone


def _phone_digits(raw: str) -> str:
    """Return only the 10-digit part after removing +57/57 prefix."""
    clean = raw.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if clean.startswith("+57"):
        clean = clean[3:]
    elif clean.startswith("57"):
        clean = clean[2:]
    return clean


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_solicitud_flow(
    message_content: str,
    draft_key: str,
    ciudad_invalida_key: str,
    send_fn: Callable[[str], Awaitable[None]],
    settings,
    send_buttons_fn: Optional[Callable[[str, List[Dict[str, str]]], Awaitable[None]]] = None,
) -> Dict[str, Any]:
    """
    Core conversation flow for solicitud creation.

    Args:
        message_content: User's message text (already extracted from platform message)
        draft_key: Redis key for the in-progress solicitud draft
        ciudad_invalida_key: Redis key tracking invalid city attempts
        send_fn: async callable(text: str) — platform-specific send function
        settings: App settings instance
        send_buttons_fn: optional async callable(body_text, buttons) — sends interactive
            buttons (WhatsApp only). When provided, confirmation uses buttons instead of
            "Respondé SÍ" plain-text instructions.
    """
    try:
        existing_draft = await redis_manager.get_json(draft_key)

        if existing_draft:
            if _is_phone_only(message_content, existing_draft):
                digits = re.sub(r'\D', '', message_content)
                existing_draft.setdefault("cliente", {})["telefono"] = digits
                existing_draft.pop("_status", None)
                existing_draft.pop("_last_bot_message", None)
                return await _validate_and_confirm(
                    existing_draft, draft_key, ciudad_invalida_key, send_fn, settings, send_buttons_fn
                )
            return await _handle_draft_intent(
                message_content, existing_draft, draft_key, ciudad_invalida_key, send_fn, settings, send_buttons_fn
            )

        extracted = await _extract_data(message_content, None, draft_key, send_fn, settings)
        if extracted is None:
            return {"success": False, "error": "extraction_failed"}

        extracted.pop("_status", None)
        extracted.pop("_last_bot_message", None)
        return await _validate_and_confirm(
            extracted, draft_key, ciudad_invalida_key, send_fn, settings, send_buttons_fn
        )

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Could not parse data in solicitud flow: {e}")
        await send_fn(
            "🤔 No pude entender tu mensaje correctamente.\n\n"
            "Por favor, enviame la información en este formato:\n\n"
            "Soy [tu nombre], mi teléfono es [+57...], necesito [repuestos] "
            "para [marca modelo año] en [ciudad]\n\n"
            "_Ejemplo: Soy Juan Pérez, mi teléfono es +573001234567, "
            "necesito pastillas de freno para Chevrolet Spark 2015 en Bogotá_"
        )
        return {"success": True, "action": "info_requested"}

    except Exception as e:
        logger.error(f"Unhandled error in solicitud flow: {e}")
        await send_fn(
            "Lo siento, hubo un problema técnico procesando tu solicitud.\n\n"
            "Por favor, intentá de nuevo en unos minutos."
        )
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Intent analysis (existing draft)
# ---------------------------------------------------------------------------


async def _handle_draft_intent(
    message_content: str,
    existing_draft: dict,
    draft_key: str,
    ciudad_invalida_key: str,
    send_fn: Callable[[str], Awaitable[None]],
    settings,
    send_buttons_fn: Optional[Callable[[str, List[Dict[str, str]]], Awaitable[None]]] = None,
) -> Dict[str, Any]:
    draft_context = {
        "cliente": existing_draft.get("cliente", {}),
        "vehiculo": existing_draft.get("vehiculo", {}),
        "repuestos": existing_draft.get("repuestos", []),
    }
    last_bot_message = existing_draft.get("_last_bot_message", "")
    last_repuesto = (
        existing_draft["repuestos"][-1].get("nombre", "")
        if existing_draft.get("repuestos")
        else "Ninguno"
    )

    system_prompt = INTENT_SYSTEM_PROMPT.format(
        draft_context=json.dumps(draft_context, ensure_ascii=False),
        last_repuesto=last_repuesto,
        last_bot_message=last_bot_message,
    )

    from app.services.llm.openai_adapter import openai_adapter
    raw = await openai_adapter.chat_complete(system_prompt, message_content, timeout=15.0)

    if raw is None:
        logger.error("OpenAI intent returned None — failing open as correction attempt")
        existing_draft["_status"] = "correcting"
        await redis_manager.set_json(draft_key, existing_draft, ttl=DRAFT_TTL)
        return {"success": False, "error": "openai_unavailable"}

    try:
        intent_data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse intent JSON: {e}")
        existing_draft["_status"] = "correcting"
        await redis_manager.set_json(draft_key, existing_draft, ttl=DRAFT_TTL)
        return {"success": False, "error": "intent_parse_error"}

    intent = intent_data.get("intent")

    # --- CONFIRM ---
    if intent == "confirm":
        extracted = dict(existing_draft)
        vehiculo = extracted.get("vehiculo", {})
        cliente = extracted.get("cliente", {})

        raw_anio = str(vehiculo.get("anio", "")).strip()
        if not raw_anio.isdigit() or not (1980 <= int(raw_anio) <= 2026):
            await redis_manager.set_json(draft_key, existing_draft, ttl=DRAFT_TTL)
            await send_fn(
                "✅ He guardado los datos, pero me falta saber el *año del vehículo* "
                "(ej: 2022) para poder crear la solicitud.\n\nPor favor, decime el año."
            )
            return {"success": True, "action": "year_requested"}

        extracted.pop("_status", None)
        extracted.pop("_last_bot_message", None)
        await redis_manager.delete(draft_key)
        return await _create_solicitud(extracted, send_fn, settings)

    # --- REJECT ---
    if intent == "reject":
        await redis_manager.delete(draft_key)
        await send_fn(
            "✅ Entendido, cancelé todo.\n\n"
            "Si cambiás de opinión y necesitás repuestos, solo escribime. ¡Estoy aquí para ayudarte!"
        )
        return {"success": True, "action": "cancelled"}

    # --- QUESTION ---
    if intent == "question":
        answer = intent_data.get("answer") or (
            "Entiendo tu pregunta. Los datos que tengo registrados están correctos según lo que me compartiste."
        )
        vehiculo = existing_draft.get("vehiculo", {})
        msg = (
            f"💬 {answer}\n\n"
            f"📋 Resumen actual:\n"
            f"👤 Cliente: {existing_draft['cliente']['nombre']}\n"
            f"📞 Teléfono: {existing_draft['cliente']['telefono']}\n"
            f"📍 Ciudad: {existing_draft['cliente']['ciudad']}\n\n"
            f"🚗 Vehículo: {vehiculo.get('marca','')} {vehiculo.get('linea','')} {vehiculo.get('anio','')}\n\n"
            + format_repuestos_list(existing_draft["repuestos"])
        )
        existing_draft["_last_bot_message"] = msg
        await redis_manager.set_json(draft_key, existing_draft, ttl=DRAFT_TTL)
        await send_fn(msg)
        if send_buttons_fn:
            await send_buttons_fn(
                "¿Está todo correcto?",
                [
                    {"id": "confirm_yes", "title": "Confirmar"},
                    {"id": "confirm_edit", "title": "Corregir algo"},
                    {"id": "confirm_cancel", "title": "Cancelar"},
                ],
            )
        else:
            await send_fn("\n¿Está todo correcto o necesitás ajustar algo?")
        return {"success": True, "action": "question_answered"}

    # --- CORRECT ---
    if intent == "correct":
        msg_lower = message_content.lower().strip()
        if msg_lower in {"no", "nop", "nope", "nel", "no está bien", "no esta bien"}:
            await send_fn(
                "Entiendo. ¿Qué información querés corregir?\n\n"
                "Podés decirme, por ejemplo:\n"
                "• La ciudad es Amagá\n"
                "• El teléfono es 3001234567\n"
                "• Agregá pastillas traseras\n"
                "• El año es 2019"
            )
            return {"success": True, "action": "correction_requested"}

        updated = intent_data.get("updated_data", {})
        if updated.get("cliente"):
            for k, v in updated["cliente"].items():
                if v:
                    existing_draft.setdefault("cliente", {})[k] = v
        if updated.get("vehiculo"):
            for k, v in updated["vehiculo"].items():
                if v:
                    existing_draft.setdefault("vehiculo", {})[k] = v
        if updated.get("repuestos"):
            existing_draft["repuestos"] = updated["repuestos"]

        return await _validate_and_confirm(
            existing_draft, draft_key, ciudad_invalida_key, send_fn, settings, send_buttons_fn
        )

    # Unknown intent — treat as data and re-extract
    extracted = await _extract_data(message_content, existing_draft, draft_key, send_fn, settings)
    if extracted is None:
        return {"success": False, "error": "extraction_failed"}
    extracted.pop("_status", None)
    extracted.pop("_last_bot_message", None)
    return await _validate_and_confirm(extracted, draft_key, ciudad_invalida_key, send_fn, settings, send_buttons_fn)


# ---------------------------------------------------------------------------
# Data extraction (no draft)
# ---------------------------------------------------------------------------


async def _extract_data(
    message_content: str,
    existing_draft: Optional[dict],
    draft_key: str,
    send_fn: Callable[[str], Awaitable[None]],
    settings,
) -> Optional[dict]:
    from app.services.llm.openai_adapter import openai_adapter
    raw = await openai_adapter.chat_complete(EXTRACTION_SYSTEM_PROMPT, message_content, timeout=30.0)

    if raw is None:
        logger.error("OpenAI extraction returned None")
        await send_fn(ERR_PROCESS_MSG)
        return None

    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse extraction JSON: {e} — raw: {raw[:200]}")
        await send_fn(ERR_PROCESS_MSG)
        return None

    if existing_draft:
        # Merge: only fill empty fields in the existing draft
        if not existing_draft.get("repuestos") and extracted.get("repuestos"):
            existing_draft["repuestos"] = extracted["repuestos"]
        v_draft = existing_draft.setdefault("vehiculo", {})
        v_new = extracted.get("vehiculo", {})
        for field in ("marca", "linea", "anio"):
            if not v_draft.get(field) and v_new.get(field):
                v_draft[field] = v_new[field]
        c_draft = existing_draft.setdefault("cliente", {})
        c_new = extracted.get("cliente", {})
        for field in ("nombre", "telefono", "ciudad"):
            if not c_draft.get(field) and c_new.get(field):
                c_draft[field] = c_new[field]
        return existing_draft

    return extracted


# ---------------------------------------------------------------------------
# Validation and confirmation request
# ---------------------------------------------------------------------------

async def _validate_and_confirm(
    extracted_data: dict,
    draft_key: str,
    ciudad_invalida_key: str,
    send_fn: Callable[[str], Awaitable[None]],
    settings,
    send_buttons_fn: Optional[Callable[[str, List[Dict[str, str]]], Awaitable[None]]] = None,
) -> Dict[str, Any]:
    vehiculo = extracted_data.get("vehiculo", {})
    cliente = extracted_data.get("cliente", {})

    missing_fields = []

    if not extracted_data.get("repuestos"):
        missing_fields.append("repuestos")

    if not vehiculo.get("marca"):
        missing_fields.append("marca del vehículo")
    if not vehiculo.get("anio"):
        missing_fields.append("año del vehículo")

    if not cliente.get("nombre"):
        missing_fields.append("nombre del cliente")

    if not cliente.get("telefono"):
        missing_fields.append("teléfono del cliente")
    else:
        digits = _phone_digits(cliente["telefono"])
        if len(digits) != 10 or not digits.isdigit():
            extracted_data["_status"] = "invalid_phone"
            await redis_manager.set_json(draft_key, extracted_data, ttl=DRAFT_TTL)
            msg = (
                f"⚠️ El teléfono '{cliente['telefono']}' no es válido.\n\n"
                "📱 Por favor, enviame un teléfono colombiano completo con 10 dígitos.\n\n"
                "Ejemplo: 3001234567\n\n"
                "✅ Ya tengo guardado:\n"
            )
            if cliente.get("nombre"):
                msg += f"• Nombre: {cliente['nombre']}\n"
            if extracted_data.get("repuestos"):
                msg += f"• {len(extracted_data['repuestos'])} repuesto(s)\n"
            if vehiculo.get("marca"):
                msg += f"• Vehículo: {vehiculo.get('marca','')} {vehiculo.get('linea','')}\n"
            if cliente.get("ciudad"):
                msg += f"• Ciudad: {cliente['ciudad']}\n"
            await send_fn(msg)
            return {"success": True, "action": "invalid_phone_detected"}

    if not cliente.get("ciudad"):
        missing_fields.append("ciudad")

    if missing_fields:
        await redis_manager.set_json(draft_key, extracted_data, ttl=DRAFT_TTL)
        msg = "🤔 Para crear tu solicitud necesito la siguiente información:\n\n"
        for field in missing_fields:
            msg += f"❌ {field}\n"
        if extracted_data.get("repuestos"):
            msg += f"\n✅ Ya tengo: {len(extracted_data['repuestos'])} repuesto(s)\n"
        if vehiculo.get("marca"):
            msg += f"✅ Ya tengo: Vehículo {vehiculo.get('marca','')} {vehiculo.get('linea','')}\n"
        msg += "\n📝 Por favor enviame la información que falta."
        await send_fn(msg)
        return {"success": True, "action": "info_requested", "missing_fields": missing_fields}

    # All fields present — validate city
    ciudad_normalizada = limpiar_ciudad(cliente["ciudad"])

    try:
        async with httpx.AsyncClient(timeout=10.0) as geo_client:
            geo_resp = await geo_client.get(
                f"{settings.core_api_url}/v1/solicitudes/services/municipio",
                params={"ciudad": ciudad_normalizada},
                headers={
                    "X-Service-Name": str(settings.service_name or "agent-ia"),
                    "X-Service-API-Key": str(settings.service_api_key or ""),
                },
            )
    except Exception as e:
        logger.error(f"City validation request failed: {e}")
        geo_resp = None

    if geo_resp and geo_resp.status_code == 200:
        municipio_data = geo_resp.json()
        departamento = municipio_data["departamento"]
        ciudad_display = f"{ciudad_normalizada.title()} - {departamento}"
        extracted_data["cliente"]["ciudad_display"] = ciudad_display
        extracted_data["_municipio_id"] = municipio_data["id"]
        extracted_data["_departamento"] = departamento

        telefono_display = cliente["telefono"].replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

        summary_msg = (
            "📋 Perfecto, aquí está el resumen:\n\n"
            f"👤 Cliente: {cliente['nombre']}\n"
            f"📞 Teléfono: {telefono_display}\n"
            f"📍 Ciudad: {ciudad_normalizada.title()}\n\n"
            f"🚗 Vehículo: {vehiculo.get('marca','')} {vehiculo.get('linea','')} {vehiculo.get('anio','')}\n\n"
            "🔧 Repuestos:\n"
            + format_repuestos_list(extracted_data["repuestos"]).rstrip("\n")
        )

        extracted_data["_status"] = "pending_confirmation"
        extracted_data["_last_bot_message"] = summary_msg
        await redis_manager.set_json(draft_key, extracted_data, ttl=DRAFT_TTL)

        if send_buttons_fn:
            await send_fn(summary_msg)
            await send_buttons_fn(
                "¿Todo está correcto?",
                [
                    {"id": "confirm_yes", "title": "Confirmar"},
                    {"id": "confirm_edit", "title": "Corregir algo"},
                    {"id": "confirm_cancel", "title": "Cancelar"},
                ],
            )
        else:
            await send_fn(summary_msg + "\n\n¿Todo está bien? Respondé *SÍ* para confirmar o decime qué querés corregir.")

        return {"success": True, "action": "confirmation_requested"}

    # City not found
    ciudad_anterior = await redis_manager.get(ciudad_invalida_key)
    if ciudad_anterior:
        if isinstance(ciudad_anterior, bytes):
            ciudad_anterior = ciudad_anterior.decode("utf-8")
        ciudad_anterior = ciudad_anterior.upper()

    if ciudad_anterior and ciudad_anterior == ciudad_normalizada:
        await redis_manager.delete(draft_key)
        await redis_manager.delete(ciudad_invalida_key)
        await send_fn(
            f"😔 Entiendo, gracias por verificar.\n\n"
            f"Lamentablemente, en este momento no tenemos cobertura en {cliente['ciudad']}.\n\n"
            "📍 Operamos solo en ciudades donde tenemos asesores registrados.\n\n"
            "Si en el futuro necesitás repuestos en otra ciudad donde sí tengamos servicio, "
            "con gusto te ayudo. ¡Estoy aquí cuando me necesités! 😊"
        )
        return {"success": False, "error": "sin_cobertura"}

    await redis_manager.set(ciudad_invalida_key, ciudad_normalizada, ttl=DRAFT_TTL)
    extracted_data["_status"] = "pending_confirmation"
    extracted_data["_last_bot_message"] = f"Verificando ciudad '{cliente['ciudad']}'"
    await redis_manager.set_json(draft_key, extracted_data, ttl=DRAFT_TTL)
    await send_fn(
        f"🤔 No encontré la ciudad '{cliente['ciudad']}' en nuestra base de datos.\n\n"
        "¿Podrías verificar el nombre? A veces hay errores de escritura.\n\n"
        "Si el nombre es correcto, es posible que aún no tengamos cobertura en esa zona."
    )
    return {"success": True, "action": "ciudad_validation_pending"}


# ---------------------------------------------------------------------------
# Solicitud creation
# ---------------------------------------------------------------------------

async def _create_solicitud(
    extracted_data: dict,
    send_fn: Callable[[str], Awaitable[None]],
    settings,
) -> Dict[str, Any]:
    vehiculo = extracted_data.get("vehiculo", {})
    cliente = extracted_data.get("cliente", {})

    raw_anio = str(vehiculo.get("anio", "")).strip()
    if not raw_anio.isdigit() or not (1980 <= int(raw_anio) <= 2026):
        await send_fn(
            "✅ He guardado los datos, pero me falta saber el *año del vehículo* "
            "(ej: 2022) para poder crear la solicitud.\n\nPor favor, decime el año."
        )
        return {"success": True, "action": "year_requested"}

    anio = int(raw_anio)

    repuestos_formatted = [
        {
            "nombre": r["nombre"],
            "cantidad": r.get("cantidad", 1),
            "marca_vehiculo": vehiculo.get("marca", "N/A"),
            "linea_vehiculo": vehiculo.get("linea") or "N/A",
            "anio_vehiculo": anio,
            "observaciones": r.get("observaciones", ""),
        }
        for r in extracted_data["repuestos"]
    ]

    telefono = _normalize_phone(cliente["telefono"])
    if len(telefono) != 13:
        await send_fn(
            f"⚠️ El teléfono '{cliente['telefono']}' parece incompleto.\n\n"
            "📱 Por favor, enviame tu teléfono completo con 10 dígitos.\n\nEjemplo: 3001234567"
        )
        return {"success": True, "action": "phone_requested"}

    municipio_id = extracted_data.get("_municipio_id")
    departamento = extracted_data.get("_departamento")
    ciudad_display = cliente.get("ciudad_display", cliente["ciudad"])

    ciudad_para_bd = cliente["ciudad"]
    if " - " in ciudad_para_bd:
        ciudad_para_bd = ciudad_para_bd.split(" - ")[0].strip()
    ciudad_normalizada = limpiar_ciudad(ciudad_para_bd)

    payload = {
        "cliente": {"nombre": cliente["nombre"], "telefono": telefono},
        "municipio_id": municipio_id,
        "ciudad_origen": ciudad_normalizada,
        "departamento_origen": departamento,
        "repuestos": repuestos_formatted,
    }
    if cliente.get("email"):
        payload["cliente"]["email"] = cliente["email"]

    try:
        async with httpx.AsyncClient(timeout=30.0) as api_client:
            api_resp = await api_client.post(
                f"{settings.core_api_url}/v1/solicitudes/services/bot",
                json=payload,
                headers={
                    "X-Service-Name": str(settings.service_name or "agent-ia"),
                    "X-Service-API-Key": str(settings.service_api_key or ""),
                },
            )
    except Exception as e:
        logger.error(f"Error calling core-api to create solicitud: {e}")
        await send_fn(
            "❌ Error al crear la solicitud. Por favor intentá de nuevo en unos minutos."
        )
        return {"success": False, "error": str(e)}

    if api_resp.status_code == 201:
        result = api_resp.json()
        solicitud_id = result["id"]
        codigo = result.get("codigo_solicitud", solicitud_id[:8] + "...")

        msg = (
            f"✅ ¡Solicitud creada!\n\n"
            f"📋 Número: {codigo}\n\n"
            f"👤 Cliente: {cliente['nombre']}\n"
            f"📞 Teléfono: {telefono}\n"
            f"📍 Ciudad: {ciudad_display}\n\n"
            f"🚗 Vehículo: {vehiculo.get('marca','')} {vehiculo.get('linea','')} {vehiculo.get('anio','')}\n\n"
            + format_repuestos_list(extracted_data["repuestos"])
            + "\n🔍 Estamos buscando las mejores ofertas para vos. "
            "Te avisamos cuando tengamos propuestas. ¡Gracias por usar TeLOO! 🚗"
        )
        await send_fn(msg)
        return {"success": True, "action": "solicitud_created", "solicitud_id": solicitud_id}

    logger.error(f"Core API error creating solicitud: {api_resp.status_code} — {api_resp.text}")
    await send_fn(
        f"❌ Error al crear la solicitud ({api_resp.status_code}).\n\n"
        "Por favor intentá de nuevo más tarde."
    )
    return {"success": False, "error": f"api_error_{api_resp.status_code}"}
