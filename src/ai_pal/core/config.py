"""Configuration management for AI Pal."""

from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Main configuration for AI Pal."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys (Optional)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None

    # Local Model Configuration
    local_models_path: Path = Field(default=Path("./models"))
    default_local_model: Optional[str] = None
    use_gpu: bool = True
    max_gpu_memory: float = Field(default=0.8, ge=0.1, le=1.0)
    cpu_threads: int = Field(default=4, ge=1)

    # Privacy & Security
    enable_pii_scrubbing: bool = True
    encryption_key: Optional[str] = None
    max_history_days: int = Field(default=90, ge=1)
    local_only_mode: bool = False

    # Module Configuration
    enable_ethics_module: bool = True  # Cannot be disabled
    enable_echo_chamber_buster: bool = True
    enable_learning_module: bool = True
    enable_dream_module: bool = True
    enable_personal_data_module: bool = True

    # Database
    database_url: str = "sqlite:///./data/ai_pal.db"
    redis_url: Optional[str] = "redis://localhost:6379/0"

    # API Server
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1024, le=65535)
    api_reload: bool = False

    # Logging
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_file: Path = Field(default=Path("./logs/ai_pal.log"))

    # Agency Calculus (AC-AI) Framework
    enable_four_gates: bool = True
    min_agency_delta: float = Field(default=0.0)
    max_epistemic_debt: float = Field(default=0.3, ge=0.0, le=1.0)
    min_bhir: float = Field(default=1.0, ge=0.0)
    max_goodhart_divergence: float = Field(default=0.2, ge=0.0, le=1.0)

    # Dream Module
    dream_schedule: str = "0 3 * * *"  # Cron format
    dream_duration: int = Field(default=60, ge=1)  # minutes

    # Learning Module
    default_vark_style: str = Field(default="detect", pattern="^(Visual|Aural|Read|Kinesthetic|detect)$")
    learning_velocity_window: int = Field(default=7, ge=1)  # days

    @validator("enable_ethics_module")
    def ethics_module_required(cls, v: bool) -> bool:
        """Ethics module cannot be disabled."""
        if not v:
            raise ValueError("Ethics module is required and cannot be disabled")
        return v

    @validator("local_models_path", "log_file")
    def ensure_path_exists(cls, v: Path) -> Path:
        """Ensure directories exist for paths."""
        if v.suffix:  # It's a file path
            v.parent.mkdir(parents=True, exist_ok=True)
        else:  # It's a directory path
            v.mkdir(parents=True, exist_ok=True)
        return v

    def get_enabled_modules(self) -> list[str]:
        """Get list of enabled module names."""
        modules = []
        if self.enable_ethics_module:
            modules.append("ethics")
        if self.enable_echo_chamber_buster:
            modules.append("echo_chamber_buster")
        if self.enable_learning_module:
            modules.append("learning")
        if self.enable_dream_module:
            modules.append("dream")
        if self.enable_personal_data_module:
            modules.append("personal_data")
        return modules

    def has_cloud_api_keys(self) -> bool:
        """Check if any cloud API keys are configured."""
        return bool(
            self.openai_api_key or self.anthropic_api_key or self.cohere_api_key
        )

    def can_use_cloud(self) -> bool:
        """Check if cloud LLM access is available and allowed."""
        return not self.local_only_mode and self.has_cloud_api_keys()


# Global settings instance
settings = Settings()
