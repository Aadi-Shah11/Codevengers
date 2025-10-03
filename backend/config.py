# Database and application configuration

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str = "sqlite:///./campus_access_control.db"
    
    # API configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # OCR configuration
    OCR_CONFIDENCE_THRESHOLD: float = 0.7
    MAX_VIDEO_SIZE_MB: int = 10
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"

settings = Settings()