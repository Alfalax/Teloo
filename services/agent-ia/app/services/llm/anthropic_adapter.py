"""
Anthropic Claude LLM adapter
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


class AnthropicAdapter(LLMAdapter):
    """Anthropic Claude adapter - premium for multimedia content"""
    
    def __init__(self):
        super().__init__(
            name="anthropic",
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key
        )
        self.api_url = "https://api.anthropic.com/v1"
        self.cost_per_token = 0.015  # Premium cost
        self.capabilities = [
            LLMCapability.TEXT_PROCESSING,
            LLMCapability.IMAGE_ANALYSIS,
            LLMCapability.AUDIO_TRANSCRIPTION,
            LLMCapability.DOCUMENT_EXTRACTION,
            LLMCapability.STRUCTURED_OUTPUT
        ]
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        )
    
    async def process_text(self, request: LLMRequest) -> LLMResponse:
        """Process text with Claude"""
        try:
            system_prompt = """Eres un experto en repuestos automotrices con conocimiento especializado del mercado colombiano. Procesa mensajes complejos que pueden incluir múltiples repuestos, jerga técnica, abreviaciones, y referencias cruzadas.

Extrae y devuelve SOLO un JSON válido con esta estructura:
{
  "repuestos": [
    {
      "nombre": "nombre del repuesto normalizado y específico",
      "codigo": "código de parte si se menciona",
      "cantidad": 1,
      "especificaciones": "especificaciones técnicas detalladas",
      "marca_preferida": "marca específica si se menciona"
    }
  ],
  "vehiculo": {
    "marca": "marca del vehículo",
    "linea": "línea/modelo específico",
    "anio": "año si se menciona",
    "motor": "especificaciones del motor",
    "transmision": "tipo de transmisión si se menciona"
  },
  "cliente": {
    "nombre": "nombre completo si se menciona",
    "telefono": "teléfono en formato +57XXXXXXXXXX",
    "ciudad": "ciudad normalizada",
    "preferencias": "preferencias específicas mencionadas"
  },
  "contexto": {
    "urgencia": "nivel de urgencia expresado",
    "presupuesto": "rango de presupuesto si se menciona",
    "uso_vehiculo": "uso del vehículo si se menciona"
  }
}

Maneja jerga colombiana y técnica:
- "Cauchos" = llantas/neumáticos
- "Plumas" = amortiguadores
- "Empaque" = junta/sello
- Identifica marcas locales vs importadas

Si no encuentras información, usa null. NO agregues explicaciones, solo el JSON."""

            payload = {
                "model": self.model,
                "max_tokens": request.max_tokens or 1000,
                "temperature": request.temperature or 0.1,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": request.text
                    }
                ]
            }
            
            response = await self.client.post(
                f"{self.api_url}/messages",
                json=payload
            )
            
            if response.status_code != 200:
                raise ProviderError(f"Anthropic API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Extract response
            content = data["content"][0]["text"]
            usage = data.get("usage", {})
            
            # Calculate cost
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            cost = total_tokens * self.cost_per_token
            
            # Convert to OpenAI-style usage format
            usage_formatted = {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": total_tokens
            }
            
            return LLMResponse(
                content=content,
                usage=usage_formatted,
                model=self.model,
                provider=self.name,
                latency_ms=0,  # Will be set by base class
                cost_usd=cost
            )
            
        except httpx.TimeoutException:
            raise ProviderTimeoutError(f"Anthropic request timeout")
        except Exception as e:
            logger.error(f"Anthropic processing error: {e}")
            raise ProviderError(f"Anthropic error: {str(e)}")
    
    async def process_image(self, request: LLMRequest) -> LLMResponse:
        """Process image with Claude Vision"""
        try:
            system_prompt = """Analiza esta imagen relacionada con repuestos automotrices con máximo detalle. Extrae toda la información visible incluyendo códigos de parte, especificaciones técnicas, marcas, números de serie, y cualquier texto o símbolo relevante.

