"""
Tests for Scheduler Service and Background Jobs
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from services.scheduler_service import SchedulerService
from jobs.scheduled_jobs import procesar_expiracion_ofertas, enviar_notificaciones_expiracion


class TestSchedulerService:
    """Test cases for SchedulerService"""
    
    @pytest.fixture
    async def scheduler_service(self):
        """Create scheduler service instance for testing"""
        service = SchedulerService()
        return service
    
    def test_scheduler_initialization(self, scheduler_service):
        """Test scheduler service initialization"""
        assert scheduler_service.scheduler is None
        assert scheduler_service.redis_client is None
        assert not scheduler_service._is_running
    
    def test_get_job_status_not_initialized(self, scheduler_service):
        """Test job status when scheduler not initialized"""
        status = scheduler_service.get_job_status()
        assert status['status'] == 'not_initialized'
        assert status['jobs'] == []


class TestScheduledJobs:
    """Test cases for scheduled job functions"""
    
    @pytest.mark.asyncio
    async def test_procesar_expiracion_ofertas_success(self):
        """Test successful offer expiration processing"""
        
        # Mock the configuration service
        mock_config = {
            'timeout_ofertas_horas': 20
        }
        
        # Mock the offers service
        mock_result = {
            'success': True,
            'ofertas_expiradas': 3,
            'ofertas_ids': ['id1', 'id2', 'id3'],
            'horas_expiracion': 20,
            'message': '3 ofertas marcadas como expiradas'
        }
        
        with patch('jobs.scheduled_jobs.ConfiguracionService.get_config', return_value=mock_config), \
             patch('jobs.scheduled_jobs.OfertasService.marcar_ofertas_expiradas', return_value=mock_result):
            
            result = await procesar_expiracion_ofertas()
            
            assert result['success'] is True
            assert result['ofertas_procesadas'] == 3
            assert result['timeout_horas'] == 20
            assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_procesar_expiracion_ofertas_custom_timeout(self):
        """Test offer expiration processing with custom timeout"""
        
        mock_result = {
            'success': True,
            'ofertas_expiradas': 1,
            'ofertas_ids': ['id1'],
            'horas_expiracion': 48,
            'message': '1 ofertas marcadas como expiradas'
        }
        
        with patch('jobs.scheduled_jobs.OfertasService.marcar_ofertas_expiradas', return_value=mock_result):
            
            result = await procesar_expiracion_ofertas(timeout_horas=48)
            
            assert result['success'] is True
            assert result['ofertas_procesadas'] == 1
            assert result['timeout_horas'] == 48
    
    @pytest.mark.asyncio
    async def test_procesar_expiracion_ofertas_error(self):
        """Test offer expiration processing with error"""
        
        with patch('jobs.scheduled_jobs.OfertasService.marcar_ofertas_expiradas', side_effect=Exception("Database error")):
            
            result = await procesar_expiracion_ofertas()
            
            assert result['success'] is False
            assert 'error' in result
            assert 'Database error' in result['error']
    
    @pytest.mark.asyncio
    async def test_enviar_notificaciones_expiracion_no_offers(self):
        """Test expiration notifications when no offers need warning"""
        
        mock_config = {
            'timeout_ofertas_horas': 20,
            'notificacion_expiracion_horas_antes': 2
        }
        
        # Mock empty offer list
        with patch('jobs.scheduled_jobs.ConfiguracionService.get_config', return_value=mock_config), \
             patch('models.oferta.Oferta.filter') as mock_filter:
            
            # Mock the filter to return empty async iterator
            mock_filter.return_value.prefetch_related.return_value = []
            
            result = await enviar_notificaciones_expiracion()
            
            assert result['success'] is True
            assert result['notificaciones_enviadas'] == 0
            assert result['advertencia_horas'] == 2


class TestConfigurationIntegration:
    """Test configuration integration with scheduler"""
    
    @pytest.mark.asyncio
    async def test_timeout_configuration_validation(self):
        """Test that timeout configuration is properly validated"""
        
        from services.configuracion_service import ConfiguracionService
        
        # Test valid timeout values
        valid_params = {
            'timeout_ofertas_horas': 24,
            'notificacion_expiracion_horas_antes': 3
        }
        
        # This should not raise an exception
        ConfiguracionService._validar_parametros_generales(valid_params)
    
    def test_invalid_timeout_configuration(self):
        """Test that invalid timeout configuration is rejected"""
        
        from services.configuracion_service import ConfiguracionService
        from fastapi import HTTPException
        
        # Test invalid timeout values
        invalid_params = {
            'timeout_ofertas_horas': 200,  # Too high (max 168)
            'notificacion_expiracion_horas_antes': 15  # Too high (max 12)
        }
        
        with pytest.raises(HTTPException):
            ConfiguracionService._validar_parametros_generales(invalid_params)


class TestJobExecution:
    """Test manual job execution"""
    
    @pytest.mark.asyncio
    async def test_ejecutar_job_manual_valid_job(self):
        """Test manual execution of valid job"""
        
        from jobs.scheduled_jobs import ejecutar_job_manual
        
        with patch('jobs.scheduled_jobs.procesar_expiracion_ofertas') as mock_job:
            mock_job.return_value = {'success': True, 'ofertas_procesadas': 2}
            
            result = await ejecutar_job_manual('procesar_expiracion_ofertas')
            
            assert result['success'] is True
            mock_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ejecutar_job_manual_invalid_job(self):
        """Test manual execution of invalid job"""
        
        from jobs.scheduled_jobs import ejecutar_job_manual
        
        result = await ejecutar_job_manual('invalid_job_name')
        
        assert result['success'] is False
        assert 'Job desconocido' in result['error']


# Integration test fixtures
@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    mock_client = AsyncMock()
    mock_client.exists.return_value = False
    mock_client.setex.return_value = True
    mock_client.publish.return_value = True
    return mock_client


@pytest.fixture
def mock_oferta():
    """Mock Oferta instance for testing"""
    mock_oferta = MagicMock()
    mock_oferta.id = "test-offer-id"
    mock_oferta.codigo_oferta = "OF-TEST123"
    mock_oferta.monto_total = 1500000
    mock_oferta.created_at = datetime.now() - timedelta(hours=18)
    
    # Mock related objects
    mock_oferta.solicitud.id = "test-solicitud-id"
    mock_oferta.solicitud.cliente.usuario.telefono = "+573001234567"
    mock_oferta.solicitud.cliente.usuario.nombre_completo = "Juan Pérez"
    mock_oferta.asesor.usuario.nombre_completo = "María García"
    
    return mock_oferta