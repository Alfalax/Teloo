"""
Escalamiento Service for TeLOO V3
Handles advisor escalation algorithm with geographic proximity, activity, performance and trust metrics
"""

from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import logging
from models.geografia import Municipio, EvaluacionAsesorTemp
from models.user import Asesor
from models.solicitud import Solicitud
from models.analytics import (
    HistorialRespuestaOferta, 
    OfertaHistorica, 
    AuditoriaTienda,
    ParametroConfig
)
from models.enums import CanalNotificacion, EstadoAsesor, EstadoUsuario
from services.events_service import events_service
from services.notification_service import notification_service
from models.analytics import ParametroConfig
from utils.datetime_utils import now_utc


class EscalamientoService:
    """
    Service for advisor escalation algorithm
    Implements the 4-variable scoring system with geographic proximity
    """
    
    @staticmethod
    async def calcular_proximidad(
        municipio_solicitud: Municipio, 
        municipio_asesor: Municipio
    ) -> Tuple[Decimal, str]:
        """
        Calcula proximidad geográfica entre municipio de solicitud y asesor
        USANDO OBJETOS Municipio directamente - Fuente única de verdad
        
        Niveles de proximidad:
        - 5.0: Misma ciudad
        - 4.0: Área metropolitana
        - 3.5: Hub logístico  
        - 3.0: Otras ciudades (fallback)
        
        Args:
            municipio_solicitud: Municipio donde se originó la solicitud
            municipio_asesor: Municipio donde está ubicado el asesor
            
        Returns:
            Tuple[Decimal, str]: (puntaje_proximidad, criterio_aplicado)
        """
        
        # Nivel 1: Misma ciudad (5.0)
        if municipio_solicitud.id == municipio_asesor.id:
            return Decimal('5.0'), "misma_ciudad"
        
        # Nivel 2: Área metropolitana (4.0)
        if (municipio_solicitud.area_metropolitana and 
            municipio_solicitud.area_metropolitana != 'NO' and
            municipio_solicitud.area_metropolitana == municipio_asesor.area_metropolitana):
            return Decimal('4.0'), "area_metropolitana"
        
        # Nivel 3: Hub logístico (3.5)
        if municipio_solicitud.hub_logistico == municipio_asesor.hub_logistico:
            return Decimal('3.5'), "hub_logistico"
        
        # Nivel 4: Fallback para ciudades sin cobertura (3.0)
        return Decimal('3.0'), "fuera_de_cobertura"
    
    @staticmethod
    async def calcular_actividad_reciente(
        asesor_id: str, 
        periodo_dias: int = 30
    ) -> Decimal:
        """
        Calcula actividad reciente del asesor en escala 1-5
        
        Fórmula: (ofertas_respondidas / ofertas_enviadas) * 100
        Normalización: actividad_5 = 1 + 4 * (pct / 100)
        
        Args:
            asesor_id: ID del asesor
            periodo_dias: Período a evaluar (default 30 días)
            
        Returns:
            Decimal: Puntaje de actividad en escala 1-5
        """
        
        from utils.datetime_utils import now_utc, add_days
        fecha_inicio = add_days(now_utc(), -periodo_dias)
        
        # Obtener historial de respuestas en el período
        historial = await HistorialRespuestaOferta.filter(
            asesor_id=asesor_id,
            fecha_envio__gte=fecha_inicio
        ).all()
        
        if not historial:
            # Fallback: Sin datos = 1.0 en escala 1-5
            fallbacks = await EscalamientoService.aplicar_fallbacks_metricas(asesor_id)
            return fallbacks['actividad_reciente']
        
        # Calcular porcentaje de respuesta
        total_enviadas = len(historial)
        total_respondidas = sum(1 for h in historial if h.respondio)
        
        if total_enviadas == 0:
            return Decimal('1.0')
        
        pct_actividad = (total_respondidas / total_enviadas) * 100
        
        # Normalizar a escala 1-5
        actividad_5 = 1 + 4 * (pct_actividad / 100)
        
        return Decimal(str(round(actividad_5, 2)))
    
    @staticmethod
    async def calcular_desempeno_historico(
        asesor_id: str,
        periodo_meses: int = 6
    ) -> Decimal:
        """
        Calcula desempeño histórico del asesor en escala 1-5
        
        Componentes:
        - Tasa adjudicación (50%): ofertas ganadoras / total ofertas
        - Tasa cumplimiento (30%): entregas exitosas / ofertas aceptadas
        - Eficiencia respuesta (20%): tiempo promedio de respuesta
        
        Args:
            asesor_id: ID del asesor
            periodo_meses: Período a evaluar (default 6 meses)
            
        Returns:
            Decimal: Puntaje de desempeño en escala 1-5
        """
        
        fecha_inicio = add_days(now_utc(), -(periodo_meses * 30))
        
        # Obtener ofertas históricas en el período
        ofertas_hist = await OfertaHistorica.filter(
            asesor_id=asesor_id,
            fecha__gte=fecha_inicio.date()
        ).all()
        
        if not ofertas_hist:
            # Fallback: Sin datos = 1.0 en escala 1-5
            fallbacks = await EscalamientoService.aplicar_fallbacks_metricas(asesor_id)
            return fallbacks['desempeno_historico']
        
        total_ofertas = len(ofertas_hist)
        ofertas_adjudicadas = [o for o in ofertas_hist if o.adjudicada]
        ofertas_aceptadas = [o for o in ofertas_adjudicadas if o.aceptada_cliente]
        ofertas_exitosas = [o for o in ofertas_aceptadas if o.entrega_exitosa]
        
        # 1. Tasa de adjudicación (50%)
        tasa_adjudicacion = len(ofertas_adjudicadas) / total_ofertas if total_ofertas > 0 else 0
        
        # 2. Tasa de cumplimiento (30%)
        tasa_cumplimiento = len(ofertas_exitosas) / len(ofertas_aceptadas) if ofertas_aceptadas else 0
        
        # 3. Eficiencia de respuesta (20%)
        # Normalizar tiempo de respuesta (menor tiempo = mejor puntaje)
        tiempos_respuesta = [o.tiempo_respuesta_seg for o in ofertas_hist if o.tiempo_respuesta_seg]
        if tiempos_respuesta:
            tiempo_promedio_seg = sum(tiempos_respuesta) / len(tiempos_respuesta)
            # Normalizar: 1 hora = 100%, 24 horas = 0%
            eficiencia_respuesta = max(0, 1 - (tiempo_promedio_seg / (24 * 3600)))
        else:
            eficiencia_respuesta = 0
        
        # Calcular puntaje ponderado
        puntaje_ponderado = (
            tasa_adjudicacion * 0.5 +
            tasa_cumplimiento * 0.3 +
            eficiencia_respuesta * 0.2
        )
        
        # Normalizar a escala 1-5
        desempeno_5 = 1 + 4 * puntaje_ponderado
        
        return Decimal(str(round(desempeno_5, 2)))
    
    @staticmethod
    async def obtener_nivel_confianza(
        asesor_id: str,
        vigencia_dias: int = 30
    ) -> Decimal:
        """
        Obtiene el nivel de confianza del asesor desde la tabla asesores
        
        Args:
            asesor_id: ID del asesor
            vigencia_dias: Días de vigencia de la auditoría (no usado actualmente)
            
        Returns:
            Decimal: Nivel de confianza en escala 1-5
        """
        from models.user import Asesor
        
        # Leer directamente el campo confianza de la tabla asesores
        asesor = await Asesor.get_or_none(id=asesor_id)
        
        if asesor and asesor.confianza:
            return Decimal(str(asesor.confianza))
        
        # Fallback: Si no existe el asesor o no tiene confianza = 3.0
        return Decimal('3.0')
    
    @staticmethod
    async def determinar_asesores_elegibles(solicitud: Solicitud) -> List[Asesor]:
        """
        Determina asesores elegibles basado en 3 características geográficas
        USANDO FK municipio_id - Fuente única de verdad
        
        Características:
        1. Asesores de misma ciudad
        2. Asesores de todas las áreas metropolitanas nacionales  
        3. Asesores del hub logístico de la ciudad
        
        Args:
            solicitud: Solicitud para la cual determinar asesores
            
        Returns:
            List[Asesor]: Lista de asesores elegibles sin duplicados
        """
        
        ciudad_solicitud = solicitud.ciudad_origen
        departamento_solicitud = solicitud.departamento_origen
        
        # Normalizar ciudad y departamento de la solicitud
        ciudad_norm = Municipio.normalizar_ciudad(ciudad_solicitud)
        departamento_norm = Municipio.normalizar_ciudad(departamento_solicitud)
        
        # Obtener municipio de la solicitud usando ciudad Y departamento
        municipio_solicitud = await Municipio.get_or_none(
            municipio_norm=ciudad_norm,
            departamento=departamento_norm
        )
        
        if not municipio_solicitud:
            logger.warning(f"Ciudad {ciudad_solicitud}, {departamento_solicitud} no encontrada en base de datos de municipios")
            # Fallback: buscar todos los asesores activos
            asesores_fallback = await Asesor.filter(
                estado=EstadoAsesor.ACTIVO,
                usuario__estado=EstadoUsuario.ACTIVO
            ).prefetch_related('usuario', 'municipio').all()
            logger.info(f"Fallback: {len(asesores_fallback)} asesores activos")
            return asesores_fallback
        
        logger.info(f"📍 Municipio solicitud: {municipio_solicitud.municipio} ({municipio_solicitud.departamento})")
        logger.info(f"   Hub: {municipio_solicitud.hub_logistico}, Área Metro: {municipio_solicitud.area_metropolitana}")
        
        asesores_elegibles = set()
        
        # Característica 1: Asesores de misma ciudad (JOIN directo por FK)
        asesores_misma_ciudad = await Asesor.filter(
            municipio_id=municipio_solicitud.id,
            estado=EstadoAsesor.ACTIVO,
            usuario__estado=EstadoUsuario.ACTIVO
        ).prefetch_related('usuario', 'municipio').all()
        
        for asesor in asesores_misma_ciudad:
            asesores_elegibles.add(asesor.id)
        
        logger.info(f"✅ Característica 1 - Misma ciudad ({municipio_solicitud.municipio}): {len(asesores_misma_ciudad)} asesores")
        
        # Característica 2: Asesores de TODAS las áreas metropolitanas nacionales
        # IMPORTANTE: Esto se aplica SIEMPRE, sin importar si la solicitud viene de área metropolitana o no
        asesores_areas_metro = await Asesor.filter(
            municipio__area_metropolitana__isnull=False,
            municipio__area_metropolitana__not='NO',
            estado=EstadoAsesor.ACTIVO,
            usuario__estado=EstadoUsuario.ACTIVO
        ).prefetch_related('usuario', 'municipio').all()
        
        for asesor in asesores_areas_metro:
            asesores_elegibles.add(asesor.id)
        
        logger.info(f"✅ Característica 2 - Áreas metropolitanas nacionales (SIEMPRE): {len(asesores_areas_metro)} asesores, {len(asesores_elegibles)} acumulados")
        
        # Característica 3: Asesores del hub logístico de la ciudad (JOIN directo)
        asesores_hub = await Asesor.filter(
            municipio__hub_logistico=municipio_solicitud.hub_logistico,
            estado=EstadoAsesor.ACTIVO,
            usuario__estado=EstadoUsuario.ACTIVO
        ).prefetch_related('usuario', 'municipio').all()
        
        for asesor in asesores_hub:
            asesores_elegibles.add(asesor.id)
        
        logger.info(f"✅ Característica 3 - Hub logístico ({municipio_solicitud.hub_logistico}): {len(asesores_hub)} asesores, {len(asesores_elegibles)} acumulados")
        
        # Obtener objetos Asesor únicos con todas las relaciones
        asesores_finales = await Asesor.filter(
            id__in=list(asesores_elegibles)
        ).prefetch_related('usuario', 'municipio').all()
        
        logger.info(f"🎯 Total asesores elegibles (sin duplicados): {len(asesores_finales)}")
        
        return asesores_finales
    
    @staticmethod
    async def calcular_puntaje_asesor(
        asesor: Asesor, 
        solicitud: Solicitud,
        pesos: Optional[Dict[str, float]] = None
    ) -> Tuple[Decimal, Dict[str, Decimal]]:
        """
        Calcula puntaje total del asesor para una solicitud específica con manejo robusto de errores
        
        Variables y pesos por defecto:
        - Proximidad geográfica: 40%
        - Actividad reciente: 25%  
        - Desempeño histórico: 20%
        - Nivel de confianza: 15%
        
        Args:
            asesor: Asesor a evaluar
            solicitud: Solicitud para contexto geográfico
            pesos: Pesos personalizados (opcional)
            
        Returns:
            Tuple[Decimal, Dict]: (puntaje_total, variables_individuales)
        """
        
        # Pesos por defecto
        if pesos is None:
            pesos = {
                'proximidad': 0.40,
                'actividad': 0.25,
                'desempeno': 0.20,
                'confianza': 0.15
            }
        
        # Variables para almacenar resultados y errores
        variables = {}
        errores_calculo = []
        
        # 1. Calcular proximidad geográfica (crítica - no puede fallar)
        try:
            # Obtener municipio de la solicitud usando FK directo
            municipio_solicitud = solicitud.municipio if hasattr(solicitud, 'municipio') and solicitud.municipio else None
            
            # Si no está precargado, obtenerlo por ID
            if not municipio_solicitud and solicitud.municipio_id:
                municipio_solicitud = await Municipio.get_or_none(id=solicitud.municipio_id)
            
            if not municipio_solicitud:
                logger.warning(f"Municipio solicitud {solicitud.ciudad_origen} no encontrado")
                variables['proximidad'] = Decimal('3.0')
                variables['criterio_proximidad'] = "municipio_no_encontrado"
            elif not asesor.municipio:
                logger.warning(f"Asesor {asesor.id} sin municipio asignado")
                variables['proximidad'] = Decimal('3.0')
                variables['criterio_proximidad'] = "asesor_sin_municipio"
            else:
                # Usar objetos Municipio directamente
                proximidad, criterio_prox = await EscalamientoService.calcular_proximidad(
                    municipio_solicitud, 
                    asesor.municipio
                )
                variables['proximidad'] = proximidad
                variables['criterio_proximidad'] = criterio_prox
        except Exception as e:
            logger.error(f"Error calculando proximidad para asesor {asesor.id}: {e}")
            # Fallback crítico - proximidad por defecto
            variables['proximidad'] = Decimal('3.0')
            variables['criterio_proximidad'] = "error_calculo"
            errores_calculo.append(f"proximidad: {str(e)}")
        
        # 2. Calcular actividad reciente (con fallback)
        try:
            actividad = await EscalamientoService.calcular_actividad_reciente(str(asesor.id))
            variables['actividad_reciente_5'] = actividad
        except Exception as e:
            logger.warning(f"Error calculando actividad reciente para asesor {asesor.id}: {e}")
            variables['actividad_reciente_5'] = Decimal('1.0')  # Fallback: actividad neutra
            errores_calculo.append(f"actividad: {str(e)}")
        
        # 3. Calcular desempeño histórico (con fallback)
        try:
            desempeno = await EscalamientoService.calcular_desempeno_historico(str(asesor.id))
            variables['desempeno_historico_5'] = desempeno
        except Exception as e:
            logger.warning(f"Error calculando desempeño histórico para asesor {asesor.id}: {e}")
            variables['desempeno_historico_5'] = Decimal('1.0')  # Fallback: desempeño neutro
            errores_calculo.append(f"desempeno: {str(e)}")
        
        # 4. Obtener nivel de confianza (con fallback)
        try:
            confianza = await EscalamientoService.obtener_nivel_confianza(str(asesor.id))
            variables['nivel_confianza'] = confianza
        except Exception as e:
            logger.warning(f"Error obteniendo nivel de confianza para asesor {asesor.id}: {e}")
            variables['nivel_confianza'] = Decimal('3.0')  # Fallback: confianza media
            errores_calculo.append(f"confianza: {str(e)}")
        
        # Validar que todas las variables estén presentes
        required_vars = ['proximidad', 'actividad_reciente_5', 'desempeno_historico_5', 'nivel_confianza']
        for var in required_vars:
            if var not in variables:
                logger.error(f"Variable {var} faltante para asesor {asesor.id}, aplicando fallback")
                fallback_values = {
                    'proximidad': Decimal('3.0'),
                    'actividad_reciente_5': Decimal('1.0'),
                    'desempeno_historico_5': Decimal('1.0'),
                    'nivel_confianza': Decimal('3.0')
                }
                variables[var] = fallback_values[var]
        
        # Calcular puntaje total ponderado con manejo de errores
        try:
            puntaje_total = (
                float(variables['proximidad']) * pesos['proximidad'] +
                float(variables['actividad_reciente_5']) * pesos['actividad'] +
                float(variables['desempeno_historico_5']) * pesos['desempeno'] +
                float(variables['nivel_confianza']) * pesos['confianza']
            )
            
            # Validar que el puntaje esté en rango válido (1.0 - 5.0)
            if puntaje_total < 1.0:
                logger.warning(f"Puntaje calculado {puntaje_total} < 1.0 para asesor {asesor.id}, ajustando a 1.0")
                puntaje_total = 1.0
            elif puntaje_total > 5.0:
                logger.warning(f"Puntaje calculado {puntaje_total} > 5.0 para asesor {asesor.id}, ajustando a 5.0")
                puntaje_total = 5.0
            
        except Exception as e:
            logger.error(f"Error calculando puntaje total para asesor {asesor.id}: {e}")
            # Fallback: puntaje promedio basado en confianza
            puntaje_total = float(variables.get('nivel_confianza', Decimal('3.0')))
            errores_calculo.append(f"puntaje_total: {str(e)}")
        
        # Agregar información de errores a las variables si hubo problemas
        if errores_calculo:
            variables['errores_calculo'] = errores_calculo
            logger.warning(f"Asesor {asesor.id} calculado con {len(errores_calculo)} errores: {errores_calculo}")
        
        return Decimal(str(round(puntaje_total, 2))), variables
    
    @staticmethod
    async def clasificar_por_niveles(
        evaluaciones: List[Tuple[Asesor, Decimal, Dict[str, Decimal]]],
        umbrales: Optional[Dict[str, float]] = None
    ) -> Dict[int, List[Dict]]:
        """
        Clasifica asesores en niveles 1-5 según puntaje total
        
        Umbrales por defecto:
        - Nivel 1: >= 4.5
        - Nivel 2: >= 4.0  
        - Nivel 3: >= 3.5
        - Nivel 4: >= 3.0
        - Nivel 5: < 3.0
        
        Args:
            evaluaciones: Lista de (asesor, puntaje_total, variables)
            umbrales: Umbrales personalizados (opcional)
            
        Returns:
            Dict[int, List]: Asesores agrupados por nivel
        """
        
        # Umbrales por defecto
        if umbrales is None:
            umbrales = {
                'nivel1_min': 4.5,
                'nivel2_min': 4.0,
                'nivel3_min': 3.5,
                'nivel4_min': 3.0
            }
        
        # Obtener configuración de canales y tiempos por nivel
        config_canales = await ParametroConfig.get_valor('canales_por_nivel', {
            1: 'WHATSAPP',
            2: 'WHATSAPP', 
            3: 'PUSH',
            4: 'PUSH',
            5: 'PUSH'
        })
        
        config_tiempos = await ParametroConfig.get_valor('tiempos_espera_nivel', {
            1: 15,  # minutos
            2: 20,
            3: 25,
            4: 30,
            5: 35
        })
        
        # Clasificar por niveles
        niveles = {1: [], 2: [], 3: [], 4: [], 5: []}
        
        for asesor, puntaje_total, variables in evaluaciones:
            # Determinar nivel según puntaje
            if float(puntaje_total) >= umbrales['nivel1_min']:
                nivel = 1
            elif float(puntaje_total) >= umbrales['nivel2_min']:
                nivel = 2
            elif float(puntaje_total) >= umbrales['nivel3_min']:
                nivel = 3
            elif float(puntaje_total) >= umbrales['nivel4_min']:
                nivel = 4
            else:
                nivel = 5
            
            # Crear registro de evaluación
            evaluacion_data = {
                'asesor': asesor,
                'puntaje_total': puntaje_total,
                'nivel_entrega': nivel,
                'canal': CanalNotificacion(config_canales.get(nivel, 'PUSH')),
                'tiempo_espera_min': config_tiempos.get(nivel, 30),
                'variables': variables
            }
            
            niveles[nivel].append(evaluacion_data)
        
        # Log estadísticas de clasificación
        for nivel, asesores in niveles.items():
            if asesores:
                logger.info(f"Nivel {nivel}: {len(asesores)} asesores - Canal: {config_canales.get(nivel)}")
        
        return niveles
    
    @staticmethod
    async def guardar_evaluaciones_temp(
        solicitud: Solicitud,
        niveles: Dict[int, List[Dict]]
    ) -> List[EvaluacionAsesorTemp]:
        """
        Guarda evaluaciones temporales en la base de datos
        
        Args:
            solicitud: Solicitud para la cual se evaluaron los asesores
            niveles: Asesores clasificados por nivel
            
        Returns:
            List[EvaluacionAsesorTemp]: Evaluaciones creadas
        """
        
        evaluaciones_creadas = []
        
        for nivel, asesores_nivel in niveles.items():
            for eval_data in asesores_nivel:
                asesor = eval_data['asesor']
                variables = eval_data['variables']
                
                # Crear evaluación temporal con fecha_notificacion
                fecha_notificacion = datetime.now()
                evaluacion = await EvaluacionAsesorTemp.create(
                    solicitud=solicitud,
                    asesor=asesor,
                    proximidad=variables['proximidad'],
                    actividad_reciente_5=variables['actividad_reciente_5'],
                    desempeno_historico_5=variables['desempeno_historico_5'],
                    nivel_confianza=variables['nivel_confianza'],
                    puntaje_total=eval_data['puntaje_total'],
                    nivel_entrega=eval_data['nivel_entrega'],
                    canal=eval_data['canal'],
                    tiempo_espera_min=eval_data['tiempo_espera_min'],
                    criterio_proximidad=variables['criterio_proximidad'],
                    ciudad_asesor=asesor.ciudad,
                    ciudad_solicitud=solicitud.ciudad_origen,
                    fecha_notificacion=fecha_notificacion,  # Establecer fecha de notificación
                    fecha_timeout=fecha_notificacion + timedelta(minutes=eval_data['tiempo_espera_min']),
                    detalles_calculo={
                        'pesos': {
                            'proximidad': 0.40,
                            'actividad': 0.25,
                            'desempeno': 0.20,
                            'confianza': 0.15
                        },
                        'variables_calculadas': {
                            'proximidad': float(variables['proximidad']),
                            'actividad_reciente_5': float(variables['actividad_reciente_5']),
                            'desempeno_historico_5': float(variables['desempeno_historico_5']),
                            'nivel_confianza': float(variables['nivel_confianza'])
                        },
                        'timestamp_calculo': datetime.now().isoformat()
                    }
                )
                
                evaluaciones_creadas.append(evaluacion)
        
        logger.info(f"Guardadas {len(evaluaciones_creadas)} evaluaciones temporales para solicitud {solicitud.id}")
        
        # Registrar en historial_respuestas_ofertas para métricas de actividad
        try:
            fecha_asignacion = datetime.utcnow()
            
            for evaluacion in evaluaciones_creadas:
                await events_service.on_solicitud_escalada(
                    solicitud_id=solicitud.id,
                    asesores_notificados=[{'asesor_id': evaluacion.asesor.id}],
                    nivel=evaluacion.nivel_entrega,
                    canal=evaluacion.canal.value
                )
            
            logger.info(f"✅ Registrados {len(evaluaciones_creadas)} asesores en historial_respuestas_ofertas")
        except Exception as e:
            logger.error(f"❌ Error registrando historial de respuestas: {e}", exc_info=True)
        
        return evaluaciones_creadas
    
    @staticmethod
    async def ejecutar_oleada(
        solicitud: Solicitud,
        nivel: int,
        redis_client=None
    ) -> Dict:
        """
        Ejecuta oleada de notificaciones para un nivel específico
        
        Args:
            solicitud: Solicitud para la cual ejecutar oleada
            nivel: Nivel de asesores a notificar (1-5)
            redis_client: Cliente Redis para publicar eventos
            
        Returns:
            Dict: Resultado de la ejecución
        """
        try:
            # Obtener asesores del nivel desde EvaluacionAsesorTemp
            from models.solicitud import EvaluacionAsesorTemp
            evaluaciones = await EvaluacionAsesorTemp.filter(
                solicitud=solicitud,
                nivel_entrega=nivel
            ).prefetch_related('asesor__usuario').all()
            
            if not evaluaciones:
                logger.warning(f"No hay asesores en nivel {nivel} para solicitud {solicitud.id}")
                return {
                    'success': False,
                    'message': f'No hay asesores en nivel {nivel}',
                    'asesores_notificados': 0
                }
            
            notificados = 0
            
            # Enviar notificaciones según el canal configurado para cada asesor
            for evaluacion in evaluaciones:
                try:
                    user_id = str(evaluacion.asesor.usuario.id)
                    canal = evaluacion.canal
                    
                    logger.info(f"Notificando asesor {evaluacion.asesor.usuario.nombre_completo} vía {canal}")
                    
                    # Usar el servicio de notificación unificado
                    exito = await notification_service.send_notification(
                        user_id=user_id,
                        title="Nueva Solicitud de Repuestos",
                        message=f"Tienes una nueva solicitud ({solicitud.codigo_solicitud}) disponible en Nivel {nivel}.",
                        notification_type="solicitud_nueva",
                        data={
                            "solicitud_id": str(solicitud.id),
                            "codigo": solicitud.codigo_solicitud,
                            "nivel": nivel,
                            "vehiculo": f"{solicitud.marca_vehiculo} {solicitud.linea_vehiculo}"
                        },
                        priority="high" if nivel <= 2 else "normal"
                    )
                    
                    if exito:
                        # Marcar como notificado
                        evaluacion.fecha_notificacion = now_utc()
                        evaluacion.fecha_timeout = now_utc() + timedelta(
                            minutes=evaluacion.tiempo_espera_min
                        )
                        await evaluacion.save()
                        notificados += 1
                        
                except Exception as e:
                    logger.error(f"Error notificando al asesor {evaluacion.asesor.id}: {e}")
            
            # Registrar evento en tablas auxiliares para métricas de escalamiento
            try:
                asesores_notificados_data = []
                for evaluacion in evaluaciones:
                    if evaluacion.fecha_notificacion:
                        asesores_notificados_data.append({
                            'asesor_id': str(evaluacion.asesor.id)
                        })
                
                if asesores_notificados_data:
                    await events_service.on_solicitud_escalada(
                        solicitud_id=str(solicitud.id),
                        asesores_notificados=asesores_notificados_data,
                        nivel=nivel,
                        canal="MIXTO" # Puede ser WhatsApp o Push
                    )
            except Exception as e:
                logger.error(f"Error registrando evento solicitud_escalada: {e}")
            
            return {
                'success': True,
                'message': f'Oleada Nivel {nivel} ejecutada',
                'asesores_notificados': notificados
            }
            
        except Exception as e:
            logger.error(f"Error crítico en ejecutar_oleada: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    async def verificar_cierre_anticipado(
        solicitud: Solicitud,
        ofertas_minimas_deseadas: Optional[int] = None
    ) -> bool:
        """
        Verifica si se puede cerrar anticipadamente el escalamiento
        
        Args:
            solicitud: Solicitud a verificar
            ofertas_minimas_deseadas: Número mínimo de ofertas (default: solicitud.ofertas_minimas_deseadas)
            
        Returns:
            bool: True si se puede cerrar anticipadamente
        """
        
        # Usar configuración de la solicitud si no se especifica
        if ofertas_minimas_deseadas is None:
            ofertas_minimas_deseadas = solicitud.ofertas_minimas_deseadas or 2
        
        # Contar ofertas recibidas en estado ENVIADA
        ofertas_recibidas = await solicitud.contar_ofertas_activas()
        
        logger.info(
            f"Solicitud {solicitud.id}: {ofertas_recibidas} ofertas recibidas, "
            f"mínimo deseado: {ofertas_minimas_deseadas}"
        )
        
        # Verificar si se alcanzó el mínimo
        puede_cerrar = ofertas_recibidas >= ofertas_minimas_deseadas
        
        if puede_cerrar:
            logger.info(f"Solicitud {solicitud.id}: Cierre anticipado activado")
        
        return puede_cerrar
    
    @staticmethod
    async def validar_asesor_elegible(asesor: Asesor) -> Tuple[bool, str]:
        """
        Valida si un asesor es elegible para participar en escalamiento
        
        Validaciones:
        - Estado activo
        - Usuario activo
        - Confianza mínima para operar
        
        Args:
            asesor: Asesor a validar
            
        Returns:
            Tuple[bool, str]: (es_elegible, razon_exclusion)
        """
        
        # Verificar estado del asesor
        if not asesor.is_active():
            return False, f"Asesor inactivo (estado: {asesor.estado})"
        
        # Verificar estado del usuario
        if not asesor.usuario.is_active():
            return False, f"Usuario inactivo (estado: {asesor.usuario.estado})"
        
        # Verificar confianza mínima
        parametros_generales = await ParametroConfig.get_valor('parametros_generales', {})
        confianza_minima = parametros_generales.get('confianza_minima_operar', 2.0)
        
        if not asesor.cumple_confianza_minima(confianza_minima):
            return False, f"Confianza insuficiente ({asesor.confianza} < {confianza_minima})"
        
        return True, "Elegible"
    
    @staticmethod
    async def filtrar_asesores_elegibles(asesores: List[Asesor]) -> Tuple[List[Asesor], List[Dict]]:
        """
        Filtra asesores elegibles y registra exclusiones
        
        Args:
            asesores: Lista de asesores a filtrar
            
        Returns:
            Tuple[List[Asesor], List[Dict]]: (asesores_elegibles, asesores_excluidos)
        """
        
        asesores_elegibles = []
        asesores_excluidos = []
        
        for asesor in asesores:
            es_elegible, razon = await EscalamientoService.validar_asesor_elegible(asesor)
            
            if es_elegible:
                asesores_elegibles.append(asesor)
            else:
                asesores_excluidos.append({
                    'asesor_id': str(asesor.id),
                    'nombre': asesor.usuario.nombre_completo,
                    'ciudad': asesor.ciudad,
                    'razon_exclusion': razon
                })
                
                logger.warning(f"Asesor excluido: {asesor.usuario.nombre_completo} - {razon}")
        
        logger.info(f"Filtrado: {len(asesores_elegibles)} elegibles, {len(asesores_excluidos)} excluidos")
        
        return asesores_elegibles, asesores_excluidos
    
    @staticmethod
    async def manejar_ciudad_sin_cobertura(ciudad: str) -> Tuple[Decimal, str]:
        """
        Maneja casos de ciudades sin área metropolitana ni hub logístico
        
        Args:
            ciudad: Ciudad sin cobertura geográfica
            
        Returns:
            Tuple[Decimal, str]: (proximidad_fallback, criterio)
        """
        
        from services.error_handler_service import ErrorHandlerService
        
        # Use enhanced geographic fallback handling
        fallback_data = await ErrorHandlerService.handle_geographic_fallback(ciudad)
        
        return fallback_data['proximidad'], fallback_data['criterio']
    
    @staticmethod
    async def aplicar_fallbacks_metricas(asesor_id: str) -> Dict[str, Decimal]:
        """
        Aplica valores fallback para métricas faltantes
        Lee valores configurables desde BD, con fallback a 3.0 si no existen
        
        Args:
            asesor_id: ID del asesor
            
        Returns:
            Dict: Métricas con fallbacks aplicados
        """
        # Obtener valores configurables desde BD
        try:
            fallback_actividad = await ParametroConfig.get_valor(
                'fallback_actividad_asesores_nuevos',
                default=3.0
            )
            fallback_desempeno = await ParametroConfig.get_valor(
                'fallback_desempeno_asesores_nuevos',
                default=3.0
            )
        except Exception as e:
            logger.warning(f"Error obteniendo fallbacks configurables: {e}. Usando valores por defecto.")
            fallback_actividad = 3.0
            fallback_desempeno = 3.0
        
        fallbacks = {
            'actividad_reciente': Decimal(str(fallback_actividad)),
            'desempeno_historico': Decimal(str(fallback_desempeno)),
            'nivel_confianza': Decimal('3.0')  # Este siempre es 3.0 por defecto
        }
        
        logger.info(f"Aplicando fallbacks configurables para asesor {asesor_id}: {fallbacks}")
        
        return fallbacks
    
    @staticmethod
    async def procesar_escalamiento_completo(solicitud: Solicitud) -> Dict:
        """
        Procesa escalamiento completo con manejo robusto de errores
        
        Args:
            solicitud: Solicitud a procesar
            
        Returns:
            Dict: Resultado completo del escalamiento
        """
        
        try:
            logger.info(f"Iniciando escalamiento completo para solicitud {solicitud.id}")
            
            # 1. Determinar asesores elegibles
            asesores_candidatos = await EscalamientoService.determinar_asesores_elegibles(solicitud)
            
            if not asesores_candidatos:
                logger.warning(f"No se encontraron asesores candidatos para solicitud {solicitud.id}")
                return {
                    'success': False,
                    'error': 'No hay asesores disponibles en la zona geográfica',
                    'asesores_evaluados': 0
                }
            
            # 2. Filtrar asesores elegibles (validaciones de confianza, estado, etc.)
            asesores_elegibles, asesores_excluidos = await EscalamientoService.filtrar_asesores_elegibles(asesores_candidatos)
            
            if not asesores_elegibles:
                logger.warning(f"Todos los asesores fueron excluidos para solicitud {solicitud.id}")
                return {
                    'success': False,
                    'error': 'No hay asesores elegibles después de aplicar filtros',
                    'asesores_candidatos': len(asesores_candidatos),
                    'asesores_excluidos': asesores_excluidos
                }
            
            # 3. Calcular puntajes con manejo de errores
            evaluaciones = []
            errores_calculo = []
            
            for asesor in asesores_elegibles:
                try:
                    puntaje_total, variables = await EscalamientoService.calcular_puntaje_asesor(asesor, solicitud)
                    evaluaciones.append((asesor, puntaje_total, variables))
                    
                except Exception as e:
                    logger.error(f"Error calculando puntaje para asesor {asesor.id}: {e}")
                    errores_calculo.append({
                        'asesor_id': str(asesor.id),
                        'error': str(e)
                    })
            
            if not evaluaciones:
                return {
                    'success': False,
                    'error': 'No se pudieron calcular puntajes para ningún asesor',
                    'errores_calculo': errores_calculo
                }
            
            # 4. Clasificar por niveles
            niveles = await EscalamientoService.clasificar_por_niveles(evaluaciones)
            
            # 5. Guardar evaluaciones temporales
            evaluaciones_guardadas = await EscalamientoService.guardar_evaluaciones_temp(solicitud, niveles)
            
            # 6. Estadísticas del resultado
            total_por_nivel = {nivel: len(asesores) for nivel, asesores in niveles.items() if asesores}
            
            return {
                'success': True,
                'message': 'Escalamiento completado exitosamente',
                'estadisticas': {
                    'asesores_candidatos': len(asesores_candidatos),
                    'asesores_elegibles': len(asesores_elegibles),
                    'asesores_excluidos': len(asesores_excluidos),
                    'evaluaciones_exitosas': len(evaluaciones),
                    'errores_calculo': len(errores_calculo),
                    'evaluaciones_guardadas': len(evaluaciones_guardadas),
                    'distribucion_niveles': total_por_nivel
                },
                'asesores_excluidos': asesores_excluidos,
                'errores_calculo': errores_calculo,
                'niveles_generados': list(total_por_nivel.keys())
            }
            
        except Exception as e:
            logger.error(f"Error crítico en escalamiento para solicitud {solicitud.id}: {e}")
            return {
                'success': False,
                'error': f'Error crítico en escalamiento: {str(e)}',
                'solicitud_id': str(solicitud.id)
            }
    
    @staticmethod
    async def ejecutar_escalamiento_con_primera_oleada(solicitud_id: str) -> Dict:
        """
        Ejecuta el escalamiento completo y la primera oleada automáticamente
        
        Args:
            solicitud_id: ID de la solicitud
            
        Returns:
            Dict: Resultado del escalamiento y primera oleada
        """
        try:
            # 1. Obtener solicitud
            solicitud = await Solicitud.get_or_none(id=solicitud_id).prefetch_related('cliente__usuario', 'municipio')
            
            if not solicitud:
                return {
                    'success': False,
                    'error': f'Solicitud {solicitud_id} no encontrada'
                }
            
            logger.info(f"🚀 Ejecutando escalamiento automático para solicitud {solicitud_id}")
            
            # 2. Procesar escalamiento completo (evaluar y clasificar asesores)
            resultado_escalamiento = await EscalamientoService.procesar_escalamiento_completo(solicitud)
            
            if not resultado_escalamiento['success']:
                logger.error(f"❌ Escalamiento falló: {resultado_escalamiento.get('error')}")
                return resultado_escalamiento
            
            # 3. Determinar el nivel inicial (el nivel más bajo con asesores)
            niveles_disponibles = sorted(resultado_escalamiento['niveles_generados'])
            
            if not niveles_disponibles:
                logger.warning(f"⚠️ No hay niveles disponibles para solicitud {solicitud_id}")
                return {
                    'success': False,
                    'error': 'No se generaron niveles de escalamiento'
                }
            
            nivel_inicial = niveles_disponibles[0]  # Empezar por el nivel más bajo (mejor)
            
            logger.info(f"📊 Niveles generados: {niveles_disponibles}, iniciando en Nivel {nivel_inicial}")
            
            # 4. Actualizar nivel de la solicitud
            solicitud.nivel_actual = nivel_inicial
            from utils.datetime_utils import now_utc
            solicitud.fecha_escalamiento = now_utc()
            await solicitud.save()
            
            logger.info(f"✅ Solicitud {solicitud_id} actualizada a Nivel {nivel_inicial}")
            
            # 5. Ejecutar primera oleada (notificar asesores del nivel inicial)
            resultado_oleada = await EscalamientoService.ejecutar_oleada(solicitud, nivel_inicial)
            
            logger.info(f"🎯 Primera oleada: {resultado_oleada.get('asesores_notificados', 0)} asesores notificados en Nivel {nivel_inicial}")
            
            return {
                'success': True,
                'message': 'Escalamiento y primera oleada ejecutados exitosamente',
                'escalamiento': resultado_escalamiento,
                'primera_oleada': resultado_oleada,
                'nivel_actual': nivel_inicial
            }
            
        except Exception as e:
            logger.error(f"❌ Error crítico ejecutando escalamiento con primera oleada: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': f'Error crítico: {str(e)}',
                'solicitud_id': solicitud_id
            }
