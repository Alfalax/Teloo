"""
Tests for Evaluation System - TeLOO V3
Tests de cálculo de puntajes, cobertura mínima, cascada, adjudicación por excepción,
evaluación completa, timeout, concurrencia y expiración de ofertas
"""

import pytest
import pytest_asyncio
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from services.evaluacion_service import EvaluacionService
from services.concurrencia_service import ConcurrenciaService
from services.configuracion_service import ConfiguracionService
from models.oferta import Oferta, OfertaDetalle, AdjudicacionRepuesto, Evaluacion
from models.solicitud import Solicitud, RepuestoSolicitado
from models.user import Usuario, Asesor, Cliente
from models.enums import EstadoSolicitud, EstadoOferta


class TestEvaluacionPuntajes:
    """Tests para cálculo de puntajes de ofertas"""
    
    @pytest_asyncio.fixture
    async def mock_config(self):
        """Mock configuration for evaluation weights"""
        return {
            'precio': 0.50,
            'tiempo_entrega': 0.35,
            'garantia': 0.15
        }
    
    @pytest_asyncio.fixture
    async def sample_repuesto(self):
        """Sample repuesto for testing"""
        repuesto = MagicMock()
        repuesto.id = "rep-123"
        repuesto.nombre = "Filtro de Aceite"
        return repuesto
    
    @pytest_asyncio.fixture
    async def sample_ofertas_data(self):
        """Sample offers data for testing scoring"""
        return [
            {
                'precio': Decimal('50000'),
                'tiempo': 5,
                'garantia': 12,
                'asesor': 'Asesor A'
            },
            {
                'precio': Decimal('45000'),
                'tiempo': 7,
                'garantia': 6,
                'asesor': 'Asesor B'
            },
            {
                'precio': Decimal('55000'),
                'tiempo': 3,
                'garantia': 18,
                'asesor': 'Asesor C'
            }
        ]  
  
    @pytest.mark.asyncio
    @patch('services.evaluacion_service.ConfiguracionService.get_config')
    async def test_calculo_puntajes_ofertas(self, mock_config, sample_repuesto, sample_ofertas_data):
        """Test calculation of offer scores with different price, time and warranty values"""
        
        # Setup mocks
        mock_config.return_value = {
            'precio': 0.50,
            'tiempo_entrega': 0.35,
            'garantia': 0.15
        }
        
        # Create mock offers and details
        mock_ofertas = []
        mock_detalles = []
        
        for i, data in enumerate(sample_ofertas_data):
            # Mock offer
            oferta = MagicMock()
            oferta.id = f"oferta-{i+1}"
            oferta.asesor.usuario.nombre_completo = data['asesor']
            
            # Mock detail with AsyncMock for update_from_dict
            detalle = MagicMock()
            detalle.precio_unitario = data['precio']
            detalle.tiempo_entrega_dias = data['tiempo']
            detalle.garantia_meses = data['garantia']
            detalle.update_from_dict = AsyncMock(return_value=None)
            
            mock_ofertas.append(oferta)
            mock_detalles.append(detalle)
        
        # Mock OfertaDetalle.get_or_none to return details sequentially
        with patch('models.oferta.OfertaDetalle.get_or_none') as mock_get_detalle:
            # Create async side effect function
            async def async_side_effect(*args, **kwargs):
                # Return the next detail in sequence
                if hasattr(async_side_effect, 'call_count'):
                    async_side_effect.call_count += 1
                else:
                    async_side_effect.call_count = 0
                
                if async_side_effect.call_count < len(mock_detalles):
                    return mock_detalles[async_side_effect.call_count]
                return None
            
            mock_get_detalle.side_effect = async_side_effect
            
            # Execute evaluation
            resultado = await EvaluacionService.evaluar_repuesto(sample_repuesto, mock_ofertas)
            
            # Verify result structure
            assert resultado['success'] is True
            assert resultado['repuesto_id'] == "rep-123"
            assert resultado['ofertas_evaluadas'] == 3
            assert 'ganador' in resultado
            assert 'todas_evaluaciones' in resultado
            
            # Verify scoring logic - check that a winner was selected
            ganador = resultado['ganador']
            assert ganador['asesor_nombre'] in ['Asesor A', 'Asesor B', 'Asesor C']
            assert ganador['puntaje_total'] > 0
        
        # Verify all offers were scored
        todas_eval = resultado['todas_evaluaciones']
        assert len(todas_eval) == 3
        
        # Verify scores are normalized (0-1 range)
        for eval_data in todas_eval:
            scores = eval_data['scores']
            assert 0 <= scores['precio'] <= 1
            assert 0 <= scores['tiempo'] <= 1
            assert 0 <= scores['garantia'] <= 1
    
    @pytest.mark.asyncio
    async def test_calculo_puntajes_ofertas_iguales(self, sample_repuesto):
        """Test scoring when all offers have identical values"""
        
        with patch('services.evaluacion_service.ConfiguracionService.get_config') as mock_config:
            mock_config.return_value = {
                'precio': 0.50,
                'tiempo_entrega': 0.35,
                'garantia': 0.15
            }
            
            # Create identical offers
            ofertas_identicas = []
            for i in range(3):
                oferta = MagicMock()
                oferta.id = f"oferta-{i+1}"
                oferta.asesor.usuario.nombre_completo = f"Asesor {i+1}"
                ofertas_identicas.append(oferta)
            
            # Mock identical details
            with patch('models.oferta.OfertaDetalle.get_or_none') as mock_get_detalle:
                mock_detalles = []
                for i in range(3):
                    detalle = MagicMock()
                    detalle.precio_unitario = Decimal('50000')
                    detalle.tiempo_entrega_dias = 5
                    detalle.garantia_meses = 12
                    detalle.update_from_dict = AsyncMock()
                    mock_detalles.append(detalle)
                
                # Create async side effect function
                async def async_side_effect(*args, **kwargs):
                    if hasattr(async_side_effect, 'call_count'):
                        async_side_effect.call_count += 1
                    else:
                        async_side_effect.call_count = 0
                    
                    if async_side_effect.call_count < len(mock_detalles):
                        return mock_detalles[async_side_effect.call_count]
                    return None
                
                mock_get_detalle.side_effect = async_side_effect
                
                resultado = await EvaluacionService.evaluar_repuesto(sample_repuesto, ofertas_identicas)
                
                # All offers should have identical scores (1.0 for each criterion)
                todas_eval = resultado['todas_evaluaciones']
                for eval_data in todas_eval:
                    scores = eval_data['scores']
                    assert scores['precio'] == 1.0
                    assert scores['tiempo'] == 1.0
                    assert scores['garantia'] == 1.0
                    assert eval_data['puntaje_total'] == 1.0  # All weights sum to 1.0
    
    @pytest.mark.asyncio
    async def test_no_ofertas_disponibles(self, sample_repuesto):
        """Test evaluation when no offers are available for a repuesto"""
        
        with patch('services.evaluacion_service.ConfiguracionService.get_config') as mock_config:
            mock_config.return_value = {
                'precio': 0.50,
                'tiempo_entrega': 0.35,
                'garantia': 0.15
            }
            
            with patch('models.oferta.OfertaDetalle.get_or_none', return_value=None):
                resultado = await EvaluacionService.evaluar_repuesto(sample_repuesto, [])
                
                assert resultado['success'] is False
                assert resultado['motivo'] == 'no_ofertas_disponibles'
                assert resultado['ofertas_evaluadas'] == 0
                assert resultado['ganador'] is None


