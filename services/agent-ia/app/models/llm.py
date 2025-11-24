"""
LLM provider data models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ComplexityLevel(str, Enum):
    """Content complexity levels"""
    SIMPLE = "simple"           # Level 1: Short, direct messages
    COMPLEX = "complex"         # Level 2: Long messages, multiple parts, slang
    STRUCTURED = "structured"   # Level 3: Excel, PDFs, structured documents
    MULTIMEDIA = "multimedia"   # Level 4: Audio, images, videos


class LLMProvider(str, Enum):
    """Available LLM providers"""
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    REGEX = "regex"
    BASIC = "basic"


class LLMCapability(str, Enum):
    """LLM capabilities"""
    TEXT_PROCESSING = "text_processing"
    IMAGE_ANALYSIS = "image_analysis"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    DOCUMENT_EXTRACTION = "document_extraction"
    STRUCTURED_OUTPUT = "structured_output"


class ProcessedData(BaseModel):
    """Processed data from LLM"""
    # Extracted entities
    repuestos: List[Dict[str, Any]] = []
    vehiculo: Optional[Dict[str, str]] = None
    cliente: Optional[Dict[str, str]] = None
    
    # Processing metadata
    provider_used: str
    complexity_level: str
    confidence_score: float = 0.0
    processing_time_ms: int = 0
    
    # Raw data
    raw_text: Optional[str] = None
    extracted_entities: Dict[str, Any] = {}
    
    # Validation flags
    is_complete: bool = False
    missing_fields: List[str] = []


class LLMRequest(BaseModel):
    """Request to LLM provider"""
    text: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    document_url: Optional[str] = None
    context: Dict[str, Any] = {}
    complexity_level: ComplexityLevel
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class LLMResponse(BaseModel):
    """Response from LLM provider"""
    content: str
    usage: Optional[Dict[str, Any]] = None  # Changed to Any to support nested objects from OpenAI
    model: str
    provider: str
    latency_ms: int
    cost_usd: Optional[float] = None


class ProviderMetrics(BaseModel):
    """Metrics for LLM provider"""
    provider_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: int = 0
    total_cost_usd: float = 0.0
    accuracy_score: float = 0.0
    availability_pct: float = 100.0
    last_used: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100.0
    
    @property
    def avg_latency_ms(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency_ms / self.successful_requests
    
    @property
    def avg_cost_per_request(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_cost_usd / self.successful_requests


class ProviderRanking(BaseModel):
    """Provider ranking for optimization"""
    provider: str
    score: float
    factors: Dict[str, float]
    recommended_for: List[ComplexityLevel]


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerInfo(BaseModel):
    """Circuit breaker information"""
    provider: str
    state: CircuitBreakerState
    failure_count: int
    last_failure_time: Optional[datetime] = None
    next_attempt_time: Optional[datetime] = None


class CacheEntry(BaseModel):
    """Cache entry for LLM responses"""
    request_hash: str
    response: ProcessedData
    created_at: datetime
    ttl_seconds: int
    provider_used: str
    hit_count: int = 0


class ProviderConfig(BaseModel):
    """Configuration for LLM provider"""
    enabled: bool = True
    max_requests_per_minute: int = 60
    max_cost_per_day: float = 10.0
    timeout_seconds: int = 30
    retry_attempts: int = 3
    circuit_breaker_threshold: int = 3
    circuit_breaker_timeout: int = 300
    priority: int = 1  # Lower number = higher priority