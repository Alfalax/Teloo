"""
Service for creating solicitudes from WhatsApp conversations
"""

import logging
import httpx
import json
import unicodedata
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

from app.models.llm import ProcessedData
from app.models.conversation import ConversationContext
from app.core.config import settings
from app.services.whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)


def limpiar_ciudad(ciudad: str) -> str:
    """
    Limpia el nombre de la ciudad removiendo departamentos que las personas suelen agregar.
    
    Ejemplos:
        "Bello Antioquia" -> "BELLO"
        "Cali Valle" -> "CALI"
        "Medellín Antioquia" -> "MEDELLIN"
        "Medellin - ANTIOQUIA" -> "MEDELLIN"
    
    Args:
        ciudad: Nombre de la ciudad posiblemente con departamento
        
    Returns:
        Nombre de la ciudad limpio y normalizado (sin tildes, mayúsculas)
    """
    if not ciudad:
        return ""
    
    ciudad_limpia = ciudad.strip()
    
    # Departamentos de Colombia que las personas suelen agregar
    departamentos_colombia = [
        'ANTIOQUIA', 'VALLE DEL CAUCA', 'VALLE', 'CUNDINAMARCA', 'ATLANTICO', 
        'BOLIVAR', 'SANTANDER', 'NORTE DE SANTANDER', 'CAUCA', 'NARIÑO', 'NARINO',
        'TOLIMA', 'HUILA', 'META', 'CORDOBA', 'CESAR', 'MAGDALENA', 
        'BOYACA', 'CALDAS', 'RISARALDA', 'QUINDIO', 'CHOCO', 'SUCRE',
        'LA GUAJIRA', 'GUAJIRA', 'CASANARE', 'ARAUCA', 'PUTUMAYO',
        'CAQUETA', 'VICHADA', 'GUAINIA', 'GUAVIARE', 'VAUPES', 'AMAZONAS'
    ]
    
    # Normalizar: quitar tildes y convertir a mayúsculas
    ciudad_normalizada = ''.join(
        c for c in unicodedata.normalize('NFD', ciudad_limpia)
        if unicodedata.category(c) != 'Mn'
    ).upper()
    
    # Remover separadores comunes (guión, coma, etc.) y reemplazar por espacios
    # Esto maneja casos como "Medellin - ANTIOQUIA" o "Medellin-ANTIOQUIA"
    ciudad_normalizada = ciudad_normalizada.replace(' - ', ' ')
    ciudad_normalizada = ciudad_normalizada.replace('-', ' ')
    ciudad_normalizada = ciudad_normalizada.replace(',', ' ')
    ciudad_normalizada = ciudad_normalizada.replace('  ', ' ')
    
    # Limpiar espacios múltiples y trim
    ciudad_normalizada = ' '.join(ciudad_normalizada.split()).strip()
    
    # Remover departamento si está presente al final o al inicio
    for depto in departamentos_colombia:
        # Buscar al final (caso más común: "MEDELLIN ANTIOQUIA")
        if ciudad_normalizada.endswith(f" {depto}"):
            ciudad_normalizada = ciudad_normalizada[:-len(f" {depto}")].strip()
            logger.info(f"Ciudad limpiada: '{ciudad}' -> '{ciudad_normalizada}'")
            break
        # Buscar al inicio (caso menos común: "ANTIOQUIA MEDELLIN")
        elif ciudad_normalizada.startswith(f"{depto} "):
            ciudad_normalizada = ciudad_normalizada[len(f"{depto} "):].strip()
            logger.info(f"Ciudad limpiada: '{ciudad}' -> '{ciudad_normalizada}'")
            break
    
    # Limpieza final: remover cualquier guión o espacio sobrante
    ciudad_normalizada = ciudad_normalizada.strip(' -')
    
    return ciudad_normalizada


