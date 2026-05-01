"""
Centralized configuration for core-api using Pydantic BaseSettings.
Replaces scattered os.getenv() calls across the codebase.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    port: int = 8000

    # Database
    database_url: str = "postgres://teloo:teloo123@localhost:5432/teloo_v3"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # JWT
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Security
    internal_api_key: str = ""
    allowed_origins: str = (
        "https://app.teloo.cloud,https://admin.teloo.cloud,"
        "https://advisor.teloo.cloud,https://teloo.cloud,https://www.teloo.cloud"
    )
    trusted_proxy_hosts: str = "*"

    # Service-to-service auth
    agent_ia_api_key: str = ""
    analytics_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