class TestCoberturaMinima:
    """Tests para regla de cobertura mínima"""
    
    @pytest_asyncio.fixture
    async def mock_config_cobertura(self):
        """Mock configuration with minimum coverage"""
        return {
            'cobertura_minima_pct': 50.0
        }
    
    @pytest_asyncio.fixture
    async def sample_solicitud_data(self):
        """Sample solicitud with multiple repuestos"""
        return {
            'total_repuestos': 4,  # 4 repuestos in solicitud
            'repuesto_actual': 'Filtro de Aceite'
        }    

    @patch('services.evaluacion_service.ConfiguracionService.get_config')
    @patch('models.oferta.OfertaDetalle.filter')
    @patch('models.oferta.OfertaDetalle.get_or_none')
    @patch('services.evaluacion_service.EvaluacionService.evaluar_repuesto')
    @pytest.mark.asyncio
    async def test_cobertura_suficiente_gana(self, mock_evaluar, mock_get_detalle, 
                                           mock_filter, mock_config, sample_repuesto, 
                                           mock_config_cobertura, sample_solicitud_data):
        """Test that offer with sufficient coverage wins"""
        
        mock_config.return_value = mock_config_cobertura
        
        # Create offer with good coverage (3/4 = 75% > 50%)
        oferta_buena_cobertura = MagicMock()
        oferta_buena_cobertura.id = "oferta-1"
        oferta_buena_cobertura.asesor.usuario.nombre_completo = "Asesor Cobertura Alta"
        
        detalle = MagicMock()
        detalle.precio_unitario = Decimal('50000')
        detalle.tiempo_entrega_dias = 5
        detalle.garantia_meses = 12
        
        # Mock coverage calculation (3 repuestos covered out of 4)
        mock_filter.return_value.count = AsyncMock(return_value=3)
        mock_get_detalle.return_value = detalle
        
        # Mock detailed evaluation
        mock_evaluar.return_value = {
            'success': True,
            'ganador': {
                'oferta_id': 'oferta-1',
                'asesor_nombre': 'Asesor Cobertura Alta',
                'puntaje_total': 0.85,
                'precio': 50000
            }
        }
        
        resultado = await EvaluacionService.evaluar_repuesto_con_cobertura(
            sample_repuesto, [oferta_buena_cobertura], sample_solicitud_data['total_repuestos']
        )
        
        assert resultado['success'] is True
        assert resultado['motivo'] == 'mejor_puntaje_con_cobertura'
        assert resultado['ganador']['asesor_nombre'] == 'Asesor Cobertura Alta'
        assert resultado['cobertura_aplicada']['cumple_cobertura'] is True
        assert resultado['cobertura_aplicada']['cobertura_obtenida'] == 75.0
    
    @patch('services.evaluacion_service.ConfiguracionService.get_config')
    @patch('models.oferta.OfertaDetalle.filter')
    @patch('models.oferta.OfertaDetalle.get_or_none')
    @pytest.mark.asyncio
    async def test_cobertura_insuficiente_rechaza(self, mock_get_detalle, mock_filter, 
                                                 mock_config, sample_repuesto, 
                                                 mock_config_cobertura, sample_solicitud_data):
        """Test that offer with insufficient coverage is rejected"""
        
        mock_config.return_value = mock_config_cobertura
        
        # Create offer with poor coverage (1/4 = 25% < 50%)
        oferta_mala_cobertura = MagicMock()
        oferta_mala_cobertura.id = "oferta-1"
        oferta_mala_cobertura.asesor.usuario.nombre_completo = "Asesor Cobertura Baja"
        
        detalle = MagicMock()
        mock_get_detalle.return_value = detalle
        
        # Mock coverage calculation (1 repuesto covered out of 4)
        mock_filter.return_value.count = AsyncMock(return_value=1)
        
        resultado = await EvaluacionService.evaluar_repuesto_con_cobertura(
            sample_repuesto, [oferta_mala_cobertura], sample_solicitud_data['total_repuestos']
        )
        
        assert resultado['success'] is False
        assert resultado['motivo'] == 'ninguna_oferta_cumple_cobertura'
        assert resultado['cobertura_aplicada']['cumple_cobertura'] is False
        assert resultado['cobertura_aplicada']['mejor_cobertura_disponible'] == 25.0


