"""
Service for sending evaluation results to clients via WhatsApp
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal

from app.core.config import settings
from app.services.whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)


class ResultsService:
    """Service for sending evaluation results to clients"""
    
    def __init__(self):
        self.core_api_url = settings.core_api_url
        self.timeout = settings.core_api_timeout
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Content-Type": "application/json"
            }
        )
    
    async def enviar_resultado_evaluacion(self, solicitud_id: str) -> Dict[str, Any]:
        """
        Main function to send evaluation results to client
        
        Args:
            solicitud_id: ID of the solicitud to send results for
            
        Returns:
            Dict with operation result
        """
        try:
            logger.info(f"Sending evaluation results for solicitud {solicitud_id}")
            
            # Get evaluation results from Core API
            evaluation_data = await self._get_evaluation_results(solicitud_id)
            if not evaluation_data["success"]:
                return {
                    "success": False,
                    "error": "No se pudieron obtener los resultados de evaluación",
                    "details": evaluation_data["error"]
                }
            
            solicitud = evaluation_data["solicitud"]
            adjudicaciones = evaluation_data["adjudicaciones"]
            
            if not adjudicaciones:
                return {
                    "success": False,
                    "error": "No hay ofertas ganadoras para enviar",
                    "solicitud_id": solicitud_id
                }
            
            # Get client phone number
            client_phone = solicitud.get("cliente", {}).get("telefono")
            if not client_phone:
                return {
                    "success": False,
                    "error": "No se encontró el teléfono del cliente",
                    "solicitud_id": solicitud_id
                }
            
            # Determine message type and format message
            message = await self._format_result_message(solicitud, adjudicaciones)
            
            # Send message to client
            success = await whatsapp_service.send_text_message(client_phone, message)
            
            if success:
                logger.info(f"Evaluation results sent successfully to {client_phone}")
                return {
                    "success": True,
                    "solicitud_id": solicitud_id,
                    "client_phone": client_phone,
                    "message": "Resultados enviados exitosamente"
                }
            else:
                return {
                    "success": False,
                    "error": "Error enviando mensaje por WhatsApp",
                    "solicitud_id": solicitud_id
                }
                
        except Exception as e:
            logger.error(f"Error sending evaluation results for {solicitud_id}: {e}")
            return {
                "success": False,
                "error": "Error interno del sistema",
                "details": str(e),
                "solicitud_id": solicitud_id
            }
    
    async def _get_evaluation_results(self, solicitud_id: str) -> Dict[str, Any]:
        """Get evaluation results from Core API"""
        try:
            # Get solicitud with adjudications
            response = await self.client.get(
                f"{self.core_api_url}/v1/solicitudes/{solicitud_id}/resultados"
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "solicitud": data["solicitud"],
                    "adjudicaciones": data["adjudicaciones"]
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "Solicitud no encontrada"
                }
            else:
                logger.error(f"Failed to get evaluation results: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Error obteniendo resultados: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error getting evaluation results: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _format_result_message(self, solicitud: Dict[str, Any], adjudicaciones: List[Dict[str, Any]]) -> str:
        """Format result message based on type (single vs mixed offer)"""
        try:
            # Determine if it's a single or mixed adjudication
            unique_asesores = set(adj["asesor"]["id"] for adj in adjudicaciones)
            is_mixed = len(unique_asesores) > 1
            
            if is_mixed:
                return await self._format_mixed_offer_message(solicitud, adjudicaciones)
            else:
                return await self._format_single_offer_message(solicitud, adjudicaciones)
                
        except Exception as e:
            logger.error(f"Error formatting result message: {e}")
            return "Error formateando el mensaje de resultados."
    
    async def _format_single_offer_message(self, solicitud: Dict[str, Any], adjudicaciones: List[Dict[str, Any]]) -> str:
        """Format message for single offer (Requirement 6.1)"""
        try:
            # Get the single asesor
            asesor = adjudicaciones[0]["asesor"]
            
            # Calculate totals
            total_precio = sum(Decimal(str(adj["precio_adjudicado"])) * adj["cantidad_adjudicada"] for adj in adjudicaciones)
            
            # Get delivery time (use the maximum from all items)
            tiempo_entrega = max(adj["tiempo_entrega_adjudicado"] for adj in adjudicaciones)
            
            # Get warranty (use the minimum from all items)
            garantia = min(adj["garantia_adjudicada"] for adj in adjudicaciones)
            
            # Format repuestos list
            repuestos_list = []
            for adj in adjudicaciones:
                nombre = adj["repuesto_solicitado"]["nombre"]
                cantidad = adj["cantidad_adjudicada"]
                precio_unit = Decimal(str(adj["precio_adjudicado"]))
                precio_total = precio_unit * cantidad
                
                if cantidad > 1:
                    repuestos_list.append(f"• {cantidad}x {nombre} - ${precio_total:,.0f}")
                else:
                    repuestos_list.append(f"• {nombre} - ${precio_total:,.0f}")
            
            # Format delivery time
            if tiempo_entrega == 0:
                tiempo_str = "Inmediato"
            elif tiempo_entrega == 1:
                tiempo_str = "1 día"
            else:
                tiempo_str = f"{tiempo_entrega} días"
            
            # Format warranty
            if garantia == 1:
                garantia_str = "1 mes"
            elif garantia < 12:
                garantia_str = f"{garantia} meses"
            else:
                años = garantia // 12
                meses_restantes = garantia % 12
                if meses_restantes == 0:
                    garantia_str = f"{años} año{'s' if años > 1 else ''}"
                else:
                    garantia_str = f"{años} año{'s' if años > 1 else ''} y {meses_restantes} mes{'es' if meses_restantes > 1 else ''}"
            
            message = f"""🎉 *¡Tenemos una oferta para ti!*

