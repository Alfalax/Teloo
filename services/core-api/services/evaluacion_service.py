"""
Evaluacion Service for TeLOO V3
Handles offer evaluation, scoring, and adjudication logic
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime
import asyncio
import json

from models.oferta import Oferta, OfertaDetalle, AdjudicacionRepuesto, Evaluacion
from models.solicitud import Solicitud, RepuestoSolicitado
from models.enums import EstadoSolicitud, EstadoOferta
from services.configuracion_service import ConfiguracionService

logger = logging.getLogger(__name__)


class EvaluacionService:
    """Service for evaluating offers and determining winners"""
    
    @staticmethod
    async def evaluar_repuesto(
        repuesto: RepuestoSolicitado,
        ofertas_disponibles: List[Oferta]
    ) -> Dict[str, Any]:
        """
        Evaluate offers for a specific repuesto and determine the winner
        
        Args:
            repuesto: The repuesto to evaluate
            ofertas_disponibles: List of available offers
            
        Returns:
            Dict with evaluation result including winner and scores
        """
        try:
            # Get evaluation weights from configuration
            config = await ConfiguracionService.get_config('pesos_evaluacion_ofertas')
            peso_precio = Decimal(str(config['precio']))
            peso_tiempo = Decimal(str(config['tiempo_entrega']))
            peso_garantia = Decimal(str(config['garantia']))
            
            # Filter offers that include this specific repuesto
            ofertas_con_repuesto = []
            for oferta in ofertas_disponibles:
                # Check if this offer includes the repuesto
                detalle = await OfertaDetalle.get_or_none(
                    oferta=oferta,
                    repuesto_solicitado=repuesto
                )
                if detalle:
                    ofertas_con_repuesto.append((oferta, detalle))
            
            if not ofertas_con_repuesto:
                return {
                    'success': False,
                    'repuesto_id': str(repuesto.id),
                    'repuesto_nombre': repuesto.nombre,
                    'ofertas_evaluadas': 0,
                    'ganador': None,
                    'motivo': 'no_ofertas_disponibles',
                    'message': f'No hay ofertas disponibles para {repuesto.nombre}'
                }
            
            # Calculate scores for each offer
            evaluaciones_ofertas = []
            
            # Get min/max values for normalization
            precios = [detalle.precio_unitario for _, detalle in ofertas_con_repuesto]
            tiempos = [detalle.tiempo_entrega_dias for _, detalle in ofertas_con_repuesto]
            garantias = [detalle.garantia_meses for _, detalle in ofertas_con_repuesto]
            
            precio_min, precio_max = min(precios), max(precios)
            tiempo_min, tiempo_max = min(tiempos), max(tiempos)
            garantia_min, garantia_max = min(garantias), max(garantias)
            
            for oferta, detalle in ofertas_con_repuesto:
                # Calculate normalized scores (0-1 scale)
                # Price: lower is better (inverted)
                if precio_max == precio_min:
                    score_precio = Decimal('1.0')
                else:
                    score_precio = (precio_max - detalle.precio_unitario) / (precio_max - precio_min)
                
                # Time: lower is better (inverted)
                if tiempo_max == tiempo_min:
                    score_tiempo = Decimal('1.0')
                else:
                    score_tiempo = Decimal(str((tiempo_max - detalle.tiempo_entrega_dias) / (tiempo_max - tiempo_min)))
                
                # Warranty: higher is better
                if garantia_max == garantia_min:
                    score_garantia = Decimal('1.0')
                else:
                    score_garantia = Decimal(str((detalle.garantia_meses - garantia_min) / (garantia_max - garantia_min)))
                
                # Calculate weighted total score
                puntaje_total = (
                    score_precio * peso_precio +
                    score_tiempo * peso_tiempo +
                    score_garantia * peso_garantia
                )
                
                # Update detalle with individual scores
                await detalle.update_from_dict({
                    'puntaje_precio': score_precio,
                    'puntaje_tiempo': score_tiempo,
                    'puntaje_garantia': score_garantia,
                    'puntaje_total': puntaje_total
                })
                
                evaluaciones_ofertas.append({
                    'oferta': oferta,
                    'detalle': detalle,
                    'puntaje_total': puntaje_total,
                    'scores': {
                        'precio': float(score_precio),
                        'tiempo': float(score_tiempo),
                        'garantia': float(score_garantia)
                    }
                })
            
            # Sort by score descending (best first)
            evaluaciones_ofertas.sort(key=lambda x: x['puntaje_total'], reverse=True)
            
            # The winner is the offer with the highest score
            mejor_evaluacion = evaluaciones_ofertas[0]
            oferta_ganadora = mejor_evaluacion['oferta']
            detalle_ganador = mejor_evaluacion['detalle']
            
            logger.info(
                f"Repuesto {repuesto.nombre} evaluado: {len(evaluaciones_ofertas)} ofertas, "
                f"ganador: {oferta_ganadora.asesor.usuario.nombre_completo} "
                f"con puntaje {mejor_evaluacion['puntaje_total']:.3f}"
            )
            
            return {
                'success': True,
                'repuesto_id': str(repuesto.id),
                'repuesto_nombre': repuesto.nombre,
                'ofertas_evaluadas': len(evaluaciones_ofertas),
                'ganador': {
                    'oferta_id': str(oferta_ganadora.id),
                    'detalle_id': str(detalle_ganador.id),
                    'asesor_id': str(oferta_ganadora.asesor.id),
                    'asesor_nombre': oferta_ganadora.asesor.usuario.nombre_completo,
                    'puntaje_total': float(mejor_evaluacion['puntaje_total']),
                    'precio': float(detalle_ganador.precio_unitario),
                    'tiempo_entrega': detalle_ganador.tiempo_entrega_dias,
                    'garantia': detalle_ganador.garantia_meses,
                    'scores_detallados': mejor_evaluacion['scores']
                },
                'todas_evaluaciones': [
                    {
                        'oferta_id': str(eval_data['oferta'].id),
                        'asesor_nombre': eval_data['oferta'].asesor.usuario.nombre_completo,
                        'puntaje_total': float(eval_data['puntaje_total']),
                        'precio': float(eval_data['detalle'].precio_unitario),
                        'tiempo_entrega': eval_data['detalle'].tiempo_entrega_dias,
                        'garantia': eval_data['detalle'].garantia_meses,
                        'scores': eval_data['scores']
                    }
                    for eval_data in evaluaciones_ofertas
                ],
                'configuracion_usada': {
                    'peso_precio': float(peso_precio),
                    'peso_tiempo': float(peso_tiempo),
                    'peso_garantia': float(peso_garantia)
                }
            }
            
        except Exception as e:
            logger.error(f"Error evaluando repuesto {repuesto.id}: {e}")
            return {
                'success': False,
                'repuesto_id': str(repuesto.id),
                'repuesto_nombre': repuesto.nombre,
                'ofertas_evaluadas': 0,
                'ganador': None,
                'error': str(e),
                'message': f'Error evaluando {repuesto.nombre}: {str(e)}'
            }
    
    @staticmethod
    async def evaluar_repuesto_con_cobertura(
        repuesto: RepuestoSolicitado,
        ofertas_disponibles: List[Oferta],
        total_repuestos_solicitud: int
    ) -> Dict[str, Any]:
        """
        Evaluate offers for a repuesto applying minimum coverage rule
        
        ALGORITMO CORRECTO:
        1. Filtrar ofertas por cobertura >= 50% (a nivel de oferta completa)
        2. De las ofertas que pasan el filtro, evaluar solo las que tienen este repuesto
        3. Calcular puntajes con fórmula (precio + tiempo + garantía)
        4. Adjudicar al mejor puntaje
        5. Excepción: Si solo hay un oferente, adjudicar sin importar cobertura
        
        Args:
            repuesto: The repuesto to evaluate
            ofertas_disponibles: List of available offers
            total_repuestos_solicitud: Total number of repuestos in the solicitud
            
        Returns:
            Dict with evaluation result including coverage analysis
        """
        try:
            # Get minimum coverage from configuration
            config = await ConfiguracionService.get_config('parametros_generales')
            cobertura_minima_pct = Decimal(str(config['cobertura_minima_porcentaje']))
            
            # PASO 1: Calcular cobertura de cada oferta y filtrar por cobertura mínima
            ofertas_con_cobertura_suficiente = []
            ofertas_con_cobertura_insuficiente = []
            
            for oferta in ofertas_disponibles:
                # Calculate coverage: (repuestos_cubiertos / total_repuestos) * 100
                repuestos_cubiertos = await OfertaDetalle.filter(oferta=oferta).count()
                cobertura_pct = Decimal(str((repuestos_cubiertos / total_repuestos_solicitud) * 100))
                
                oferta_data = {
                    'oferta': oferta,
                    'cobertura_pct': cobertura_pct
                }
                
                if cobertura_pct >= cobertura_minima_pct:
                    ofertas_con_cobertura_suficiente.append(oferta_data)
                else:
                    ofertas_con_cobertura_insuficiente.append(oferta_data)
            
            # PASO 2: De las ofertas con cobertura suficiente, filtrar las que tienen este repuesto
            ofertas_con_repuesto = []
            for oferta_data in ofertas_con_cobertura_suficiente:
                oferta = oferta_data['oferta']
                detalle = await OfertaDetalle.get_or_none(
                    oferta=oferta,
                    repuesto_solicitado=repuesto
                )
                if detalle:
                    ofertas_con_repuesto.append({
                        'oferta': oferta,
                        'detalle': detalle,
                        'cobertura_pct': oferta_data['cobertura_pct']
                    })
            
            # PASO 3: Si no hay ofertas con cobertura suficiente, aplicar excepción
            if not ofertas_con_repuesto:
                # Buscar en ofertas con cobertura insuficiente (excepción: único oferente)
                ofertas_excepcion = []
                for oferta_data in ofertas_con_cobertura_insuficiente:
                    oferta = oferta_data['oferta']
                    detalle = await OfertaDetalle.get_or_none(
                        oferta=oferta,
                        repuesto_solicitado=repuesto
                    )
                    if detalle:
                        ofertas_excepcion.append({
                            'oferta': oferta,
                            'detalle': detalle,
                            'cobertura_pct': oferta_data['cobertura_pct']
                        })
                
                # Si solo hay una oferta (único oferente), adjudicar por excepción
                if len(ofertas_excepcion) == 1:
                    ofertas_con_repuesto = ofertas_excepcion
                    logger.info(
                        f"Aplicando excepción de único oferente para {repuesto.nombre}: "
                        f"{ofertas_excepcion[0]['oferta'].asesor.usuario.nombre_completo} "
                        f"con cobertura {ofertas_excepcion[0]['cobertura_pct']:.1f}%"
                    )
                else:
                    return {
                        'success': False,
                        'repuesto_id': str(repuesto.id),
                        'repuesto_nombre': repuesto.nombre,
                        'ofertas_evaluadas': 0,
                        'ganador': None,
                        'motivo': 'no_ofertas_con_cobertura_suficiente',
                        'cobertura_aplicada': {
                            'cobertura_minima_requerida': float(cobertura_minima_pct),
                            'ofertas_totales': len(ofertas_disponibles),
                            'ofertas_con_cobertura': len(ofertas_con_cobertura_suficiente),
                            'ofertas_con_repuesto': 0
                        },
                        'message': f'No hay ofertas con cobertura suficiente para {repuesto.nombre}'
                    }
            
            # PASO 4: Evaluar ofertas que pasaron el filtro usando la fórmula
            # Extraer solo las ofertas para evaluar
            ofertas_a_evaluar = [od['oferta'] for od in ofertas_con_repuesto]
            
            evaluacion_detallada = await EvaluacionService.evaluar_repuesto(
                repuesto, ofertas_a_evaluar
            )
            
            if not evaluacion_detallada['success']:
                return evaluacion_detallada
            
            # PASO 5: Agregar información de cobertura al ganador
            ganador_info = evaluacion_detallada['ganador']
            ganador_oferta_id = ganador_info['oferta_id']
            
            # Buscar la cobertura del ganador
            cobertura_ganador = next(
                (od['cobertura_pct'] for od in ofertas_con_repuesto if str(od['oferta'].id) == ganador_oferta_id),
                Decimal('0')
            )
            
            ganador_info['cobertura_pct'] = float(cobertura_ganador)
            ganador_info['cumple_cobertura_minima'] = cobertura_ganador >= cobertura_minima_pct
            ganador_info['es_adjudicacion_por_excepcion'] = cobertura_ganador < cobertura_minima_pct
            
            motivo = 'mejor_puntaje_con_cobertura'
            if cobertura_ganador < cobertura_minima_pct:
                motivo = 'unica_oferta_disponible'
            
            logger.info(
                f"Repuesto {repuesto.nombre} adjudicado por {motivo}: "
                f"cobertura {cobertura_ganador:.1f}% (mínimo {cobertura_minima_pct}%), "
                f"asesor: {ganador_info['asesor_nombre']}, "
                f"puntaje: {ganador_info['puntaje_total']:.3f}"
            )
            
            return {
                'success': True,
                'repuesto_id': str(repuesto.id),
                'repuesto_nombre': repuesto.nombre,
                'ofertas_evaluadas': len(ofertas_con_repuesto),
                'ganador': ganador_info,
                'motivo': motivo,
                'cobertura_aplicada': {
                    'cobertura_minima_requerida': float(cobertura_minima_pct),
                    'cobertura_obtenida': float(cobertura_ganador),
                    'cumple_cobertura': cobertura_ganador >= cobertura_minima_pct,
                    'es_unica_oferta': len(ofertas_con_repuesto) == 1
                },
                'todas_evaluaciones': evaluacion_detallada.get('todas_evaluaciones', []),
                'todas_coberturas': [
                    {
                        'oferta_id': str(od['oferta'].id),
                        'asesor_nombre': od['oferta'].asesor.usuario.nombre_completo,
                        'cobertura_pct': float(od['cobertura_pct']),
                        'cumple_minimo': od['cobertura_pct'] >= cobertura_minima_pct
                    }
                    for od in ofertas_con_repuesto
                ]
            }
            
        except Exception as e:
            logger.error(f"Error evaluando repuesto con cobertura {repuesto.id}: {e}")
            return {
                'success': False,
                'repuesto_id': str(repuesto.id),
                'repuesto_nombre': repuesto.nombre,
                'ofertas_evaluadas': 0,
                'ganador': None,
                'error': str(e),
                'message': f'Error evaluando {repuesto.nombre} con cobertura: {str(e)}'
            } 
   
    @staticmethod
    async def evaluar_solicitud(solicitud_id: str) -> Dict[str, Any]:
        """
        Evaluate complete solicitud - all repuestos individually
        
        Args:
            solicitud_id: ID of the solicitud to evaluate
            
        Returns:
            Dict with complete evaluation results and adjudications
        """
        try:
            start_time = datetime.now()
            
            # Get solicitud with all relationships
            solicitud = await Solicitud.get_or_none(id=solicitud_id).prefetch_related(
                'repuestos_solicitados',
                'ofertas__asesor__usuario',
                'ofertas__detalles__repuesto_solicitado'
            )
            
            if not solicitud:
                raise ValueError(f"Solicitud {solicitud_id} no encontrada")
            
            if not solicitud.is_evaluable():
                raise ValueError(f"Solicitud {solicitud_id} no puede ser evaluada (estado: {solicitud.estado})")
            
            # Get all active offers (ENVIADA state)
            ofertas_activas = [
                oferta for oferta in solicitud.ofertas 
                if oferta.estado == EstadoOferta.ENVIADA
            ]
            
            if not ofertas_activas:
                # No offers to evaluate - close solicitud without offers
                await solicitud.update_from_dict({
                    'estado': EstadoSolicitud.CERRADA_SIN_OFERTAS,
                    'fecha_evaluacion': datetime.now()
                })
                
                return {
                    'success': False,
                    'solicitud_id': str(solicitud.id),
                    'codigo_solicitud': solicitud.codigo_solicitud,
                    'ofertas_evaluadas': 0,
                    'repuestos_adjudicados': 0,
                    'adjudicaciones': [],
                    'estado_final': EstadoSolicitud.CERRADA_SIN_OFERTAS,
                    'message': 'Solicitud cerrada sin ofertas disponibles'
                }
            
            # Get configuration for evaluation
            config_evaluacion = await ConfiguracionService.get_config('pesos_evaluacion_ofertas')
            config_general = await ConfiguracionService.get_config('parametros_generales')
            
            # Evaluate each repuesto individually
            evaluaciones_repuestos = []
            adjudicaciones_creadas = []
            total_repuestos = len(solicitud.repuestos_solicitados)
            
            for repuesto in solicitud.repuestos_solicitados:
                evaluacion_repuesto = await EvaluacionService.evaluar_repuesto_con_cobertura(
                    repuesto=repuesto,
                    ofertas_disponibles=ofertas_activas,
                    total_repuestos_solicitud=total_repuestos
                )
                
                evaluaciones_repuestos.append(evaluacion_repuesto)
                
                # Create adjudication if there's a winner
                if evaluacion_repuesto['success'] and evaluacion_repuesto['ganador']:
                    ganador = evaluacion_repuesto['ganador']
                    
                    # Get the winning offer and detail
                    oferta_ganadora = await Oferta.get(id=ganador['oferta_id']).prefetch_related('asesor__usuario')
                    detalle_ganador = await OfertaDetalle.get(id=ganador['detalle_id'])
                    
                    # Create adjudication
                    adjudicacion = await AdjudicacionRepuesto.create(
                        solicitud=solicitud,
                        oferta=oferta_ganadora,
                        repuesto_solicitado=repuesto,
                        oferta_detalle=detalle_ganador,
                        puntaje_obtenido=Decimal(str(ganador['puntaje_total'])),
                        precio_adjudicado=detalle_ganador.precio_unitario,
                        tiempo_entrega_adjudicado=detalle_ganador.tiempo_entrega_dias,
                        garantia_adjudicada=detalle_ganador.garantia_meses,
                        cantidad_adjudicada=detalle_ganador.cantidad,
                        motivo_adjudicacion=evaluacion_repuesto['motivo'],
                        cobertura_oferta=Decimal(str(ganador.get('cobertura_pct', 0)))
                    )
                    
                    adjudicaciones_creadas.append(adjudicacion)
                    
                    logger.info(
                        f"Adjudicación creada: {repuesto.nombre} → "
                        f"{oferta_ganadora.asesor.usuario.nombre_completo} "
                        f"(${detalle_ganador.precio_unitario:,.0f})"
                    )
            
            # Update offer states based on results
            ofertas_ganadoras = set()
            ofertas_no_seleccionadas = set()
            
            for adjudicacion in adjudicaciones_creadas:
                ofertas_ganadoras.add(adjudicacion.oferta.id)
            
            for oferta in ofertas_activas:
                if oferta.id in ofertas_ganadoras:
                    await oferta.update_from_dict({'estado': EstadoOferta.GANADORA})
                else:
                    await oferta.update_from_dict({'estado': EstadoOferta.NO_SELECCIONADA})
                    ofertas_no_seleccionadas.add(oferta.id)
            
            # Calculate totals
            monto_total_adjudicado = sum(
                adj.precio_adjudicado * adj.cantidad_adjudicada 
                for adj in adjudicaciones_creadas
            )
            
            # Update solicitud state
            nuevo_estado = EstadoSolicitud.EVALUADA
            if len(adjudicaciones_creadas) == 0:
                nuevo_estado = EstadoSolicitud.CERRADA_SIN_OFERTAS
            
            await solicitud.update_from_dict({
                'estado': nuevo_estado,
                'fecha_evaluacion': datetime.now(),
                'monto_total_adjudicado': monto_total_adjudicado
            })
            await solicitud.save()
            
            # Calculate evaluation metrics
            end_time = datetime.now()
            tiempo_evaluacion_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Determine if it's a mixed adjudication (multiple different asesores won)
            asesores_ganadores = set(adj.oferta.asesor.id for adj in adjudicaciones_creadas)
            es_adjudicacion_mixta = len(asesores_ganadores) > 1
            
            # Count offers by coverage compliance
            ofertas_con_cobertura_suficiente = sum(
                1 for eval_rep in evaluaciones_repuestos 
                if eval_rep and eval_rep.get('cobertura_aplicada', {}).get('cumple_cobertura', False)
            )
            
            ofertas_por_excepcion = sum(
                1 for eval_rep in evaluaciones_repuestos 
                if eval_rep and eval_rep.get('ganador') and eval_rep.get('ganador', {}).get('es_adjudicacion_por_excepcion', False)
            )
            
            # Create evaluation record for audit
            evaluacion_record = await Evaluacion.create(
                solicitud=solicitud,
                total_ofertas_evaluadas=len(ofertas_activas),
                total_repuestos_adjudicados=len(adjudicaciones_creadas),
                monto_total_adjudicado=monto_total_adjudicado,
                peso_precio=Decimal(str(config_evaluacion['precio'])),
                peso_tiempo=Decimal(str(config_evaluacion['tiempo_entrega'])),
                peso_garantia=Decimal(str(config_evaluacion['garantia'])),
                cobertura_minima=Decimal(str(config_general['cobertura_minima_porcentaje'])) / 100,
                tiempo_evaluacion_ms=tiempo_evaluacion_ms,
                ofertas_con_cobertura_suficiente=ofertas_con_cobertura_suficiente,
                ofertas_por_excepcion=ofertas_por_excepcion,
                es_adjudicacion_mixta=es_adjudicacion_mixta,
                asesores_ganadores=len(asesores_ganadores),
                detalles_evaluacion={
                    'evaluaciones_por_repuesto': evaluaciones_repuestos,
                    'configuracion_usada': {
                        'pesos_evaluacion': config_evaluacion,
                        'parametros_generales': config_general
                    }
                }
            )
            
            logger.info(
                f"Evaluación completada para solicitud {solicitud.codigo_solicitud}: "
                f"{len(adjudicaciones_creadas)}/{total_repuestos} repuestos adjudicados, "
                f"{len(asesores_ganadores)} asesores ganadores, "
                f"monto total: ${monto_total_adjudicado:,.0f}, "
                f"tiempo: {tiempo_evaluacion_ms}ms"
            )
            
            return {
                'success': True,
                'solicitud_id': str(solicitud.id),
                'codigo_solicitud': solicitud.codigo_solicitud,
                'evaluacion_id': str(evaluacion_record.id),
                'ofertas_evaluadas': len(ofertas_activas),
                'repuestos_adjudicados': len(adjudicaciones_creadas),
                'repuestos_totales': total_repuestos,
                'tasa_adjudicacion': (len(adjudicaciones_creadas) / total_repuestos) * 100,
                'monto_total_adjudicado': float(monto_total_adjudicado),
                'tiempo_evaluacion_ms': tiempo_evaluacion_ms,
                'estado_final': nuevo_estado,
                'es_adjudicacion_mixta': es_adjudicacion_mixta,
                'asesores_ganadores': len(asesores_ganadores),
                'ofertas_ganadoras': len(ofertas_ganadoras),
                'ofertas_no_seleccionadas': len(ofertas_no_seleccionadas),
                'adjudicaciones': [
                    {
                        'adjudicacion_id': str(adj.id),
                        'repuesto_nombre': adj.repuesto_solicitado.nombre,
                        'asesor_id': str(adj.oferta.asesor.id),
                        'asesor_nombre': adj.oferta.asesor.usuario.nombre_completo,
                        'precio_adjudicado': float(adj.precio_adjudicado),
                        'tiempo_entrega': adj.tiempo_entrega_adjudicado,
                        'garantia_meses': adj.garantia_adjudicada,
                        'cantidad': adj.cantidad_adjudicada,
                        'puntaje_obtenido': float(adj.puntaje_obtenido),
                        'motivo': adj.motivo_adjudicacion,
                        'cobertura_pct': float(adj.cobertura_oferta)
                    }
                    for adj in adjudicaciones_creadas
                ],
                'evaluaciones_detalladas': evaluaciones_repuestos,
                'configuracion_usada': {
                    'pesos_evaluacion': config_evaluacion,
                    'cobertura_minima_pct': config_general['cobertura_minima_porcentaje']
                },
                'metricas': {
                    'ofertas_con_cobertura_suficiente': ofertas_con_cobertura_suficiente,
                    'ofertas_por_excepcion': ofertas_por_excepcion,
                    'tiempo_promedio_por_repuesto_ms': tiempo_evaluacion_ms / total_repuestos if total_repuestos > 0 else 0
                },
                'message': f'Evaluación completada: {len(adjudicaciones_creadas)}/{total_repuestos} repuestos adjudicados'
            }
            
        except ValueError as e:
            logger.error(f"Error de validación evaluando solicitud {solicitud_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado evaluando solicitud {solicitud_id}: {e}")
            raise ValueError(f"Error interno evaluando solicitud: {str(e)}")
    
    @staticmethod
    async def ejecutar_evaluacion_con_timeout(
        solicitud_id: str,
        timeout_segundos: Optional[int] = None,
        redis_client=None
    ) -> Dict[str, Any]:
        """
        Execute evaluation with timeout handling and event publishing
        
        Args:
            solicitud_id: ID of the solicitud to evaluate
            timeout_segundos: Timeout in seconds (uses config default if None)
            redis_client: Redis client for publishing events
            
        Returns:
            Dict with evaluation result or timeout error
        """
        try:
            # Get timeout from configuration if not provided
            if timeout_segundos is None:
                config = await ConfiguracionService.get_config('parametros_generales')
                timeout_segundos = config['timeout_evaluacion_seg']
            
            # Validate solicitud exists and has offers
            solicitud = await Solicitud.get_or_none(id=solicitud_id).prefetch_related('ofertas')
            if not solicitud:
                raise ValueError(f"Solicitud {solicitud_id} no encontrada")
            
            # Check if solicitud has offers in ENVIADA state
            ofertas_enviadas = [
                oferta for oferta in solicitud.ofertas 
                if oferta.estado == EstadoOferta.ENVIADA
            ]
            
            if not ofertas_enviadas:
                raise ValueError(
                    f"Solicitud {solicitud_id} no tiene ofertas en estado ENVIADA para evaluar"
                )
            
            logger.info(
                f"Iniciando evaluación con timeout de {timeout_segundos}s para solicitud "
                f"{solicitud.codigo_solicitud} con {len(ofertas_enviadas)} ofertas"
            )
            
            # Execute evaluation with enhanced timeout handling
            from services.error_handler_service import ErrorHandlerService
            
            timeout_result = await ErrorHandlerService.execute_with_timeout(
                EvaluacionService.evaluar_solicitud,
                timeout_segundos,
                f"evaluacion_solicitud_{solicitud.codigo_solicitud}",
                solicitud_id
            )
            
            if timeout_result['success']:
                resultado = timeout_result['result']
                
                # Publish success event to Redis
                if redis_client and resultado['success']:
                    try:
                        evento_data = {
                            'tipo_evento': 'evaluacion.completed',
                            'solicitud_id': str(solicitud.id),
                            'evaluacion_id': resultado['evaluacion_id'],
                            'ofertas_evaluadas': resultado['ofertas_evaluadas'],
                            'repuestos_adjudicados': resultado['repuestos_adjudicados'],
                            'repuestos_totales': resultado['repuestos_totales'],
                            'monto_total_adjudicado': resultado['monto_total_adjudicado'],
                            'tiempo_evaluacion_ms': resultado['tiempo_evaluacion_ms'],
                            'es_adjudicacion_mixta': resultado['es_adjudicacion_mixta'],
                            'asesores_ganadores': resultado['asesores_ganadores'],
                            'estado_final': resultado['estado_final'],
                            'adjudicaciones': resultado['adjudicaciones'],
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        await redis_client.publish('evaluacion.completed', json.dumps(evento_data))
                        logger.info(f"Evento evaluacion.completed publicado para solicitud {solicitud.id}")
                        
                    except Exception as e:
                        logger.error(f"Error publicando evento evaluacion.completed a Redis: {e}")
                
                return resultado
            else:
                # Handle timeout or execution error
                if timeout_result['error'] == 'timeout':
                    # Use enhanced timeout handling
                    timeout_data = await ErrorHandlerService.handle_evaluation_timeout(
                        str(solicitud.id),
                        timeout_segundos,
                        len(ofertas_enviadas)
                    )
                    
                    # Publish timeout event to Redis
                    if redis_client:
                        try:
                            evento_timeout = {
                                'tipo_evento': 'evaluacion.timeout',
                                'solicitud_id': str(solicitud.id),
                                'codigo_solicitud': solicitud.codigo_solicitud,
                                'timeout_segundos': timeout_segundos,
                                'ofertas_disponibles': len(ofertas_enviadas),
                                'timeout_data': timeout_data,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            await redis_client.publish('evaluacion.timeout', json.dumps(evento_timeout))
                            logger.info(f"Evento evaluacion.timeout publicado para solicitud {solicitud.id}")
                            
                        except Exception as e:
                            logger.error(f"Error publicando evento timeout a Redis: {e}")
                    
                    return {
                        'success': False,
                        'solicitud_id': str(solicitud.id),
                        'codigo_solicitud': solicitud.codigo_solicitud,
                        'error': 'timeout',
                        'timeout_segundos': timeout_segundos,
                        'ofertas_disponibles': len(ofertas_enviadas),
                        'timeout_data': timeout_data,
                        'message': f'Evaluación excedió el tiempo límite de {timeout_segundos} segundos'
                    }
                else:
                    # Execution error
                    return {
                        'success': False,
                        'solicitud_id': str(solicitud.id),
                        'codigo_solicitud': solicitud.codigo_solicitud,
                        'error': 'execution_error',
                        'error_message': timeout_result['error_message'],
                        'exception_type': timeout_result.get('exception_type'),
                        'ofertas_disponibles': len(ofertas_enviadas),
                        'message': f'Error ejecutando evaluación: {timeout_result["error_message"]}'
                    }
                
        except ValueError as e:
            logger.error(f"Error de validación en evaluación con timeout: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en evaluación con timeout: {e}")
            raise ValueError(f"Error interno en evaluación: {str(e)}")
    
    @staticmethod
    async def get_evaluacion_by_solicitud(solicitud_id: str) -> Optional[Dict[str, Any]]:
        """
        Get evaluation record for a solicitud
        
        Args:
            solicitud_id: ID of the solicitud
            
        Returns:
            Dict with evaluation data or None if not found
        """
        try:
            evaluacion = await Evaluacion.get_or_none(solicitud_id=solicitud_id).prefetch_related(
                'solicitud__repuestos_solicitados',
                'solicitud__adjudicaciones__oferta__asesor__usuario',
                'solicitud__adjudicaciones__repuesto_solicitado'
            )
            
            if not evaluacion:
                return None
            
            # Get adjudications
            adjudicaciones = evaluacion.solicitud.adjudicaciones
            
            return {
                'evaluacion_id': str(evaluacion.id),
                'solicitud_id': str(evaluacion.solicitud.id),
                'codigo_solicitud': evaluacion.solicitud.codigo_solicitud,
                'fecha_evaluacion': evaluacion.created_at.isoformat(),
                'total_ofertas_evaluadas': evaluacion.total_ofertas_evaluadas,
                'total_repuestos_adjudicados': evaluacion.total_repuestos_adjudicados,
                'monto_total_adjudicado': float(evaluacion.monto_total_adjudicado),
                'tiempo_evaluacion_ms': evaluacion.tiempo_evaluacion_ms,
                'es_adjudicacion_mixta': evaluacion.es_adjudicacion_mixta,
                'asesores_ganadores': evaluacion.asesores_ganadores,
                'configuracion_usada': {
                    'peso_precio': float(evaluacion.peso_precio),
                    'peso_tiempo': float(evaluacion.peso_tiempo),
                    'peso_garantia': float(evaluacion.peso_garantia),
                    'cobertura_minima': float(evaluacion.cobertura_minima)
                },
                'metricas': {
                    'ofertas_con_cobertura_suficiente': evaluacion.ofertas_con_cobertura_suficiente,
                    'ofertas_por_excepcion': evaluacion.ofertas_por_excepcion,
                    'tasa_adjudicacion': evaluacion.tasa_adjudicacion,
                    'duracion_evaluacion_seg': evaluacion.duracion_evaluacion_seg
                },
                'adjudicaciones': [
                    {
                        'adjudicacion_id': str(adj.id),
                        'repuesto_nombre': adj.repuesto_solicitado.nombre,
                        'asesor_id': str(adj.oferta.asesor.id),
                        'asesor_nombre': adj.oferta.asesor.usuario.nombre_completo,
                        'precio_adjudicado': float(adj.precio_adjudicado),
                        'tiempo_entrega': adj.tiempo_entrega_adjudicado,
                        'garantia_meses': adj.garantia_adjudicada,
                        'cantidad': adj.cantidad_adjudicada,
                        'puntaje_obtenido': float(adj.puntaje_obtenido),
                        'motivo': adj.motivo_adjudicacion,
                        'cobertura_pct': float(adj.cobertura_oferta)
                    }
                    for adj in adjudicaciones
                ],
                'detalles_evaluacion': evaluacion.detalles_evaluacion
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo evaluación para solicitud {solicitud_id}: {e}")
            return None
    
    @staticmethod
    async def procesar_expiracion_ofertas(
        horas_expiracion: int = 20,
        redis_client=None
    ) -> Dict[str, Any]:
        """
        Process offer expiration - mark offers as expired after specified hours
        This function should be called by a scheduled job every hour
        
        Args:
            horas_expiracion: Hours after which offers expire (default 20)
            redis_client: Redis client for publishing events
            
        Returns:
            Dict with expiration processing results
        """
        try:
            from datetime import timedelta
            
            # Calculate expiration cutoff time
            cutoff_time = datetime.now() - timedelta(hours=horas_expiracion)
            
            # Find offers to expire (ENVIADA state and created before cutoff)
            ofertas_a_expirar = await Oferta.filter(
                estado=EstadoOferta.ENVIADA,
                created_at__lt=cutoff_time
            ).prefetch_related('solicitud', 'asesor__usuario')
            
            ofertas_expiradas = []
            notificaciones_enviadas = []
            
            for oferta in ofertas_a_expirar:
                try:
                    # Update offer state to EXPIRADA
                    await oferta.update_from_dict({
                        'estado': EstadoOferta.EXPIRADA,
                        'fecha_expiracion': datetime.now(),
                        'updated_at': datetime.now()
                    })
                    
                    ofertas_expiradas.append({
                        'oferta_id': str(oferta.id),
                        'codigo_oferta': oferta.codigo_oferta,
                        'solicitud_id': str(oferta.solicitud.id),
                        'asesor_id': str(oferta.asesor.id),
                        'asesor_nombre': oferta.asesor.usuario.nombre_completo,
                        'horas_transcurridas': (datetime.now() - oferta.created_at).total_seconds() / 3600,
                        'monto_total': float(oferta.monto_total)
                    })
                    
                    # Publish expiration event to Redis
                    if redis_client:
                        try:
                            evento_data = {
                                'tipo_evento': 'oferta.expired',
                                'oferta_id': str(oferta.id),
                                'solicitud_id': str(oferta.solicitud.id),
                                'asesor_id': str(oferta.asesor.id),
                                'horas_expiracion': horas_expiracion,
                                'horas_transcurridas': (datetime.now() - oferta.created_at).total_seconds() / 3600,
                                'monto_total': float(oferta.monto_total),
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            await redis_client.publish('oferta.expired', json.dumps(evento_data))
                            
                        except Exception as e:
                            logger.error(f"Error publicando evento de expiración a Redis: {e}")
                    
                    logger.info(
                        f"Oferta {oferta.codigo_oferta} expirada automáticamente "
                        f"después de {(datetime.now() - oferta.created_at).total_seconds() / 3600:.1f} horas"
                    )
                    
                except Exception as e:
                    logger.error(f"Error expirando oferta {oferta.id}: {e}")
                    continue
            
            # Log summary
            logger.info(
                f"Proceso de expiración completado: {len(ofertas_expiradas)} ofertas expiradas "
                f"de {len(ofertas_a_expirar)} candidatas"
            )
            
            return {
                'success': True,
                'horas_expiracion': horas_expiracion,
                'ofertas_procesadas': len(ofertas_a_expirar),
                'ofertas_expiradas': len(ofertas_expiradas),
                'notificaciones_enviadas': len(notificaciones_enviadas),
                'detalles_ofertas_expiradas': ofertas_expiradas,
                'timestamp': datetime.now().isoformat(),
                'message': f'{len(ofertas_expiradas)} ofertas marcadas como expiradas'
            }
            
        except Exception as e:
            logger.error(f"Error en proceso de expiración de ofertas: {e}")
            return {
                'success': False,
                'error': str(e),
                'horas_expiracion': horas_expiracion,
                'ofertas_procesadas': 0,
                'ofertas_expiradas': 0,
                'message': f'Error procesando expiración: {str(e)}'
            }
    
    @staticmethod
    async def notificar_expiracion_proxima(
        horas_antes_expiracion: int = 2,
        horas_expiracion_total: int = 20,
        redis_client=None
    ) -> Dict[str, Any]:
        """
        Notify clients about offers that will expire soon
        This function should be called by a scheduled job
        
        Args:
            horas_antes_expiracion: Hours before expiration to send notification (default 2)
            horas_expiracion_total: Total hours for offer expiration (default 20)
            redis_client: Redis client for publishing events
            
        Returns:
            Dict with notification results
        """
        try:
            from datetime import timedelta
            
            # Calculate time window for notifications
            # Offers created between (total - before) and (total - before - 1) hours ago
            tiempo_notificacion_inicio = datetime.now() - timedelta(
                hours=horas_expiracion_total - horas_antes_expiracion
            )
            tiempo_notificacion_fin = datetime.now() - timedelta(
                hours=horas_expiracion_total - horas_antes_expiracion - 1
            )
            
            # Find offers that need expiration notification
            ofertas_por_expirar = await Oferta.filter(
                estado=EstadoOferta.ENVIADA,
                created_at__gte=tiempo_notificacion_fin,
                created_at__lt=tiempo_notificacion_inicio
            ).prefetch_related('solicitud__cliente__usuario', 'asesor__usuario')
            
            notificaciones_enviadas = []
            
            for oferta in ofertas_por_expirar:
                try:
                    # Calculate exact time remaining
                    tiempo_creacion = oferta.created_at
                    tiempo_expiracion = tiempo_creacion + timedelta(hours=horas_expiracion_total)
                    horas_restantes = (tiempo_expiracion - datetime.now()).total_seconds() / 3600
                    
                    if horas_restantes > 0:  # Only notify if not already expired
                        # Publish notification event to Redis
                        if redis_client:
                            try:
                                evento_data = {
                                    'tipo_evento': 'oferta.expiration_warning',
                                    'oferta_id': str(oferta.id),
                                    'solicitud_id': str(oferta.solicitud.id),
                                    'cliente_id': str(oferta.solicitud.cliente.id),
                                    'cliente_telefono': oferta.solicitud.cliente.usuario.telefono,
                                    'horas_restantes': round(horas_restantes, 1),
                                    'tiempo_expiracion': tiempo_expiracion.isoformat(),
                                    'monto_total': float(oferta.monto_total),
                                    'cantidad_repuestos': oferta.cantidad_repuestos,
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                await redis_client.publish('oferta.expiration_warning', json.dumps(evento_data))
                                
                                notificaciones_enviadas.append({
                                    'oferta_id': str(oferta.id),
                                    'cliente_telefono': oferta.solicitud.cliente.usuario.telefono,
                                    'horas_restantes': round(horas_restantes, 1)
                                })
                                
                            except Exception as e:
                                logger.error(f"Error publicando notificación de expiración a Redis: {e}")
                        
                        logger.info(
                            f"Notificación de expiración enviada para oferta {oferta.codigo_oferta}: "
                            f"{horas_restantes:.1f} horas restantes"
                        )
                    
                except Exception as e:
                    logger.error(f"Error notificando expiración próxima para oferta {oferta.id}: {e}")
                    continue
            
            logger.info(
                f"Proceso de notificación de expiración completado: "
                f"{len(notificaciones_enviadas)} notificaciones enviadas"
            )
            
            return {
                'success': True,
                'horas_antes_expiracion': horas_antes_expiracion,
                'ofertas_evaluadas': len(ofertas_por_expirar),
                'notificaciones_enviadas': len(notificaciones_enviadas),
                'detalles_notificaciones': notificaciones_enviadas,
                'timestamp': datetime.now().isoformat(),
                'message': f'{len(notificaciones_enviadas)} notificaciones de expiración enviadas'
            }
            
        except Exception as e:
            logger.error(f"Error en proceso de notificación de expiración: {e}")
            return {
                'success': False,
                'error': str(e),
                'ofertas_evaluadas': 0,
                'notificaciones_enviadas': 0,
                'message': f'Error procesando notificaciones: {str(e)}'
            }
    
    @staticmethod
    async def get_ofertas_proximas_a_expirar(
        horas_limite: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Get offers that will expire within specified hours
        
        Args:
            horas_limite: Hours limit to consider "próximas a expirar"
            
        Returns:
            List of offers that will expire soon
        """
        try:
            from datetime import timedelta
            
            # Get configuration for expiration time
            config = await ConfiguracionService.get_config('parametros_generales')
            horas_expiracion = config.get('timeout_ofertas_horas', 20)
            
            # Calculate cutoff time
            tiempo_limite = datetime.now() - timedelta(hours=horas_expiracion - horas_limite)
            
            # Find offers that will expire soon
            ofertas_proximas = await Oferta.filter(
                estado=EstadoOferta.ENVIADA,
                created_at__lt=tiempo_limite
            ).prefetch_related('solicitud__cliente__usuario', 'asesor__usuario')
            
            resultado = []
            
            for oferta in ofertas_proximas:
                tiempo_creacion = oferta.created_at
                tiempo_expiracion = tiempo_creacion + timedelta(hours=horas_expiracion)
                horas_restantes = (tiempo_expiracion - datetime.now()).total_seconds() / 3600
                
                if horas_restantes > 0:  # Only include if not already expired
                    resultado.append({
                        'oferta_id': str(oferta.id),
                        'codigo_oferta': oferta.codigo_oferta,
                        'solicitud_id': str(oferta.solicitud.id),
                        'cliente_telefono': oferta.solicitud.cliente.usuario.telefono,
                        'asesor_nombre': oferta.asesor.usuario.nombre_completo,
                        'monto_total': float(oferta.monto_total),
                        'cantidad_repuestos': oferta.cantidad_repuestos,
                        'created_at': oferta.created_at.isoformat(),
                        'tiempo_expiracion': tiempo_expiracion.isoformat(),
                        'horas_restantes': round(horas_restantes, 1),
                        'minutos_restantes': round(horas_restantes * 60),
                        'es_critica': horas_restantes <= 1  # Less than 1 hour remaining
                    })
            
            # Sort by time remaining (most urgent first)
            resultado.sort(key=lambda x: x['horas_restantes'])
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error obteniendo ofertas próximas a expirar: {e}")
            return []