class TestCascadaCobertura:
    """Tests para cascada cuando mejor oferta no cumple 50%"""
    
    @patch('services.evaluacion_service.ConfiguracionService.get_config')
    @patch('models.oferta.OfertaDetalle.filter')
    @patch('models.oferta.OfertaDetalle.get_or_none')
    @patch('services.evaluacion_service.EvaluacionService.evaluar_repuesto')
    @pytest.mark.asyncio
    async def test_cascada_encuentra_cobertura_suficiente(self, mock_evaluar, mock_get_detalle, 
                                                        mock_filter, mock_config, sample_repuesto):
        """Test cascade logic finds offer with sufficient coverage after rejecting others"""
        
        mock_config.return_value = {'cobertura_minima_pct': 50.0}
        
        # Create multiple offers with different coverage levels
        ofertas = []
        coberturas = [25, 40, 60]  # Only third one meets 50% minimum
        
        for i, cobertura_pct in enumerate(coberturas):
            oferta = MagicMock()
            oferta.id = f"oferta-{i+1}"
            oferta.asesor.usuario.nombre_completo = f"Asesor {i+1}"
            ofertas.append(oferta)
        
        # Mock details
        mock_get_detalle.side_effect = [MagicMock() for _ in range(3)]
        
        # Mock coverage calculations - return coverage in descending order
        coverage_counts = [1, 2, 3]  # Out of 4 total repuestos
        mock_filter.return_value.count = AsyncMock()
        mock_filter.return_value.count.side_effect = coverage_counts
        
        # Mock detailed evaluation for winning offer
        mock_evaluar.return_value = {
            'success': True,
            'ganador': {
                'oferta_id': 'oferta-3',
                'asesor_nombre': 'Asesor 3',
                'puntaje_total': 0.80
            }
        }
        
        resultado = await EvaluacionService.evaluar_repuesto_con_cobertura(
            sample_repuesto, ofertas, 4
        )
        
        assert resultado['success'] is True
        assert resultado['ganador']['asesor_nombre'] == 'Asesor 3'
        assert resultado['ofertas_descartadas_por_cobertura'] == 2  # First two rejected
        assert resultado['cobertura_aplicada']['cobertura_obtenida'] == 75.0  # 3/4 = 75%


class TestAdjudicacionExcepcion:
    """Tests para adjudicación por excepción (única oferta)"""
    
    @patch('services.evaluacion_service.ConfiguracionService.get_config')
    @patch('models.oferta.OfertaDetalle.filter')
    @patch('models.oferta.OfertaDetalle.get_or_none')
    @patch('services.evaluacion_service.EvaluacionService.evaluar_repuesto')
    @pytest.mark.asyncio
    async def test_unica_oferta_gana_sin_cobertura(self, mock_evaluar, mock_get_detalle, 
                                                  mock_filter, mock_config, sample_repuesto):
        """Test that single offer wins even without meeting coverage requirement"""
        
        mock_config.return_value = {'cobertura_minima_pct': 50.0}
        
        # Single offer with insufficient coverage (1/4 = 25% < 50%)
        oferta_unica = MagicMock()
        oferta_unica.id = "oferta-unica"
        oferta_unica.asesor.usuario.nombre_completo = "Único Asesor"
        
        mock_get_detalle.return_value = MagicMock()
        mock_filter.return_value.count = AsyncMock(return_value=1)  # 1/4 = 25%
        
        # Mock detailed evaluation
        mock_evaluar.return_value = {
            'success': True,
            'ganador': {
                'oferta_id': 'oferta-unica',
                'asesor_nombre': 'Único Asesor',
                'puntaje_total': 0.70
            }
        }
        
        resultado = await EvaluacionService.evaluar_repuesto_con_cobertura(
            sample_repuesto, [oferta_unica], 4
        )
        
        assert resultado['success'] is True
        assert resultado['motivo'] == 'unica_oferta_disponible'
        assert resultado['ganador']['es_adjudicacion_por_excepcion'] is True
        assert resultado['cobertura_aplicada']['cumple_cobertura'] is False
        assert resultado['cobertura_aplicada']['es_unica_oferta'] is True