class SolicitudService:
    """Service for creating solicitudes in the Core API"""
    
    def __init__(self):
        self.core_api_url = settings.core_api_url
        self.timeout = settings.core_api_timeout
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Content-Type": "application/json"
            }
        )
    
    async def create_solicitud_from_whatsapp(self, solicitud_data: Dict[str, Any]) -> Optional[str]:
        """
        Create solicitud from conversation data (simplified interface)
        
        Args:
            solicitud_data: Dict with cliente, vehiculo, repuestos, conversation_id
            
        Returns:
            Solicitud ID if successful, None if failed
        """
        try:
            # Prepare data for Core API
            core_api_data = {
                "cliente_id": None,  # Will be set after creating/getting cliente
                "ciudad_origen": solicitud_data.get("cliente", {}).get("ciudad", ""),
                "departamento_origen": solicitud_data.get("cliente", {}).get("departamento", ""),
                "metadata_json": {
                    "origen": "whatsapp",
                    "conversation_id": solicitud_data.get("conversation_id", ""),
                    "created_from_agent_ia": True
                }
            }
            
            # Create or get cliente
            cliente_result = await self._create_or_get_cliente(solicitud_data["cliente"])
            if not cliente_result["success"]:
                logger.error(f"Failed to create/get cliente: {cliente_result['error']}")
                return None
            
            core_api_data["cliente_id"] = cliente_result["cliente_id"]
            
            # Prepare repuestos data
            repuestos_data = []
            for repuesto in solicitud_data.get("repuestos", []):
                repuesto_data = {
                    "nombre": repuesto.get("nombre", "").strip(),
                    "cantidad": repuesto.get("cantidad", 1),
                    "marca_vehiculo": solicitud_data.get("vehiculo", {}).get("marca", ""),
                    "linea_vehiculo": solicitud_data.get("vehiculo", {}).get("linea", ""),
                    "anio_vehiculo": int(solicitud_data.get("vehiculo", {}).get("anio", 0)) if solicitud_data.get("vehiculo", {}).get("anio") else None,
                    "observaciones": repuesto.get("especificaciones", "") or repuesto.get("observaciones", "")
                }
                
                if repuesto.get("codigo"):
                    repuesto_data["codigo"] = repuesto["codigo"]
                
                repuestos_data.append(repuesto_data)
            
            core_api_data["repuestos"] = repuestos_data
            
            # Create solicitud
            solicitud_result = await self._create_solicitud(core_api_data)
            if solicitud_result["success"]:
                return solicitud_result["solicitud_id"]
            else:
                logger.error(f"Failed to create solicitud: {solicitud_result['error']}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating solicitud from WhatsApp: {e}")
            return None
    
    async def crear_solicitud_desde_whatsapp(self, datos_extraidos: ProcessedData, conversation: ConversationContext) -> Dict[str, Any]:
        """
        Main function to create solicitud from WhatsApp data
        
        Args:
            datos_extraidos: Processed data from NLP
            conversation: Conversation context with accumulated data
            
        Returns:
            Dict with solicitud creation result
        """
        try:
            logger.info(f"Creating solicitud from WhatsApp for {conversation.phone_number}")
            
            # Validate extracted data
            validation_result = await self._validate_datos_extraidos(datos_extraidos, conversation)
            if not validation_result["is_valid"]:
                return {
                    "success": False,
                    "error": "Datos incompletos",
                    "validation_errors": validation_result["errors"],
                    "missing_fields": validation_result["missing_fields"]
                }
            
            # Prepare solicitud data
            solicitud_data = await self._prepare_solicitud_data(datos_extraidos, conversation)
            
            # Create or get cliente
            cliente_result = await self._create_or_get_cliente(solicitud_data["cliente"])
            if not cliente_result["success"]:
                return {
                    "success": False,
                    "error": "Error creando cliente",
                    "details": cliente_result["error"]
                }
            
            cliente_id = cliente_result["cliente_id"]
            solicitud_data["cliente_id"] = cliente_id
            
            # Create solicitud
            solicitud_result = await self._create_solicitud(solicitud_data)
            if not solicitud_result["success"]:
                return {
                    "success": False,
                    "error": "Error creando solicitud",
                    "details": solicitud_result["error"]
                }
            
            solicitud_id = solicitud_result["solicitud_id"]
            
            # Send confirmation to client
            await self._send_confirmation_message(conversation.phone_number, solicitud_id, solicitud_data)
            
            return {
                "success": True,
                "solicitud_id": solicitud_id,
                "cliente_id": cliente_id,
                "message": "Solicitud creada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error creating solicitud from WhatsApp: {e}")
            return {
                "success": False,
                "error": "Error interno del sistema",
                "details": str(e)
            }
    
    async def _validate_datos_extraidos(self, datos_extraidos: ProcessedData, conversation: ConversationContext) -> Dict[str, Any]:
        """Validate extracted data before creating solicitud"""
        errors = []
        missing_fields = []
        
        try:
            # Use accumulated data from conversation (more complete)
            repuestos = conversation.accumulated_repuestos or datos_extraidos.repuestos
            vehiculo = conversation.accumulated_vehiculo or datos_extraidos.vehiculo
            cliente = conversation.accumulated_cliente or datos_extraidos.cliente
            
            # Validate repuestos
            if not repuestos:
                errors.append("No se encontraron repuestos en la solicitud")
                missing_fields.append("repuestos")
            else:
                for i, repuesto in enumerate(repuestos):
                    if not repuesto.get("nombre"):
                        errors.append(f"Repuesto {i+1} sin nombre")
                    elif len(repuesto["nombre"].strip()) < 3:
                        errors.append(f"Nombre de repuesto {i+1} muy corto")
            
            # Validate vehiculo
            if not vehiculo:
                errors.append("No se encontró información del vehículo")
                missing_fields.extend(["vehiculo.marca", "vehiculo.anio"])
            else:
                if not vehiculo.get("marca"):
                    errors.append("Falta marca del vehículo")
                    missing_fields.append("vehiculo.marca")
                
                # Validate year if provided
                if vehiculo.get("anio"):
                    try:
                        year = int(vehiculo["anio"])
                        if year < 1980 or year > 2025:
                            errors.append("Año del vehículo fuera del rango válido (1980-2025)")
                    except ValueError:
                        errors.append("Año del vehículo debe ser un número")
            
            # Validate cliente
            if not cliente:
                errors.append("No se encontró información del cliente")
                missing_fields.extend(["cliente.telefono", "cliente.ciudad"])
            else:
                # Validate phone number
                telefono = cliente.get("telefono")
                if not telefono:
                    errors.append("Falta número de teléfono del cliente")
                    missing_fields.append("cliente.telefono")
                elif not self._validate_phone_number(telefono):
                    errors.append("Formato de teléfono inválido (debe ser +57XXXXXXXXXX)")
                
                # City is recommended but not required
                if not cliente.get("ciudad"):
                    missing_fields.append("cliente.ciudad")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "missing_fields": missing_fields
            }
            
        except Exception as e:
            logger.error(f"Error validating extracted data: {e}")
            return {
                "is_valid": False,
                "errors": [f"Error de validación: {str(e)}"],
                "missing_fields": []
            }
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate Colombian phone number format"""
        # Colombian mobile number pattern: +57 followed by 10 digits starting with 3
        pattern = r'^\+57[3][0-9]{9}$'
        return bool(re.match(pattern, phone))
    
    async def _prepare_solicitud_data(self, datos_extraidos: ProcessedData, conversation: ConversationContext) -> Dict[str, Any]:
        """Prepare solicitud data for Core API"""
        try:
            # Use accumulated data from conversation (more complete)
            repuestos = conversation.accumulated_repuestos or datos_extraidos.repuestos
            vehiculo = conversation.accumulated_vehiculo or datos_extraidos.vehiculo
            cliente = conversation.accumulated_cliente or datos_extraidos.cliente
            
            # Prepare repuestos data
            repuestos_data = []
            for repuesto in repuestos:
                repuesto_data = {
                    "nombre": repuesto.get("nombre", "").strip(),
                    "cantidad": repuesto.get("cantidad", 1),
                    "marca_vehiculo": vehiculo.get("marca", "") if vehiculo else "",
                    "linea_vehiculo": vehiculo.get("linea", "") if vehiculo else "",
                    "anio_vehiculo": int(vehiculo.get("anio", 0)) if vehiculo and vehiculo.get("anio") else None,
                    "observaciones": repuesto.get("especificaciones", "") or repuesto.get("observaciones", "")
                }
                
                # Add codigo if available
                if repuesto.get("codigo"):
                    repuesto_data["codigo"] = repuesto["codigo"]
                
                repuestos_data.append(repuesto_data)
            
            # Prepare cliente data
            # Limpiar ciudad antes de enviar (remover departamentos)
            ciudad_limpia = limpiar_ciudad(cliente.get("ciudad", "")) if cliente.get("ciudad") else ""
            
            cliente_data = {
                "telefono": cliente.get("telefono", ""),
                "nombre": cliente.get("nombre", "Cliente WhatsApp"),
                "ciudad": ciudad_limpia,  # Ciudad limpia sin departamento
                "departamento": cliente.get("departamento", "")
            }
            
            # Prepare solicitud metadata
            metadata = {
                "origen": "whatsapp",
                "conversation_id": conversation.phone_number,
                "provider_used": datos_extraidos.provider_used,
                "confidence_score": datos_extraidos.confidence_score,
                "processing_time_ms": datos_extraidos.processing_time_ms,
                "created_from_agent_ia": True,
                "total_conversation_turns": conversation.total_turns
            }
            
            return {
                "repuestos": repuestos_data,
                "cliente": cliente_data,
                "ciudad_origen": ciudad_limpia,  # Ciudad limpia sin departamento
                "departamento_origen": cliente.get("departamento", ""),
                "metadata_json": metadata
            }
            
        except Exception as e:
            logger.error(f"Error preparing solicitud data: {e}")
            raise
    
    async def _create_or_get_cliente(self, cliente_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or get existing cliente"""
        try:
            # First, try to find existing cliente by phone
            search_response = await self.client.get(
                f"{self.core_api_url}/v1/clientes",
                params={"telefono": cliente_data["telefono"]}
            )
            
            if search_response.status_code == 200:
                clientes = search_response.json()
                if clientes and len(clientes) > 0:
                    # Cliente exists, return ID
                    cliente_id = clientes[0]["id"]
                    logger.info(f"Found existing cliente: {cliente_id}")
                    return {
                        "success": True,
                        "cliente_id": cliente_id,
                        "created": False
                    }
            
            # Cliente doesn't exist, create new one
            create_response = await self.client.post(
                f"{self.core_api_url}/v1/clientes",
                json=cliente_data
            )
            
            if create_response.status_code == 201:
                cliente = create_response.json()
                cliente_id = cliente["id"]
                logger.info(f"Created new cliente: {cliente_id}")
                return {
                    "success": True,
                    "cliente_id": cliente_id,
                    "created": True
                }
            else:
                logger.error(f"Failed to create cliente: {create_response.status_code} - {create_response.text}")
                return {
                    "success": False,
                    "error": f"Error creating cliente: {create_response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error creating/getting cliente: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_solicitud(self, solicitud_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create solicitud in Core API"""
        try:
            response = await self.client.post(
                f"{self.core_api_url}/v1/solicitudes",
                json=solicitud_data
            )
            
            if response.status_code == 201:
                solicitud = response.json()
                solicitud_id = solicitud["id"]
                logger.info(f"Created solicitud: {solicitud_id}")
                return {
                    "success": True,
                    "solicitud_id": solicitud_id,
                    "solicitud": solicitud
                }
            else:
                logger.error(f"Failed to create solicitud: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Error creating solicitud: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error creating solicitud: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_confirmation_message(self, phone_number: str, solicitud_id: str, solicitud_data: Dict[str, Any]):
        """Send confirmation message to client"""
        try:
            # Prepare confirmation message
            repuestos_list = []
            for repuesto in solicitud_data["repuestos"]:
                nombre = repuesto["nombre"]
                cantidad = repuesto.get("cantidad", 1)
                if cantidad > 1:
                    repuestos_list.append(f"• {cantidad}x {nombre}")
                else:
                    repuestos_list.append(f"• {nombre}")
            
            vehiculo_info = ""
            if solicitud_data["repuestos"]:
                first_repuesto = solicitud_data["repuestos"][0]
                if first_repuesto.get("marca_vehiculo") and first_repuesto.get("linea_vehiculo"):
                    vehiculo_info = f" para {first_repuesto['marca_vehiculo']} {first_repuesto['linea_vehiculo']}"
                    if first_repuesto.get("anio_vehiculo"):
                        vehiculo_info += f" {first_repuesto['anio_vehiculo']}"
            
            message = f"""✅ *Solicitud creada exitosamente*

*Número de solicitud:* {solicitud_id}

*Repuestos solicitados{vehiculo_info}:*
{chr(10).join(repuestos_list)}

Estamos buscando las mejores ofertas para ti. Te notificaremos cuando tengamos propuestas disponibles.

¡Gracias por usar TeLOO! 🚗"""
            
            # Send message
            success = await whatsapp_service.send_text_message(phone_number, message)
            
            if success:
                logger.info(f"Confirmation message sent to {phone_number}")
            else:
                logger.error(f"Failed to send confirmation message to {phone_number}")
                
        except Exception as e:
            logger.error(f"Error sending confirmation message: {e}")
    
    async def get_solicitud_status(self, solicitud_id: str) -> Optional[Dict[str, Any]]:
        """Get solicitud status from Core API"""
        try:
            response = await self.client.get(
                f"{self.core_api_url}/v1/solicitudes/{solicitud_id}"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get solicitud status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting solicitud status: {e}")
            return None
    
    async def validate_ciudad(self, ciudad: str) -> bool:
        """Validate if city exists in the system"""
        try:
            # This would typically call the Core API to validate the city
            # For now, we'll do basic validation
            if not ciudad or len(ciudad.strip()) < 3:
                return False
            
            # List of major Colombian cities (this could be fetched from Core API)
            valid_cities = [
                'bogota', 'bogotá', 'medellin', 'medellín', 'cali', 'barranquilla', 'cartagena',
                'cucuta', 'cúcuta', 'bucaramanga', 'pereira', 'ibague', 'ibagué', 'santa marta',
                'villavicencio', 'manizales', 'neiva', 'soledad', 'armenia',
                'monteria', 'montería', 'valledupar', 'pasto', 'popayan', 'popayán', 'tunja'
            ]
            
            ciudad_normalized = ciudad.lower().strip()
            return ciudad_normalized in valid_cities
            
        except Exception as e:
            logger.error(f"Error validating city: {e}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global solicitud service instance
solicitud_service = SolicitudService()