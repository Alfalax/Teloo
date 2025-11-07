"""
Tests for Solicitud Service
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.solicitud_service import solicitud_service
from app.models.llm import ProcessedData
from app.models.conversation import ConversationContext


@pytest.fixture
def sample_processed_data():
    """Sample processed data"""
    return ProcessedData(
        repuestos=[
            {
                "nombre": "pastillas de freno",
                "codigo": "PF001",
                "cantidad": 1
            }
        ],
        vehiculo={
            "marca": "Toyota",
            "linea": "Corolla",
            "anio": "2015"
        },
        cliente={
            "telefono": "+573001234567",
            "nombre": "Juan Pérez",
            "ciudad": "Bogotá"
        },
        provider_used="deepseek",
        complexity_level="simple",
        confidence_score=0.85,
        processing_time_ms=150,
        is_complete=True,
        missing_fields=[]
    )


@pytest.fixture
def sample_conversation():
    """Sample conversation context"""
    return ConversationContext(
        phone_number="+573001234567",
        accumulated_repuestos=[
            {
                "nombre": "pastillas de freno",
                "codigo": "PF001",
                "cantidad": 1
            }
        ],
        accumulated_vehiculo={
            "marca": "Toyota",
            "linea": "Corolla",
            "anio": "2015"
        },
        accumulated_cliente={
            "telefono": "+573001234567",
            "nombre": "Juan Pérez",
            "ciudad": "Bogotá"
        },
        total_turns=4
    )


class TestSolicitudService:
    """Test Solicitud Service functionality"""
    
    def test_validate_phone_number_valid(self):
        """Test valid phone number validation"""
        valid_phones = [
            "+573001234567",
            "+573101234567",
            "+573201234567"
        ]
        
        for phone in valid_phones:
            assert solicitud_service._validate_phone_number(phone) is True
    
    def test_validate_phone_number_invalid(self):
        """Test invalid phone number validation"""
        invalid_phones = [
            "3001234567",  # Missing +57
            "+57300123456",  # Too short
            "+5730012345678",  # Too long
            "+573001234567x",  # Invalid character
            "+572001234567",  # Doesn't start with 3
            "+1234567890"  # Wrong country code
        ]
        
        for phone in invalid_phones:
            assert solicitud_service._validate_phone_number(phone) is False
    
    @pytest.mark.asyncio
    async def test_validate_datos_extraidos_valid(self, sample_processed_data, sample_conversation):
        """Test validation of valid extracted data"""
        validation = await solicitud_service._validate_datos_extraidos(sample_processed_data, sample_conversation)
        
        assert validation["is_valid"] is True
        assert len(validation["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_datos_extraidos_missing_repuestos(self, sample_processed_data, sample_conversation):
        """Test validation with missing repuestos"""
        sample_conversation.accumulated_repuestos = []
        sample_processed_data.repuestos = []
        
        validation = await solicitud_service._validate_datos_extraidos(sample_processed_data, sample_conversation)
        
        assert validation["is_valid"] is False
        assert "No se encontraron repuestos en la solicitud" in validation["errors"]
        assert "repuestos" in validation["missing_fields"]
    
    @pytest.mark.asyncio
    async def test_validate_datos_extraidos_invalid_phone(self, sample_processed_data, sample_conversation):
        """Test validation with invalid phone number"""
        sample_conversation.accumulated_cliente["telefono"] = "3001234567"  # Missing +57
        
        validation = await solicitud_service._validate_datos_extraidos(sample_processed_data, sample_conversation)
        
        assert validation["is_valid"] is False
        assert "Formato de teléfono inválido (debe ser +57XXXXXXXXXX)" in validation["errors"]
    
    @pytest.mark.asyncio
    async def test_validate_datos_extraidos_invalid_year(self, sample_processed_data, sample_conversation):
        """Test validation with invalid vehicle year"""
        sample_conversation.accumulated_vehiculo["anio"] = "1970"  # Too old
        
        validation = await solicitud_service._validate_datos_extraidos(sample_processed_data, sample_conversation)
        
        assert validation["is_valid"] is False
        assert "Año del vehículo fuera del rango válido (1980-2025)" in validation["errors"]
    
    @pytest.mark.asyncio
    async def test_prepare_solicitud_data(self, sample_processed_data, sample_conversation):
        """Test solicitud data preparation"""
        solicitud_data = await solicitud_service._prepare_solicitud_data(sample_processed_data, sample_conversation)
        
        assert len(solicitud_data["repuestos"]) == 1
        assert solicitud_data["repuestos"][0]["nombre"] == "pastillas de freno"
        assert solicitud_data["repuestos"][0]["marca_vehiculo"] == "Toyota"
        assert solicitud_data["repuestos"][0]["anio_vehiculo"] == 2015
        
        assert solicitud_data["cliente"]["telefono"] == "+573001234567"
        assert solicitud_data["cliente"]["nombre"] == "Juan Pérez"
        assert solicitud_data["cliente"]["ciudad"] == "Bogotá"
        
        assert solicitud_data["metadata_json"]["origen"] == "whatsapp"
        assert solicitud_data["metadata_json"]["provider_used"] == "deepseek"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    @patch('httpx.AsyncClient.post')
    async def test_create_or_get_cliente_existing(self, mock_post, mock_get):
        """Test getting existing cliente"""
        # Mock existing cliente found
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"id": "cliente123", "telefono": "+573001234567"}]
        )
        
        cliente_data = {"telefono": "+573001234567", "nombre": "Juan"}
        result = await solicitud_service._create_or_get_cliente(cliente_data)
        
        assert result["success"] is True
        assert result["cliente_id"] == "cliente123"
        assert result["created"] is False
        
        # Should not call POST (create)
        mock_post.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    @patch('httpx.AsyncClient.post')
    async def test_create_or_get_cliente_new(self, mock_post, mock_get):
        """Test creating new cliente"""
        # Mock no existing cliente found
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: []
        )
        
        # Mock successful creation
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": "cliente456", "telefono": "+573001234567"}
        )
        
        cliente_data = {"telefono": "+573001234567", "nombre": "Juan"}
        result = await solicitud_service._create_or_get_cliente(cliente_data)
        
        assert result["success"] is True
        assert result["cliente_id"] == "cliente456"
        assert result["created"] is True
        
        # Should call POST (create)
        mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_create_solicitud_success(self, mock_post):
        """Test successful solicitud creation"""
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": "sol123", "estado": "ABIERTA"}
        )
        
        solicitud_data = {"cliente_id": "cliente123", "repuestos": []}
        result = await solicitud_service._create_solicitud(solicitud_data)
        
        assert result["success"] is True
        assert result["solicitud_id"] == "sol123"
        mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_create_solicitud_failure(self, mock_post):
        """Test failed solicitud creation"""
        mock_post.return_value = MagicMock(
            status_code=400,
            text="Bad request"
        )
        
        solicitud_data = {"cliente_id": "cliente123", "repuestos": []}
        result = await solicitud_service._create_solicitud(solicitud_data)
        
        assert result["success"] is False
        assert "Error creating solicitud" in result["error"]
    
    @pytest.mark.asyncio
    @patch('app.services.whatsapp_service.whatsapp_service.send_text_message')
    async def test_send_confirmation_message(self, mock_send):
        """Test sending confirmation message"""
        mock_send.return_value = True
        
        solicitud_data = {
            "repuestos": [
                {
                    "nombre": "pastillas de freno",
                    "cantidad": 1,
                    "marca_vehiculo": "Toyota",
                    "linea_vehiculo": "Corolla",
                    "anio_vehiculo": 2015
                }
            ]
        }
        
        await solicitud_service._send_confirmation_message(
            "+573001234567",
            "SOL123",
            solicitud_data
        )
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == "+573001234567"  # Phone number
        message = call_args[0][1]  # Message content
        assert "SOL123" in message
        assert "pastillas de freno" in message
        assert "Toyota Corolla 2015" in message
    
    @pytest.mark.asyncio
    @patch.object(solicitud_service, '_validate_datos_extraidos')
    @patch.object(solicitud_service, '_create_or_get_cliente')
    @patch.object(solicitud_service, '_create_solicitud')
    @patch.object(solicitud_service, '_send_confirmation_message')
    async def test_crear_solicitud_desde_whatsapp_success(
        self, mock_send, mock_create_sol, mock_create_cliente, mock_validate,
        sample_processed_data, sample_conversation
    ):
        """Test successful solicitud creation from WhatsApp"""
        # Mock validation success
        mock_validate.return_value = {"is_valid": True, "errors": [], "missing_fields": []}
        
        # Mock cliente creation success
        mock_create_cliente.return_value = {"success": True, "cliente_id": "cliente123"}
        
        # Mock solicitud creation success
        mock_create_sol.return_value = {"success": True, "solicitud_id": "SOL123"}
        
        # Mock message sending
        mock_send.return_value = None
        
        result = await solicitud_service.crear_solicitud_desde_whatsapp(
            sample_processed_data,
            sample_conversation
        )
        
        assert result["success"] is True
        assert result["solicitud_id"] == "SOL123"
        assert result["cliente_id"] == "cliente123"
        
        mock_validate.assert_called_once()
        mock_create_cliente.assert_called_once()
        mock_create_sol.assert_called_once()
        mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.object(solicitud_service, '_validate_datos_extraidos')
    async def test_crear_solicitud_desde_whatsapp_validation_failure(
        self, mock_validate, sample_processed_data, sample_conversation
    ):
        """Test solicitud creation with validation failure"""
        # Mock validation failure
        mock_validate.return_value = {
            "is_valid": False,
            "errors": ["Missing repuestos"],
            "missing_fields": ["repuestos"]
        }
        
        result = await solicitud_service.crear_solicitud_desde_whatsapp(
            sample_processed_data,
            sample_conversation
        )
        
        assert result["success"] is False
        assert result["error"] == "Datos incompletos"
        assert "Missing repuestos" in result["validation_errors"]
    
    @pytest.mark.asyncio
    async def test_validate_ciudad_valid(self):
        """Test valid city validation"""
        valid_cities = ["Bogotá", "Medellín", "Cali", "Barranquilla"]
        
        for city in valid_cities:
            is_valid = await solicitud_service.validate_ciudad(city)
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_ciudad_invalid(self):
        """Test invalid city validation"""
        invalid_cities = ["", "XY", "InvalidCity123"]
        
        for city in invalid_cities:
            is_valid = await solicitud_service.validate_ciudad(city)
            assert is_valid is False
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_get_solicitud_status_success(self, mock_get):
        """Test getting solicitud status"""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"id": "SOL123", "estado": "ABIERTA"}
        )
        
        status = await solicitud_service.get_solicitud_status("SOL123")
        
        assert status is not None
        assert status["id"] == "SOL123"
        assert status["estado"] == "ABIERTA"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_get_solicitud_status_not_found(self, mock_get):
        """Test getting solicitud status when not found"""
        mock_get.return_value = MagicMock(status_code=404)
        
        status = await solicitud_service.get_solicitud_status("SOL999")
        
        assert status is None