"""
Analytics Service Configuration
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "analytics"
    VERSION: str = "3.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgres://teloo:teloo123@localhost:5432/teloo_v3")
    DATABASE_REPLICA_URL: Optional[str] = os.getenv("DATABASE_REPLICA_URL")  # Para consultas de solo lectura
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Analytics específico
    METRICS_CACHE_TTL: int = int(os.getenv("METRICS_CACHE_TTL", "300"))  # 5 minutos
    BATCH_JOB_HOUR: int = int(os.getenv("BATCH_JOB_HOUR", "2"))  # 2 AM
    ALERT_THRESHOLDS: dict = {
        "error_rate": float(os.getenv("ALERT_ERROR_RATE", "0.05")),  # 5%
        "latency_p95": float(os.getenv("ALERT_LATENCY_P95", "300")),  # 300ms
        "conversion_rate": float(os.getenv("ALERT_CONVERSION_RATE", "0.1"))  # 10%
    }
    
    # Configuración de alertas
    ALERT_CHECK_INTERVAL: int = int(os.getenv("ALERT_CHECK_INTERVAL", "300"))  # 5 minutos
    
    # Email configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "alerts@teloo.com")
    ALERT_EMAIL_TO: str = os.getenv("ALERT_EMAIL_TO", "admin@teloo.com")
    
    # Slack configuration
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#alerts")
    
    # Eventos Redis
    REDIS_EVENTS_CHANNEL: str = "teloo:events"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from environment

settings = Settings()