class TestEvaluacionCompleta:
    """Tests para evaluación completa con múltiples repuestos"""
    
    @pytest_asyncio.fixture
    async def mock_solicitud_completa(self):
        """Mock complete solicitud with multiple repuestos and offers"""
        solicitud = MagicMock()
        solicitud.id = "sol-123"
        solicitud.codigo_solicitud = "SOL-2024-001"
        solicitud.is_evaluable.return_value = True
        
        # Multiple repuestos
        repuestos = []
        for i in range(3):
            repuesto = MagicMock()
            repuesto.id = f"rep-{i+1}"
            repuesto.nombre = f"Repuesto {i+1}"
            repuestos.append(repuesto)
        
        solicitud.repuestos_solicitados = repuestos
        
        # Multiple offers
        ofertas = []
        for i in range(2):
            oferta = MagicMock()
            oferta.id = f"oferta-{i+1}"
            oferta.estado = EstadoOferta.ENVIADA
            oferta.asesor.id = f"asesor-{i+1}"
            oferta.asesor.usuario.nombre_completo = f"Asesor {i+1}"
            ofertas.append(oferta)
        
        solicitud.ofertas = ofertas
        return solicitud
    
    @patch('models.solicitud.Solicitud.get_or_none')
    @patch('services.evaluacion_service.EvaluacionService.evaluar_repuesto_con_cobertura')
    @patch('models.oferta.AdjudicacionRepuesto.create')
    @patch('models.evaluacion.Evaluacion.create')
    @patch('services.evaluacion_service.ConfiguracionService.get_config')
    @pytest.mark.asyncio
    async def test_evaluacion_solicitud_exitosa(self, mock_config, mock_eval_create, 
                                               mock_adj_create, mock_evaluar_repuesto, 
                                               mock_get_solicitud, mock_solicitud_completa):
        """Test successful complete solicitud evaluation"""
        
        # Setup mocks
        mock_get_solicitud.return_value = mock_solicitud_completa
        mock_config.side_effect = [
            {'precio': 0.5, 'tiempo_entrega': 0.35, 'garantia': 0.15},  # evaluation weights
            {'cobertura_minima_pct': 50.0}  # general params
        ]
        
        # Mock successful evaluations for all repuestos
        evaluaciones_exitosas = []
        adjudicaciones_mock = []
        
        for i in range(3):
            evaluacion = {
                'success': True,
                'ganador': {
                    'oferta_id': f'oferta-{(i % 2) + 1}',
                    'detalle_id': f'detalle-{i+1}',
                    'asesor_nombre': f'Asesor {(i % 2) + 1}',
                    'puntaje_total': 0.8 + (i * 0.05),
                    'cobertura_pct': 60.0
                },
                'motivo': 'mejor_puntaje_con_cobertura'
            }
            evaluaciones_exitosas.append(evaluacion)
            
            # Mock adjudication creation
            adj_mock = MagicMock()
            adj_mock.id = f"adj-{i+1}"
            adj_mock.precio_adjudicado = Decimal('50000')
            adj_mock.cantidad_adjudicada = 1
            adj_mock.oferta.asesor.id = f"asesor-{(i % 2) + 1}"
            adj_mock.oferta.asesor.usuario.nombre_completo = f'Asesor {(i % 2) + 1}'
            adj_mock.repuesto_solicitado.nombre = f'Repuesto {i+1}'
            adjudicaciones_mock.append(adj_mock)
        
        mock_evaluar_repuesto.side_effect = evaluaciones_exitosas
        mock_adj_create.side_effect = adjudicaciones_mock
        
        # Mock evaluation record creation
        eval_record = MagicMock()
        eval_record.id = "eval-123"
        mock_eval_create.return_value = eval_record
        
        # Mock offer updates
        for oferta in mock_solicitud_completa.ofertas:
            oferta.update_from_dict = AsyncMock()
        
        # Mock solicitud update
        mock_solicitud_completa.update_from_dict = AsyncMock()
        
        # Execute evaluation
        resultado = await EvaluacionService.evaluar_solicitud("sol-123")
        
        # Verify results
        assert resultado['success'] is True
        assert resultado['repuestos_adjudicados'] == 3
        assert resultado['repuestos_totales'] == 3
        assert resultado['tasa_adjudicacion'] == 100.0
        assert resultado['es_adjudicacion_mixta'] is True  # 2 different asesores
        assert resultado['asesores_ganadores'] == 2
        assert len(resultado['adjudicaciones']) == 3
        
        # Verify adjudications were created
        assert mock_adj_create.call_count == 3
        
        # Verify evaluation record was created
        mock_eval_create.assert_called_once()
    
    @patch('models.solicitud.Solicitud.get_or_none')
    @pytest.mark.asyncio
    async def test_evaluacion_solicitud_sin_ofertas(self, mock_get_solicitud):
        """Test evaluation when solicitud has no active offers"""
        
        solicitud = MagicMock()
        solicitud.id = "sol-123"
        solicitud.codigo_solicitud = "SOL-2024-001"
        solicitud.is_evaluable.return_value = True
        solicitud.ofertas = []  # No offers
        solicitud.update_from_dict = AsyncMock()
        
        mock_get_solicitud.return_value = solicitud
        
        resultado = await EvaluacionService.evaluar_solicitud("sol-123")
        
        assert resultado['success'] is False
        assert resultado['ofertas_evaluadas'] == 0
        assert resultado['repuestos_adjudicados'] == 0
        assert resultado['estado_final'] == EstadoSolicitud.CERRADA_SIN_OFERTAS
    
    @patch('models.solicitud.Solicitud.get_or_none')
    @pytest.mark.asyncio
    async def test_evaluacion_solicitud_no_evaluable(self, mock_get_solicitud):
        """Test evaluation of non-evaluable solicitud"""
        
        solicitud = MagicMock()
        solicitud.id = "sol-123"
        solicitud.is_evaluable.return_value = False
        solicitud.estado = EstadoSolicitud.CERRADA
        
        mock_get_solicitud.return_value = solicitud
        
        with pytest.raises(ValueError, match="no puede ser evaluada"):
            await EvaluacionService.evaluar_solicitud("sol-123")


