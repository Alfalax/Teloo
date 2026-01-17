"""
Configuration settings for Agent IA Service
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "TeLOO V3 Agent IA"
    version: str = "3.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    api_v1_str: str = "/v1"
    
    # Core API Integration
    core_api_url: str = "http://core-api:8000"
    core_api_timeout: int = 30
    
    # Service Authentication
    service_name: str = "agent-ia"
    service_api_key: Optional[str] = None
    
    # Redis Configuration
    redis_url: str = "redis://redis:6379"
    redis_pool_size: int = 10
    
    # WhatsApp Configuration
    whatsapp_access_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None
    whatsapp_webhook_secret: Optional[str] = None
    whatsapp_api_version: str = "v18.0"
    whatsapp_api_url: str = "https://graph.facebook.com"
    
    # Telegram Configuration
    telegram_bot_token: Optional[str] = None
    telegram_enabled: bool = True
    
    # Audio Processing Configuration
    audio_primary_strategy: str = "whisper"  # whisper, anthropic, gemini, openai
    audio_fallback_strategy: str = "openai"  # openai, anthropic, gemini
    audio_fallback_enabled: bool = True
    audio_fallback_confidence_threshold: float = 0.6
    audio_min_transcription_length: int = 10
    audio_transcription_cache_enabled: bool = True
    audio_transcription_cache_ttl: int = 86400  # 24 hours
    
    # LLM Providers Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"  # Economical model - $0.15/1M tokens
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.3
    
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_max_tokens: int = 1000
    
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"  # Latest fast model
    
    deepseek_api_key: Optional[str] = None
    deepseek_api_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    
    # Local LLM Configuration (Ollama)
    local_llm_enabled: bool = False
    local_llm_url: str = "http://localhost:11434"
    local_llm_model: str = "llama3.1:8b"
    
    # NLP Configuration
    nlp_fallback_strategy: List[str] = ["regex", "deepseek", "gemini", "openai", "anthropic", "basic"]
    nlp_timeout_seconds: int = 10
    nlp_max_retries: int = 3
    
    # Circuit Breaker Configuration
    circuit_breaker_failure_threshold: int = 3
    circuit_breaker_timeout_seconds: int = 300
    
    # Conversation Management
    conversation_ttl_hours: int = 1
    max_conversation_turns: int = 10
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_per_ip: int = 100
    
    # Webhook Security
    webhook_signature_verification: bool = True
    
    
    # Cache Configuration
    cache_ttl_hours: int = 24
    
    @field_validator("redis_url")
    @classmethod
    def clean_redis_url(cls, v: str) -> str:
        if v:
            return v.strip()
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()