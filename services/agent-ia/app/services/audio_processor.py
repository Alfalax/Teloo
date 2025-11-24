"""
Hybrid audio processor with Whisper primary + Multimodal fallback
"""
import logging
import time
import hashlib
import json
from typing import Optional, Dict, Any

from app.core.config import settings
from app.core.redis import redis_manager
from app.models.audio import (
    AudioProcessingResult,
    AudioStrategy,
    FallbackReason,
    AudioValidationResult,
    AudioQuality
)
from app.services.llm.whisper_adapter import whisper_adapter
from app.services.llm.anthropic_adapter import AnthropicAdapter
from app.services.llm.gemini_adapter import GeminiAdapter
from app.services.llm.openai_adapter import OpenAIAdapter
from app.services.llm.deepseek_adapter import DeepseekAdapter
from app.services.llm.metrics_collector import metrics_collector
from app.models.llm import LLMRequest

logger = logging.getLogger(__name__)


class AudioValidator:
    """Validates audio processing results"""
    
    def __init__(self):
        self.confidence_threshold = 0.6
        self.min_transcription_length = 10
        self.problematic_words = [
            "[inaudible]", "[ruido]", "[unclear]", "[noise]",
            "...", "mmm", "ehh", "umm", "[static]"
        ]
    
    def validate_transcription(self, transcription: str) -> AudioValidationResult:
        """Validate transcription quality"""
        # Check length
        if len(transcription.strip()) < self.min_transcription_length:
            return AudioValidationResult.create_failure(
                FallbackReason.EMPTY_TRANSCRIPTION,
                {"transcription_length": len(transcription)}
            )
        
        # Check for problematic words
        problematic_found = []
        transcription_lower = transcription.lower()
        for word in self.problematic_words:
            if word in transcription_lower:
                problematic_found.append(word)
        
        if problematic_found:
            return AudioValidationResult.create_failure(
                FallbackReason.POOR_AUDIO_QUALITY,
                {"problematic_words": problematic_found}
            )
        
        return AudioValidationResult.create_success()
    
    def validate_entities_result(self, result: Dict[str, Any]) -> AudioValidationResult:
        """Validate entity extraction result"""
        confidence = result.get("confidence_score", 0.0)
        repuestos = result.get("repuestos", [])
        vehiculo = result.get("vehiculo")
        
        # Check confidence
        if confidence < self.confidence_threshold:
            return AudioValidationResult.create_failure(
                FallbackReason.LOW_CONFIDENCE,
                {"confidence": confidence, "threshold": self.confidence_threshold}
            )
        
        # Check if entities were found
        if not repuestos and not vehiculo:
            return AudioValidationResult.create_failure(
                FallbackReason.NO_ENTITIES,
                {"repuestos_count": len(repuestos), "has_vehiculo": bool(vehiculo)}
            )
        
        return AudioValidationResult.create_success()


