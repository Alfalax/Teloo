"""
Tests for Error Handler Service
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from services.error_handler_service import (
    ErrorHandlerService,
    timeout_handler,
    fallback_on_error,
    TimeoutError,
    FallbackError
)


class TestErrorHandlerService:
    """Test cases for ErrorHandlerService"""
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_success(self):
        """Test successful execution within timeout"""
        
        async def mock_function(value):
            await asyncio.sleep(0.1)  # Short delay
            return {"result": value}
        
        result = await ErrorHandlerService.execute_with_timeout(
            mock_function,
            1,
            "test_operation",
            "test_value"
        )
        
        assert result['success'] is True
        assert result['result']['result'] == "test_value"
        assert result['operation'] == "test_operation"
        assert result['duration_seconds'] < 1.0
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_timeout(self):
        """Test timeout handling"""
        
        async def slow_function():
            await asyncio.sleep(2)  # Longer than timeout
            return {"result": "should_not_reach"}
        
        result = await ErrorHandlerService.execute_with_timeout(
            slow_function,
            0.5,
            "slow_operation"
        )
        
        assert result['success'] is False
        assert result['error'] == 'timeout'
        assert result['timeout_seconds'] == 0.5
        assert result['operation'] == "slow_operation"
        assert 'timed out' in result['error_message']
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_exception(self):
        """Test exception handling"""
        
        async def failing_function():
            raise ValueError("Test error")
        
        result = await ErrorHandlerService.execute_with_timeout(
            failing_function,
            1,
            "failing_operation"
        )
        
        assert result['success'] is False
        assert result['error'] == 'execution_error'
        assert result['exception_type'] == 'ValueError'
        assert 'Test error' in result['error_message']
    
    @pytest.mark.asyncio
    async def test_handle_geographic_fallback(self):
        """Test geographic fallback handling"""
        
        with patch.object(ErrorHandlerService, '_log_geographic_issue', new_callable=AsyncMock):
            result = await ErrorHandlerService.handle_geographic_fallback("Ciudad_Inexistente")
            
            assert result['proximidad'] == Decimal('3.0')
            assert result['criterio'] == 'sin_cobertura_geografica'
            assert result['ciudad_problema'] == "Ciudad_Inexistente"
            assert 'timestamp' in result
            assert 'accion_requerida' in result
    
    @pytest.mark.asyncio
    async def test_handle_missing_metrics_fallback(self):
        """Test missing metrics fallback handling"""
        
        missing_metrics = ['actividad_reciente', 'desempeno_historico']
        
        with patch.object(ErrorHandlerService, '_log_missing_metrics', new_callable=AsyncMock):
            result = await ErrorHandlerService.handle_missing_metrics_fallback(
                "asesor_123",
                missing_metrics
            )
            
            assert result['actividad_reciente'] == Decimal('1.0')
            assert result['desempeno_historico'] == Decimal('1.0')
            assert 'nivel_confianza' not in result  # Not in missing list
    
    @pytest.mark.asyncio
    async def test_handle_evaluation_timeout(self):
        """Test evaluation timeout handling"""
        
        with patch('services.error_handler_service.Solicitud') as mock_solicitud_class:
            mock_solicitud = AsyncMock()
            mock_solicitud_class.get_or_none.return_value = mock_solicitud
            mock_solicitud.update_from_dict = AsyncMock()
            
            with patch.object(ErrorHandlerService, '_log_evaluation_timeout', new_callable=AsyncMock):
                result = await ErrorHandlerService.handle_evaluation_timeout(
                    "solicitud_123",
                    5,
                    3
                )
                
                assert result['solicitud_id'] == "solicitud_123"
                assert result['timeout_seconds'] == 5
                assert result['ofertas_count'] == 3
                assert 'timestamp' in result
                assert result['action_taken'] == 'solicitud_marked_as_closed'
                
                # Verify solicitud was updated
                mock_solicitud.update_from_dict.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_circuit_breaker_fallback(self):
        """Test circuit breaker fallback handling"""
        
        with patch.object(ErrorHandlerService, '_log_circuit_breaker_event', new_callable=AsyncMock):
            result = await ErrorHandlerService.handle_circuit_breaker_fallback(
                "whatsapp_api",
                "send_message",
                {"fallback": "message_queued"}
            )
            
            assert result['service_name'] == "whatsapp_api"
            assert result['operation'] == "send_message"
            assert result['fallback_applied'] is True
            assert result['fallback_result']['fallback'] == "message_queued"
            assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_validate_configuration_parameters_valid(self):
        """Test configuration validation with valid parameters"""
        
        mock_configs = {
            'pesos_escalamiento': {
                'proximidad': 0.40,
                'actividad': 0.25,
                'desempeno': 0.20,
                'confianza': 0.15
            },
            'umbrales_niveles': {
                'nivel1_min': 4.5,
                'nivel2_min': 4.0,
                'nivel3_min': 3.5,
                'nivel4_min': 3.0
            },
            'tiempos_espera_niveles': {
                'nivel1': 15,
                'nivel2': 20,
                'nivel3': 25,
                'nivel4': 30
            },
            'parametros_generales': {
                'timeout_evaluacion_seg': 5,
                'cobertura_minima_pct': 50
            }
        }
        
        with patch('services.error_handler_service.ConfiguracionService') as mock_config:
            mock_config.get_config.side_effect = lambda key: mock_configs[key]
            
            result = await ErrorHandlerService.validate_configuration_parameters()
            
            assert result['valid'] is True
            assert len(result['errors']) == 0
            assert len(result['warnings']) == 0
            assert len(result['configurations_checked']) == 4
    
    @pytest.mark.asyncio
    async def test_validate_configuration_parameters_invalid_weights(self):
        """Test configuration validation with invalid weights"""
        
        mock_configs = {
            'pesos_escalamiento': {
                'proximidad': 0.50,  # Sum = 1.10 (invalid)
                'actividad': 0.25,
                'desempeno': 0.20,
                'confianza': 0.15
            },
            'umbrales_niveles': {
                'nivel1_min': 4.5,
                'nivel2_min': 4.0,
                'nivel3_min': 3.5,
                'nivel4_min': 3.0
            },
            'tiempos_espera_niveles': {
                'nivel1': 15,
                'nivel2': 20,
                'nivel3': 25,
                'nivel4': 30
            },
            'parametros_generales': {
                'timeout_evaluacion_seg': 5,
                'cobertura_minima_pct': 50
            }
        }
        
        with patch('services.error_handler_service.ConfiguracionService') as mock_config:
            mock_config.get_config.side_effect = lambda key: mock_configs[key]
            
            result = await ErrorHandlerService.validate_configuration_parameters()
            
            assert result['valid'] is False
            assert len(result['errors']) == 1
            assert 'no suman 1.0' in result['errors'][0]
    
    @pytest.mark.asyncio
    async def test_validate_configuration_parameters_invalid_thresholds(self):
        """Test configuration validation with invalid thresholds"""
        
        mock_configs = {
            'pesos_escalamiento': {
                'proximidad': 0.40,
                'actividad': 0.25,
                'desempeno': 0.20,
                'confianza': 0.15
            },
            'umbrales_niveles': {
                'nivel1_min': 4.0,  # Should be > nivel2_min
                'nivel2_min': 4.5,  # Invalid order
                'nivel3_min': 3.5,
                'nivel4_min': 3.0
            },
            'tiempos_espera_niveles': {
                'nivel1': 15,
                'nivel2': 20,
                'nivel3': 25,
                'nivel4': 30
            },
            'parametros_generales': {
                'timeout_evaluacion_seg': 5,
                'cobertura_minima_pct': 50
            }
        }
        
        with patch('services.error_handler_service.ConfiguracionService') as mock_config:
            mock_config.get_config.side_effect = lambda key: mock_configs[key]
            
            result = await ErrorHandlerService.validate_configuration_parameters()
            
            assert result['valid'] is False
            assert len(result['errors']) == 1
            assert 'no son decrecientes' in result['errors'][0]


class TestDecorators:
    """Test cases for error handling decorators"""
    
    @pytest.mark.asyncio
    async def test_timeout_handler_decorator_success(self):
        """Test timeout handler decorator with successful execution"""
        
        @timeout_handler(1, "test_op")
        async def test_function(value):
            await asyncio.sleep(0.1)
            return {"data": value}
        
        result = await test_function("test_data")
        
        assert result['success'] is True
        assert result['result']['data'] == "test_data"
        assert result['operation'] == "test_op"
    
    @pytest.mark.asyncio
    async def test_timeout_handler_decorator_timeout(self):
        """Test timeout handler decorator with timeout"""
        
        @timeout_handler(0.2, "slow_op")
        async def slow_function():
            await asyncio.sleep(1)
            return {"data": "should_not_reach"}
        
        result = await slow_function()
        
        assert result['success'] is False
        assert result['error'] == 'timeout'
        assert result['operation'] == "slow_op"
    
    @pytest.mark.asyncio
    async def test_fallback_on_error_decorator_success(self):
        """Test fallback decorator with successful execution"""
        
        @fallback_on_error("fallback_result")
        async def test_function(value):
            return f"success_{value}"
        
        result = await test_function("test")
        assert result == "success_test"
    
    @pytest.mark.asyncio
    async def test_fallback_on_error_decorator_fallback(self):
        """Test fallback decorator with error"""
        
        @fallback_on_error("fallback_result", False)
        async def failing_function():
            raise ValueError("Test error")
        
        result = await failing_function()
        assert result == "fallback_result"


class TestLoggingMethods:
    """Test cases for logging methods"""
    
    @pytest.mark.asyncio
    async def test_log_geographic_issue(self):
        """Test geographic issue logging"""
        
        fallback_data = {
            'proximidad': Decimal('3.0'),
            'criterio': 'sin_cobertura_geografica',
            'ciudad_problema': 'TestCity'
        }
        
        with patch('services.error_handler_service.logger') as mock_logger:
            await ErrorHandlerService._log_geographic_issue("TestCity", fallback_data)
            
            # Verify logger was called
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert 'GEOGRAPHIC_ISSUE' in call_args
            assert 'TestCity' in call_args
    
    @pytest.mark.asyncio
    async def test_log_missing_metrics(self):
        """Test missing metrics logging"""
        
        missing_metrics = ['actividad_reciente', 'desempeno_historico']
        applied_fallbacks = {
            'actividad_reciente': Decimal('1.0'),
            'desempeno_historico': Decimal('1.0')
        }
        
        with patch('services.error_handler_service.logger') as mock_logger:
            await ErrorHandlerService._log_missing_metrics(
                "asesor_123",
                missing_metrics,
                applied_fallbacks
            )
            
            # Verify logger was called
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert 'MISSING_METRICS' in call_args
            assert 'asesor_123' in call_args
    
    @pytest.mark.asyncio
    async def test_log_evaluation_timeout(self):
        """Test evaluation timeout logging"""
        
        timeout_data = {
            'solicitud_id': 'sol_123',
            'timeout_seconds': 5,
            'ofertas_count': 3
        }
        
        with patch('services.error_handler_service.logger') as mock_logger:
            await ErrorHandlerService._log_evaluation_timeout(timeout_data)
            
            # Verify logger was called
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert 'EVALUATION_TIMEOUT' in call_args
            assert 'sol_123' in call_args
    
    @pytest.mark.asyncio
    async def test_log_circuit_breaker_event(self):
        """Test circuit breaker event logging"""
        
        fallback_data = {
            'service_name': 'whatsapp_api',
            'operation': 'send_message',
            'fallback_applied': True
        }
        
        with patch('services.error_handler_service.logger') as mock_logger:
            await ErrorHandlerService._log_circuit_breaker_event(fallback_data)
            
            # Verify logger was called
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert 'CIRCUIT_BREAKER' in call_args
            assert 'whatsapp_api' in call_args