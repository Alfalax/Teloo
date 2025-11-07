"""
Tests for Results endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app

client = TestClient(app)


class TestResultsEndpoints:
    """Test Results API endpoints"""
    
    @patch('app.services.results_service.results_service.enviar_resultado_evaluacion')
    def test_send_evaluation_results_success(self, mock_enviar):
        """Test successful sending of evaluation results"""
        # Mock service response
        mock_enviar.return_value = {
            "success": True,
            "message": "Resultados enviados exitosamente",
            "solicitud_id": "sol-123",
            "client_phone": "+573001234567"
        }
        
        response = client.post(
            "/v1/results/send",
            json={"solicitud_id": "sol-123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["solicitud_id"] == "sol-123"
        assert data["client_phone"] == "+573001234567"
        assert "error" not in data or data["error"] is None
    
    @patch('app.services.results_service.results_service.enviar_resultado_evaluacion')
    def test_send_evaluation_results_failure(self, mock_enviar):
        """Test failed sending of evaluation results"""
        # Mock service response
        mock_enviar.return_value = {
            "success": False,
            "error": "No se pudieron obtener los resultados",
            "solicitud_id": "sol-123"
        }
        
        response = client.post(
            "/v1/results/send",
            json={"solicitud_id": "sol-123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["solicitud_id"] == "sol-123"
        assert data["error"] == "No se pudieron obtener los resultados"
    
    def test_send_evaluation_results_invalid_request(self):
        """Test sending results with invalid request"""
        response = client.post(
            "/v1/results/send",
            json={}  # Missing solicitud_id
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_results_status(self):
        """Test getting results status"""
        response = client.get("/v1/results/status/sol-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["solicitud_id"] == "sol-123"
        assert "status" in data
    
    def test_results_health_check(self):
        """Test results health check"""
        response = client.get("/v1/results/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Results Service"
        assert data["status"] == "healthy"