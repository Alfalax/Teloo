"""
Configuration for Realtime Gateway Service
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    environment: str = "development"
    service_name: str = "realtime-gateway"
    port: int = 8003
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "RS256"
    jwt_public_key_path: str = "./keys/public.pem"
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    
    # WebSocket Configuration
    ws_ping_interval: int = 25
    ws_ping_timeout: int = 60
    ws_max_connections: int = 1000
    
    # Logging
    log_level: str = "INFO"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def get_redis_url(self) -> str:
        """Get Redis URL - use REDIS_URL env var if set, otherwise build from components"""
        # If redis_url is set from environment and not default, use it
        if self.redis_url and self.redis_url != "redis://localhost:6379/0":
            return self.redis_url
        # Otherwise build from components
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
