import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str
    gemini_api_key: str
    redis_url: str = "redis://localhost:6379"
    log_level: str = "INFO"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list = ["*"]
    rate_limit_per_minute: int = 10
    cache_ttl_seconds: int = 3600
    search_rate_limit_delay: float = 1.0
    max_search_results: int = 10
    request_timeout: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()