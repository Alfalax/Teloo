"""
Tests for Results Service
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.results_service import results_service


@pytest.fixture
def sample_solicitud():
    """Sample solicitud data"""
    return {
        "id": "sol-123",
        "codigo_solicitud": "SOL-123",
        "cliente": {
            "id": "cliente-1",
            "telefono": "+573001234567",
            "nombre": "Juan Pérez"
        }
    }


@pytest.fixture
def sample_single_adjudication():
    """Sample single adjudication (one asesor)"""
    return [
        {
            "id": "adj-1",
            "precio_adjudicado": "15000.00",
            "cantidad_adjudicada": 1,
            "tiempo_entrega_adjudicado": 2,
            "garantia_adjudicada": 6,
            "repuesto_solicitado": {
                "id": "rep-1",
                "nombre": "pastillas de freno"
            },
            "asesor": {
                "id": "asesor-1",
                "punto_venta": "Repuestos Central",
                "ciudad": "Bogotá",
                "usuario": {
                    "nombre_completo": "Carlos Rodríguez"
                }
            }
        },
        {
            "id": "adj-2",
            "precio_adjudicado": "25000.00",
            "cantidad_adjudicada": 2,
            "tiempo_entrega_adjudicado": 1,
            "garantia_adjudicada": 12,
            "repuesto_solicitado": {
                "id": "rep-2",
                "nombre": "filtro de aceite"
            },
            "asesor": {
                "id": "asesor-1",
                "punto_venta": "Repuestos Central",
                "ciudad": "Bogotá",
                "usuario": {
                    "nombre_completo": "Carlos Rodríguez"
                }
            }
        }
    ]


@pytest.fixture
def sample_mixed_adjudication():
    """Sample mixed adjudication (multiple asesores)"""
    return [
        {
            "id": "adj-1",
            "precio_adjudicado": "15000.00",
            "cantidad_adjudicada": 1,
            "tiempo_entrega_adjudicado": 2,
            "garantia_adjudicada": 6,
            "repuesto_solicitado": {
                "id": "rep-1",
                "nombre": "pastillas de freno"
            },
            "asesor": {
                "id": "asesor-1",
                "punto_venta": "Repuestos Central",
                "ciudad": "Bogotá",
                "usuario": {
                    "nombre_completo": "Carlos Rodríguez"
                }
            }
        },
        {
            "id": "adj-2",
            "precio_adjudicado": "25000.00",
            "cantidad_adjudicada": 1,
            "tiempo_entrega_adjudicado": 3,
            "garantia_adjudicada": 12,
            "repuesto_solicitado": {
                "id": "rep-2",
                "nombre": "filtro de aceite"
            },
            "asesor": {
                "id": "asesor-2",
                "punto_venta": "AutoPartes Norte",
                "ciudad": "Medellín",
                "usuario": {
                    "nombre_completo": "Ana García"
                }
            }
        }
    ]


class TestResultsService:
    """Test Results Service functionality"""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    @patch('app.services.whatsapp_service.whatsapp_service.send_text_message')
    async def test_enviar_resultado_evaluacion_success_single(
        self, mock_send, mock_get, sample_solicitud, sample_single_adjudication
    ):
        """Test successful sending of single offer results"""
        # Mock Core API response
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "solicitud": sample_solicitud,
                "adjudicaciones": sample_single_adjudication
            }
        )
        
        # Mock WhatsApp service
        mock_send.return_value = True
        
        result = await results_service.enviar_resultado_evaluacion("sol-123")
        
        assert result["success"] is True
        assert result["solicitud_id"] == "sol-123"
        assert result["client_phone"] == "+573001234567"
        
        # Verify API call
        mock_get.assert_called_once()
        
        # Verify WhatsApp message sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == "+573001234567"  # Phone number
        message = call_args[0][1]  # Message content
        assert "SOL-123" in message
        assert "Carlos Rodríguez" in message
        assert "pastillas de freno" in message
        assert "filtro de aceite" in message
        assert "$65,000" in message  # Total price
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    @patch('app.services.whatsapp_service.whatsapp_service.send_text_message')
    async def test_enviar_resultado_evaluacion_success_mixed(
        self, mock_send, mock_get, sample_solicitud, sample_mixed_adjudication
    ):
        """Test successful sending of mixed offer results"""
        # Mock Core API response
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "solicitud": sample_solicitud,
                "adjudicaciones": sample_mixed_adjudication
            }
        )
        
        # Mock WhatsApp service
        mock_send.return_value = True
        
        result = await results_service.enviar_resultado_evaluacion("sol-123")
        
        assert result["success"] is True
        
        # Verify message content for mixed offers
        call_args = mock_send.call_args
        message = call_args[0][1]
        assert "2 repuestos cubiertos" in message
        assert "2 proveedores seleccionados" in message
        assert "Carlos Rodríguez" in message
        assert "Ana García" in message
        assert "$40,000" in message  # Total price
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_enviar_resultado_evaluacion_no_adjudications(self, mock_get, sample_solicitud):
        """Test sending results when no adjudications exist"""
        # Mock Core API response with no adjudications
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "solicitud": sample_solicitud,
                "adjudicaciones": []
            }
        )
        
        result = await results_service.enviar_resultado_evaluacion("sol-123")
        
        assert result["success"] is False
        assert result["error"] == "No hay ofertas ganadoras para enviar"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_enviar_resultado_evaluacion_solicitud_not_found(self, mock_get):
        """Test sending results for non-existent solicitud"""
        # Mock Core API 404 response
        mock_get.return_value = MagicMock(status_code=404)
        
        result = await results_service.enviar_resultado_evaluacion("sol-999")
        
        assert result["success"] is False
        assert "No se pudieron obtener los resultados" in result["error"]
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    @patch('app.services.whatsapp_service.whatsapp_service.send_text_message')
    async def test_enviar_resultado_evaluacion_whatsapp_failure(
        self, mock_send, mock_get, sample_solicitud, sample_single_adjudication
    ):
        """Test handling WhatsApp sending failure"""
        # Mock Core API response
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "solicitud": sample_solicitud,
                "adjudicaciones": sample_single_adjudication
            }
        )
        
        # Mock WhatsApp failure
        mock_send.return_value = False
        
        result = await results_service.enviar_resultado_evaluacion("sol-123")
        
        assert result["success"] is False
        assert result["error"] == "Error enviando mensaje por WhatsApp"
    
    @pytest.mark.asyncio
    async def test_format_single_offer_message(self, sample_solicitud, sample_single_adjudication):
        """Test formatting single offer message"""
        message = await results_service._format_single_offer_message(
            sample_solicitud, sample_single_adjudication
        )
        
        assert "¡Tenemos una oferta para ti!" in message
        assert "SOL-123" in message
        assert "pastillas de freno" in message
        assert "2x filtro de aceite" in message
        assert "$65,000" in message  # Total price
        assert "2 días" in message  # Max delivery time
        assert "6 meses" in message  # Min warranty
        assert "Carlos Rodríguez" in message
        assert "Repuestos Central" in message
        assert "SÍ" in message
        assert "NO" in message
        assert "DETALLES" in message
    
    @pytest.mark.asyncio
    async def test_format_mixed_offer_message(self, sample_solicitud, sample_mixed_adjudication):
        """Test formatting mixed offer message"""
        message = await results_service._format_mixed_offer_message(
            sample_solicitud, sample_mixed_adjudication
        )
        
        assert "¡Tenemos ofertas para ti!" in message
        assert "2 repuestos cubiertos" in message
        assert "2 proveedores seleccionados" in message
        assert "Carlos Rodríguez" in message
        assert "Ana García" in message
        assert "$40,000" in message  # Total price
        assert "SÍ" in message
        assert "NO" in message
        assert "DETALLES" in message
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    @patch('app.services.whatsapp_service.whatsapp_service.send_text_message')
    async def test_handle_client_response_accept(self, mock_send, mock_post):
        """Test handling client acceptance"""
        # Mock Core API success
        mock_post.return_value = MagicMock(status_code=200)
        mock_send.return_value = True
        
        result = await results_service.handle_client_response(
            "+573001234567", "SÍ", "sol-123"
        )
        
        assert result["success"] is True
        assert result["action"] == "accepted"
        
        # Verify API call to accept
        mock_post.assert_called_once_with(
            f"{results_service.core_api_url}/v1/solicitudes/sol-123/aceptar"
        )
        
        # Verify confirmation message sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        message = call_args[0][1]
        assert "¡Perfecto! Oferta aceptada" in message
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    @patch('app.services.whatsapp_service.whatsapp_service.send_text_message')
    async def test_handle_client_response_reject(self, mock_send, mock_post):
        """Test handling client rejection"""
        # Mock Core API success
        mock_post.return_value = MagicMock(status_code=200)
        mock_send.return_value = True
        
        result = await results_service.handle_client_response(
            "+573001234567", "NO", "sol-123"
        )
        
        assert result["success"] is True
        assert result["action"] == "rejected"
        
        # Verify API call to reject
        mock_post.assert_called_once_with(
            f"{results_service.core_api_url}/v1/solicitudes/sol-123/rechazar"
        )
        
        # Verify confirmation message sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        message = call_args[0][1]
        assert "Oferta rechazada" in message
    
    @pytest.mark.asyncio
    @patch.object(results_service, '_get_evaluation_results')
    @patch('app.services.whatsapp_service.whatsapp_service.send_text_message')
    async def test_handle_client_response_details(
        self, mock_send, mock_get_results, sample_solicitud, sample_single_adjudication
    ):
        """Test handling client request for details"""
        # Mock evaluation results
        mock_get_results.return_value = {
            "success": True,
            "solicitud": sample_solicitud,
            "adjudicaciones": sample_single_adjudication
        }
        mock_send.return_value = True
        
        result = await results_service.handle_client_response(
            "+573001234567", "DETALLES", "sol-123"
        )
        
        assert result["success"] is True
        assert result["action"] == "details_sent"
        
        # Verify two messages sent (details + follow-up)
        assert mock_send.call_count == 2
        
        # Check first message (details)
        first_call = mock_send.call_args_list[0]
        details_message = first_call[0][1]
        assert "Detalles completos" in details_message
        assert "Carlos Rodríguez" in details_message
        
        # Check second message (follow-up)
        second_call = mock_send.call_args_list[1]
        followup_message = second_call[0][1]
        assert "¿Qué decides?" in followup_message
    
    @pytest.mark.asyncio
    @patch('app.services.whatsapp_service.whatsapp_service.send_text_message')
    async def test_handle_client_response_invalid(self, mock_send):
        """Test handling invalid client response"""
        mock_send.return_value = True
        
        result = await results_service.handle_client_response(
            "+573001234567", "MAYBE", "sol-123"
        )
        
        assert result["success"] is True
        assert result["action"] == "clarification_sent"
        
        # Verify clarification message sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        message = call_args[0][1]
        assert "No entendí tu respuesta" in message
        assert "SÍ" in message
        assert "NO" in message
        assert "DETALLES" in message
    
    @pytest.mark.asyncio
    async def test_format_detailed_message(self, sample_mixed_adjudication):
        """Test formatting detailed message"""
        message = await results_service._format_detailed_message(sample_mixed_adjudication)
        
        assert "Detalles completos de la oferta" in message
        assert "Carlos Rodríguez" in message
        assert "Ana García" in message
        assert "pastillas de freno" in message
        assert "filtro de aceite" in message
        assert "$15,000" in message
        assert "$25,000" in message
        assert "2 días" in message
        assert "3 días" in message
        assert "6 meses" in message
        assert "1 año" in message
    
    @pytest.mark.asyncio
    async def test_warranty_formatting(self):
        """Test warranty formatting in messages"""
        # Test different warranty periods
        test_cases = [
            (1, "1 mes"),
            (6, "6 meses"),
            (12, "1 año"),
            (18, "1 año y 6 meses"),
            (24, "2 años"),
            (30, "2 años y 6 meses")
        ]
        
        for garantia_meses, expected in test_cases:
            # Create test adjudication
            adj = {
                "garantia_adjudicada": garantia_meses,
                "precio_adjudicado": "10000.00",
                "cantidad_adjudicada": 1,
                "tiempo_entrega_adjudicado": 1,
                "repuesto_solicitado": {"nombre": "test"},
                "asesor": {
                    "id": "asesor-1",
                    "punto_venta": "Test",
                    "ciudad": "Test",
                    "usuario": {"nombre_completo": "Test"}
                }
            }
            
            message = await results_service._format_detailed_message([adj])
            assert expected in message
    
    @pytest.mark.asyncio
    async def test_delivery_time_formatting(self):
        """Test delivery time formatting in messages"""
        # Test different delivery times
        test_cases = [
            (0, "Inmediato"),
            (1, "1 día"),
            (5, "5 días")
        ]
        
        for tiempo_dias, expected in test_cases:
            # Create test adjudication
            adj = {
                "tiempo_entrega_adjudicado": tiempo_dias,
                "precio_adjudicado": "10000.00",
                "cantidad_adjudicada": 1,
                "garantia_adjudicada": 6,
                "repuesto_solicitado": {"nombre": "test"},
                "asesor": {
                    "id": "asesor-1",
                    "punto_venta": "Test",
                    "ciudad": "Test",
                    "usuario": {"nombre_completo": "Test"}
                }
            }
            
            message = await results_service._format_detailed_message([adj])
            assert expected in message