"""
Ollama local LLM adapter
"""

import httpx
import json
import logging
from typing import List, Optional

from app.core.config import settings
from app.models.llm import (
    LLMRequest, 
    LLMResponse, 
    LLMCapability,
    ComplexityLevel
)
from .base_adapter import LLMAdapter, ProviderError, ProviderTimeoutError

logger = logging.getLogger(__name__)


class OllamaAdapter(LLMAdapter):
    """Ollama local LLM adapter - free but requires local setup"""
    
    def __init__(self):
        super().__init__(
            name="ollama",
            model=settings.local_llm_model,
            api_key=None  # No API key needed for local
        )
        self.api_url = settings.local_llm_url
        self.cost_per_token = 0.0  # Free
        self.capabilities = [
            LLMCapability.TEXT_PROCESSING,
            LLMCapability.STRUCTURED_OUTPUT
        ]
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout)
        )
    
    async def process_text(self, request: LLMRequest) -> LLMResponse:
        """Process text with Ollama"""
        try:
            # Prepare system prompt for auto parts extraction
            system_prompt = """Eres un experto en repuestos automotrices. Extrae información estructurada de mensajes de WhatsApp.

Extrae y devuelve SOLO un JSON válido con esta estructura:
{
  "repuestos": [
    {
      "nombre": "nombre del repuesto",
      "codigo": "código si se menciona",
      "cantidad": 1
    }
  ],
  "vehiculo": {
    "marca": "marca del vehículo",
    "linea": "línea/modelo",
    "anio": "año si se menciona"
  },
  "cliente": {
    "nombre": "nombre si se menciona",
    "telefono": "teléfono si se menciona",
    "ciudad": "ciudad si se menciona"
  }
}

Si no encuentras información, usa null. NO agregues explicaciones, solo el JSON."""

            payload = {
                "model": self.model,
                "prompt": f"System: {system_prompt}\n\nUser: {request.text}\n\nAssistant:",
                "stream": False,
                "options": {
                    "temperature": request.temperature or 0.1,
                    "num_predict": request.max_tokens or 500
                }
            }
            
            response = await self.client.post(
                f"{self.api_url}/api/generate",
                json=payload
            )
            
            if response.status_code != 200:
                raise ProviderError(f"Ollama API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Extract response
            content = data.get("response", "")
            
            # Ollama doesn't provide detailed usage stats
            usage = {
                "prompt_tokens": len(request.text.split()) * 1.3,  # Rough estimate
                "completion_tokens": len(content.split()) * 1.3,
                "total_tokens": 0
            }
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            
            return LLMResponse(
                content=content,
                usage=usage,
                model=self.model,
                provider=self.name,
                latency_ms=0,  # Will be set by base class
                cost_usd=0.0  # Free
            )
            
        except httpx.TimeoutException:
            raise ProviderTimeoutError(f"Ollama request timeout")
        except httpx.ConnectError:
            raise ProviderError("Ollama server not available. Make sure Ollama is running locally.")
        except Exception as e:
            logger.error(f"Ollama processing error: {e}")
            raise ProviderError(f"Ollama error: {str(e)}")
    
    async def process_image(self, request: LLMRequest) -> LLMResponse:
        """Ollama doesn't support image processing by default"""
        raise ProviderError("Ollama does not support image processing")
    
    async def process_audio(self, request: LLMRequest) -> LLMResponse:
        """Ollama doesn't support audio processing"""
        raise ProviderError("Ollama does not support audio processing")
    
    async def process_document(self, request: LLMRequest) -> LLMResponse:
        """Ollama doesn't support document processing"""
        raise ProviderError("Ollama does not support document processing")
    
    def get_capabilities(self) -> List[LLMCapability]:
        """Get Ollama capabilities"""
        return self.capabilities
    
    def get_cost_estimate(self, input_size: int) -> float:
        """Ollama is free"""
        return 0.0
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        return settings.local_llm_enabled
    
    async def health_check(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = await self.client.get(f"{self.api_url}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    def supports_complexity(self, complexity: ComplexityLevel) -> bool:
        """Ollama is good for simple text"""
        return complexity in [ComplexityLevel.SIMPLE]
    
    def get_priority_for_complexity(self, complexity: ComplexityLevel) -> int:
        """Priority for different complexity levels"""
        if complexity == ComplexityLevel.SIMPLE:
            return 2  # Good fallback for simple text (after Deepseek)
        else:
            return 10  # Low priority for complex content
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()