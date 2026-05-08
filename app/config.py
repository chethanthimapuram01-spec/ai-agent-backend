"""
Production Configuration Module

Manages environment-specific settings for the AI Agent Backend.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # ====================
    # REQUIRED SETTINGS
    # ====================
    
    openai_api_key: str = Field(..., description="OpenAI API key")
    
    # ====================
    # SERVER CONFIGURATION
    # ====================
    
    environment: str = Field(default="development", description="Environment: development, staging, production")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of uvicorn workers")
    log_level: str = Field(default="info", description="Logging level")
    
    # ====================
    # DATABASE
    # ====================
    
    database_url: Optional[str] = Field(default=None, description="PostgreSQL connection string")
    
    # ====================
    # VECTOR DATABASE
    # ====================
    
    chroma_persist_dir: str = Field(default="./chroma_db", description="ChromaDB persistence directory")
    chroma_collection: str = Field(default="documents", description="ChromaDB collection name")
    
    # ====================
    # FILE UPLOAD
    # ====================
    
    upload_dir: str = Field(default="./uploads", description="Upload directory")
    max_file_size_mb: int = Field(default=10, description="Max file size in MB")
    allowed_extensions: str = Field(default=".pdf,.docx", description="Allowed file extensions")
    
    # ====================
    # AI MODEL CONFIG
    # ====================
    
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI chat model")
    openai_embedding_model: str = Field(default="text-embedding-ada-002", description="OpenAI embedding model")
    llm_temperature: float = Field(default=0.7, description="LLM temperature")
    max_tokens: int = Field(default=2000, description="Max tokens for LLM")
    
    # ====================
    # TRACE LOGGING
    # ====================
    
    trace_db_path: str = Field(default="./traces.db", description="SQLite trace database path")
    enable_trace_logging: bool = Field(default=True, description="Enable trace logging")
    
    # ====================
    # SESSION MANAGEMENT
    # ====================
    
    session_timeout_minutes: int = Field(default=60, description="Session timeout in minutes")
    
    # ====================
    # CORS
    # ====================
    
    cors_origins: str = Field(default="*", description="CORS allowed origins")
    cors_methods: str = Field(default="GET,POST,PUT,DELETE,OPTIONS", description="CORS allowed methods")
    cors_headers: str = Field(default="*", description="CORS allowed headers")
    
    # ====================
    # MONITORING
    # ====================
    
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    app_name: str = Field(default="ai-agent-backend", description="Application name")
    
    # ====================
    # DEVELOPMENT
    # ====================
    
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    enable_docs: bool = Field(default=True, description="Enable API docs")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as list"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def allowed_extensions_list(self) -> list[str]:
        """Get allowed file extensions as list"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.max_file_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings
    
    Returns:
        Settings instance
    """
    return settings


# Production-specific configurations
if settings.is_production:
    # Disable debug and reload in production
    settings.debug = False
    settings.reload = False
    
    # Ensure critical settings are configured
    assert settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here", \
        "OPENAI_API_KEY must be set in production"
    
    # Warn about insecure CORS in production
    if settings.cors_origins == "*":
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("CORS is set to allow all origins in production. This may be insecure!")
