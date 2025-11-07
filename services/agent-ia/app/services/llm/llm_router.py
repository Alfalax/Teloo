"""
LLM Router for automatic provider selection
"""

import logging
import hashlib
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from app.models.llm import (
    ComplexityLevel, 
    LLMProvider, 
    LLMRequest, 
    ProcessedData,
    CacheEntry
)
from app.core.redis import redis_manager
from app.core.config import settings
from .circuit_breaker import circuit_breaker_manager
from .metrics_collector import metrics_collector

logger = logging.getLogger(__name__)


class ComplexityAnalyzer:
    """Analyze content complexity to determine appropriate LLM provider"""
    
    def __init__(self):
        self.simple_indicators = [
            # Short messages
            lambda text: len(text.split()) < 20,
            # Common patterns
            lambda text: any(pattern in text.lower() for pattern in [
                "necesito", "quiero", "busco", "precio", "cuanto cuesta"
            ]),
            # Single part requests
            lambda text: text.count(',') < 2 and text.count('y') < 2
        ]
        
        self.complex_indicators = [
            # Long messages
            lambda text: len(text.split()) > 50,
            # Multiple parts
            lambda text: text.count(',') > 3 or text.count('y') > 3,
            # Technical terms
            lambda text: any(term in text.lower() for term in [
                "especificacion", "codigo", "oem", "compatible", "motor", "transmision"
            ]),
            # Colombian slang
            lambda text: any(slang in text.lower() for slang in [
                "cauchos", "plumas", "empaque", "muelleo"
            ])
        ]
        
        self.structured_indicators = [
            # File extensions or structured data mentions
            lambda text: any(ext in text.lower() for ext in [
                ".xlsx", ".csv", ".pdf", "excel", "tabla", "lista"
            ]),
            # Structured data patterns
            lambda text: text.count('\n') > 5 or text.count('\t') > 3
        ]
    
    def analyze_text_complexity(self, text: str) -> ComplexityLevel:
        """Analyze text complexity"""
        if not text:
            return ComplexityLevel.SIMPLE
        
        # Check for structured data indicators
        structured_score = sum(1 for indicator in self.structured_indicators if indicator(text))
        if structured_score > 0:
            return ComplexityLevel.STRUCTURED
        
        # Check for complex indicators
        complex_score = sum(1 for indicator in self.complex_indicators if indicator(text))
        simple_score = sum(1 for indicator in self.simple_indicators if indicator(text))
        
        if complex_score > simple_score:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.SIMPLE
    
    def analyze_content_complexity(
        self, 
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        document_url: Optional[str] = None
    ) -> ComplexityLevel:
        """Analyze overall content complexity"""
        
        # Multimedia content
        if image_url or audio_url:
            return ComplexityLevel.MULTIMEDIA
        
        # Document content
        if document_url:
            return ComplexityLevel.STRUCTURED
        
        # Text content
        if text:
            return self.analyze_text_complexity(text)
        
        return ComplexityLevel.SIMPLE


