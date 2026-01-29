"""
Configuration management using environment variables
"""

import os
from typing import List
from functools import lru_cache
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""
    
    # App
    APP_NAME: str = "ParlayGalaxy Worker"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    # Security
    WORKER_SECRET: str = os.getenv("WORKER_SECRET", "dev-secret-change-in-production")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://parlaygalaxy.vercel.app",
        "https://galaxyparlay.vercel.app",
        "https://*.vercel.app",
    ]
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", os.getenv("NEXT_PUBLIC_SUPABASE_URL", ""))
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # API-Football
    APIFOOTBALL_API_KEY: str = os.getenv("APIFOOTBALL_API_KEY", "")
    APIFOOTBALL_BASE_URL: str = os.getenv(
        "APIFOOTBALL_BASE_URL",
        "https://v3.football.api-sports.io"
    )
    
    # Redis (Cache)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Rate Limiting
    API_RATE_LIMIT: float = 0.03  # 0.03 req/sec = ~2500/day
    API_BURST_CAPACITY: int = 10
    CIRCUIT_BREAKER_THRESHOLD: int = 3
    CIRCUIT_BREAKER_TIMEOUT: int = 300  # 5 minutes
    
    # Anthropic (Claude Haiku for AI Analysis)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Monitoring
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    
    # Model
    MODEL_VERSION: str = "v1.0.0"
    MIN_CALIBRATION_SAMPLES: int = 30
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
