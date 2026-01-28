"""
Main LLM Provider Service that coordinates all providers
"""

import time
import json
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

from app.models.llm import (
    LLMRequest, 
    LLMResponse, 
    ProcessedData, 
    LLMProvider,
    ComplexityLevel,
    ProviderConfig
)
from app.core.config import settings
from .base_adapter import LLMAdapter, ProviderError, ProviderTimeoutError, ProviderUnavailableError
from .deepseek_adapter import DeepseekAdapter
from .ollama_adapter import OllamaAdapter
from .gemini_adapter import GeminiAdapter
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter
from .llm_router import llm_router
from .circuit_breaker import circuit_breaker_manager
from .metrics_collector import metrics_collector

logger = logging.getLogger(__name__)


class RegexProcessor:
    """Simple regex-based processor for fallback"""
    
    def __init__(self):
        import re
        
        # Common auto parts patterns
        self.parts_patterns = [
            (r'pastillas?\s+(?:de\s+)?freno', 'pastillas de freno'),
            (r'discos?\s+(?:de\s+)?freno', 'discos de freno'),
            (r'aceite\s+(?:de\s+)?motor', 'aceite de motor'),
            (r'filtros?\s+(?:de\s+)?aceite', 'filtro de aceite'),
            (r'filtros?\s+(?:de\s+)?aire', 'filtro de aire'),
            (r'amortiguadores?|plumas?', 'amortiguadores'),
            (r'cauchos?|llantas?|neumaticos?', 'llantas'),
            (r'baterias?', 'batería'),
            (r'bujias?', 'bujías'),
            (r'correas?', 'correa'),
            (r'empaques?|juntas?', 'empaque')
        ]
        
        # Vehicle patterns
        self.vehicle_patterns = [
            (r'(toyota|chevrolet|nissan|mazda|hyundai|kia|ford|volkswagen)\s+(\w+)\s+(\d{4})', 'vehicle'),
            (r'(\w+)\s+(\d{4})', 'vehicle_year')
        ]
        
        # Phone patterns
        self.phone_pattern = r'(\+?57\s?)?[3][0-9]{9}'
        
        # City patterns (major Colombian cities)
        self.cities = [
            'bogota', 'medellin', 'cali', 'barranquilla', 'cartagena',
            'cucuta', 'bucaramanga', 'pereira', 'ibague', 'santa marta',
            'villavicencio', 'manizales', 'neiva', 'soledad', 'armenia'
        ]
    
    def extract_parts(self, text: str) -> List[Dict[str, Any]]:
        """Extract auto parts using regex"""
        import re
        parts = []
        text_lower = text.lower()
        
        for pattern, normalized_name in self.parts_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                parts.append({
                    "nombre": normalized_name,
                    "codigo": None,
                    "cantidad": 1
                })
        
        return parts
    
    def extract_vehicle(self, text: str) -> Optional[Dict[str, str]]:
        """Extract vehicle info using regex"""
        import re
        text_lower = text.lower()
        
        for pattern, pattern_type in self.vehicle_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if pattern_type == 'vehicle':
                    return {
                        "marca": match.group(1).title(),
                        "linea": match.group(2).title(),
                        "anio": match.group(3)
                    }
                elif pattern_type == 'vehicle_year':
                    return {
                        "marca": "",
                        "linea": match.group(1).title(),
                        "anio": match.group(2)
                    }
        
        return None
    
    def extract_client(self, text: str) -> Optional[Dict[str, str]]:
        """Extract client info using regex"""
        import re
        client = {}
        
        # Extract phone
        phone_match = re.search(self.phone_pattern, text)
        if phone_match:
            phone = phone_match.group(0)
            if not phone.startswith('+57'):
                phone = '+57' + phone.replace(' ', '')
            client["telefono"] = phone
        
        # Extract city
        text_lower = text.lower()
        for city in self.cities:
            if city in text_lower:
                client["ciudad"] = city.title()
                break
        
        return client if client else None
    
    def process(self, text: str) -> ProcessedData:
        """Process text with regex patterns"""
        parts = self.extract_parts(text)
        vehicle = self.extract_vehicle(text)
        client = self.extract_client(text)
        
        return ProcessedData(
            repuestos=parts,
            vehiculo=vehicle,
            cliente=client,
            provider_used="regex",
            complexity_level="simple",
            confidence_score=0.6 if parts else 0.3,
            processing_time_ms=1,
            raw_text=text,
            is_complete=bool(parts and vehicle),
            missing_fields=[]
        )


class BasicProcessor:
    """Basic fallback processor"""
    
    def process(self, text: str) -> ProcessedData:
        """Basic processing - just return the text"""
        return ProcessedData(
            repuestos=[],
            vehiculo=None,
            cliente=None,
            provider_used="basic",
            complexity_level="simple",
            confidence_score=0.1,
            processing_time_ms=1,
            raw_text=text,
            is_complete=False,
            missing_fields=["repuestos", "vehiculo", "cliente"]
        )