Devuelve SOLO un JSON válido con esta estructura:
{
  "repuestos": [
    {
      "nombre": "nombre específico y detallado del repuesto",
      "codigo": "código de parte visible",
      "marca": "marca del repuesto",
      "numero_serie": "número de serie si es visible",
      "especificaciones": "todas las especificaciones técnicas visibles",
      "condicion": "nuevo/usado/remanufacturado si es determinable"
    }
  ],
  "texto_extraido": "todo el texto visible en la imagen, incluyendo números pequeños",
  "vehiculo": {
    "marca": "marca del vehículo si es visible",
    "modelo": "modelo específico si es visible",
    "anio": "año si es visible",
    "motor": "especificaciones del motor si son visibles"
  },
  "calidad_imagen": "evaluación de la calidad y claridad de la imagen",
  "observaciones": "cualquier información adicional relevante o recomendaciones"
}"""

            # Extract base64 data from data URL if needed
            image_data = request.image_url
            if image_data.startswith("data:image/"):
                # Extract base64 part from data URL
                image_data = image_data.split(",", 1)[1]
            
            # Prepare image content
            payload = {
                "model": self.model,
                "max_tokens": 1500,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analiza esta imagen de repuesto automotriz con máximo detalle:"
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = await self.client.post(
                f"{self.api_url}/messages",
                json=payload
            )
            
            if response.status_code != 200:
                raise ProviderError(f"Anthropic Vision API error: {response.status_code} - {response.text}")
            
            data = response.json()
            content = data["content"][0]["text"]
            usage = data.get("usage", {})
            
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            cost = total_tokens * self.cost_per_token
            
            usage_formatted = {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": total_tokens
            }
            
            return LLMResponse(
                content=content,
                usage=usage_formatted,
                model=self.model,
                provider=self.name,
                latency_ms=0,
                cost_usd=cost
            )
            
        except Exception as e:
            logger.error(f"Anthropic image processing error: {e}")
            raise ProviderError(f"Anthropic image error: {str(e)}")
    
    async def process_audio(self, request: LLMRequest) -> LLMResponse:
        """Process audio with Claude (transcription + analysis)"""
        try:
            # Note: Claude doesn't directly process audio, but we can simulate
            # the workflow where audio is first transcribed and then analyzed
            
            system_prompt = """Analiza esta transcripción de audio de un cliente solicitando repuestos automotrices. El audio puede tener ruido de fondo, interrupciones, y pronunciación no clara.

Extrae y devuelve SOLO un JSON válido con esta estructura:
{
  "repuestos": [
    {
      "nombre": "nombre del repuesto interpretado",
      "codigo": "código si se menciona",
      "cantidad": 1,
      "confianza": "nivel de confianza en la interpretación (alto/medio/bajo)"
    }
  ],
  "vehiculo": {
    "marca": "marca del vehículo",
    "modelo": "modelo si se entiende",
    "anio": "año si se menciona"
  },
  "cliente": {
    "nombre": "nombre si se menciona",
    "telefono": "teléfono si se menciona",
    "ciudad": "ciudad si se menciona"
  },
  "calidad_audio": "evaluación de la calidad del audio",
  "incertidumbres": ["lista de partes que no se entendieron claramente"],
  "recomendaciones": "preguntas de clarificación recomendadas"
}"""

            # In a real implementation, you'd first transcribe the audio
            # For now, we'll assume the audio URL contains transcribed text
            payload = {
                "model": self.model,
                "max_tokens": 1000,
                "temperature": 0.2,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analiza esta transcripción de audio: {request.text or 'Audio transcription would go here'}"
                    }
                ]
            }
            
            response = await self.client.post(
                f"{self.api_url}/messages",
                json=payload
            )
            
            if response.status_code != 200:
                raise ProviderError(f"Anthropic audio API error: {response.status_code} - {response.text}")
            
            data = response.json()
            content = data["content"][0]["text"]
            usage = data.get("usage", {})
            
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            cost = total_tokens * self.cost_per_token
            
            usage_formatted = {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": total_tokens
            }
            
            return LLMResponse(
                content=content,
                usage=usage_formatted,
                model=self.model,
                provider=self.name,
                latency_ms=0,
                cost_usd=cost
            )
            
        except Exception as e:
            logger.error(f"Anthropic audio processing error: {e}")
            raise ProviderError(f"Anthropic audio error: {str(e)}")
    
    async def process_document(self, request: LLMRequest) -> LLMResponse:
        """Process structured document with Claude"""
        try:
            system_prompt = """Analiza este documento estructurado de repuestos automotrices (Excel, CSV, PDF, etc.) con máximo detalle. Extrae información de inventario, precios, especificaciones, compatibilidades y cualquier dato relevante.

