"""
Tests for WhatsApp webhook functionality
"""

import pytest
import json
import hmac
import hashlib
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app
from app.core.config import settings


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def sample_webhook_data():
    """Sample WhatsApp webhook data"""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "573001234567",
                                "phone_number_id": "123456789"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Test User"
                                    },
                                    "wa_id": "573001234567"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "573001234567",
                                    "id": "wamid.test123",
                                    "timestamp": "1640995200",
                                    "text": {
                                        "body": "Necesito pastillas de freno para Toyota Corolla 2015"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }


def create_webhook_signature(payload: str, secret: str) -> str:
    """Create webhook signature for testing"""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


class TestWhatsAppWebhook:
    """Test WhatsApp webhook endpoints"""
    
    def test_webhook_verification_success(self, client):
        """Test successful webhook verification"""
        response = client.get(
            "/v1/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "test_challenge_123",
                "hub.verify_token": settings.whatsapp_verify_token
            }
        )
        
        assert response.status_code == 200
        assert response.text == "test_challenge_123"
    
    def test_webhook_verification_invalid_token(self, client):
        """Test webhook verification with invalid token"""
        response = client.get(
            "/v1/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "test_challenge_123",
                "hub.verify_token": "invalid_token"
            }
        )
        
        assert response.status_code == 403
        assert "Invalid verify token" in response.json()["detail"]
    
    def test_webhook_verification_invalid_mode(self, client):
        """Test webhook verification with invalid mode"""
        response = client.get(
            "/v1/webhooks/whatsapp",
            params={
                "hub.mode": "invalid_mode",
                "hub.challenge": "test_challenge_123",
                "hub.verify_token": settings.whatsapp_verify_token
            }
        )
        
        assert response.status_code == 400
        assert "Invalid hub mode" in response.json()["detail"]
    
    @patch('app.services.whatsapp_service.whatsapp_service.queue_message_for_processing')
    @patch('app.core.redis.redis_manager.incr')
    @patch('app.core.redis.redis_manager.get')
    def test_webhook_message_processing(self, mock_redis_get, mock_redis_incr, mock_queue, client, sample_webhook_data):
        """Test webhook message processing"""
        # Mock rate limiting
        mock_redis_get.return_value = "1"
        mock_redis_incr.return_value = 2
        
        # Mock message queuing
        mock_queue.return_value = True
        
        # Create signature
        payload = json.dumps(sample_webhook_data)
        signature = create_webhook_signature(payload, settings.whatsapp_webhook_secret)
        
        response = client.post(
            "/v1/webhooks/whatsapp",
            json=sample_webhook_data,
            headers={
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "received"
        
        # Verify message was queued
        mock_queue.assert_called_once()
    
    @patch('app.core.redis.redis_manager.incr')
    @patch('app.core.redis.redis_manager.get')
    def test_webhook_rate_limiting(self, mock_redis_get, mock_redis_incr, client, sample_webhook_data):
        """Test webhook rate limiting"""
        # Mock rate limit exceeded
        mock_redis_get.return_value = str(settings.rate_limit_per_minute)
        
        payload = json.dumps(sample_webhook_data)
        signature = create_webhook_signature(payload, settings.whatsapp_webhook_secret)
        
        response = client.post(
            "/v1/webhooks/whatsapp",
            json=sample_webhook_data,
            headers={
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
    
    def test_webhook_invalid_signature(self, client, sample_webhook_data):
        """Test webhook with invalid signature"""
        response = client.post(
            "/v1/webhooks/whatsapp",
            json=sample_webhook_data,
            headers={
                "X-Hub-Signature-256": "sha256=invalid_signature",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 403
        assert "Invalid signature" in response.json()["detail"]
    
    def test_webhook_status_endpoint(self, client):
        """Test webhook status endpoint"""
        response = client.get("/v1/webhooks/whatsapp/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "WhatsApp Webhook"
        assert data["status"] == "active"
        assert "configuration" in data
        assert "queue_info" in data


class TestMessageExtraction:
    """Test message extraction from webhook"""
    
    def test_extract_text_message(self, sample_webhook_data):
        """Test extracting text message"""
        from app.models.whatsapp import WhatsAppWebhook
        from app.services.whatsapp_service import whatsapp_service
        
        webhook = WhatsAppWebhook(**sample_webhook_data)
        message = whatsapp_service.extract_message_from_webhook(webhook)
        
        assert message is not None
        assert message.message_id == "wamid.test123"
        assert message.from_number == "573001234567"
        assert message.message_type == "text"
        assert message.text_content == "Necesito pastillas de freno para Toyota Corolla 2015"
    
    def test_extract_image_message(self):
        """Test extracting image message"""
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "573001234567",
                                        "id": "wamid.image123",
                                        "timestamp": "1640995200",
                                        "type": "image",
                                        "image": {
                                            "id": "media123",
                                            "caption": "Foto del repuesto que necesito"
                                        }
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        
        from app.models.whatsapp import WhatsAppWebhook
        from app.services.whatsapp_service import whatsapp_service
        
        webhook = WhatsAppWebhook(**webhook_data)
        message = whatsapp_service.extract_message_from_webhook(webhook)
        
        assert message is not None
        assert message.message_id == "wamid.image123"
        assert message.message_type == "image"
        assert message.media_url == "media123"
        assert message.media_type == "image"
        assert message.text_content == "Foto del repuesto que necesito"
    
    def test_extract_no_message(self):
        """Test webhook with no messages (status update)"""
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {
                                        "id": "wamid.test123",
                                        "status": "delivered",
                                        "timestamp": "1640995200"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        
        from app.models.whatsapp import WhatsAppWebhook
        from app.services.whatsapp_service import whatsapp_service
        
        webhook = WhatsAppWebhook(**webhook_data)
        message = whatsapp_service.extract_message_from_webhook(webhook)
        
        assert message is None