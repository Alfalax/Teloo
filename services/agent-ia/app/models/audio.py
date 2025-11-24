"""
Audio processing models
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class AudioStrategy(str, Enum):
    """Audio processing strategies"""
    WHISPER = "whisper"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENAI = "openai"


class FallbackReason(str, Enum):
    """Reasons for activating fallback"""
    ERROR = "error"
    LOW_CONFIDENCE = "low_confidence"
    EMPTY_TRANSCRIPTION = "empty_transcription"
    NO_ENTITIES = "no_entities"
    TIMEOUT = "timeout"
    POOR_AUDIO_QUALITY = "poor_audio_quality"


class AudioQuality(str, Enum):
    """Audio quality levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class TranscriptionResult(BaseModel):
    """Result from audio transcription"""
    text: str
    language: str = "es"
    duration_minutes: float
    processing_time_ms: int
    cost_usd: float
    provider: str
    model: str
    quality_indicators: Dict[str, Any] = Field(default_factory=dict)


class AudioProcessingResult(BaseModel):
    """Complete result from audio processing"""
    # Extracted data
    repuestos: List[Dict[str, Any]]
    vehiculo: Optional[Dict[str, Any]] = None
    cliente: Optional[Dict[str, Any]] = None
    
    # Processing metadata
    strategy_used: AudioStrategy
    fallback_used: bool = False
    fallback_reason: Optional[FallbackReason] = None
    
    # Quality metrics
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: int
    cost_usd: float
    
    # Transcription data
    transcription: Optional[str] = None
    transcription_cached: bool = False
    transcription_quality: AudioQuality = AudioQuality.UNKNOWN
    
    # Timestamps
    processed_at: datetime = Field(default_factory=datetime.now)
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation flags
    has_problematic_words: bool = False
    problematic_words: List[str] = Field(default_factory=list)
    
    @property
    def is_successful(self) -> bool:
        """Check if processing was successful"""
        return (
            self.confidence_score >= 0.6 and
            (len(self.repuestos) > 0 or self.vehiculo is not None) and
            not self.has_problematic_words
        )
    
    @property
    def total_entities_found(self) -> int:
        """Count total entities found"""
        count = len(self.repuestos)
        if self.vehiculo:
            count += 1
        if self.cliente:
            count += 1
        return count


class AudioValidationResult(BaseModel):
    """Result from audio validation checks"""
    is_valid: bool
    should_use_fallback: bool
    fallback_reason: Optional[FallbackReason] = None
    validation_details: Dict[str, Any] = Field(default_factory=dict)
    
    # Specific validation flags
    length_ok: bool = True
    quality_ok: bool = True
    confidence_ok: bool = True
    entities_ok: bool = True
    
    # Problematic content
    problematic_words_found: List[str] = Field(default_factory=list)
    
    @classmethod
    def create_success(cls) -> "AudioValidationResult":
        """Create successful validation result"""
        return cls(
            is_valid=True,
            should_use_fallback=False
        )
    
    @classmethod
    def create_failure(
        cls, 
        reason: FallbackReason, 
        details: Optional[Dict[str, Any]] = None
    ) -> "AudioValidationResult":
        """Create failed validation result"""
        return cls(
            is_valid=False,
            should_use_fallback=True,
            fallback_reason=reason,
            validation_details=details or {}
        )