Devuelve SOLO un JSON válido con esta estructura:
{
  "repuestos": [
    {
      "nombre": "nombre completo del repuesto",
      "codigo": "código de parte",
      "precio": "precio con moneda",
      "cantidad_disponible": "stock disponible",
      "especificaciones": "especificaciones técnicas completas",
      "compatibilidad": "vehículos compatibles",
      "marca": "marca del repuesto",
      "proveedor": "proveedor si se menciona"
    }
  ],
  "estructura_documento": "descripción detallada de la estructura",
  "metadatos": {
    "total_items": "número total de repuestos",
    "categorias": ["categorías de repuestos encontradas"],
    "rango_precios": "rango de precios encontrado",
    "marcas": ["marcas encontradas"]
  },
  "calidad_datos": "evaluación de la completitud y calidad de los datos",
  "observaciones": "información adicional relevante o problemas encontrados"
}"""

            payload = {
                "model": self.model,
                "max_tokens": 2000,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analiza este documento de repuestos automotrices:\n\n{request.text}"
                    }
                ]
            }
            
            response = await self.client.post(
                f"{self.api_url}/messages",
                json=payload
            )
            
            if response.status_code != 200:
                raise ProviderError(f"Anthropic document API error: {response.status_code} - {response.text}")
            
            data = response.json()
            content = data["content"][0]["text"]
            usage = data.get("usage", {})
            
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            cost = total_tokens * self.cost_per_token
            
            usage_formatted = {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": total_tokens
            }
            
            return LLMResponse(
                content=content,
                usage=usage_formatted,
                model=self.model,
                provider=self.name,
                latency_ms=0,
                cost_usd=cost
            )
            
        except Exception as e:
            logger.error(f"Anthropic document processing error: {e}")
            raise ProviderError(f"Anthropic document error: {str(e)}")
    
    def get_capabilities(self) -> List[LLMCapability]:
        """Get Anthropic capabilities"""
        return self.capabilities
    
    def get_cost_estimate(self, input_size: int) -> float:
        """Estimate cost based on input size"""
        estimated_tokens = input_size * 0.25
        return estimated_tokens * self.cost_per_token
    
    def is_available(self) -> bool:
        """Check if Anthropic is available"""
        return bool(self.api_key)
    
    def supports_complexity(self, complexity: ComplexityLevel) -> bool:
        """Anthropic supports all complexity levels"""
        return True
    
    def get_priority_for_complexity(self, complexity: ComplexityLevel) -> int:
        """Priority for different complexity levels"""
        if complexity == ComplexityLevel.MULTIMEDIA:
            return 1  # Highest priority for multimedia content
        elif complexity == ComplexityLevel.STRUCTURED:
            return 2  # Very good for structured documents
        elif complexity == ComplexityLevel.COMPLEX:
            return 3  # Good for complex text
        elif complexity == ComplexityLevel.SIMPLE:
            return 5  # Expensive for simple text
        else:
            return 5
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()