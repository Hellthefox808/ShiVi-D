"""
Briefing: Global Configuration & Environment Settings for ShiVi Backend.
Reason: Uses Pydantic BaseSettings to enforce strict typing, validation, and sensible fallbacks.
Defaults to local async SQLite (`shivi_local.db`) so the application can run zero-config in an isolated offline laptop.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Briefing: Application configuration schema parsed from environment variables or .env file.
    Reason: Centralizes database URLs, object storage credentials, and cryptographic signing keys.
    """
    # Service naming and API version prefixes
    PROJECT_NAME: str = "ShiVi Operations Core API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    
    # Database: Default to local SQLite with aiosqlite driver for immediate zero-config execution
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./shivi_local.db")
    
    # Redis URL for pub/sub, caching, and rate limiting
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # MinIO / S3 Object Storage for photographic verification evidence (Phase 7)
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minio_admin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minio_secret_password")
    MINIO_BUCKET: str = "shivi-evidence"
    MINIO_SECURE: bool = False
    
    # Cryptographic Security & JWT Bearer Token Lifespan
    JWT_SECRET: str = os.getenv("JWT_SECRET", "shivi_jwt_super_secret_key_2026")
    ALGORITHM: str = "HS256"
    # Long expiration (7 days) because field nodes may be deployed without identity re-authentication
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )


# Singleton settings instance accessed throughout the application
settings = Settings()