*Solicitud:* {solicitud['codigo_solicitud']}

*Repuestos ofrecidos:*
{chr(10).join(repuestos_list)}

*💰 Precio total:* ${total_precio:,.0f}
*🚚 Tiempo de entrega:* {tiempo_str}
*🛡️ Garantía:* {garantia_str}
*🏪 Proveedor:* {asesor['usuario']['nombre_completo']}
*📍 Ubicación:* {asesor['punto_venta']}, {asesor['ciudad']}

*¿Qué deseas hacer?*
Responde con:
• *SÍ* - Para aceptar la oferta
• *NO* - Para rechazar la oferta  
• *DETALLES* - Para más información

¡Esperamos tu respuesta! 😊"""
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting single offer message: {e}")
            return "Error formateando mensaje de oferta única."
    
    async def _format_mixed_offer_message(self, solicitud: Dict[str, Any], adjudicaciones: List[Dict[str, Any]]) -> str:
        """Format message for mixed offers (Requirement 6.2)"""
        try:
            # Group adjudications by asesor
            asesores_dict = {}
            for adj in adjudicaciones:
                asesor_id = adj["asesor"]["id"]
                if asesor_id not in asesores_dict:
                    asesores_dict[asesor_id] = {
                        "asesor": adj["asesor"],
                        "repuestos": [],
                        "total_precio": Decimal('0')
                    }
                
                precio_total = Decimal(str(adj["precio_adjudicado"])) * adj["cantidad_adjudicada"]
                asesores_dict[asesor_id]["repuestos"].append({
                    "nombre": adj["repuesto_solicitado"]["nombre"],
                    "cantidad": adj["cantidad_adjudicada"],
                    "precio_total": precio_total
                })
                asesores_dict[asesor_id]["total_precio"] += precio_total
            
            # Calculate totals
            total_precio_general = sum(Decimal(str(adj["precio_adjudicado"])) * adj["cantidad_adjudicada"] for adj in adjudicaciones)
            total_repuestos = len(adjudicaciones)
            num_asesores = len(asesores_dict)
            
            # Format asesores summary
            asesores_summary = []
            for asesor_data in asesores_dict.values():
                asesor = asesor_data["asesor"]
                repuestos = asesor_data["repuestos"]
                total_asesor = asesor_data["total_precio"]
                
                repuestos_str = ", ".join([
                    f"{r['cantidad']}x {r['nombre']}" if r['cantidad'] > 1 else r['nombre']
                    for r in repuestos
                ])
                
                asesores_summary.append(
                    f"*{asesor['usuario']['nombre_completo']}* ({asesor['ciudad']})\n"
                    f"  {repuestos_str}\n"
                    f"  Subtotal: ${total_asesor:,.0f}"
                )
            
            message = f"""🎉 *¡Tenemos ofertas para ti!*

