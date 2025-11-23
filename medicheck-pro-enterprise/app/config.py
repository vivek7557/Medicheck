import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AppConfig(BaseModel):
    """Application configuration model"""
    
    # API Keys
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    google_api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    pubmed_api_key: str = Field(default_factory=lambda: os.getenv("PUBMED_API_KEY", ""))
    
    # Database Configuration
    mongodb_uri: str = Field(default_factory=lambda: os.getenv("MONGODB_URI", "mongodb://localhost:27017/medicheck"))
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    
    # Application Settings
    streamlit_port: int = Field(default_factory=lambda: int(os.getenv("STREAMLIT_SERVER_PORT", "8501")))
    debug_mode: bool = Field(default_factory=lambda: os.getenv("DEBUG_MODE", "false").lower() == "true")
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    
    # Vector Store Configuration
    vector_store_path: str = Field(default_factory=lambda: os.getenv("VECTOR_STORE_PATH", "./vector_store"))
    chroma_db_path: str = Field(default_factory=lambda: os.getenv("CHROMA_DB_PATH", "./chroma_db"))
    
    # Observability
    otel_exporter_endpoint: str = Field(default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))
    prometheus_port: int = Field(default_factory=lambda: int(os.getenv("PROMETHEUS_PORT", "9090")))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global configuration instance
config = AppConfig()

def get_config() -> AppConfig:
    """Get the application configuration"""
    return config