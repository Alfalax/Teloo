"""
Whisper adapter for audio transcription
"""
import logging
import httpx
import hashlib
import time
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class WhisperAdapter:
    """Adapter for OpenAI Whisper API"""
    
    def __init__(self):
        self.provider_name = "whisper"
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        self.model = "whisper-1"
        self.language = "es"
        
        # Pricing (per minute)
        self.cost_per_minute = 0.006  # $0.006 per minute
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured for Whisper")
    
    async def transcribe(self, audio_url: str) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper API
        
        Args:
            audio_url: URL of the audio file
            
        Returns:
            Dict with transcription result
        """
        start_time = time.time()
        
        try:
            # Download audio file
            audio_data = await self._download_audio(audio_url)
            if not audio_data:
                raise Exception("Failed to download audio file")
            
            # Get audio duration for cost calculation
            duration_minutes = await self._estimate_audio_duration(audio_data)
            
            # Transcribe with Whisper
            transcription = await self._call_whisper_api(audio_data)
            
            processing_time = int((time.time() - start_time) * 1000)
            cost = duration_minutes * self.cost_per_minute
            
            result = {
                "text": transcription,
                "language": self.language,
                "duration_minutes": duration_minutes,
                "processing_time_ms": processing_time,
                "cost_usd": cost,
                "provider": self.provider_name,
                "model": self.model
            }
            
            logger.info(
                f"Whisper transcription completed: {len(transcription)} chars, "
                f"{duration_minutes:.2f}min, ${cost:.4f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise
    
    async def _download_audio(self, audio_url: str) -> Optional[bytes]:
        """Download audio file from URL"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(audio_url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return None
    
    async def _estimate_audio_duration(self, audio_data: bytes) -> float:
        """
        Estimate audio duration in minutes
        Rough estimation based on file size.
        """
        try:
            # Rough estimation: ~16KB per second for compressed audio
            estimated_seconds = len(audio_data) / 16000
            return max(0.1, estimated_seconds / 60)  # Minimum 0.1 minutes
        except Exception:
            return 1.0  # Default to 1 minute if estimation fails
    
    async def _call_whisper_api(self, audio_data: bytes) -> str:
        """Call OpenAI Whisper API"""
        try:
            url = f"{self.base_url}/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Prepare multipart form data
            files = {
                "file": ("audio.ogg", audio_data, "audio/ogg"),
            }
            
            data = {
                "model": self.model,
                "language": self.language,
                "response_format": "text"
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url, 
                    headers=headers, 
                    files=files,
                    data=data
                )
                response.raise_for_status()
                
                # Whisper returns plain text when response_format=text
                transcription = response.text.strip()
                
                if not transcription:
                    logger.warning("Whisper returned empty transcription")
                    return ""
                
                return transcription
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Whisper API HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Whisper API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Whisper API call failed: {e}")
            raise


# Global Whisper adapter instance
whisper_adapter = WhisperAdapter()