*Solicitud:* {solicitud['codigo_solicitud']}

*Resumen de ofertas:*
• {total_repuestos} repuesto{'s' if total_repuestos > 1 else ''} cubierto{'s' if total_repuestos > 1 else ''}
• {num_asesores} proveedor{'es' if num_asesores > 1 else ''} seleccionado{'s' if num_asesores > 1 else ''}

*Distribución por proveedor:*
{chr(10).join(asesores_summary)}

*💰 Precio total:* ${total_precio_general:,.0f}

*¿Qué deseas hacer?*
Responde con:
• *SÍ* - Para aceptar todas las ofertas
• *NO* - Para rechazar todas las ofertas
• *DETALLES* - Para más información de cada proveedor

¡Esperamos tu respuesta! 😊"""
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting mixed offer message: {e}")
            return "Error formateando mensaje de ofertas múltiples."
    
    async def handle_client_response(self, phone_number: str, response: str, solicitud_id: str) -> Dict[str, Any]:
        """
        Handle client response to evaluation results (Requirement 6.3)
        
        Args:
            phone_number: Client phone number
            response: Client response (SÍ, NO, DETALLES)
            solicitud_id: ID of the solicitud
            
        Returns:
            Dict with operation result
        """
        try:
            response_normalized = response.upper().strip()
            
            if response_normalized in ["SI", "SÍ", "YES", "ACEPTO", "ACEPTAR"]:
                return await self._handle_accept_response(phone_number, solicitud_id)
            elif response_normalized in ["NO", "RECHAZO", "RECHAZAR"]:
                return await self._handle_reject_response(phone_number, solicitud_id)
            elif response_normalized in ["DETALLES", "DETALLE", "INFO", "INFORMACIÓN", "MAS INFO"]:
                return await self._handle_details_response(phone_number, solicitud_id)
            else:
                # Send clarification message
                clarification_msg = """No entendí tu respuesta. Por favor responde con:

• *SÍ* - Para aceptar la oferta
• *NO* - Para rechazar la oferta
• *DETALLES* - Para más información

¿Cuál es tu decisión? 🤔"""
                
                await whatsapp_service.send_text_message(phone_number, clarification_msg)
                
                return {
                    "success": True,
                    "action": "clarification_sent",
                    "message": "Mensaje de aclaración enviado"
                }
                
        except Exception as e:
            logger.error(f"Error handling client response: {e}")
            return {
                "success": False,
                "error": "Error procesando respuesta del cliente",
                "details": str(e)
            }
    
    async def _handle_accept_response(self, phone_number: str, solicitud_id: str) -> Dict[str, Any]:
        """Handle client acceptance"""
        try:
            # Update offers status to ACEPTADA in Core API
            response = await self.client.post(
                f"{self.core_api_url}/v1/solicitudes/{solicitud_id}/aceptar"
            )
            
            if response.status_code == 200:
                # Send confirmation message
                confirmation_msg = """✅ *¡Perfecto! Oferta aceptada*

Hemos notificado a tu(s) proveedor(es) y pronto se pondrán en contacto contigo para coordinar la entrega.

*Próximos pasos:*
• El proveedor te contactará directamente
• Coordinarán lugar y forma de entrega
• Realizarás el pago según lo acordado

¡Gracias por usar TeLOO! 🚗✨"""
                
                await whatsapp_service.send_text_message(phone_number, confirmation_msg)
                
                return {
                    "success": True,
                    "action": "accepted",
                    "message": "Oferta aceptada exitosamente"
                }
            else:
                logger.error(f"Failed to accept offers: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": "Error aceptando la oferta en el sistema"
                }
                
        except Exception as e:
            logger.error(f"Error handling accept response: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_reject_response(self, phone_number: str, solicitud_id: str) -> Dict[str, Any]:
        """Handle client rejection"""
        try:
            # Update offers status to RECHAZADA in Core API
            response = await self.client.post(
                f"{self.core_api_url}/v1/solicitudes/{solicitud_id}/rechazar"
            )
            
            if response.status_code == 200:
                # Send confirmation message
                confirmation_msg = """❌ *Oferta rechazada*

Entendemos que la oferta no cumplió con tus expectativas.

*¿Te gustaría hacer una nueva solicitud?*
Simplemente envíanos los repuestos que necesitas y buscaremos nuevas opciones para ti.

