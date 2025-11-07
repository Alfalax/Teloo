"""
Tests for Conversation Service
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.services.conversation_service import conversation_service
from app.models.conversation import ConversationContext, ConversationState, MessageTurn
from app.models.whatsapp import ProcessedMessage
from app.models.llm import ProcessedData


@pytest.fixture
def sample_message():
    """Sample WhatsApp message"""
    return ProcessedMessage(
        message_id="wamid.test123",
        from_number="+573001234567",
        timestamp=datetime.now(),
        message_type="text",
        text_content="Necesito pastillas de freno para Toyota Corolla 2015"
    )


@pytest.fixture
def sample_processed_data():
    """Sample processed data"""
    return ProcessedData(
        repuestos=[
            {
                "nombre": "pastillas de freno",
                "codigo": None,
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
        state=ConversationState.GATHERING_INFO,
        accumulated_repuestos=[
            {"nombre": "pastillas de freno", "cantidad": 1}
        ],
        accumulated_vehiculo={
            "marca": "Toyota",
            "linea": "Corolla"
        },
        accumulated_cliente={
            "telefono": "+573001234567"
        }
    )


class TestConversationService:
    """Test Conversation Service functionality"""
    
    @patch('app.services.nlp_service.nlp_service.procesar_mensaje_whatsapp')
    @patch('app.core.redis.redis_manager.get')
    @patch('app.core.redis.redis_manager.set')
    async def test_gestionar_conversacion_new(self, mock_set, mock_get, mock_nlp, sample_message, sample_processed_data):
        """Test managing new conversation"""
        # Mock no existing conversation
        mock_get.return_value = None
        mock_set.return_value = True
        mock_nlp.return_value = sample_processed_data
        
        conversation, response = await conversation_service.gestionar_conversacion(
            "+573001234567", 
            sample_message
        )
        
        assert conversation.phone_number == "+573001234567"
        assert len(conversation.turns) == 2  # User turn + system turn
        assert conversation.turns[0].from_user is True
        assert conversation.turns[1].from_user is False
        assert len(conversation.accumulated_repuestos) > 0
        assert conversation.accumulated_vehiculo is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    @patch('app.services.nlp_service.nlp_service.procesar_mensaje_whatsapp')
    @patch('app.core.redis.redis_manager.get')
    @patch('app.core.redis.redis_manager.set')
    async def test_gestionar_conversacion_existing(self, mock_set, mock_get, mock_nlp, sample_conversation, sample_message, sample_processed_data):
        """Test managing existing conversation"""
        # Mock existing conversation
        import json
        mock_get.return_value = json.dumps(sample_conversation.model_dump(), default=str)
        mock_set.return_value = True
        mock_nlp.return_value = sample_processed_data
        
        conversation, response = await conversation_service.gestionar_conversacion(
            "+573001234567", 
            sample_message
        )
        
        assert conversation.phone_number == "+573001234567"
        assert len(conversation.turns) >= 2
        assert isinstance(response, str)
    
    async def test_update_accumulated_data(self, sample_conversation, sample_processed_data):
        """Test updating accumulated data"""
        initial_repuestos_count = len(sample_conversation.accumulated_repuestos)
        
        await conversation_service._update_accumulated_data(sample_conversation, sample_processed_data)
        
        # Should merge data
        assert sample_conversation.accumulated_vehiculo["anio"] == "2015"
        assert sample_conversation.accumulated_cliente["nombre"] == "Juan Pérez"
        assert sample_conversation.accumulated_cliente["ciudad"] == "Bogotá"
    
    async def test_calculate_completeness(self, sample_conversation):
        """Test completeness calculation"""
        # Initially incomplete
        await conversation_service._calculate_completeness(sample_conversation)
        initial_score = sample_conversation.completeness_score
        
        # Add missing information
        sample_conversation.accumulated_vehiculo["anio"] = "2015"
        sample_conversation.accumulated_cliente["nombre"] = "Juan"
        sample_conversation.accumulated_cliente["ciudad"] = "Bogotá"
        
        await conversation_service._calculate_completeness(sample_conversation)
        
        # Should be more complete
        assert sample_conversation.completeness_score > initial_score
        assert len(sample_conversation.missing_fields) < 6
    
    async def test_validate_completitud_valid(self):
        """Test validation of complete conversation"""
        complete_conversation = ConversationContext(
            phone_number="+573001234567",
            accumulated_repuestos=[{"nombre": "pastillas de freno"}],
            accumulated_vehiculo={"marca": "Toyota", "anio": "2015"},
            accumulated_cliente={"telefono": "+573001234567", "ciudad": "Bogotá"}
        )
        
        is_valid = await conversation_service.validate_completitud(complete_conversation)
        assert is_valid is True
    
    async def test_validate_completitud_invalid(self):
        """Test validation of incomplete conversation"""
        incomplete_conversation = ConversationContext(
            phone_number="+573001234567",
            accumulated_repuestos=[],  # Missing repuestos
            accumulated_vehiculo=None,  # Missing vehicle
            accumulated_cliente={"telefono": "+573001234567"}
        )
        
        is_valid = await conversation_service.validate_completitud(incomplete_conversation)
        assert is_valid is False
    
    async def test_generate_confirmation_message(self):
        """Test confirmation message generation"""
        complete_conversation = ConversationContext(
            phone_number="+573001234567",
            accumulated_repuestos=[{"nombre": "pastillas de freno", "cantidad": 1}],
            accumulated_vehiculo={"marca": "Toyota", "linea": "Corolla", "anio": "2015"},
            accumulated_cliente={"telefono": "+573001234567", "nombre": "Juan", "ciudad": "Bogotá"}
        )
        
        message = await conversation_service._generate_confirmation_message(complete_conversation)
        
        assert "pastillas de freno" in message
        assert "Toyota" in message
        assert "Juan" in message
        assert "SÍ" in message or "NO" in message
    
    async def test_generate_clarification_message(self):
        """Test clarification message generation"""
        incomplete_conversation = ConversationContext(
            phone_number="+573001234567",
            missing_fields=["repuestos", "vehiculo.marca"]
        )
        
        message = await conversation_service._generate_clarification_message(incomplete_conversation)
        
        assert isinstance(message, str)
        assert len(message) > 0
        assert "?" in message  # Should be a question
    
    @patch('app.core.redis.redis_manager.set')
    async def test_close_conversation(self, mock_set):
        """Test closing conversation"""
        mock_set.return_value = True
        
        with patch.object(conversation_service, 'get_conversation_context') as mock_get:
            mock_conversation = ConversationContext(phone_number="+573001234567")
            mock_get.return_value = mock_conversation
            
            await conversation_service.close_conversation("+573001234567", "completed")
            
            assert mock_conversation.state == ConversationState.CLOSED


class TestConversationContext:
    """Test ConversationContext model"""
    
    def test_add_turn(self):
        """Test adding turn to conversation"""
        conversation = ConversationContext(phone_number="+573001234567")
        
        turn = MessageTurn(
            message_id="test123",
            timestamp=datetime.now(),
            from_user=True,
            content="Test message"
        )
        
        conversation.add_turn(turn)
        
        assert len(conversation.turns) == 1
        assert conversation.total_turns == 1
        assert conversation.turns[0].content == "Test message"
    
    def test_get_latest_user_message(self):
        """Test getting latest user message"""
        conversation = ConversationContext(phone_number="+573001234567")
        
        # Add system message
        system_turn = MessageTurn(
            message_id="system1",
            timestamp=datetime.now(),
            from_user=False,
            content="System message"
        )
        conversation.add_turn(system_turn)
        
        # Add user message
        user_turn = MessageTurn(
            message_id="user1",
            timestamp=datetime.now(),
            from_user=True,
            content="User message"
        )
        conversation.add_turn(user_turn)
        
        latest = conversation.get_latest_user_message()
        assert latest is not None
        assert latest.content == "User message"
        assert latest.from_user is True
    
    def test_get_conversation_summary(self):
        """Test conversation summary generation"""
        conversation = ConversationContext(
            phone_number="+573001234567",
            accumulated_repuestos=[{"nombre": "pastillas de freno"}],
            accumulated_vehiculo={"marca": "Toyota", "linea": "Corolla", "anio": "2015"},
            accumulated_cliente={"nombre": "Juan", "ciudad": "Bogotá"}
        )
        
        summary = conversation.get_conversation_summary()
        
        assert "pastillas de freno" in summary
        assert "Toyota" in summary
        assert "Juan" in summary