class TestTimeoutEvaluacion:
    """Tests para timeout de evaluación y manejo de errores"""
    
    @patch('models.solicitud.Solicitud.get_or_none')
    @patch('services.evaluacion_service.ConfiguracionService.get_config')
    @pytest.mark.asyncio
    async def test_timeout_evaluacion(self, mock_config, mock_get_solicitud):
        """Test evaluation timeout handling"""
        
        # Setup solicitud with offers
        solicitud = MagicMock()
        solicitud.id = "sol-123"
        solicitud.codigo_solicitud = "SOL-2024-001"
        
        oferta = MagicMock()
        oferta.estado = EstadoOferta.ENVIADA
        solicitud.ofertas = [oferta]
        
        mock_get_solicitud.return_value = solicitud
        mock_config.return_value = {'timeout_evaluacion_seg': 1}  # 1 second timeout
        
        # Mock a slow evaluation that will timeout
        with patch('services.evaluacion_service.EvaluacionService.evaluar_solicitud') as mock_eval:
            async def slow_evaluation(solicitud_id):
                await asyncio.sleep(2)  # Sleep longer than timeout
                return {'success': True}
            
            mock_eval.side_effect = slow_evaluation
            
            # Mock Redis client
            redis_mock = MagicMock()
            redis_mock.publish = AsyncMock()
            
            resultado = await EvaluacionService.ejecutar_evaluacion_con_timeout(
                "sol-123", timeout_segundos=1, redis_client=redis_mock
            )
            
            assert resultado['success'] is False
            assert resultado['error'] == 'timeout'
            assert resultado['timeout_segundos'] == 1
            
            # Verify timeout event was published
            redis_mock.publish.assert_called_once()
            call_args = redis_mock.publish.call_args
            assert call_args[0][0] == 'evaluacion.timeout'
    
    @patch('models.solicitud.Solicitud.get_or_none')
    @patch('services.evaluacion_service.EvaluacionService.evaluar_solicitud')
    @pytest.mark.asyncio
    async def test_evaluacion_con_timeout_exitosa(self, mock_eval, mock_get_solicitud):
        """Test successful evaluation within timeout"""
        
        # Setup solicitud
        solicitud = MagicMock()
        solicitud.id = "sol-123"
        solicitud.codigo_solicitud = "SOL-2024-001"
        
        oferta = MagicMock()
        oferta.estado = EstadoOferta.ENVIADA
        solicitud.ofertas = [oferta]
        
        mock_get_solicitud.return_value = solicitud
        
        # Mock successful evaluation
        mock_eval.return_value = {
            'success': True,
            'evaluacion_id': 'eval-123',
            'ofertas_evaluadas': 1,
            'repuestos_adjudicados': 1,
            'repuestos_totales': 1,
            'monto_total_adjudicado': 50000,
            'tiempo_evaluacion_ms': 500,
            'es_adjudicacion_mixta': False,
            'asesores_ganadores': 1,
            'estado_final': EstadoSolicitud.EVALUADA,
            'adjudicaciones': []
        }
        
        # Mock Redis client
        redis_mock = MagicMock()
        redis_mock.publish = AsyncMock()
        
        resultado = await EvaluacionService.ejecutar_evaluacion_con_timeout(
            "sol-123", timeout_segundos=5, redis_client=redis_mock
        )
        
        assert resultado['success'] is True
        assert resultado['evaluacion_id'] == 'eval-123'
        
        # Verify success event was published
        redis_mock.publish.assert_called_once()
        call_args = redis_mock.publish.call_args
        assert call_args[0][0] == 'evaluacion.completed'


