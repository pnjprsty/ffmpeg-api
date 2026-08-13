"""
Application configuration using Pydantic Settings.
Loads configuration from .env file and environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""
    
    # Output directory configuration
    output_dir: str = Field(
        default="/output",
        description="Directory for output files (videos, logs, etc)",
        alias="OUTPUT_DIR"
    )
    
    # Render timeout
    render_timeout: int = Field(
        default=300,
        description="Timeout for rendering process in seconds",
        alias="RENDER_TIMEOUT"
    )
    
    # FastAPI settings
    host: str = Field(
        default="127.0.0.1",
        description="API server host",
        alias="HOST"
    )
    
    port: int = Field(
        default=9000,
        description="API server port",
        alias="PORT"
    )
    
    reload: bool = Field(
        default=False,
        description="Enable auto-reload on code changes",
        alias="RELOAD"
    )
    
    log_level: str = Field(
        default="info",
        description="Logging level (debug, info, warning, error, critical)",
        alias="LOG_LEVEL"
    )
    
    # Docker settings (optional)
    puid: int = Field(
        default=1000,
        description="Process user ID (Docker)",
        alias="PUID"
    )
    
    pgid: int = Field(
        default=1000,
        description="Process group ID (Docker)",
        alias="PGID"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    
    def get_output_dir(self) -> str:
        """Get output directory with validation."""
        return self.output_dir
    
    def get_render_timeout(self) -> int:
        """Get render timeout in seconds."""
        return self.render_timeout


# Global settings instance
settings = Settings()
