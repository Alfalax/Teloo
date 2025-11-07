"""
Base LLM adapter interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import time
import logging

from app.models.llm import (
    LLMRequest, 
    LLMResponse, 
    ProcessedData, 
    LLMCapability,
    ComplexityLevel
)

logger = logging.getLogger(__name__)


class LLMAdapter(ABC):
    """Base class for LLM adapters"""
    
    def __init__(self, name: str, model: str, api_key: Optional[str] = None):
        self.name = name
        self.model = model
        self.api_key = api_key
        self.capabilities: List[LLMCapability] = []
        self.cost_per_token = 0.0
        self.max_tokens = 1000
        self.timeout = 30
    
    @abstractmethod
    async def process_text(self, request: LLMRequest) -> LLMResponse:
        """Process text content"""
        pass
    
    @abstractmethod
    async def process_image(self, request: LLMRequest) -> LLMResponse:
        """Process image content"""
        pass
    
    @abstractmethod
    async def process_audio(self, request: LLMRequest) -> LLMResponse:
        """Process audio content"""
        pass
    
    @abstractmethod
    async def process_document(self, request: LLMRequest) -> LLMResponse:
        """Process document content"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[LLMCapability]:
        """Get provider capabilities"""
        pass
    
    @abstractmethod
    def get_cost_estimate(self, input_size: int) -> float:
        """Estimate cost for input size"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass
    
    async def process_request(self, request: LLMRequest) -> LLMResponse:
        """Main processing method that routes to specific handlers"""
        start_time = time.time()
        
        try:
            # Route based on content type priority
            if request.image_url:
                if LLMCapability.IMAGE_ANALYSIS not in self.get_capabilities():
                    raise ValueError(f"Provider {self.name} does not support image analysis")
                response = await self.process_image(request)
            elif request.audio_url:
                if LLMCapability.AUDIO_TRANSCRIPTION not in self.get_capabilities():
                    raise ValueError(f"Provider {self.name} does not support audio transcription")
                response = await self.process_audio(request)
            elif request.document_url:
                if LLMCapability.DOCUMENT_EXTRACTION not in self.get_capabilities():
                    raise ValueError(f"Provider {self.name} does not support document extraction")
                response = await self.process_document(request)
            elif request.text:
                if LLMCapability.TEXT_PROCESSING not in self.get_capabilities():
                    raise ValueError(f"Provider {self.name} does not support text processing")
                response = await self.process_text(request)
            else:
                raise ValueError("No content provided in request")
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            response.latency_ms = latency_ms
            response.provider = self.name
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing request with {self.name}: {e}")
            raise
    
    def supports_complexity(self, complexity: ComplexityLevel) -> bool:
        """Check if provider supports complexity level"""
        # Default implementation - can be overridden
        return True
    
    def get_priority_for_complexity(self, complexity: ComplexityLevel) -> int:
        """Get priority score for complexity level (lower = better)"""
        # Default implementation - can be overridden
        return 5


class LLMError(Exception):
    """Base LLM error"""
    pass


class ProviderTimeoutError(LLMError):
    """Provider timeout error"""
    pass


class ProviderError(LLMError):
    """General provider error"""
    pass


class ProviderUnavailableError(LLMError):
    """Provider unavailable error"""
    pass