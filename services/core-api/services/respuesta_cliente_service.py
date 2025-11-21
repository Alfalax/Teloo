"""
Respuesta Cliente Service for TeLOO V3
Processes client responses to winning offers using NLP
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from models.solicitud import Solicitud
from models.oferta import AdjudicacionRepuesto, Oferta
from models.enums import EstadoSolicitud, EstadoOferta
from services.events_service import events_service

logger = logging.getLogger(__name__)


class RespuestaClienteService:
    """Service for processing client responses"""
    
    @staticmethod
    async def procesar_respuesta(
        solicitud_id: str,
        respuesta_texto: str,
        usar_nlp: bool = True
    ) -> Dict[str, Any]:
        """
        Process client response to offers
        
        Args:
            solicitud_id: ID of the solicitud
            respuesta_texto: Client's response text
            usar_nlp: Whether to use NLP for intent detection
            
        Returns:
            Dict with processing result
        """
        try:
            logger.info(f"🔍 Procesando respuesta del cliente para solicitud {solicitud_id}")
            logger.info(f"   Texto: '{respuesta_texto}'")
            logger.info(f"   Usar NLP: {usar_nlp}")
            
            # Get solicitud
            solicitud = await Solicitud.get(id=solicitud_id).prefetch_related(
                'cliente__usuario',
                'adjudicaciones__oferta__asesor__usuario',
                'adjudicaciones__repuesto_solicitado'
            )
            
            logger.info(f"   Solicitud: {solicitud.codigo_solicitud}")
            logger.info(f"   Estado actual: {solicitud.estado}")
            
            if solicitud.estado != EstadoSolicitud.EVALUADA:
                error_msg = f"Solicitud no está en estado EVALUADA: {solicitud.estado}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'solicitud_id': solicitud_id,
                    'error': error_msg
                }
            
            # Check if there are adjudications
            adjudicaciones_count = len(solicitud.adjudicaciones)
            logger.info(f"   Adjudicaciones: {adjudicaciones_count}")
            
            if adjudicaciones_count == 0:
                error_msg = "No hay adjudicaciones para esta solicitud"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'solicitud_id': solicitud_id,
                    'error': error_msg
                }
            
            # Detect intent
            logger.info(f"🤖 Detectando intención...")
            if usar_nlp:
                intencion = await RespuestaClienteService._detectar_intencion_nlp(
                    respuesta_texto,
                    solicitud
                )
            else:
                intencion = await RespuestaClienteService._detectar_intencion_simple(
                    respuesta_texto,
                    solicitud
                )
            
            logger.info(f"✅ Intención detectada: {intencion}")
            
            # Check if intent is unknown
            if intencion['tipo'] == 'desconocido':
                error_msg = f"No se pudo entender la respuesta. Por favor responde con 'acepto' o 'rechazo'."
                logger.warning(f"⚠️ {error_msg}")
                return {
                    'success': False,
                    'solicitud_id': solicitud_id,
                    'error': error_msg
                }
            
            # Process based on intent
            logger.info(f"⚙️ Procesando intención: {intencion['tipo']}")
            
            if intencion['tipo'] == 'aceptar_todo':
                resultado = await RespuestaClienteService._procesar_aceptacion_total(solicitud)
            
            elif intencion['tipo'] == 'rechazar_todo':
                resultado = await RespuestaClienteService._procesar_rechazo_total(solicitud)
            
            elif intencion['tipo'] == 'aceptar_parcial':
                resultado = await RespuestaClienteService._procesar_aceptacion_parcial(
                    solicitud,
                    intencion['repuestos_aceptados']
                )
            
            elif intencion['tipo'] == 'rechazar_parcial':
                resultado = await RespuestaClienteService._procesar_rechazo_parcial(
                    solicitud,
                    intencion['repuestos_rechazados']
                )
            
            else:
                error_msg = f"Intención no reconocida: {intencion['tipo']}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'solicitud_id': solicitud_id,
                    'error': error_msg
                }
            
            # Update solicitud with response text (timestamp will be updated_at)
            solicitud.respuesta_cliente_texto = respuesta_texto
            await solicitud.save()
            
            logger.info(f"✅ Respuesta procesada exitosamente: {resultado.get('tipo_respuesta')}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error procesando respuesta para solicitud {solicitud_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'solicitud_id': solicitud_id,
                'error': str(e)
            }
    
    @staticmethod
    async def _detectar_intencion_simple(
        texto: str,
        solicitud: Solicitud
    ) -> Dict[str, Any]:
        """
        Detect intent using simple pattern matching
        
        Args:
            texto: Response text
            solicitud: Solicitud instance
            
        Returns:
            Dict with intent information
        """
        texto_lower = texto.lower().strip()
        
        # Get total repuestos
        adjudicaciones = await AdjudicacionRepuesto.filter(solicitud=solicitud).all()
        total_repuestos = len(adjudicaciones)
        
        # Pattern: "acepto todo" or "acepto"
        if re.search(r'\b(acepto|aceptar|si|ok|vale)\s*(todo|todos|todas)?\b', texto_lower):
            # Check if there are specific numbers
            numeros = re.findall(r'\b(\d+)\b', texto)
            if numeros:
                # Partial acceptance
                indices = [int(n) for n in numeros if 1 <= int(n) <= total_repuestos]
                return {
                    'tipo': 'aceptar_parcial',
                    'repuestos_aceptados': indices,
                    'confianza': 0.9
                }
            else:
                # Accept all
                return {
                    'tipo': 'aceptar_todo',
                    'confianza': 0.95
                }
        
        # Pattern: "rechazo todo" or "no"
        if re.search(r'\b(rechazo|rechazar|no|nada|ninguno)\s*(todo|todos|todas)?\b', texto_lower):
            # Check if there are specific numbers
            numeros = re.findall(r'\b(\d+)\b', texto)
            if numeros:
                # Partial rejection
                indices = [int(n) for n in numeros if 1 <= int(n) <= total_repuestos]
                return {
                    'tipo': 'rechazar_parcial',
                    'repuestos_rechazados': indices,
                    'confianza': 0.9
                }
            else:
                # Reject all
                return {
                    'tipo': 'rechazar_todo',
                    'confianza': 0.95
                }
        
        # Pattern: "acepto 1,3,5" or "acepto 1 y 3"
        numeros = re.findall(r'\b(\d+)\b', texto)
        if numeros and any(word in texto_lower for word in ['acepto', 'aceptar', 'si']):
            indices = [int(n) for n in numeros if 1 <= int(n) <= total_repuestos]
            if indices:
                return {
                    'tipo': 'aceptar_parcial',
                    'repuestos_aceptados': indices,
                    'confianza': 0.85
                }
        
        # Default: unclear intent
        return {
            'tipo': 'desconocido',
            'confianza': 0.0,
            'texto_original': texto
        }
    
    @staticmethod
    async def _detectar_intencion_nlp(
        texto: str,
        solicitud: Solicitud
    ) -> Dict[str, Any]:
        """
        Detect intent using NLP (OpenAI GPT-4o-mini)
        
        Args:
            texto: Response text
            solicitud: Solicitud instance
            
        Returns:
            Dict with intent information
        """
        try:
            import httpx
            import os
            import json
            
            # Get adjudicaciones to know how many parts we have
            adjudicaciones = await AdjudicacionRepuesto.filter(solicitud=solicitud).prefetch_related(
                'repuesto_solicitado', 'oferta__asesor'
            ).all()
            total_repuestos = len(adjudicaciones)
            
            logger.info(f"Detectando intención NLP para {total_repuestos} repuestos")
            
            # Build repuestos list for context
            repuestos_info = []
            for i, adj in enumerate(adjudicaciones, 1):
                repuestos_info.append(f"{i}. {adj.repuesto_solicitado.nombre}")
            
            # Create prompt for OpenAI
            prompt = f"""Analiza la siguiente respuesta de un cliente a una propuesta de repuestos y determina su intención.

