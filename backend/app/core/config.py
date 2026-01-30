from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union, Any
import json


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://cycling:cycling@postgres:5432/cycling_lineage"
    
    # Application
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "ChainLines"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        elif isinstance(v, list):
            # If it's already a list, ensure it's not a nested list like [['a', 'b']]
            if len(v) == 1 and isinstance(v[0], list):
                return v[0]
            return v
        return v

    # Timeline cache
    TIMELINE_CACHE_ENABLED: bool = False
    TIMELINE_CACHE_TTL_SECONDS: int = 300

    # Scraper settings
    SCRAPER_ENABLED: bool = False
    SCRAPER_MIN_DELAY: int = 15  # seconds between requests to same domain
    SCRAPER_USER_AGENT: str = "CyclingLineageBot/1.0"
    SCRAPER_INTERVAL: int = 300  # seconds between full cycles
    
    # Auth settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:5173/auth/callback"
    
    # Admin settings
    ADMIN_EMAILS: List[str] = []
    
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_STRONG_RANDOM_SECRET"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth scopes
    GOOGLE_SCOPES: List[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