class TestValidacionesConcurrencia:
    """Tests para validaciones de concurrencia"""
    
    @patch('services.concurrencia_service.ConcurrenciaService.is_evaluacion_en_progreso')
    @pytest.mark.asyncio
    async def test_validacion_oferta_evaluacion_en_progreso(self, mock_is_evaluacion):
        """Test offer validation when evaluation is in progress"""
        
        mock_is_evaluacion.return_value = True
        
        with pytest.raises(ValueError, match="evaluación en progreso"):
            await ConcurrenciaService.validar_oferta_concurrencia("sol-123")
    
    @patch('services.concurrencia_service.ConcurrenciaService.is_evaluacion_en_progreso')
    @pytest.mark.asyncio
    async def test_validacion_oferta_sin_evaluacion(self, mock_is_evaluacion):
        """Test offer validation when no evaluation is in progress"""
        
        mock_is_evaluacion.return_value = False
        
        resultado = await ConcurrenciaService.validar_oferta_concurrencia("sol-123")
        
        assert resultado['valid'] is True
        assert resultado['evaluacion_en_progreso'] is False
    
    @pytest.mark.asyncio
    async def test_lock_evaluacion_adquisicion_exitosa(self):
        """Test successful evaluation lock acquisition"""
        
        # Mock Redis client
        redis_mock = MagicMock()
        redis_mock.set = AsyncMock(return_value=True)  # Lock acquired
        redis_mock.eval = AsyncMock(return_value=1)  # Lock released
        
        async with ConcurrenciaService.lock_evaluacion("sol-123", redis_mock) as token:
            assert token is not None
            assert len(token) > 0
        
        # Verify lock was acquired and released
        redis_mock.set.assert_called_once()
        redis_mock.eval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lock_evaluacion_fallo_adquisicion(self):
        """Test failed evaluation lock acquisition"""
        
        # Mock Redis client that always fails to acquire lock
        redis_mock = MagicMock()
        redis_mock.set = AsyncMock(return_value=False)  # Lock not acquired
        
        with patch('services.concurrencia_service.ConcurrenciaService.LOCK_MAX_RETRIES', 2):
            with patch('services.concurrencia_service.ConcurrenciaService.LOCK_RETRY_DELAY', 0.01):
                with pytest.raises(RuntimeError, match="No se pudo adquirir lock"):
                    async with ConcurrenciaService.lock_evaluacion("sol-123", redis_mock):
                        pass
    
    @pytest.mark.asyncio
    async def test_get_lock_info_existente(self):
        """Test getting information about existing lock"""
        
        redis_mock = MagicMock()
        redis_mock.get = AsyncMock(return_value="token-12345678")
        redis_mock.ttl = AsyncMock(return_value=300)  # 5 minutes remaining
        
        info = await ConcurrenciaService.get_lock_info("sol-123", redis_mock)
        
        assert info is not None
        assert info['solicitud_id'] == "sol-123"
        assert info['ttl_seconds'] == 300
        assert info['is_active'] is True
    
    @pytest.mark.asyncio
    async def test_force_release_lock(self):
        """Test force release of evaluation lock"""
        
        redis_mock = MagicMock()
        redis_mock.get = AsyncMock(return_value="token-12345678")
        redis_mock.ttl = AsyncMock(return_value=300)
        redis_mock.delete = AsyncMock(return_value=1)  # Lock deleted
        
        with patch('services.concurrencia_service.ConcurrenciaService.get_lock_info') as mock_info:
            mock_info.return_value = {'lock_token': 'token-123...'}
            
            resultado = await ConcurrenciaService.force_release_lock(
                "sol-123", redis_mock, "admin_override"
            )
            
            assert resultado['success'] is True
            assert resultado['reason'] == "admin_override"


