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
            # Get solicitud
            solicitud = await Solicitud.get(id=solicitud_id).prefetch_related(
                'cliente__usuario',
                'adjudicaciones__oferta__asesor__usuario',
                'adjudicaciones__repuesto_solicitado'
            )
            
            if solicitud.estado != EstadoSolicitud.EVALUADA:
                raise ValueError(f"Solicitud no está en estado EVALUADA: {solicitud.estado}")
            
            # Detect intent
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
            
            logger.info(f"Intención detectada para solicitud {solicitud.codigo_solicitud}: {intencion}")
            
            # Process based on intent
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
                raise ValueError(f"Intención no reconocida: {intencion['tipo']}")
            
            # Update solicitud with response text (timestamp will be updated_at)
            solicitud.respuesta_cliente_texto = respuesta_texto
            await solicitud.save()
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error procesando respuesta para solicitud {solicitud_id}: {e}")
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
        Detect intent using NLP (GPT-4 via Agent IA service)
        
        Args:
            texto: Response text
            solicitud: Solicitud instance
            
        Returns:
            Dict with intent information
        """
        # TODO: Integrate with Agent IA NLP service
        # For now, use simple detection
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
            solicitud.estado = EstadoSolicitud.EVALUADA
            solicitud.cliente_acepto = True
            await solicitud.save()
            
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
            solicitud.estado = EstadoSolicitud.CERRADA_SIN_OFERTAS
            solicitud.cliente_acepto = False
            await solicitud.save()
            
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
            solicitud.estado = EstadoSolicitud.EVALUADA
            solicitud.cliente_acepto = True  # Partial acceptance is still acceptance
            await solicitud.save()
            
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
