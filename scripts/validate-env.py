#!/usr/bin/env python3
"""
Environment Variables Validation Script
Validates that all required environment variables are set before starting services
"""

import os
import sys
from typing import List, Dict, Optional
from enum import Enum


class Severity(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationResult:
    def __init__(self, var_name: str, severity: Severity, message: str, is_valid: bool):
        self.var_name = var_name
        self.severity = severity
        self.message = message
        self.is_valid = is_valid


class EnvValidator:
    def __init__(self, service_name: str, environment: str):
        self.service_name = service_name
        self.environment = environment
        self.results: List[ValidationResult] = []
        
    def validate_required(self, var_name: str, description: str = "") -> bool:
        """Validate that a required variable is set"""
        value = os.getenv(var_name)
        if not value:
            self.results.append(ValidationResult(
                var_name,
                Severity.CRITICAL,
                f"Required variable not set: {description}",
                False
            ))
            return False
        self.results.append(ValidationResult(
            var_name,
            Severity.INFO,
            f"✓ Set correctly",
            True
        ))
        return True
    
    def validate_optional(self, var_name: str, default: str, description: str = "") -> bool:
        """Validate an optional variable and set default if not present"""
        value = os.getenv(var_name)
        if not value:
            os.environ[var_name] = default
            self.results.append(ValidationResult(
                var_name,
                Severity.WARNING,
                f"Using default value: {default}",
                True
            ))
            return True
        self.results.append(ValidationResult(
            var_name,
            Severity.INFO,
            f"✓ Set correctly",
            True
        ))
        return True
    
    def validate_url(self, var_name: str, description: str = "") -> bool:
        """Validate that a URL is properly formatted"""
        value = os.getenv(var_name)
        if not value:
            self.results.append(ValidationResult(
                var_name,
                Severity.CRITICAL,
                f"Required URL not set: {description}",
                False
            ))
            return False
        
        if not (value.startswith('http://') or value.startswith('https://') or 
                value.startswith('postgres://') or value.startswith('redis://')):
            self.results.append(ValidationResult(
                var_name,
                Severity.WARNING,
                f"URL may be malformed: {value[:30]}...",
                True
            ))
            return True
        
        self.results.append(ValidationResult(
            var_name,
            Severity.INFO,
            f"✓ Valid URL format",
            True
        ))
        return True
    
    def validate_production_secret(self, var_name: str, description: str = "") -> bool:
        """Validate that production secrets are strong"""
        value = os.getenv(var_name)
        
        if not value:
            self.results.append(ValidationResult(
                var_name,
                Severity.CRITICAL,
                f"Production secret not set: {description}",
                False
            ))
            return False
        
        # In production, check for weak/default values
        if self.environment == "production":
            weak_patterns = [
                "test", "dev", "development", "example", "your-", "change-in-production",
                "12345", "password", "secret"
            ]
            value_lower = value.lower()
            
            for pattern in weak_patterns:
                if pattern in value_lower:
                    self.results.append(ValidationResult(
                        var_name,
                        Severity.CRITICAL,
                        f"⚠️  SECURITY RISK: Weak/default value detected in production!",
                        False
                    ))
                    return False
            
            # Check minimum length for production secrets
            if len(value) < 32:
                self.results.append(ValidationResult(
                    var_name,
                    Severity.WARNING,
                    f"Secret may be too short for production (< 32 chars)",
                    True
                ))
                return True
        
        self.results.append(ValidationResult(
            var_name,
            Severity.INFO,
            f"✓ Secret set correctly",
            True
        ))
        return True
    
    def print_results(self):
        """Print validation results"""
        print(f"\n{'='*80}")
        print(f"Environment Validation: {self.service_name} ({self.environment})")
        print(f"{'='*80}\n")
        
        critical_count = 0
        warning_count = 0
        
        for result in self.results:
            icon = "✓" if result.is_valid else "✗"
            color = ""
            reset = ""
            
            if result.severity == Severity.CRITICAL:
                color = "\033[91m"  # Red
                reset = "\033[0m"
                critical_count += 1
            elif result.severity == Severity.WARNING:
                color = "\033[93m"  # Yellow
                reset = "\033[0m"
                warning_count += 1
            else:
                color = "\033[92m"  # Green
                reset = "\033[0m"
            
            print(f"{color}[{result.severity.value}]{reset} {icon} {result.var_name}")
            print(f"  {result.message}\n")
        
        print(f"{'='*80}")
        print(f"Summary: {len(self.results)} variables checked")
        print(f"  Critical Issues: {critical_count}")
        print(f"  Warnings: {warning_count}")
        print(f"  Valid: {len(self.results) - critical_count - warning_count}")
        print(f"{'='*80}\n")
        
        return critical_count == 0


def validate_core_api():
    """Validate Core API environment variables"""
    env = os.getenv("ENVIRONMENT", "development")
    validator = EnvValidator("Core API", env)
    
    # Database
    validator.validate_url("DATABASE_URL", "PostgreSQL connection string")
    
    # Redis
    validator.validate_url("REDIS_URL", "Redis connection string")
    
    # MinIO
    validator.validate_required("MINIO_ENDPOINT", "MinIO endpoint")
    validator.validate_required("MINIO_ACCESS_KEY", "MinIO access key")
    validator.validate_production_secret("MINIO_SECRET_KEY", "MinIO secret key")
    
    # JWT
    validator.validate_production_secret("JWT_SECRET_KEY", "JWT signing key")
    validator.validate_optional("JWT_ALGORITHM", "RS256", "JWT algorithm")
    validator.validate_optional("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15", "Access token expiry")
    
    # Service Auth
    validator.validate_production_secret("AGENT_IA_API_KEY", "Agent IA service key")
    validator.validate_production_secret("ANALYTICS_API_KEY", "Analytics service key")
    
    # Application
    validator.validate_required("ENVIRONMENT", "Environment name")
    validator.validate_optional("LOG_LEVEL", "INFO", "Logging level")
    validator.validate_optional("TIMEZONE", "America/Bogota", "System timezone")
    
    return validator.print_results()


def validate_agent_ia():
    """Validate Agent IA environment variables"""
    env = os.getenv("ENVIRONMENT", "development")
    validator = EnvValidator("Agent IA", env)
    
    # Core API Integration
    validator.validate_url("CORE_API_URL", "Core API endpoint")
    validator.validate_production_secret("SERVICE_API_KEY", "Service authentication key")
    
    # Redis
    validator.validate_url("REDIS_URL", "Redis connection string")
    
    # WhatsApp
    validator.validate_production_secret("WHATSAPP_ACCESS_TOKEN", "WhatsApp API token")
    validator.validate_required("WHATSAPP_PHONE_NUMBER_ID", "WhatsApp phone number ID")
    validator.validate_production_secret("WHATSAPP_VERIFY_TOKEN", "WhatsApp webhook verify token")
    
    # LLM Providers
    if env != "development":
        validator.validate_production_secret("OPENAI_API_KEY", "OpenAI API key")
        validator.validate_production_secret("ANTHROPIC_API_KEY", "Anthropic API key")
    
    # Application
    validator.validate_required("ENVIRONMENT", "Environment name")
    validator.validate_optional("LOG_LEVEL", "INFO", "Logging level")
    
    return validator.print_results()


def validate_analytics():
    """Validate Analytics Service environment variables"""
    env = os.getenv("ENVIRONMENT", "development")
    validator = EnvValidator("Analytics Service", env)
    
    # Database
    validator.validate_url("DATABASE_URL", "PostgreSQL connection string")
    
    # Redis
    validator.validate_url("REDIS_URL", "Redis connection string")
    
    # Application
    validator.validate_required("ENVIRONMENT", "Environment name")
    validator.validate_optional("LOG_LEVEL", "INFO", "Logging level")
    
    # Optional: Alert configuration
    if env == "production":
        validator.validate_optional("SMTP_SERVER", "smtp.gmail.com", "SMTP server")
        validator.validate_optional("ALERT_EMAIL_TO", "admin@teloo.com", "Alert email recipients")
    
    return validator.print_results()


def validate_realtime_gateway():
    """Validate Realtime Gateway environment variables"""
    env = os.getenv("ENVIRONMENT", "development")
    validator = EnvValidator("Realtime Gateway", env)
    
    # Redis
    validator.validate_url("REDIS_URL", "Redis connection string")
    
    # JWT
    validator.validate_production_secret("JWT_SECRET_KEY", "JWT signing key")
    
    # Application
    validator.validate_required("ENVIRONMENT", "Environment name")
    validator.validate_optional("LOG_LEVEL", "INFO", "Logging level")
    
    return validator.print_results()


def validate_files():
    """Validate Files Service environment variables"""
    env = os.getenv("ENVIRONMENT", "development")
    validator = EnvValidator("Files Service", env)
    
    # MinIO
    validator.validate_required("MINIO_ENDPOINT", "MinIO endpoint")
    validator.validate_required("MINIO_ACCESS_KEY", "MinIO access key")
    validator.validate_production_secret("MINIO_SECRET_KEY", "MinIO secret key")
    
    # Redis
    validator.validate_url("REDIS_URL", "Redis connection string")
    
    # Application
    validator.validate_required("ENVIRONMENT", "Environment name")
    validator.validate_optional("LOG_LEVEL", "INFO", "Logging level")
    
    return validator.print_results()


def main():
    """Main validation entry point"""
    service = os.getenv("SERVICE_NAME", "").lower()
    
    validators = {
        "core-api": validate_core_api,
        "agent-ia": validate_agent_ia,
        "analytics": validate_analytics,
        "realtime-gateway": validate_realtime_gateway,
        "files": validate_files,
    }
    
    if not service:
        print("ERROR: SERVICE_NAME environment variable not set")
        print("Usage: SERVICE_NAME=core-api python validate-env.py")
        sys.exit(1)
    
    if service not in validators:
        print(f"ERROR: Unknown service '{service}'")
        print(f"Valid services: {', '.join(validators.keys())}")
        sys.exit(1)
    
    # Run validation
    is_valid = validators[service]()
    
    if not is_valid:
        print("\n❌ Environment validation FAILED!")
        print("Please fix the critical issues before starting the service.\n")
        sys.exit(1)
    else:
        print("\n✅ Environment validation PASSED!")
        print("Service is ready to start.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