¡Estamos aquí para ayudarte! 🚗"""
                
                await whatsapp_service.send_text_message(phone_number, confirmation_msg)
                
                return {
                    "success": True,
                    "action": "rejected",
                    "message": "Oferta rechazada exitosamente"
                }
            else:
                logger.error(f"Failed to reject offers: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": "Error rechazando la oferta en el sistema"
                }
                
        except Exception as e:
            logger.error(f"Error handling reject response: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_details_response(self, phone_number: str, solicitud_id: str) -> Dict[str, Any]:
        """Handle client request for details"""
        try:
            # Get detailed information
            evaluation_data = await self._get_evaluation_results(solicitud_id)
            if not evaluation_data["success"]:
                return {
                    "success": False,
                    "error": "No se pudieron obtener los detalles"
                }
            
            adjudicaciones = evaluation_data["adjudicaciones"]
            
            # Format detailed message
            details_msg = await self._format_detailed_message(adjudicaciones)
            
            await whatsapp_service.send_text_message(phone_number, details_msg)
            
            # Send follow-up question
            followup_msg = """*¿Qué decides?*
• *SÍ* - Para aceptar la oferta
• *NO* - Para rechazar la oferta

¿Cuál es tu decisión? 🤔"""
            
            await whatsapp_service.send_text_message(phone_number, followup_msg)
            
            return {
                "success": True,
                "action": "details_sent",
                "message": "Detalles enviados exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error handling details response: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _format_detailed_message(self, adjudicaciones: List[Dict[str, Any]]) -> str:
        """Format detailed information message"""
        try:
            details_sections = []
            
            # Group by asesor
            asesores_dict = {}
            for adj in adjudicaciones:
                asesor_id = adj["asesor"]["id"]
                if asesor_id not in asesores_dict:
                    asesores_dict[asesor_id] = {
                        "asesor": adj["asesor"],
                        "repuestos": []
                    }
                asesores_dict[asesor_id]["repuestos"].append(adj)
            
            for asesor_data in asesores_dict.values():
                asesor = asesor_data["asesor"]
                repuestos = asesor_data["repuestos"]
                
                # Format asesor section
                section = f"""*🏪 {asesor['usuario']['nombre_completo']}*
📍 {asesor['punto_venta']}, {asesor['ciudad']}

*Repuestos ofrecidos:*"""
                
                for adj in repuestos:
                    nombre = adj["repuesto_solicitado"]["nombre"]
                    cantidad = adj["cantidad_adjudicada"]
                    precio_unit = Decimal(str(adj["precio_adjudicado"]))
                    precio_total = precio_unit * cantidad
                    tiempo = adj["tiempo_entrega_adjudicado"]
                    garantia = adj["garantia_adjudicada"]
                    
                    # Format delivery time
                    if tiempo == 0:
                        tiempo_str = "Inmediato"
                    elif tiempo == 1:
                        tiempo_str = "1 día"
                    else:
                        tiempo_str = f"{tiempo} días"
                    
                    # Format warranty
                    if garantia == 1:
                        garantia_str = "1 mes"
                    elif garantia < 12:
                        garantia_str = f"{garantia} meses"
                    else:
                        años = garantia // 12
                        meses_restantes = garantia % 12
                        if meses_restantes == 0:
                            garantia_str = f"{años} año{'s' if años > 1 else ''}"
                        else:
                            garantia_str = f"{años} año{'s' if años > 1 else ''} y {meses_restantes} mes{'es' if meses_restantes > 1 else ''}"
                    
                    cantidad_str = f"{cantidad}x " if cantidad > 1 else ""
                    
                    section += f"""
• {cantidad_str}{nombre}
  💰 ${precio_total:,.0f} (${precio_unit:,.0f} c/u)
  🚚 {tiempo_str}
  🛡️ {garantia_str}"""
                
                details_sections.append(section)
            
            message = f"""📋 *Detalles completos de la oferta*

{chr(10).join(details_sections)}

*Información importante:*
• Los precios incluyen garantía
• El tiempo de entrega se cuenta desde la confirmación
• El pago se coordina directamente con cada proveedor"""
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting detailed message: {e}")
            return "Error formateando los detalles de la oferta."
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global results service instance
results_service = ResultsService()