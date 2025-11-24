"""
Tests for Audio Processor
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.audio_processor import AudioProcessor, AudioValidator
from app.models.audio import (
    AudioStrategy,
    FallbackReason,
    AudioProcessingResult,
    AudioValidationResult
)


class TestAudioValidator:
    """Tests for AudioValidator"""
    
    def setup_method(self):
        self.validator = AudioValidator()
    
    def test_validate_transcription_success(self):
        """Test successful transcription validation"""
        transcription = "necesito pastillas de freno para toyota corolla 2015"
        result = self.validator.validate_transcription(transcription)
        
        assert result.is_valid is True
        assert result.should_use_fallback is False
    
    def test_validate_transcription_too_short(self):
        """Test transcription too short"""
        transcription = "hola"
        result = self.validator.validate_transcription(transcription)
        
        assert result.is_valid is False
        assert result.should_use_fallback is True
        assert result.fallback_reason == FallbackReason.EMPTY_TRANSCRIPTION
    
    def test_validate_transcription_problematic_words(self):
        """Test transcription with problematic words"""
        transcription = "necesito [inaudible] para toyota [ruido] 2015"
        result = self.validator.validate_transcription(transcription)
        
        assert result.is_valid is False
        assert result.should_use_fallback is True
        assert result.fallback_reason == FallbackReason.POOR_AUDIO_QUALITY
        assert "[inaudible]" in result.validation_details["problematic_words"]
    
    def test_validate_entities_success(self):
        """Test successful entity validation"""
        entities = {
            "repuestos": [{"nombre": "pastillas de freno"}],
            "vehiculo": {"marca": "Toyota", "modelo": "Corolla"},
            "confidence_score": 0.85
        }
        result = self.validator.validate_entities_result(entities)
        
        assert result.is_valid is True
        assert result.should_use_fallback is False
    
    def test_validate_entities_low_confidence(self):
        """Test entity validation with low confidence"""
        entities = {
            "repuestos": [{"nombre": "repuestos"}],
            "vehiculo": None,
            "confidence_score": 0.35
        }
        result = self.validator.validate_entities_result(entities)
        
        assert result.is_valid is False
        assert result.should_use_fallback is True
        assert result.fallback_reason == FallbackReason.LOW_CONFIDENCE
    
    def test_validate_entities_no_entities(self):
        """Test entity validation with no entities found"""
        entities = {
            "repuestos": [],
            "vehiculo": None,
            "confidence_score": 0.70
        }
        result = self.validator.validate_entities_result(entities)
        
        assert result.is_valid is False
        assert result.should_use_fallback is True
        assert result.fallback_reason == FallbackReason.NO_ENTITIES


class TestAudioProcessor:
    """Tests for AudioProcessor"""
    
    def setup_method(self):
        self.processor = AudioProcessor()
    
    @pytest.mark.asyncio
    async def test_process_audio_whisper_success(self):
        """Test successful audio processing with Whisper"""
        audio_url = "https://example.com/audio.ogg"
        
        # Mock Whisper transcription
        with patch.object(
            self.processor.whisper,
            'transcribe',
            new_callable=AsyncMock
        ) as mock_whisper:
            mock_whisper.return_value = {
                "text": "necesito pastillas de freno para toyota corolla 2015",
                "language": "es",
                "duration_minutes": 0.5,
                "processing_time_ms": 1000,
                "cost_usd": 0.003,
                "provider": "whisper",
                "model": "whisper-1"
            }
            
            # Mock Deepseek extraction
            with patch.object(
                self.processor.deepseek,
                'process_text',
                new_callable=AsyncMock
            ) as mock_deepseek:
                mock_response = MagicMock()
                mock_response.content = '{"repuestos": [{"nombre": "pastillas de freno"}], "vehiculo": {"marca": "Toyota", "modelo": "Corolla", "anio": 2015}}'
                mock_response.cost_usd = 0.0001
                mock_deepseek.return_value = mock_response
                
                # Process audio
                result = await self.processor.process_audio(audio_url)
                
                # Assertions
                assert result.strategy_used == AudioStrategy.WHISPER
                assert result.fallback_used is False
                assert len(result.repuestos) == 1
                assert result.repuestos[0]["nombre"] == "pastillas de freno"
                assert result.vehiculo["marca"] == "Toyota"
                assert result.confidence_score >= 0.6
                assert result.transcription is not None
    
    @pytest.mark.asyncio
    async def test_process_audio_fallback_low_confidence(self):
        """Test audio processing with fallback due to low confidence"""
        audio_url = "https://example.com/audio.ogg"
        
        # Mock Whisper transcription
        with patch.object(
            self.processor.whisper,
            'transcribe',
            new_callable=AsyncMock
        ) as mock_whisper:
            mock_whisper.return_value = {
                "text": "necesito repuestos",
                "language": "es",
                "duration_minutes": 0.3,
                "processing_time_ms": 800,
                "cost_usd": 0.002,
                "provider": "whisper",
                "model": "whisper-1"
            }
            
            # Mock Deepseek extraction (low confidence)
            with patch.object(
                self.processor.deepseek,
                'process_text',
                new_callable=AsyncMock
            ) as mock_deepseek:
                mock_response = MagicMock()
                mock_response.content = '{"repuestos": [], "vehiculo": null}'
                mock_response.cost_usd = 0.0001
                mock_deepseek.return_value = mock_response
                
                # Mock Anthropic fallback
                with patch.object(
                    self.processor.anthropic,
                    'process_audio',
                    new_callable=AsyncMock
                ) as mock_anthropic:
                    mock_anthropic_response = MagicMock()
                    mock_anthropic_response.content = '{"repuestos": [{"nombre": "pastillas de freno"}], "vehiculo": {"marca": "Toyota"}}'
                    mock_anthropic_response.cost_usd = 0.012
                    mock_anthropic.return_value = mock_anthropic_response
                    
                    # Process audio
                    result = await self.processor.process_audio(audio_url)
                    
                    # Assertions
                    assert result.strategy_used == AudioStrategy.ANTHROPIC
                    assert result.fallback_used is True
                    assert result.fallback_reason == FallbackReason.NO_ENTITIES
                    assert len(result.repuestos) == 1
    
    @pytest.mark.asyncio
    async def test_process_audio_fallback_poor_quality(self):
        """Test audio processing with fallback due to poor audio quality"""
        audio_url = "https://example.com/audio.ogg"
        
        # Mock Whisper transcription with problematic words
        with patch.object(
            self.processor.whisper,
            'transcribe',
            new_callable=AsyncMock
        ) as mock_whisper:
            mock_whisper.return_value = {
                "text": "necesito [inaudible] para toyota [ruido]",
                "language": "es",
                "duration_minutes": 0.4,
                "processing_time_ms": 900,
                "cost_usd": 0.0024,
                "provider": "whisper",
                "model": "whisper-1"
            }
            
            # Mock Anthropic fallback
            with patch.object(
                self.processor.anthropic,
                'process_audio',
                new_callable=AsyncMock
            ) as mock_anthropic:
                mock_anthropic_response = MagicMock()
                mock_anthropic_response.content = '{"repuestos": [{"nombre": "pastillas de freno"}], "vehiculo": {"marca": "Toyota", "modelo": "Corolla"}}'
                mock_anthropic_response.cost_usd = 0.012
                mock_anthropic.return_value = mock_anthropic_response
                
                # Process audio
                result = await self.processor.process_audio(audio_url)
                
                # Assertions
                assert result.strategy_used == AudioStrategy.ANTHROPIC
                assert result.fallback_used is True
                assert result.fallback_reason == FallbackReason.POOR_AUDIO_QUALITY
    
    @pytest.mark.asyncio
    async def test_force_strategy_anthropic(self):
        """Test forcing Anthropic strategy"""
        audio_url = "https://example.com/audio.ogg"
        
        # Mock Anthropic
        with patch.object(
            self.processor.anthropic,
            'process_audio',
            new_callable=AsyncMock
        ) as mock_anthropic:
            mock_response = MagicMock()
            mock_response.content = '{"repuestos": [{"nombre": "pastillas de freno"}], "vehiculo": {"marca": "Toyota"}}'
            mock_response.cost_usd = 0.012
            mock_anthropic.return_value = mock_response
            
            # Process with forced strategy
            result = await self.processor.process_audio(
                audio_url,
                force_strategy=AudioStrategy.ANTHROPIC
            )
            
            # Assertions
            assert result.strategy_used == AudioStrategy.ANTHROPIC
            assert result.fallback_used is False
            mock_anthropic.assert_called_once()
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        # High confidence case
        entities_high = {
            "repuestos": [{"nombre": "pastillas de freno delanteras"}],
            "vehiculo": {"marca": "Toyota", "linea": "Corolla", "anio": 2015},
            "cliente": {"telefono": "+573001234567"}
        }
        confidence_high = self.processor._calculate_confidence(entities_high)
        assert confidence_high >= 0.8
        
        # Low confidence case
        entities_low = {
            "repuestos": [],
            "vehiculo": None,
            "cliente": None
        }
        confidence_low = self.processor._calculate_confidence(entities_low)
        assert confidence_low < 0.3
    
    def test_generate_cache_key(self):
        """Test cache key generation"""
        audio_url = "https://example.com/audio.ogg"
        key1 = self.processor._generate_cache_key(audio_url)
        key2 = self.processor._generate_cache_key(audio_url)
        
        # Same URL should generate same key
        assert key1 == key2
        assert len(key1) == 16  # SHA256 hash truncated to 16 chars
        
        # Different URL should generate different key
        key3 = self.processor._generate_cache_key("https://example.com/other.ogg")
        assert key1 != key3