CONTEXTO:
- El cliente recibió una propuesta con {total_repuestos} repuestos
- Repuestos en la propuesta:
{chr(10).join(repuestos_info)}

RESPUESTA DEL CLIENTE:
"{texto}"

INSTRUCCIONES:
Determina la intención del cliente y responde SOLO con un JSON válido (sin markdown, sin explicaciones adicionales) con esta estructura:

Para aceptar todo:
{{"tipo": "aceptar_todo", "confianza": 0.95}}

Para rechazar todo:
{{"tipo": "rechazar_todo", "confianza": 0.95}}

Para aceptar algunos repuestos específicos:
{{"tipo": "aceptar_parcial", "repuestos_aceptados": [1, 3, 5], "confianza": 0.90}}

Para rechazar algunos repuestos específicos:
{{"tipo": "rechazar_parcial", "repuestos_rechazados": [2, 4], "confianza": 0.90}}

Si no está claro:
{{"tipo": "desconocido", "confianza": 0.0, "texto_original": "{texto}"}}

IMPORTANTE:
- Interpreta variaciones, errores de tipeo y lenguaje natural
- ACEPTAR TODO incluye: "acepto", "de acuerdo", "aprobado", "ok", "listo", "dale", "perfecto", "está bien", "estoy de acuerdo", "esta bien", "todo bien", "si", "sí", "confirmo", "conforme", "excelente"
- RECHAZAR TODO incluye: "no", "rechazo", "cancelar", "no acepto", "no quiero"
- Si menciona números específicos (ej: "acepto 1,3"), identifícalos como aceptación/rechazo parcial
- Si NO menciona números Y usa palabras de aceptación = aceptar_todo
- Responde SOLO con el JSON, sin texto adicional"""

            # Call OpenAI API
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.warning("OPENAI_API_KEY not found, falling back to simple detection")
                return await RespuestaClienteService._detectar_intencion_simple(texto, solicitud)
            
            logger.info(f"Llamando a OpenAI API para detectar intención: '{texto}'")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Eres un asistente que analiza respuestas de clientes y determina su intención. Respondes SOLO con JSON válido, sin markdown ni texto adicional."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.3,
                        "max_tokens": 200
                    }
                )
                
                logger.info(f"OpenAI API response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content'].strip()
                    
                    logger.info(f"OpenAI raw response: {content}")
                    
                    # Remove markdown code blocks if present
                    content = content.replace('```json', '').replace('```', '').strip()
                    
                    # Parse JSON response
                    intencion = json.loads(content)
                    
                    logger.info(f"✅ NLP intent detected: {intencion}")
                    return intencion
                else:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    logger.warning("Falling back to simple detection")
                    return await RespuestaClienteService._detectar_intencion_simple(texto, solicitud)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing OpenAI JSON response: {e}")
            logger.warning("Falling back to simple detection")
            return await RespuestaClienteService._detectar_intencion_simple(texto, solicitud)
        except Exception as e:
            logger.error(f"Error in NLP intent detection: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback to simple detection
            logger.warning("Falling back to simple detection")
            return await RespuestaClienteService._detectar_intencion_simple(texto, solicitud)
    
    @staticmethod
    async def _procesar_aceptacion_total(solicitud: Solicitud) -> Dict[str, Any]:
        """
        Process total acceptance of all offers
        
        Args:
            solicitud: Solicitud instance
            
        Returns:
            Dict with result
        """
        try:
            # Get all adjudications
            adjudicaciones = await AdjudicacionRepuesto.filter(
                solicitud=solicitud
            ).prefetch_related('oferta__asesor__usuario', 'repuesto_solicitado')
            
            # Update all winning offers to ACEPTADA
            ofertas_ganadoras_ids = set(adj.oferta.id for adj in adjudicaciones)
            repuestos_nombres = [adj.repuesto_solicitado.nombre for adj in adjudicaciones]
            
            for oferta_id in ofertas_ganadoras_ids:
                oferta = await Oferta.get(id=oferta_id)
                oferta.estado = EstadoOferta.ACEPTADA
                await oferta.save()
                
                # Register event
                await events_service.on_cliente_acepto_oferta(str(oferta_id))
            
            # Update solicitud state
            solicitud.estado = EstadoSolicitud.OFERTAS_ACEPTADAS
            solicitud.cliente_acepto = True
            # Only update the fields we changed, not fecha_notificacion_cliente
            await solicitud.save(update_fields=['estado', 'cliente_acepto'])
            
            logger.info(
                f"Cliente aceptó todas las ofertas para solicitud {solicitud.codigo_solicitud}: "
                f"{len(ofertas_ganadoras_ids)} ofertas aceptadas"
            )
            
            return {
                'success': True,
                'solicitud_id': str(solicitud.id),
                'tipo_respuesta': 'aceptacion_total',
                'ofertas_aceptadas': len(ofertas_ganadoras_ids),
                'repuestos_aceptados': repuestos_nombres,
                'mensaje': 'Todas las ofertas han sido aceptadas. Los asesores te contactarán pronto.'
            }
            
        except Exception as e:
            logger.error(f"Error procesando aceptación total: {e}")
            raise
    
    @staticmethod
    async def _procesar_rechazo_total(solicitud: Solicitud) -> Dict[str, Any]:
        """
        Process total rejection of all offers
        
        Args:
            solicitud: Solicitud instance
            
        Returns:
            Dict with result
        """
        try:
            # Get all adjudications
            adjudicaciones = await AdjudicacionRepuesto.filter(
                solicitud=solicitud
            ).prefetch_related('oferta', 'repuesto_solicitado')
            
            # Update all winning offers to RECHAZADA
            ofertas_ganadoras_ids = set(adj.oferta.id for adj in adjudicaciones)
            repuestos_nombres = [adj.repuesto_solicitado.nombre for adj in adjudicaciones]
            
            for oferta_id in ofertas_ganadoras_ids:
                oferta = await Oferta.get(id=oferta_id)
                oferta.estado = EstadoOferta.RECHAZADA
                await oferta.save()
                
                # Register event
                await events_service.on_cliente_rechazo_oferta(str(oferta_id))
            
            # Update solicitud state
            solicitud.estado = EstadoSolicitud.OFERTAS_RECHAZADAS
            solicitud.cliente_acepto = False
            # Only update the fields we changed
            await solicitud.save(update_fields=['estado', 'cliente_acepto'])
            
            logger.info(
                f"Cliente rechazó todas las ofertas para solicitud {solicitud.codigo_solicitud}"
            )
            
            return {
                'success': True,
                'solicitud_id': str(solicitud.id),
                'tipo_respuesta': 'rechazo_total',
                'repuestos_rechazados': repuestos_nombres,
                'mensaje': 'Todas las ofertas han sido rechazadas. Gracias por usar TeLOO.'
            }
            
        except Exception as e:
            logger.error(f"Error procesando rechazo total: {e}")
            raise
    
    @staticmethod
    async def _procesar_aceptacion_parcial(
        solicitud: Solicitud,
        indices_aceptados: List[int]
    ) -> Dict[str, Any]:
        """
        Process partial acceptance of offers
        
        Args:
            solicitud: Solicitud instance
            indices_aceptados: List of repuesto indices (1-based) to accept
            
        Returns:
            Dict with result
        """
        try:
            # Get all adjudications ordered
            adjudicaciones = await AdjudicacionRepuesto.filter(
                solicitud=solicitud
            ).prefetch_related('oferta', 'repuesto_solicitado').order_by('repuesto_solicitado__nombre')
            
            ofertas_aceptadas = set()
            ofertas_rechazadas = set()
            repuestos_aceptados = []
            repuestos_rechazados = []
            
            for idx, adj in enumerate(adjudicaciones, 1):
                if idx in indices_aceptados:
                    # Accept this offer
                    ofertas_aceptadas.add(adj.oferta.id)
                    repuestos_aceptados.append(adj.repuesto_solicitado.nombre)
                else:
                    # Reject this offer
                    ofertas_rechazadas.add(adj.oferta.id)
                    repuestos_rechazados.append(adj.repuesto_solicitado.nombre)
            
            # Update offer states
            for oferta_id in ofertas_aceptadas:
                oferta = await Oferta.get(id=oferta_id)
                oferta.estado = EstadoOferta.ACEPTADA
                await oferta.save()
                await events_service.on_cliente_acepto_oferta(str(oferta_id))
            
            for oferta_id in ofertas_rechazadas:
                oferta = await Oferta.get(id=oferta_id)
                oferta.estado = EstadoOferta.RECHAZADA
                await oferta.save()
                await events_service.on_cliente_rechazo_oferta(str(oferta_id))
            
            # Update solicitud
            solicitud.estado = EstadoSolicitud.OFERTAS_ACEPTADAS  # Partial acceptance is still acceptance
            solicitud.cliente_acepto = True
            # Only update the fields we changed
            await solicitud.save(update_fields=['estado', 'cliente_acepto'])
            
            logger.info(
                f"Cliente aceptó parcialmente ofertas para solicitud {solicitud.codigo_solicitud}: "
                f"{len(repuestos_aceptados)} aceptados, {len(repuestos_rechazados)} rechazados"
            )
            
            return {
                'success': True,
                'solicitud_id': str(solicitud.id),
                'tipo_respuesta': 'aceptacion_parcial',
                'repuestos_aceptados': repuestos_aceptados,
                'repuestos_rechazados': repuestos_rechazados,
                'mensaje': f'Has aceptado {len(repuestos_aceptados)} repuesto(s). Los asesores te contactarán pronto.'
            }
            
        except Exception as e:
            logger.error(f"Error procesando aceptación parcial: {e}")
            raise
    
    @staticmethod
    async def _procesar_rechazo_parcial(
        solicitud: Solicitud,
        indices_rechazados: List[int]
    ) -> Dict[str, Any]:
        """
        Process partial rejection of offers
        
        Args:
            solicitud: Solicitud instance
            indices_rechazados: List of repuesto indices (1-based) to reject
            
        Returns:
            Dict with result
        """
        try:
            # Get all adjudications ordered
            adjudicaciones = await AdjudicacionRepuesto.filter(
                solicitud=solicitud
            ).prefetch_related('oferta', 'repuesto_solicitado').order_by('repuesto_solicitado__nombre')
            
            # Convert to acceptance (inverse of rejection)
            total_repuestos = len(adjudicaciones)
            indices_aceptados = [i for i in range(1, total_repuestos + 1) if i not in indices_rechazados]
            
            # Process as partial acceptance
            return await RespuestaClienteService._procesar_aceptacion_parcial(
                solicitud,
                indices_aceptados
            )
            
        except Exception as e:
            logger.error(f"Error procesando rechazo parcial: {e}")
            raise
