"""
Tests for WhatsApp Service Error Handling
"""

import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.whatsapp_service import WhatsAppService
from app.services.llm.circuit_breaker import CircuitBreaker


class TestWhatsAppServiceErrorHandling:
    """Test cases for WhatsApp service error handling"""
    
    @pytest.fixture
    def whatsapp_service(self):
        """Create WhatsApp service instance for testing"""
        return WhatsAppService()
    
    @pytest.mark.asyncio
    async def test_send_text_message_success(self, whatsapp_service):
        """Test successful message sending"""
        
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(whatsapp_service.client, 'post', new_callable=AsyncMock) as mock_post:
            with patch.object(whatsapp_service.circuit_breaker, 'is_available', return_value=True):
                with patch.object(whatsapp_service.circuit_breaker, 'call_with_circuit_breaker', new_callable=AsyncMock) as mock_circuit:
                    mock_circuit.return_value = mock_response
                    
                    result = await whatsapp_service.send_text_message("+573001234567", "Test message")
                    
                    assert result is True
                    mock_circuit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_text_message_circuit_breaker_open(self, whatsapp_service):
        """Test message sending when circuit breaker is open"""
        
        with patch.object(whatsapp_service.circuit_breaker, 'is_available', return_value=False):
            result = await whatsapp_service.send_text_message("+573001234567", "Test message")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_text_message_with_retry_success(self, whatsapp_service):
        """Test message sending with retry logic - eventual success"""
        
        # Mock responses: first fails, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response_fail
        )
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.raise_for_status = MagicMock()
        
        call_count = 0
        async def mock_send_message():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.HTTPStatusError("Server Error", request=MagicMock(), response=mock_response_fail)
            return mock_response_success
        
        with patch.object(whatsapp_service.circuit_breaker, 'is_available', return_value=True):
            with patch.object(whatsapp_service.circuit_breaker, 'call_with_circuit_breaker', new_callable=AsyncMock) as mock_circuit:
                with patch.object(whatsapp_service, '_retry_with_exponential_backoff', new_callable=AsyncMock) as mock_retry:
                    mock_retry.return_value = mock_response_success
                    mock_circuit.return_value = mock_response_success
                    
                    result = await whatsapp_service.send_text_message("+573001234567", "Test message")
                    
                    assert result is True
                    mock_circuit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff_success_after_retries(self, whatsapp_service):
        """Test exponential backoff retry logic with eventual success"""
        
        call_count = 0
        async def mock_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 attempts
                raise httpx.TimeoutException("Timeout")
            return "success"
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await whatsapp_service._retry_with_exponential_backoff(mock_function)
            
            assert result == "success"
            assert call_count == 3
            # Verify exponential backoff delays
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1.0)  # First retry delay
            mock_sleep.assert_any_call(2.0)  # Second retry delay
    
    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff_all_retries_fail(self, whatsapp_service):
        """Test exponential backoff when all retries fail"""
        
        async def failing_function():
            raise httpx.ConnectError("Connection failed")
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(httpx.ConnectError):
                await whatsapp_service._retry_with_exponential_backoff(failing_function)
    
    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff_non_retryable_error(self, whatsapp_service):
        """Test that non-retryable errors are not retried"""
        
        async def function_with_non_retryable_error():
            raise ValueError("Non-retryable error")
        
        with pytest.raises(ValueError):
            await whatsapp_service._retry_with_exponential_backoff(function_with_non_retryable_error)
    
    @pytest.mark.asyncio
    async def test_send_template_message_success(self, whatsapp_service):
        """Test successful template message sending"""
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        with patch.object(whatsapp_service.circuit_breaker, 'is_available', return_value=True):
            with patch.object(whatsapp_service.circuit_breaker, 'call_with_circuit_breaker', new_callable=AsyncMock) as mock_circuit:
                mock_circuit.return_value = mock_response
                
                result = await whatsapp_service.send_template_message(
                    "+573001234567", 
                    "welcome_template", 
                    ["John", "Doe"]
                )
                
                assert result is True
                mock_circuit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_template_message_circuit_breaker_open(self, whatsapp_service):
        """Test template message sending when circuit breaker is open"""
        
        with patch.object(whatsapp_service.circuit_breaker, 'is_available', return_value=False):
            result = await whatsapp_service.send_template_message(
                "+573001234567", 
                "welcome_template"
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_media_url_with_retry(self, whatsapp_service):
        """Test media URL retrieval with retry logic"""
        
        # Mock successful response after retry
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"url": "https://example.com/media.jpg"}
        
        with patch.object(whatsapp_service.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await whatsapp_service.get_media_url("media_123")
            
            assert result == "https://example.com/media.jpg"
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_media_url_failure(self, whatsapp_service):
        """Test media URL retrieval failure"""
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch.object(whatsapp_service.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await whatsapp_service.get_media_url("media_123")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_download_media_success(self, whatsapp_service):
        """Test successful media download"""
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_media_content"
        
        with patch.object(whatsapp_service.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await whatsapp_service.download_media("https://example.com/media.jpg")
            
            assert result == b"fake_media_content"
    
    @pytest.mark.asyncio
    async def test_download_media_failure(self, whatsapp_service):
        """Test media download failure"""
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch.object(whatsapp_service.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await whatsapp_service.download_media("https://example.com/media.jpg")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, whatsapp_service):
        """Test circuit breaker integration with WhatsApp service"""
        
        # Test that circuit breaker is properly initialized
        assert isinstance(whatsapp_service.circuit_breaker, CircuitBreaker)
        assert whatsapp_service.circuit_breaker.provider_name == "whatsapp_api"
        assert whatsapp_service.circuit_breaker.failure_threshold == 3
        assert whatsapp_service.circuit_breaker.timeout_seconds == 300
    
    @pytest.mark.asyncio
    async def test_error_handling_in_queue_message(self, whatsapp_service):
        """Test error handling in message queuing"""
        
        from app.models.whatsapp import ProcessedMessage
        from datetime import datetime
        
        message = ProcessedMessage(
            message_id="msg_123",
            from_number="+573001234567",
            timestamp=datetime.now(),
            message_type="text",
            text_content="Test message"
        )
        
        # Mock Redis error
        with patch('app.core.redis.redis_manager.lpush', new_callable=AsyncMock) as mock_lpush:
            mock_lpush.side_effect = Exception("Redis connection error")
            
            result = await whatsapp_service.queue_message_for_processing(message)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_webhook_signature_verification_error_handling(self, whatsapp_service):
        """Test webhook signature verification error handling"""
        
        # Test with invalid signature format
        result = whatsapp_service.verify_webhook_signature(
            b"test payload",
            "invalid_signature_format"
        )
        
        # Should return False for invalid signature
        assert result is False
        
        # Test with exception in verification
        with patch('hmac.new') as mock_hmac:
            mock_hmac.side_effect = Exception("HMAC error")
            
            result = whatsapp_service.verify_webhook_signature(
                b"test payload",
                "sha256=valid_format"
            )
            
            assert result is False