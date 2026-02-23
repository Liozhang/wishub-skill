"""
WisHub Skill Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "wishub-skill"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # 认证配置
    AUTH_REQUIRED: bool = True
    AUTH_HEADER: str = "X-API-Key"

    # PostgreSQL 配置
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "wishub"
    POSTGRES_PASSWORD: str = "wishub"
    POSTGRES_DB: str = "wishub_skill"
    POSTGRES_POOL_SIZE: int = 20

    # MinIO 配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "wishub-skill-storage"
    MINIO_SECURE: bool = False

    # Elasticsearch 配置
    ES_HOST: str = "localhost:9200"
    ES_INDEX_PREFIX: str = "wishub-skill"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
