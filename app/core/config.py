"""
Application Configuration
12-Factor App principles - all config from environment
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "sre-demo-api"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"], env="ALLOWED_ORIGINS"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")  # json or text

    # Observability
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    ENABLE_TRACING: bool = Field(default=True, env="ENABLE_TRACING")
    JAEGER_ENDPOINT: str = Field(
        default="http://jaeger-collector:14268/api/traces", env="JAEGER_ENDPOINT"
    )
    OTEL_SERVICE_NAME: str = Field(default="sre-demo-api", env="OTEL_SERVICE_NAME")

    # Database (for future use)
    DATABASE_URL: str = Field(
        default="postgresql://user:pass@localhost:5432/db", env="DATABASE_URL"
    )
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")

    # Redis (for future use)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production", env="SECRET_KEY")
    API_KEY_HEADER: str = Field(default="X-API-Key", env="API_KEY_HEADER")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")

    # Graceful Shutdown
    SHUTDOWN_TIMEOUT: int = Field(default=30, env="SHUTDOWN_TIMEOUT")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
