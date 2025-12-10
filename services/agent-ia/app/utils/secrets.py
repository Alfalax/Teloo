"""
Secrets Management Utility
Handles reading secrets from Docker secrets files or environment variables
"""

import os
from typing import Optional
from pathlib import Path


def get_secret(secret_name: str, default: Optional[str] = None) -> str:
    """
    Read secret from Docker secret file or environment variable.
    
    Priority:
    1. Docker secret file (if {SECRET_NAME}_FILE env var is set)
    2. Environment variable
    3. Default value
    
    Args:
        secret_name: Name of the secret (e.g., 'JWT_SECRET_KEY')
        default: Default value if secret not found
        
    Returns:
        Secret value as string
        
    Raises:
        ValueError: If secret not found and no default provided
        
    Example:
        >>> jwt_secret = get_secret('JWT_SECRET_KEY')
        >>> db_password = get_secret('POSTGRES_PASSWORD', 'default_password')
    """
    secret_name_upper = secret_name.upper()
    
    # Try to read from Docker secret file first
    secret_file_path = os.getenv(f"{secret_name_upper}_FILE")
    
    if secret_file_path:
        secret_path = Path(secret_file_path)
        if secret_path.exists() and secret_path.is_file():
            try:
                with open(secret_path, 'r', encoding='utf-8') as f:
                    value = f.read().strip()
                    if value:
                        return value
            except Exception as e:
                print(f"Warning: Failed to read secret file {secret_file_path}: {e}")
    
    # Fall back to environment variable
    value = os.getenv(secret_name_upper)
    if value:
        return value
    
    # Use default if provided
    if default is not None:
        return default
    
    # No secret found and no default
    raise ValueError(
        f"Secret '{secret_name}' not found. "
        f"Set {secret_name_upper} environment variable or {secret_name_upper}_FILE path."
    )


def get_database_url() -> str:
    """
    Get database URL with password from secret if available.
    
    Returns:
        Complete database URL with credentials
    """
    # Try to get complete DATABASE_URL first
    db_url = os.getenv("DATABASE_URL")
    
    if db_url:
        # Check if password needs to be replaced from secret
        password_file = os.getenv("POSTGRES_PASSWORD_FILE")
        if password_file and "${POSTGRES_PASSWORD" in db_url:
            password = get_secret("POSTGRES_PASSWORD")
            db_url = db_url.replace("${POSTGRES_PASSWORD}", password)
            db_url = db_url.replace("${POSTGRES_PASSWORD_PROD}", password)
            db_url = db_url.replace("${POSTGRES_PASSWORD_STAGING}", password)
        return db_url
    
    # Build from components
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "teloo_user")
    db_password = get_secret("POSTGRES_PASSWORD", "teloo_password")
    db_name = os.getenv("DB_NAME", "teloo_v3")
    
    return f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def get_redis_url() -> str:
    """
    Get Redis URL with password from secret if available.
    
    Returns:
        Complete Redis URL with credentials
    """
    # Try to get complete REDIS_URL first
    redis_url = os.getenv("REDIS_URL")
    
    if redis_url:
        # Check if password needs to be replaced from secret
        password_file = os.getenv("REDIS_PASSWORD_FILE")
        if password_file and "${REDIS_PASSWORD" in redis_url:
            password = get_secret("REDIS_PASSWORD", "")
            if password:
                redis_url = redis_url.replace("${REDIS_PASSWORD}", password)
                redis_url = redis_url.replace("${REDIS_PASSWORD_PROD}", password)
                redis_url = redis_url.replace("${REDIS_PASSWORD_STAGING}", password)
            else:
                # Remove password placeholder if no password
                redis_url = redis_url.replace(":${REDIS_PASSWORD}@", "@")
                redis_url = redis_url.replace(":${REDIS_PASSWORD_PROD}@", "@")
                redis_url = redis_url.replace(":${REDIS_PASSWORD_STAGING}@", "@")
        return redis_url
    
    # Build from components
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_password = get_secret("REDIS_PASSWORD", "")
    redis_db = os.getenv("REDIS_DB", "0")
    
    if redis_password:
        return f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
    else:
        return f"redis://{redis_host}:{redis_port}/{redis_db}"


def get_minio_credentials() -> dict:
    """
    Get MinIO credentials from secrets or environment.
    
    Returns:
        Dictionary with MinIO configuration
    """
    return {
        "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        "access_key": get_secret("MINIO_ACCESS_KEY", "minioadmin"),
        "secret_key": get_secret("MINIO_SECRET_KEY", "minioadmin"),
        "bucket_name": os.getenv("MINIO_BUCKET_NAME", "teloo-files"),
        "secure": os.getenv("MINIO_SECURE", "false").lower() == "true"
    }


def get_jwt_config() -> dict:
    """
    Get JWT configuration from secrets or environment.
    
    Returns:
        Dictionary with JWT configuration
    """
    return {
        "secret_key": get_secret("JWT_SECRET_KEY"),
        "algorithm": os.getenv("JWT_ALGORITHM", "RS256"),
        "access_token_expire_minutes": int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")),
        "refresh_token_expire_days": int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    }


def get_service_api_keys() -> dict:
    """
    Get service-to-service API keys from secrets.
    
    Returns:
        Dictionary with service API keys
    """
    return {
        "agent_ia": get_secret("AGENT_IA_API_KEY"),
        "analytics": get_secret("ANALYTICS_API_KEY")
    }


def get_whatsapp_config() -> dict:
    """
    Get WhatsApp API configuration from secrets.
    
    Returns:
        Dictionary with WhatsApp configuration
    """
    return {
        "access_token": get_secret("WHATSAPP_ACCESS_TOKEN"),
        "phone_number_id": os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
        "verify_token": get_secret("WHATSAPP_VERIFY_TOKEN"),
        "webhook_secret": get_secret("WHATSAPP_WEBHOOK_SECRET", ""),
        "api_version": os.getenv("WHATSAPP_API_VERSION", "v18.0")
    }


def get_llm_api_keys() -> dict:
    """
    Get LLM provider API keys from secrets.
    
    Returns:
        Dictionary with LLM API keys
    """
    return {
        "openai": get_secret("OPENAI_API_KEY", ""),
        "anthropic": get_secret("ANTHROPIC_API_KEY", ""),
        "gemini": get_secret("GEMINI_API_KEY", ""),
        "deepseek": get_secret("DEEPSEEK_API_KEY", "")
    }


def validate_required_secrets(service_name: str) -> bool:
    """
    Validate that all required secrets for a service are set.
    
    Args:
        service_name: Name of the service (core-api, agent-ia, etc.)
        
    Returns:
        True if all required secrets are set, False otherwise
    """
    required_secrets = {
        "core-api": [
            "JWT_SECRET_KEY",
            "AGENT_IA_API_KEY",
            "ANALYTICS_API_KEY",
            "MINIO_SECRET_KEY"
        ],
        "agent-ia": [
            "SERVICE_API_KEY",
            "WHATSAPP_ACCESS_TOKEN",
            "WHATSAPP_VERIFY_TOKEN"
        ],
        "analytics": [],
        "realtime-gateway": [
            "JWT_SECRET_KEY"
        ],
        "files": [
            "MINIO_SECRET_KEY"
        ]
    }
    
    secrets = required_secrets.get(service_name, [])
    all_valid = True
    
    for secret in secrets:
        try:
            value = get_secret(secret)
            if not value:
                print(f"ERROR: Required secret '{secret}' is empty")
                all_valid = False
        except ValueError as e:
            print(f"ERROR: {e}")
            all_valid = False
    
    return all_valid