class LLMRouter:
    """Route requests to appropriate LLM providers based on complexity and performance"""
    
    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.cache_ttl = settings.cache_ttl_hours * 3600
        
        # Provider priority matrix by complexity
        self.provider_matrix = {
            ComplexityLevel.SIMPLE: [
                LLMProvider.DEEPSEEK,
                LLMProvider.OLLAMA,
                LLMProvider.GEMINI,
                LLMProvider.OPENAI,
                LLMProvider.ANTHROPIC
            ],
            ComplexityLevel.COMPLEX: [
                LLMProvider.GEMINI,
                LLMProvider.DEEPSEEK,
                LLMProvider.OPENAI,
                LLMProvider.ANTHROPIC,
                LLMProvider.OLLAMA
            ],
            ComplexityLevel.STRUCTURED: [
                LLMProvider.OPENAI,
                LLMProvider.GEMINI,
                LLMProvider.ANTHROPIC,
                LLMProvider.DEEPSEEK
            ],
            ComplexityLevel.MULTIMEDIA: [
                LLMProvider.ANTHROPIC,
                LLMProvider.OPENAI,
                LLMProvider.GEMINI
            ]
        }
    
    def analyze_request_complexity(self, request: LLMRequest) -> ComplexityLevel:
        """Analyze request complexity"""
        return self.complexity_analyzer.analyze_content_complexity(
            text=request.text,
            image_url=request.image_url,
            audio_url=request.audio_url,
            document_url=request.document_url
        )
    
    def get_fallback_chain(self, complexity: ComplexityLevel) -> List[LLMProvider]:
        """Get fallback chain for complexity level"""
        base_chain = self.provider_matrix.get(complexity, [LLMProvider.DEEPSEEK])
        
        # Always add regex and basic as final fallbacks
        fallback_chain = base_chain + [LLMProvider.REGEX, LLMProvider.BASIC]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_chain = []
        for provider in fallback_chain:
            if provider not in seen:
                seen.add(provider)
                unique_chain.append(provider)
        
        return unique_chain
    
    async def get_best_provider(
        self, 
        complexity: ComplexityLevel,
        exclude_providers: Optional[List[LLMProvider]] = None
    ) -> Optional[LLMProvider]:
        """Get best available provider for complexity level"""
        exclude_providers = exclude_providers or []
        fallback_chain = self.get_fallback_chain(complexity)
        
        for provider in fallback_chain:
            if provider in exclude_providers:
                continue
            
            # Skip regex and basic for now (handled separately)
            if provider in [LLMProvider.REGEX, LLMProvider.BASIC]:
                continue
            
            # Check circuit breaker
            circuit_breaker = circuit_breaker_manager.get_circuit_breaker(provider.value)
            if await circuit_breaker.is_available():
                return provider
        
        return None
    
    def generate_cache_key(self, request: LLMRequest) -> str:
        """Generate cache key for request"""
        # Create hash of request content
        content_parts = []
        if request.text:
            content_parts.append(f"text:{request.text}")
        if request.image_url:
            content_parts.append(f"image:{request.image_url}")
        if request.audio_url:
            content_parts.append(f"audio:{request.audio_url}")
        if request.document_url:
            content_parts.append(f"document:{request.document_url}")
        
        content_str = "|".join(content_parts)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]
        
        return f"llm_cache:{content_hash}"
    
    async def get_cached_response(self, request: LLMRequest) -> Optional[ProcessedData]:
        """Get cached response if available"""
        try:
            cache_key = self.generate_cache_key(request)
            cached_data = await redis_manager.get(cache_key)
            
            if cached_data:
                cache_entry = CacheEntry(**json.loads(cached_data))
                
                # Update hit count
                cache_entry.hit_count += 1
                await redis_manager.set(
                    cache_key,
                    cache_entry.model_dump_json(),
                    ttl=self.cache_ttl
                )
                
                logger.info(f"Cache hit for request (hits: {cache_entry.hit_count})")
                return cache_entry.response
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            return None
    
    async def cache_response(self, request: LLMRequest, response: ProcessedData):
        """Cache response"""
        try:
            cache_key = self.generate_cache_key(request)
            
            cache_entry = CacheEntry(
                request_hash=cache_key,
                response=response,
                created_at=datetime.now(),
                ttl_seconds=self.cache_ttl,
                provider_used=response.provider_used,
                hit_count=0
            )
            
            await redis_manager.set(
                cache_key,
                cache_entry.model_dump_json(),
                ttl=self.cache_ttl
            )
            
            logger.info(f"Cached response from {response.provider_used}")
            
        except Exception as e:
            logger.error(f"Error caching response: {e}")
    
    async def optimize_provider_selection(self) -> Dict[ComplexityLevel, List[LLMProvider]]:
        """Optimize provider selection based on recent performance"""
        try:
            # Get provider rankings
            rankings = await metrics_collector.get_provider_ranking()
            
            if not rankings:
                return self.provider_matrix
            
            # Create optimized matrix
            optimized_matrix = {}
            
            for complexity in ComplexityLevel:
                # Get providers recommended for this complexity
                recommended_providers = []
                for ranking in rankings:
                    if complexity in ranking.recommended_for:
                        recommended_providers.append((LLMProvider(ranking.provider), ranking.score))
                
                # Sort by score (descending)
                recommended_providers.sort(key=lambda x: x[1], reverse=True)
                
                # Extract provider list
                optimized_list = [provider for provider, score in recommended_providers]
                
                # Add fallback providers not in recommendations
                fallback_providers = self.provider_matrix.get(complexity, [])
                for provider in fallback_providers:
                    if provider not in optimized_list:
                        optimized_list.append(provider)
                
                optimized_matrix[complexity] = optimized_list
            
            # Update provider matrix
            self.provider_matrix = optimized_matrix
            
            logger.info("Provider selection optimized based on performance metrics")
            return optimized_matrix
            
        except Exception as e:
            logger.error(f"Error optimizing provider selection: {e}")
            return self.provider_matrix
    
    async def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        try:
            stats = {
                "provider_matrix": {
                    complexity.value: [p.value for p in providers]
                    for complexity, providers in self.provider_matrix.items()
                },
                "circuit_breaker_states": await circuit_breaker_manager.get_all_states(),
                "provider_metrics": await metrics_collector.get_all_provider_metrics(),
                "cost_summary": await metrics_collector.get_cost_summary()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting routing stats: {e}")
            return {}


# Global LLM router instance
llm_router = LLMRouter()