class TestExpiracionOfertas:
    """Tests para expiración de ofertas"""
    
    @pytest_asyncio.fixture
    async def ofertas_mock_data(self):
        """Mock offers data for expiration testing"""
        ofertas = []
        
        # Offer that should expire (created 21 hours ago)
        oferta_expirar = MagicMock()
        oferta_expirar.id = "oferta-1"
        oferta_expirar.codigo_oferta = "OF-001"
        oferta_expirar.estado = EstadoOferta.ENVIADA
        oferta_expirar.created_at = datetime.now() - timedelta(hours=21)
        oferta_expirar.solicitud.id = "sol-1"
        oferta_expirar.asesor.id = "asesor-1"
        oferta_expirar.asesor.usuario.nombre_completo = "Asesor 1"
        oferta_expirar.monto_total = Decimal('100000')
        oferta_expirar.update_from_dict = AsyncMock()
        ofertas.append(oferta_expirar)
        
        # Offer that should NOT expire (created 10 hours ago)
        oferta_vigente = MagicMock()
        oferta_vigente.id = "oferta-2"
        oferta_vigente.estado = EstadoOferta.ENVIADA
        oferta_vigente.created_at = datetime.now() - timedelta(hours=10)
        ofertas.append(oferta_vigente)
        
        return ofertas
    
    @patch('models.oferta.Oferta.filter')
    @pytest.mark.asyncio
    async def test_procesar_expiracion_ofertas(self, mock_filter, ofertas_mock_data):
        """Test processing of offer expiration"""
        
        # Mock filter to return offers to expire
        mock_filter.return_value.prefetch_related.return_value = [ofertas_mock_data[0]]
        
        # Mock Redis client
        redis_mock = MagicMock()
        redis_mock.publish = AsyncMock()
        
        resultado = await EvaluacionService.procesar_expiracion_ofertas(
            horas_expiracion=20, redis_client=redis_mock
        )
        
        assert resultado['success'] is True
        assert resultado['ofertas_expiradas'] == 1
        assert resultado['horas_expiracion'] == 20
        
        # Verify offer was updated to EXPIRADA
        ofertas_mock_data[0].update_from_dict.assert_called_once()
        update_args = ofertas_mock_data[0].update_from_dict.call_args[0][0]
        assert update_args['estado'] == EstadoOferta.EXPIRADA
        
        # Verify expiration event was published
        redis_mock.publish.assert_called_once()
    
    @patch('models.oferta.Oferta.filter')
    @pytest.mark.asyncio
    async def test_notificar_expiracion_proxima(self, mock_filter, ofertas_mock_data):
        """Test notification of upcoming offer expiration"""
        
        # Create offer that will expire in 1.5 hours
        oferta_proxima = MagicMock()
        oferta_proxima.id = "oferta-proxima"
        oferta_proxima.estado = EstadoOferta.ENVIADA
        oferta_proxima.created_at = datetime.now() - timedelta(hours=18.5)  # 1.5 hours to expire
        oferta_proxima.solicitud.cliente.id = "cliente-1"
        oferta_proxima.solicitud.cliente.usuario.telefono = "+573001234567"
        oferta_proxima.monto_total = Decimal('75000')
        oferta_proxima.cantidad_repuestos = 2
        
        mock_filter.return_value.prefetch_related.return_value = [oferta_proxima]
        
        # Mock Redis client
        redis_mock = MagicMock()
        redis_mock.publish = AsyncMock()
        
        resultado = await EvaluacionService.notificar_expiracion_proxima(
            horas_antes_expiracion=2, horas_expiracion_total=20, redis_client=redis_mock
        )
        
        assert resultado['success'] is True
        assert resultado['notificaciones_enviadas'] == 1
        
        # Verify notification event was published
        redis_mock.publish.assert_called_once()
        call_args = redis_mock.publish.call_args
        assert call_args[0][0] == 'oferta.expiration_warning'
    
    @patch('models.oferta.Oferta.filter')
    @patch('services.evaluacion_service.ConfiguracionService.get_config')
    @pytest.mark.asyncio
    async def test_get_ofertas_proximas_a_expirar(self, mock_config, mock_filter):
        """Test getting offers that will expire soon"""
        
        mock_config.return_value = {'timeout_ofertas_horas': 20}
        
        # Create offer expiring in 2 hours
        oferta_proxima = MagicMock()
        oferta_proxima.id = "oferta-1"
        oferta_proxima.codigo_oferta = "OF-001"
        oferta_proxima.created_at = datetime.now() - timedelta(hours=18)  # 2 hours to expire
        oferta_proxima.solicitud.id = "sol-1"
        oferta_proxima.solicitud.cliente.usuario.telefono = "+573001234567"
        oferta_proxima.asesor.usuario.nombre_completo = "Asesor Test"
        oferta_proxima.monto_total = Decimal('50000')
        oferta_proxima.cantidad_repuestos = 1
        
        mock_filter.return_value.prefetch_related.return_value = [oferta_proxima]
        
        ofertas_proximas = await EvaluacionService.get_ofertas_proximas_a_expirar(horas_limite=4)
        
        assert len(ofertas_proximas) == 1
        assert ofertas_proximas[0]['oferta_id'] == "oferta-1"
        assert ofertas_proximas[0]['horas_restantes'] == 2.0
        assert ofertas_proximas[0]['es_critica'] is False  # > 1 hour remaining
    
    @patch('models.oferta.Oferta.filter')
    @patch('services.evaluacion_service.ConfiguracionService.get_config')
    @pytest.mark.asyncio
    async def test_get_ofertas_criticas_expiracion(self, mock_config, mock_filter):
        """Test getting offers in critical expiration state (< 1 hour)"""
        
        mock_config.return_value = {'timeout_ofertas_horas': 20}
        
        # Create offer expiring in 30 minutes
        oferta_critica = MagicMock()
        oferta_critica.id = "oferta-critica"
        oferta_critica.codigo_oferta = "OF-CRITICA"
        oferta_critica.created_at = datetime.now() - timedelta(hours=19.5)  # 30 minutes to expire
        oferta_critica.solicitud.id = "sol-1"
        oferta_critica.solicitud.cliente.usuario.telefono = "+573001234567"
        oferta_critica.asesor.usuario.nombre_completo = "Asesor Crítico"
        oferta_critica.monto_total = Decimal('25000')
        oferta_critica.cantidad_repuestos = 1
        
        mock_filter.return_value.prefetch_related.return_value = [oferta_critica]
        
        ofertas_proximas = await EvaluacionService.get_ofertas_proximas_a_expirar(horas_limite=2)
        
        assert len(ofertas_proximas) == 1
        assert ofertas_proximas[0]['horas_restantes'] == 0.5
        assert ofertas_proximas[0]['minutos_restantes'] == 30
        assert ofertas_proximas[0]['es_critica'] is True  # < 1 hour remaining


