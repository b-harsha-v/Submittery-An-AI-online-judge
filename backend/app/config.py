import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = True
    
    # Database Settings
    DATABASE_URL: str = "postgresql+psycopg2://postgres:password@localhost:5435/submittery"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6385/0"
    
    # JWT Auth
    JWT_SECRET_KEY: str = "b9165b4cbf4d8b2d15fb3ee32c1c69cf3be52ab5f891db87bf0d5b7a0d4c1cfc"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # Gemini API Key (RAG & Coding Assistant)
    GEMINI_API_KEY: str = ""
    
    # Compiler Service URL
    COMPILER_SERVICE_URL: str = "http://localhost:8002"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