class AudioProcessor:
    """
    Hybrid audio processor with Whisper primary + Multimodal fallback
    
    Flow:
    1. Try Whisper pipeline (transcription + entity extraction)
    2. Validate result quality
    3. If validation fails → Use multimodal fallback
    4. Record metrics and return result
    """
    
    def __init__(self):
        self.primary_strategy = AudioStrategy.WHISPER
        self.fallback_strategy = AudioStrategy.OPENAI
        self.fallback_enabled = True
        
        # Validation settings
        self.validator = AudioValidator()
        
        # Cache settings
        self.cache_enabled = True
        self.cache_ttl = 86400  # 24 hours
        
        # Initialize adapters
        self.whisper = whisper_adapter
        self.deepseek = DeepseekAdapter()
        self.anthropic = AnthropicAdapter()
        self.gemini = GeminiAdapter()
        self.openai = OpenAIAdapter()
        
        logger.info(
            f"AudioProcessor initialized: primary={self.primary_strategy.value}, "
            f"fallback={self.fallback_strategy.value}"
        )
    
    async def process_audio(
        self,
        audio_url: str,
        context: Optional[Dict[str, Any]] = None,
        force_strategy: Optional[AudioStrategy] = None
    ) -> AudioProcessingResult:
        """
        Process audio with hybrid strategy
        
        Args:
            audio_url: URL of the audio file
            context: Additional context (user info, conversation history, etc.)
            force_strategy: Force specific strategy (for testing)
            
        Returns:
            AudioProcessingResult with extracted data and metadata
        """
        start_time = time.time()
        strategy = force_strategy or self.primary_strategy
        
        logger.info(f"Processing audio with strategy: {strategy.value}")
        
        try:
            # Try primary strategy
            result = await self._process_with_strategy(
                audio_url=audio_url,
                strategy=strategy,
                context=context
            )
            
            # Validate result
            validation = await self._validate_result(result, strategy)
            
            if validation.should_use_fallback and self.fallback_enabled:
                logger.warning(
                    f"Primary strategy validation failed: {validation.fallback_reason.value}. "
                    f"Attempting fallback to {self.fallback_strategy.value}"
                )
                
                # Execute fallback
                fallback_result = await self._process_with_strategy(
                    audio_url=audio_url,
                    strategy=self.fallback_strategy,
                    context=context
                )
                
                # Mark as fallback
                fallback_result.fallback_used = True
                fallback_result.fallback_reason = validation.fallback_reason
                
                # Record fallback metrics
                await self._record_fallback_metrics(
                    primary_strategy=strategy,
                    fallback_strategy=self.fallback_strategy,
                    reason=validation.fallback_reason
                )
                
                return fallback_result
            
            # Primary strategy succeeded
            return result
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            
            # Try fallback on error
            if self.fallback_enabled and strategy != self.fallback_strategy:
                logger.info(f"Attempting fallback due to error: {e}")
                try:
                    fallback_result = await self._process_with_strategy(
                        audio_url=audio_url,
                        strategy=self.fallback_strategy,
                        context=context
                    )
                    fallback_result.fallback_used = True
                    fallback_result.fallback_reason = FallbackReason.ERROR
                    
                    await self._record_fallback_metrics(
                        primary_strategy=strategy,
                        fallback_strategy=self.fallback_strategy,
                        reason=FallbackReason.ERROR
                    )
                    
                    return fallback_result
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise
            else:
                raise
        finally:
            total_time = int((time.time() - start_time) * 1000)
            logger.info(f"Audio processing completed in {total_time}ms")
    
    async def _process_with_strategy(
        self,
        audio_url: str,
        strategy: AudioStrategy,
        context: Optional[Dict[str, Any]]
    ) -> AudioProcessingResult:
        """Process audio with specific strategy"""
        if strategy == AudioStrategy.WHISPER:
            return await self._process_with_whisper_pipeline(audio_url, context)
        elif strategy == AudioStrategy.ANTHROPIC:
            return await self._process_with_anthropic(audio_url, context)
        elif strategy == AudioStrategy.GEMINI:
            return await self._process_with_gemini(audio_url, context)
        elif strategy == AudioStrategy.OPENAI:
            return await self._process_with_openai(audio_url, context)
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")
    
    async def _process_with_whisper_pipeline(
        self,
        audio_url: str,
        context: Optional[Dict[str, Any]]
    ) -> AudioProcessingResult:
        """
        Whisper pipeline: Transcription + Entity extraction
        
        Steps:
        1. Check transcription cache
        2. Transcribe with Whisper (if not cached)
        3. Cache transcription
        4. Extract entities with Deepseek
        5. Return combined result
        """
        start_time = time.time()
        
        # Check cache
        cache_key = self._generate_cache_key(audio_url)
        cached_transcription = None
        
        if self.cache_enabled:
            cached_transcription = await redis_manager.get(f"transcription:{cache_key}")
        
        if cached_transcription:
            logger.info("✅ Using cached transcription")
            transcription_result = {
                "text": cached_transcription,
                "processing_time_ms": 0,
                "cost_usd": 0.0,
                "provider": "cache",
                "model": "whisper-1",
                "language": "es",
                "duration_minutes": 0
            }
            transcription_cached = True
        else:
            # Transcribe with Whisper
            logger.info("Transcribing with Whisper...")
            transcription_result = await self.whisper.transcribe(audio_url)
            transcription_cached = False
            
            # Cache transcription
            if self.cache_enabled and transcription_result["text"]:
                await redis_manager.set(
                    f"transcription:{cache_key}",
                    transcription_result["text"],
                    ttl=self.cache_ttl
                )
                logger.info("✅ Transcription cached")
        
        transcription = transcription_result["text"]
        
        # Extract entities with Deepseek
        logger.info("Extracting entities with Deepseek...")
        request = LLMRequest(text=transcription)
        deepseek_response = await self.deepseek.process_text(request)
        
        # Parse JSON response
        entities = json.loads(deepseek_response.content)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(entities)
        
        # Combine results
        total_time = int((time.time() - start_time) * 1000)
        total_cost = transcription_result.get("cost_usd", 0.0) + deepseek_response.cost_usd
        
        return AudioProcessingResult(
            repuestos=entities.get("repuestos", []),
            vehiculo=entities.get("vehiculo"),
            cliente=entities.get("cliente"),
            strategy_used=AudioStrategy.WHISPER,
            confidence_score=confidence_score,
            processing_time_ms=total_time,
            cost_usd=total_cost,
            transcription=transcription,
            transcription_cached=transcription_cached,
            metadata={
                "whisper_time_ms": transcription_result.get("processing_time_ms", 0),
                "deepseek_time_ms": 0,  # Included in total_time
                "transcription_length": len(transcription),
                "duration_minutes": transcription_result.get("duration_minutes", 0)
            }
        )
    
    async def _process_with_anthropic(
        self,
        audio_url: str,
        context: Optional[Dict[str, Any]]
    ) -> AudioProcessingResult:
        """Process audio directly with Anthropic Claude"""
        start_time = time.time()
        
        logger.info("Processing with Anthropic Claude...")
        request = LLMRequest(audio_url=audio_url)
        response = await self.anthropic.process_audio(request)
        
        # Parse JSON response
        entities = json.loads(response.content)
        
        # Calculate confidence
        confidence_score = self._calculate_confidence(entities)
        
        total_time = int((time.time() - start_time) * 1000)
        
        return AudioProcessingResult(
            repuestos=entities.get("repuestos", []),
            vehiculo=entities.get("vehiculo"),
            cliente=entities.get("cliente"),
            strategy_used=AudioStrategy.ANTHROPIC,
            confidence_score=confidence_score,
            processing_time_ms=total_time,
            cost_usd=response.cost_usd,
            transcription=None,  # Anthropic doesn't return separate transcription
            transcription_cached=False,
            metadata={
                "model": "claude-3-5-sonnet",
                "provider": "anthropic"
            }
        )
    
    async def _process_with_gemini(
        self,
        audio_url: str,
        context: Optional[Dict[str, Any]]
    ) -> AudioProcessingResult:
        """Process audio directly with Google Gemini"""
        start_time = time.time()
        
        logger.info("Processing with Google Gemini...")
        request = LLMRequest(audio_url=audio_url)
        response = await self.gemini.process_audio(request)
        
        # Parse JSON response
        entities = json.loads(response.content)
        
        # Calculate confidence
        confidence_score = self._calculate_confidence(entities)
        
        total_time = int((time.time() - start_time) * 1000)
        
        return AudioProcessingResult(
            repuestos=entities.get("repuestos", []),
            vehiculo=entities.get("vehiculo"),
            cliente=entities.get("cliente"),
            strategy_used=AudioStrategy.GEMINI,
            confidence_score=confidence_score,
            processing_time_ms=total_time,
            cost_usd=response.cost_usd,
            transcription=None,  # Gemini doesn't return separate transcription
            transcription_cached=False,
            metadata={
                "model": "gemini-1.5-pro",
                "provider": "gemini"
            }
        )
    
    async def _process_with_openai(
        self,
        audio_url: str,
        context: Optional[Dict[str, Any]]
    ) -> AudioProcessingResult:
        """
        OpenAI pipeline: Whisper transcription + GPT-4 entity extraction
        
        Steps:
        1. Transcribe with Whisper
        2. Extract entities with GPT-4 (fallback for Deepseek)
        3. Return combined result
        """
        start_time = time.time()
        
        # Step 1: Transcribe with Whisper
        logger.info("Transcribing with Whisper (for OpenAI pipeline)...")
        transcription_result = await self.whisper.transcribe(audio_url)
        transcription_text = transcription_result["text"]
        transcription_cost = transcription_result["cost_usd"]
        
        # Step 2: Extract entities with OpenAI GPT-4
        logger.info("Extracting entities with OpenAI GPT-4...")
        request = LLMRequest(text=transcription_text)
        response = await self.openai.process_text(request)
        
        # Parse JSON response
        entities = json.loads(response.content)
        
        # Calculate confidence
        confidence_score = self._calculate_confidence(entities)
        
        total_time = int((time.time() - start_time) * 1000)
        total_cost = transcription_cost + response.cost_usd
        
        return AudioProcessingResult(
            repuestos=entities.get("repuestos", []),
            vehiculo=entities.get("vehiculo"),
            cliente=entities.get("cliente"),
            strategy_used=AudioStrategy.OPENAI,
            confidence_score=confidence_score,
            processing_time_ms=total_time,
            cost_usd=total_cost,
            transcription=transcription_text,
            transcription_cached=False,
            metadata={
                "transcription_model": "whisper-1",
                "extraction_model": "gpt-4o",
                "provider": "whisper+openai",
                "transcription_cost": transcription_cost,
                "extraction_cost": response.cost_usd
            }
        )
    
    def _calculate_confidence(self, entities: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted entities"""
        score = 0.0
        
        # Repuestos found
        repuestos = entities.get("repuestos", [])
        if repuestos:
            score += 0.4
            # Bonus for specific repuestos
            if any(r.get("nombre") and len(r.get("nombre", "")) > 5 for r in repuestos):
                score += 0.1
        
        # Vehiculo found
        vehiculo = entities.get("vehiculo")
        if vehiculo:
            if vehiculo.get("marca"):
                score += 0.2
            if vehiculo.get("linea"):
                score += 0.1
            if vehiculo.get("anio"):
                score += 0.1
        
        # Cliente found
        cliente = entities.get("cliente")
        if cliente:
            if cliente.get("telefono"):
                score += 0.1
        
        return min(1.0, score)
    
    async def _validate_result(
        self,
        result: AudioProcessingResult,
        strategy: AudioStrategy
    ) -> AudioValidationResult:
        """Validate processing result"""
        # For Whisper pipeline, validate transcription first
        if strategy == AudioStrategy.WHISPER and result.transcription:
            transcription_validation = self.validator.validate_transcription(result.transcription)
            if not transcription_validation.is_valid:
                return transcription_validation
        
        # Validate entity extraction result
        entities_data = {
            "repuestos": result.repuestos,
            "vehiculo": result.vehiculo,
            "cliente": result.cliente,
            "confidence_score": result.confidence_score
        }
        
        return self.validator.validate_entities_result(entities_data)
    
    async def _record_fallback_metrics(
        self,
        primary_strategy: AudioStrategy,
        fallback_strategy: AudioStrategy,
        reason: FallbackReason
    ):
        """Record fallback usage metrics"""
        try:
            # Record in metrics collector
            logger.info(
                f"Fallback used: {primary_strategy.value} → {fallback_strategy.value}, "
                f"reason: {reason.value}"
            )
            
            # Store in Redis for tracking
            fallback_key = f"audio_fallback:{reason.value}"
            current_count = await redis_manager.get(fallback_key) or "0"
            await redis_manager.set(fallback_key, str(int(current_count) + 1), ttl=86400)
            
        except Exception as e:
            logger.error(f"Error recording fallback metrics: {e}")
    
    def _generate_cache_key(self, audio_url: str) -> str:
        """Generate cache key for audio URL"""
        return hashlib.sha256(audio_url.encode()).hexdigest()[:16]


# Global audio processor instance
audio_processor = AudioProcessor()
