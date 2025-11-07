"""
OpenAI GPT-4 LLM adapter
"""

import httpx
import json
import logging
from typing import List, Optional
import base64

from app.core.config import settings
from app.models.llm import (
    LLMRequest, 
    LLMResponse, 
    LLMCapability,
    ComplexityLevel
)
from .base_adapter import LLMAdapter, ProviderError, ProviderTimeoutError

logger = logging.getLogger(__name__)


class OpenAIAdapter(LLMAdapter):
    """OpenAI GPT-4 adapter - excellent for structured documents"""
    
    def __init__(self):
        super().__init__(
            name="openai",
            model=settings.openai_model,
            api_key=settings.openai_api_key
        )
        self.api_url = "https://api.openai.com/v1"
        self.cost_per_token = 0.03  # High cost but high quality
        self.capabilities = [
            LLMCapability.TEXT_PROCESSING,
            LLMCapability.IMAGE_ANALYSIS,
            LLMCapability.DOCUMENT_EXTRACTION,
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
        """Process text with GPT-4"""
        try:
            system_prompt = """Eres un experto en repuestos automotrices con amplio conocimiento del mercado colombiano. Extrae información estructurada de mensajes complejos que pueden contener múltiples repuestos, especificaciones técnicas, y referencias cruzadas.

Extrae y devuelve SOLO un JSON válido con esta estructura:
{
  "repuestos": [
    {
      "nombre": "nombre del repuesto normalizado y específico",
      "codigo": "código de parte si se menciona",
      "cantidad": 1,
      "especificaciones": "especificaciones técnicas mencionadas"
    }
  ],
  "vehiculo": {
    "marca": "marca del vehículo",
    "linea": "línea/modelo específico",
    "anio": "año si se menciona",
    "motor": "especificaciones del motor si se mencionan"
  },
  "cliente": {
    "nombre": "nombre completo si se menciona",
    "telefono": "teléfono en formato +57XXXXXXXXXX",
    "ciudad": "ciudad normalizada"
  }
}

Normaliza y especifica repuestos:
- Identifica tipos específicos (pastillas delanteras/traseras, filtros de aceite/aire/combustible)
- Extrae códigos OEM, marcas específicas
- Identifica compatibilidades y especificaciones técnicas

Si no encuentras información, usa null. NO agregues explicaciones, solo el JSON."""

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.text}
                ],
                "max_tokens": request.max_tokens or 800,
                "temperature": request.temperature or 0.1,
                "response_format": {"type": "json_object"}
            }
            
            response = await self.client.post(
                f"{self.api_url}/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise ProviderError(f"OpenAI API error: {response.status_code} - {response.text}")
            
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
            raise ProviderTimeoutError(f"OpenAI request timeout")
        except Exception as e:
            logger.error(f"OpenAI processing error: {e}")
            raise ProviderError(f"OpenAI error: {str(e)}")
    
    async def process_image(self, request: LLMRequest) -> LLMResponse:
        """Process image with GPT-4 Vision"""
        try:
            system_prompt = """Analiza esta imagen relacionada con repuestos automotrices. Extrae toda la información visible incluyendo códigos de parte, especificaciones técnicas, marcas, y cualquier texto relevante.

Devuelve SOLO un JSON válido con esta estructura:
{
  "repuestos": [
    {
      "nombre": "nombre específico del repuesto",
      "codigo": "código de parte visible",
      "marca": "marca del repuesto",
      "especificaciones": "especificaciones técnicas visibles"
    }
  ],
  "texto_extraido": "todo el texto visible en la imagen",
  "vehiculo": {
    "marca": "marca del vehículo si es visible",
    "modelo": "modelo específico si es visible",
    "anio": "año si es visible"
  },
  "observaciones": "cualquier información adicional relevante"
}"""

            # Handle both data URLs and regular URLs
            image_url = request.image_url
            if not image_url.startswith("data:") and not image_url.startswith("http"):
                # Assume it's base64 data and format it properly
                image_url = f"data:image/jpeg;base64,{image_url}"

            payload = {
                "model": "gpt-4o",  # Use vision model
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analiza esta imagen de repuesto automotriz y extrae toda la información relevante:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            response = await self.client.post(
                f"{self.api_url}/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise ProviderError(f"OpenAI Vision API error: {response.status_code} - {response.text}")
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            
            cost = usage.get("total_tokens", 0) * self.cost_per_token
            
            return LLMResponse(
                content=content,
                usage=usage,
                model="gpt-4o",
                provider=self.name,
                latency_ms=0,
                cost_usd=cost
            )
            
        except Exception as e:
            logger.error(f"OpenAI image processing error: {e}")
            raise ProviderError(f"OpenAI image error: {str(e)}")
    
    async def process_audio(self, request: LLMRequest) -> LLMResponse:
        """Process audio with Whisper"""
        try:
            # This would use OpenAI's Whisper API for transcription
            # Then process the transcribed text for parts extraction
            
            # First transcribe audio
            transcription_payload = {
                "model": "whisper-1",
                "file": request.audio_url,  # This should be audio file data
                "language": "es"  # Spanish
            }
            
            # Note: This is a simplified version
            # In production, you'd need to handle file upload properly
            raise ProviderError("OpenAI audio processing not fully implemented yet")
            
        except Exception as e:
            logger.error(f"OpenAI audio processing error: {e}")
            raise ProviderError(f"OpenAI audio error: {str(e)}")
    
    async def process_document(self, request: LLMRequest) -> LLMResponse:
        """Process structured document (Excel, PDF) with GPT-4"""
        try:
            system_prompt = """Eres un experto en análisis de documentos de repuestos automotrices. Analiza este documento estructurado (Excel, CSV, etc.) y extrae información de repuestos, precios, especificaciones y compatibilidades.

Devuelve SOLO un JSON válido con esta estructura:
{
  "repuestos": [
    {
      "nombre": "nombre del repuesto",
      "codigo": "código de parte",
      "precio": "precio si está disponible",
      "cantidad": "cantidad disponible",
      "especificaciones": "especificaciones técnicas",
      "compatibilidad": "vehículos compatibles"
    }
  ],
  "estructura_documento": "descripción de la estructura del documento",
  "total_items": "número total de repuestos encontrados",
  "observaciones": "cualquier información adicional relevante"
}"""

            # For document processing, the document content would be provided as text
            # after being extracted by a document parser
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analiza este documento de repuestos:\n\n{request.text}"}
                ],
                "max_tokens": 2000,
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            
            response = await self.client.post(
                f"{self.api_url}/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise ProviderError(f"OpenAI document API error: {response.status_code} - {response.text}")
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            
            cost = usage.get("total_tokens", 0) * self.cost_per_token
            
            return LLMResponse(
                content=content,
                usage=usage,
                model=self.model,
                provider=self.name,
                latency_ms=0,
                cost_usd=cost
            )
            
        except Exception as e:
            logger.error(f"OpenAI document processing error: {e}")
            raise ProviderError(f"OpenAI document error: {str(e)}")
    
    def get_capabilities(self) -> List[LLMCapability]:
        """Get OpenAI capabilities"""
        return self.capabilities
    
    def get_cost_estimate(self, input_size: int) -> float:
        """Estimate cost based on input size"""
        estimated_tokens = input_size * 0.25
        return estimated_tokens * self.cost_per_token
    
    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        return bool(self.api_key)
    
    def supports_complexity(self, complexity: ComplexityLevel) -> bool:
        """OpenAI supports all complexity levels"""
        return True
    
    def get_priority_for_complexity(self, complexity: ComplexityLevel) -> int:
        """Priority for different complexity levels"""
        if complexity == ComplexityLevel.STRUCTURED:
            return 1  # Highest priority for structured documents
        elif complexity == ComplexityLevel.COMPLEX:
            return 2  # Very good for complex text
        elif complexity == ComplexityLevel.MULTIMEDIA:
            return 2  # Good for images with GPT-4V
        elif complexity == ComplexityLevel.SIMPLE:
            return 4  # Overkill for simple text but works well
        else:
            return 5
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()