# Integration test combining multiple scenarios
class TestEvaluacionIntegracion:
    """Integration tests combining multiple evaluation scenarios"""
    
    @patch('models.solicitud.Solicitud.get_or_none')
    @patch('services.evaluacion_service.EvaluacionService.evaluar_repuesto_con_cobertura')
    @patch('models.oferta.AdjudicacionRepuesto.create')
    @patch('models.evaluacion.Evaluacion.create')
    @patch('services.evaluacion_service.ConfiguracionService.get_config')
    @pytest.mark.asyncio
    async def test_evaluacion_mixta_con_excepcion(self, mock_config, mock_eval_create, 
                                                 mock_adj_create, mock_evaluar_repuesto, 
                                                 mock_get_solicitud):
        """Test mixed adjudication with exception case (unique offer)"""
        
        # Setup complex solicitud
        solicitud = MagicMock()
        solicitud.id = "sol-mixta"
        solicitud.codigo_solicitud = "SOL-MIXTA-001"
        solicitud.is_evaluable.return_value = True
        
        # 3 repuestos
        repuestos = [MagicMock() for _ in range(3)]
        for i, rep in enumerate(repuestos):
            rep.id = f"rep-{i+1}"
            rep.nombre = f"Repuesto {i+1}"
        solicitud.repuestos_solicitados = repuestos
        
        # 2 offers
        ofertas = [MagicMock() for _ in range(2)]
        for i, oferta in enumerate(ofertas):
            oferta.id = f"oferta-{i+1}"
            oferta.estado = EstadoOferta.ENVIADA
            oferta.asesor.id = f"asesor-{i+1}"
            oferta.asesor.usuario.nombre_completo = f"Asesor {i+1}"
            oferta.update_from_dict = AsyncMock()
        solicitud.ofertas = ofertas
        
        mock_get_solicitud.return_value = solicitud
        mock_config.side_effect = [
            {'precio': 0.5, 'tiempo_entrega': 0.35, 'garantia': 0.15},
            {'cobertura_minima_pct': 50.0}
        ]
        
        # Mock evaluations: 2 normal wins, 1 exception case
        evaluaciones = [
            {  # Repuesto 1: Asesor 1 wins with good coverage
                'success': True,
                'ganador': {
                    'oferta_id': 'oferta-1', 'detalle_id': 'det-1',
                    'asesor_nombre': 'Asesor 1', 'puntaje_total': 0.85,
                    'cobertura_pct': 75.0, 'es_adjudicacion_por_excepcion': False
                },
                'motivo': 'mejor_puntaje_con_cobertura'
            },
            {  # Repuesto 2: Asesor 2 wins with good coverage
                'success': True,
                'ganador': {
                    'oferta_id': 'oferta-2', 'detalle_id': 'det-2',
                    'asesor_nombre': 'Asesor 2', 'puntaje_total': 0.80,
                    'cobertura_pct': 60.0, 'es_adjudicacion_por_excepcion': False
                },
                'motivo': 'mejor_puntaje_con_cobertura'
            },
            {  # Repuesto 3: Asesor 1 wins by exception (unique offer)
                'success': True,
                'ganador': {
                    'oferta_id': 'oferta-1', 'detalle_id': 'det-3',
                    'asesor_nombre': 'Asesor 1', 'puntaje_total': 0.70,
                    'cobertura_pct': 25.0, 'es_adjudicacion_por_excepcion': True
                },
                'motivo': 'unica_oferta_disponible'
            }
        ]
        
        mock_evaluar_repuesto.side_effect = evaluaciones
        
        # Mock adjudication creation
        adjudicaciones = []
        for i in range(3):
            adj = MagicMock()
            adj.id = f"adj-{i+1}"
            adj.precio_adjudicado = Decimal('50000')
            adj.cantidad_adjudicada = 1
            adj.oferta.asesor.id = f"asesor-{(i % 2) + 1}"
            adj.oferta.asesor.usuario.nombre_completo = f"Asesor {(i % 2) + 1}"
            adj.repuesto_solicitado.nombre = f"Repuesto {i+1}"
            adjudicaciones.append(adj)
        
        mock_adj_create.side_effect = adjudicaciones
        
        # Mock evaluation record
        eval_record = MagicMock()
        eval_record.id = "eval-mixta"
        mock_eval_create.return_value = eval_record
        
        # Mock solicitud update
        solicitud.update_from_dict = AsyncMock()
        
        # Execute evaluation
        resultado = await EvaluacionService.evaluar_solicitud("sol-mixta")
        
        # Verify mixed adjudication results
        assert resultado['success'] is True
        assert resultado['repuestos_adjudicados'] == 3
        assert resultado['es_adjudicacion_mixta'] is True
        assert resultado['asesores_ganadores'] == 2
        
        # Verify adjudications include both normal and exception cases
        adjudicaciones_resultado = resultado['adjudicaciones']
        motivos = [adj['motivo'] for adj in adjudicaciones_resultado]
        assert 'mejor_puntaje_con_cobertura' in motivos
        assert 'unica_oferta_disponible' in motivos


if __name__ == "__main__":
    pytest.main([__file__])