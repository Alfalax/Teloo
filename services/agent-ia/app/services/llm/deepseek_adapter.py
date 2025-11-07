"""
Deepseek LLM adapter
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


class DeepseekAdapter(LLMAdapter):
    """Deepseek API adapter - optimized for simple text processing"""
    
    def __init__(self):
        super().__init__(
            name="deepseek",
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key
        )
        self.api_url = settings.deepseek_api_url
        self.cost_per_token = 0.00014  # Very low cost
        self.capabilities = [
            LLMCapability.TEXT_PROCESSING,
            LLMCapability.STRUCTURED_OUTPUT
        ]
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def process_text(self, request: LLMRequest) -> LLMResponse:
        """Process text with Deepseek"""
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
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.text}
                ],
                "max_tokens": request.max_tokens or 500,
                "temperature": request.temperature or 0.1,
                "response_format": {"type": "json_object"}
            }
            
            response = await self.client.post(
                f"{self.api_url}/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise ProviderError(f"Deepseek API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Extract response
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            
            # Calculate cost
            total_tokens = usage.get("total_tokens", 0)
            cost = total_tokens * self.cost_per_token
            
            return LLMResponse(
                content=content,
                usage=usage,
                model=self.model,
                provider=self.name,
                latency_ms=0,  # Will be set by base class
                cost_usd=cost
            )
            
        except httpx.TimeoutException:
            raise ProviderTimeoutError(f"Deepseek request timeout")
        except Exception as e:
            logger.error(f"Deepseek processing error: {e}")
            raise ProviderError(f"Deepseek error: {str(e)}")
    
    async def process_image(self, request: LLMRequest) -> LLMResponse:
        """Deepseek doesn't support image processing"""
        raise ProviderError("Deepseek does not support image processing")
    
    async def process_audio(self, request: LLMRequest) -> LLMResponse:
        """Deepseek doesn't support audio processing"""
        raise ProviderError("Deepseek does not support audio processing")
    
    async def process_document(self, request: LLMRequest) -> LLMResponse:
        """Deepseek doesn't support document processing"""
        raise ProviderError("Deepseek does not support document processing")
    
    def get_capabilities(self) -> List[LLMCapability]:
        """Get Deepseek capabilities"""
        return self.capabilities
    
    def get_cost_estimate(self, input_size: int) -> float:
        """Estimate cost based on input size"""
        # Rough estimation: 1 char ≈ 0.25 tokens
        estimated_tokens = input_size * 0.25
        return estimated_tokens * self.cost_per_token
    
    def is_available(self) -> bool:
        """Check if Deepseek is available"""
        return bool(self.api_key)
    
    def supports_complexity(self, complexity: ComplexityLevel) -> bool:
        """Deepseek is optimized for simple text"""
        return complexity in [ComplexityLevel.SIMPLE, ComplexityLevel.COMPLEX]
    
    def get_priority_for_complexity(self, complexity: ComplexityLevel) -> int:
        """Priority for different complexity levels"""
        if complexity == ComplexityLevel.SIMPLE:
            return 1  # Highest priority for simple text
        elif complexity == ComplexityLevel.COMPLEX:
            return 2  # Good for complex text
        else:
            return 10  # Low priority for structured/multimedia
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()