class LLMProviderService:
    """Main service that coordinates all LLM providers"""
    
    def __init__(self):
        self.adapters: Dict[str, LLMAdapter] = {}
        self.regex_processor = RegexProcessor()
        self.basic_processor = BasicProcessor()
        self.provider_configs: Dict[str, ProviderConfig] = {}
        
        # Initialize adapters
        self._initialize_adapters()
        self._load_provider_configs()
    
    def _initialize_adapters(self):
        """Initialize all LLM adapters"""
        try:
            # Initialize adapters based on available API keys
            if settings.deepseek_api_key:
                self.adapters["deepseek"] = DeepseekAdapter()
                logger.info("Deepseek adapter initialized")
            
            if settings.local_llm_enabled:
                self.adapters["ollama"] = OllamaAdapter()
                logger.info("Ollama adapter initialized")
            
            if settings.gemini_api_key:
                self.adapters["gemini"] = GeminiAdapter()
                logger.info("Gemini adapter initialized")
            
            if settings.openai_api_key:
                self.adapters["openai"] = OpenAIAdapter()
                logger.info("OpenAI adapter initialized")
            
            if settings.anthropic_api_key:
                self.adapters["anthropic"] = AnthropicAdapter()
                logger.info("Anthropic adapter initialized")
            
            logger.info(f"Initialized {len(self.adapters)} LLM adapters")
            
        except Exception as e:
            logger.error(f"Error initializing adapters: {e}")
    
    def _load_provider_configs(self):
        """Load provider configurations"""
        # Default configurations
        default_config = ProviderConfig()
        
        for provider_name in self.adapters.keys():
            self.provider_configs[provider_name] = default_config
    
    async def process_content(
        self, 
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        document_url: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ProcessedData:
        """Main processing method"""
        start_time = time.time()
        
        try:
            # Create temporary request for complexity analysis
            temp_request = LLMRequest(
                text=text,
                image_url=image_url,
                audio_url=audio_url,
                document_url=document_url,
                complexity_level=ComplexityLevel.SIMPLE  # Temporary value
            )
            
            # Analyze complexity
            complexity = llm_router.analyze_request_complexity(temp_request)
            
            # Create final request with correct complexity
            request = LLMRequest(
                text=text,
                image_url=image_url,
                audio_url=audio_url,
                document_url=document_url,
                context=context or {},
                complexity_level=complexity
            )
            
            # Check cache first
            cached_response = await llm_router.get_cached_response(request)
            if cached_response:
                logger.info("Returning cached response")
                return cached_response
            
            # Get fallback chain
            fallback_chain = llm_router.get_fallback_chain(request.complexity_level)
            
            # Try each provider in the fallback chain
            last_error = None
            providers_tried = []
            
            logger.info(f"Processing request with complexity {complexity.value}, fallback chain: {[p.value for p in fallback_chain]}")
            
            for provider in fallback_chain:
                providers_tried.append(provider.value)
                
                try:
                    if provider == LLMProvider.REGEX:
                        if text:
                            logger.info("Falling back to regex processing")
                            result = self.regex_processor.process(text)
                            await llm_router.cache_response(request, result)
                            logger.info(f"Regex processing successful, confidence: {result.confidence_score:.2f}")
                            return result
                        continue
                    
                    if provider == LLMProvider.BASIC:
                        logger.warning("Falling back to basic processing (all other providers failed)")
                        result = self.basic_processor.process(text or "")
                        return result
                    
                    # Check if provider is available
                    if provider.value not in self.adapters:
                        logger.warning(f"Provider {provider.value} not configured/available")
                        continue
                    
                    # Check circuit breaker
                    circuit_breaker = circuit_breaker_manager.get_circuit_breaker(provider.value)
                    if not await circuit_breaker.is_available():
                        logger.warning(f"Circuit breaker OPEN for {provider.value}, skipping")
                        continue
                    
                    # Process with provider
                    logger.info(f"Attempting processing with {provider.value}")
                    result = await self._process_with_provider(provider.value, request)
                    
                    # Cache successful result
                    await llm_router.cache_response(request, result)
                    
                    logger.info(f"Successfully processed with {provider.value}, confidence: {result.confidence_score:.2f}")
                    return result
                    
                except (ProviderTimeoutError, ProviderUnavailableError) as e:
                    logger.warning(f"Provider {provider.value} unavailable, trying next: {e}")
                    last_error = e
                    continue
                except ProviderError as e:
                    logger.error(f"Provider {provider.value} error, trying next: {e}")
                    last_error = e
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error with provider {provider.value}, trying next: {e}")
                    last_error = e
                    continue
            
            # If all providers failed, return basic processing
            logger.error(
                f"All providers failed after trying: {providers_tried}. "
                f"Last error: {last_error}. Falling back to basic processing."
            )
            return self.basic_processor.process(text or "")
            
        except Exception as e:
            logger.error(f"Error in process_content: {e}")
            return self.basic_processor.process(text or "")
        finally:
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"Total processing time: {processing_time}ms")
    
    async def _process_with_provider(self, provider_name: str, request: LLMRequest) -> ProcessedData:
        """Process request with specific provider"""
        start_time = time.time()
        
        try:
            adapter = self.adapters[provider_name]
            circuit_breaker = circuit_breaker_manager.get_circuit_breaker(provider_name)
            
            # Process with circuit breaker protection
            llm_response = await circuit_breaker.call_with_circuit_breaker(
                adapter.process_request, request
            )
            
            # Parse LLM response to ProcessedData
            processed_data = self._parse_llm_response(llm_response, request.complexity_level)
            
            # Record metrics
            processing_time = int((time.time() - start_time) * 1000)
            await metrics_collector.record_request(
                provider=provider_name,
                complexity=request.complexity_level,
                latency_ms=processing_time,
                cost_usd=llm_response.cost_usd or 0.0,
                success=True,
                accuracy_score=processed_data.confidence_score * 100
            )
            
            return processed_data
            
        except Exception as e:
            # Record failed request
            processing_time = int((time.time() - start_time) * 1000)
            await metrics_collector.record_request(
                provider=provider_name,
                complexity=request.complexity_level,
                latency_ms=processing_time,
                cost_usd=0.0,
                success=False
            )
            raise e
    
    def _parse_llm_response(self, llm_response: LLMResponse, complexity: ComplexityLevel) -> ProcessedData:
        """Parse LLM response to ProcessedData"""
        try:
            # Try to parse JSON response
            content = llm_response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            data = json.loads(content)
            
            # Extract and sanitize structured data
            repuestos = data.get("repuestos", [])
            vehiculo = data.get("vehiculo")
            cliente = data.get("cliente")
            
            # Sanitizar diccionarios para evitar errores de validación de Pydantic (null -> "")
            if isinstance(vehiculo, dict):
                vehiculo = {k: str(v) if v is not None else "" for k, v in vehiculo.items()}
            elif vehiculo is None:
                vehiculo = {}
                
            if isinstance(cliente, dict):
                cliente = {k: str(v) if v is not None else "" for k, v in cliente.items()}
            elif cliente is None:
                cliente = {}
            
            # Ensure repuestos is a list and sanitize each repuesto
            if not isinstance(repuestos, list):
                repuestos = []
            
            # Calculate completeness
            is_complete = bool(repuestos and vehiculo and vehiculo.get("marca"))
            missing_fields = []
            if not repuestos:
                missing_fields.append("repuestos")
            if not vehiculo or not vehiculo.get("marca"):
                missing_fields.append("vehiculo")
            if not cliente or not cliente.get("telefono"):
                missing_fields.append("cliente")
            
            # Calculate confidence based on completeness and provider
            confidence_score = 0.5
            if is_complete:
                confidence_score = 0.9
            elif repuestos or (vehiculo and vehiculo.get("marca")):
                confidence_score = 0.7
            
            # Adjust confidence based on provider quality
            provider_confidence_multiplier = {
                "anthropic": 1.0,
                "openai": 0.95,
                "gemini": 0.9,
                "deepseek": 0.8,
                "ollama": 0.7
            }
            confidence_score *= provider_confidence_multiplier.get(llm_response.provider, 0.8)
            
            return ProcessedData(
                repuestos=repuestos,
                vehiculo=vehiculo,
                cliente=cliente,
                provider_used=llm_response.provider,
                complexity_level=complexity.value,
                confidence_score=confidence_score,
                processing_time_ms=llm_response.latency_ms,
                raw_text=content,
                extracted_entities=data,
                is_complete=is_complete,
                missing_fields=missing_fields
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from {llm_response.provider}: {e}")
            logger.error(f"Response content: {llm_response.content}")
            
            # Return basic processed data with raw content
            return ProcessedData(
                repuestos=[],
                vehiculo=None,
                cliente=None,
                provider_used=llm_response.provider,
                complexity_level=complexity.value,
                confidence_score=0.2,
                processing_time_ms=llm_response.latency_ms,
                raw_text=llm_response.content,
                is_complete=False,
                missing_fields=["repuestos", "vehiculo", "cliente"]
            )
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            raise ProviderError(f"Failed to parse response: {str(e)}")
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {
            "available_providers": list(self.adapters.keys()),
            "circuit_breakers": await circuit_breaker_manager.get_all_states(),
            "metrics": await metrics_collector.get_all_provider_metrics(),
            "routing_stats": await llm_router.get_routing_stats()
        }
        
        return status
    
    async def optimize_routing(self):
        """Optimize provider routing based on performance"""
        await llm_router.optimize_provider_selection()
        logger.info("Provider routing optimized")
    
    async def close(self):
        """Close all adapters"""
        for adapter in self.adapters.values():
            if hasattr(adapter, 'close'):
                await adapter.close()
        logger.info("All LLM adapters closed")


# Global LLM provider service instance
llm_provider_service = LLMProviderService()