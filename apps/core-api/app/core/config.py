import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "ShiVi Operations Core API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    
    # Database: Default to local SQLite for immediate zero-config execution
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./shivi_local.db")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # MinIO / S3
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minio_admin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minio_secret_password")
    MINIO_BUCKET: str = "shivi-evidence"
    MINIO_SECURE: bool = False
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "shivi_jwt_super_secret_key_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
