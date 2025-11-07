"""
Google Gemini LLM adapter
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


class GeminiAdapter(LLMAdapter):
    """Google Gemini adapter - good for complex text processing"""
    
    def __init__(self):
        super().__init__(
            name="gemini",
            model=settings.gemini_model,
            api_key=settings.gemini_api_key
        )
        self.api_url = "https://generativelanguage.googleapis.com/v1beta"
        self.cost_per_token = 0.00125  # Medium cost
        self.capabilities = [
            LLMCapability.TEXT_PROCESSING,
            LLMCapability.IMAGE_ANALYSIS,
            LLMCapability.STRUCTURED_OUTPUT
        ]
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout)
        )
    
    async def process_text(self, request: LLMRequest) -> LLMResponse:
        """Process text with Gemini"""
        try:
            # Prepare system prompt for auto parts extraction
            system_instruction = """Eres un experto en repuestos automotrices colombiano. Extrae información estructurada de mensajes de WhatsApp que pueden contener jerga, abreviaciones y múltiples repuestos.

Extrae y devuelve SOLO un JSON válido con esta estructura:
{
  "repuestos": [
    {
      "nombre": "nombre del repuesto normalizado",
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

Normaliza términos comunes:
- "pastillas" = pastillas de freno
- "discos" = discos de freno
- "aceite" = aceite de motor
- "filtro" = filtro de aceite (especifica tipo si es claro)

Si no encuentras información, usa null. NO agregues explicaciones, solo el JSON."""

            payload = {
                "system_instruction": {
                    "parts": [{"text": system_instruction}]
                },
                "contents": [
                    {
                        "parts": [{"text": request.text}]
                    }
                ],
                "generationConfig": {
                    "temperature": request.temperature or 0.2,
                    "maxOutputTokens": request.max_tokens or 500,
                    "responseMimeType": "application/json"
                }
            }
            
            url = f"{self.api_url}/models/{self.model}:generateContent"
            params = {"key": self.api_key}
            
            response = await self.client.post(
                url,
                json=payload,
                params=params
            )
            
            if response.status_code != 200:
                raise ProviderError(f"Gemini API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Extract response
            if "candidates" not in data or not data["candidates"]:
                raise ProviderError("No response from Gemini")
            
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Extract usage info
            usage_metadata = data.get("usageMetadata", {})
            usage = {
                "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                "total_tokens": usage_metadata.get("totalTokenCount", 0)
            }
            
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
            raise ProviderTimeoutError(f"Gemini request timeout")
        except Exception as e:
            logger.error(f"Gemini processing error: {e}")
            raise ProviderError(f"Gemini error: {str(e)}")
    
    async def process_image(self, request: LLMRequest) -> LLMResponse:
        """Process image with Gemini Vision"""
        try:
            system_instruction = """Analiza esta imagen relacionada con repuestos automotrices. Extrae toda la información visible sobre repuestos, códigos de parte, especificaciones, y cualquier texto relevante.

Devuelve SOLO un JSON válido con esta estructura:
{
  "repuestos": [
    {
      "nombre": "nombre del repuesto identificado",
      "codigo": "código de parte visible",
      "especificaciones": "especificaciones técnicas visibles"
    }
  ],
  "texto_extraido": "todo el texto visible en la imagen",
  "vehiculo": {
    "marca": "marca si es visible",
    "modelo": "modelo si es visible",
    "anio": "año si es visible"
  }
}"""

            # For image processing, we need to get the image data
            # This is a simplified version - in production you'd download the image
            payload = {
                "system_instruction": {
                    "parts": [{"text": system_instruction}]
                },
                "contents": [
                    {
                        "parts": [
                            {"text": "Analiza esta imagen de repuesto automotriz:"},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": request.image_url  # This should be base64 data
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 1000,
                    "responseMimeType": "application/json"
                }
            }
            
            url = f"{self.api_url}/models/gemini-1.5-pro-vision:generateContent"
            params = {"key": self.api_key}
            
            response = await self.client.post(
                url,
                json=payload,
                params=params
            )
            
            if response.status_code != 200:
                raise ProviderError(f"Gemini Vision API error: {response.status_code} - {response.text}")
            
            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            
            usage_metadata = data.get("usageMetadata", {})
            usage = {
                "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                "total_tokens": usage_metadata.get("totalTokenCount", 0)
            }
            
            cost = usage.get("total_tokens", 0) * self.cost_per_token
            
            return LLMResponse(
                content=content,
                usage=usage,
                model="gemini-1.5-pro-vision",
                provider=self.name,
                latency_ms=0,
                cost_usd=cost
            )
            
        except Exception as e:
            logger.error(f"Gemini image processing error: {e}")
            raise ProviderError(f"Gemini image error: {str(e)}")
    
    async def process_audio(self, request: LLMRequest) -> LLMResponse:
        """Gemini doesn't support audio processing directly"""
        raise ProviderError("Gemini does not support audio processing")
    
    async def process_document(self, request: LLMRequest) -> LLMResponse:
        """Process document with Gemini"""
        # This would be similar to text processing but with document-specific prompts
        raise ProviderError("Gemini document processing not implemented yet")
    
    def get_capabilities(self) -> List[LLMCapability]:
        """Get Gemini capabilities"""
        return self.capabilities
    
    def get_cost_estimate(self, input_size: int) -> float:
        """Estimate cost based on input size"""
        estimated_tokens = input_size * 0.25
        return estimated_tokens * self.cost_per_token
    
    def is_available(self) -> bool:
        """Check if Gemini is available"""
        return bool(self.api_key)
    
    def supports_complexity(self, complexity: ComplexityLevel) -> bool:
        """Gemini supports complex text and some multimedia"""
        return complexity in [
            ComplexityLevel.SIMPLE, 
            ComplexityLevel.COMPLEX, 
            ComplexityLevel.MULTIMEDIA
        ]
    
    def get_priority_for_complexity(self, complexity: ComplexityLevel) -> int:
        """Priority for different complexity levels"""
        if complexity == ComplexityLevel.COMPLEX:
            return 1  # Highest priority for complex text
        elif complexity == ComplexityLevel.MULTIMEDIA:
            return 2  # Good for images
        elif complexity == ComplexityLevel.SIMPLE:
            return 3  # Decent for simple text
        else:
            return 8  # Lower priority for structured documents
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()