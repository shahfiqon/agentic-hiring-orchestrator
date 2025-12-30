"""Centralized configuration management using Pydantic settings.

This module provides type-safe configuration loaded from environment variables.
All settings are validated at startup to catch misconfigurations early.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Configuration is organized into logical groups:
    - LLM Configuration: Provider selection and API settings
    - llama.cpp Server Configuration: External server connection settings
    - OpenAI Configuration: Alternative provider settings
    - Workflow Parameters: Feature flags and execution settings
    - Output Configuration: Response formatting and content settings
    - API Configuration: FastAPI server settings
    - Observability: Logging and tracing configuration
    """

    # ============================================================================
    # LLM Configuration
    # ============================================================================
    llm_provider: str = Field(
        default="llamacpp-server",
        description="LLM provider to use: 'llamacpp-server', 'openai', or 'anthropic'"
    )

    # ============================================================================
    # llama.cpp Server Configuration (default provider)
    # ============================================================================
    llamacpp_base_url: str = Field(
        default="http://localhost:8080/v1",
        description="Base URL for llama.cpp server with OpenAI-compatible API"
    )
    llamacpp_api_key: str = Field(
        default="not-needed",
        description="API key for llama.cpp server (usually not required)"
    )

    # ============================================================================
    # Common LLM Settings
    # ============================================================================
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for LLM responses"
    )
    max_tokens: int = Field(
        default=8192,
        gt=0,
        description="Maximum tokens in LLM responses"
    )

    # ============================================================================
    # OpenAI Configuration (alternative provider)
    # ============================================================================
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key (required if llm_provider='openai')"
    )
    openai_model_name: str = Field(
        default="gpt-4o-2024-08-06",
        description="OpenAI model name with structured output support"
    )

    # ============================================================================
    # Anthropic Configuration (alternative provider)
    # ============================================================================
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key (required if llm_provider='anthropic')"
    )
    anthropic_model_name: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Anthropic model name (claude-3-5-sonnet-20241022, claude-3-opus-20240229, etc.)"
    )

    # ============================================================================
    # Workflow Parameters
    # ============================================================================
    enable_working_memory: bool = Field(
        default=True,
        description="Enable two-pass evaluation with working memory extraction"
    )
    enable_product_agent: bool = Field(
        default=False,
        description="Enable product agent in panel (MVP toggle)"
    )
    max_panel_agents: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of concurrent panel agents"
    )
    rubric_categories_count: int = Field(
        default=5,
        ge=3,
        le=10,
        description="Number of categories in generated rubrics"
    )
    parallel_execution: bool = Field(
        default=True,
        description="Enable parallel execution of panel agents (fan-out/fan-in)"
    )
    disagreement_threshold: float = Field(
        default=1.0,
        ge=0.0,
        le=5.0,
        description="Score delta to flag disagreements between passes"
    )

    # ============================================================================
    # Output Configuration
    # ============================================================================
    max_interview_questions_per_agent: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum interview questions per agent in interview plan"
    )
    include_evidence_citations: bool = Field(
        default=True,
        description="Require evidence citations in scoring justifications"
    )
    output_format: str = Field(
        default="json",
        description="Output format for decision packets"
    )

    # ============================================================================
    # API Configuration
    # ============================================================================
    api_host: str = Field(
        default="0.0.0.0",
        description="Host for FastAPI server"
    )
    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port for FastAPI server"
    )
    api_reload: bool = Field(
        default=True,
        description="Enable auto-reload for development"
    )

    # ============================================================================
    # Observability
    # ============================================================================
    langchain_tracing_v2: bool = Field(
        default=False,
        description="Enable LangSmith tracing for debugging"
    )
    langchain_api_key: Optional[str] = Field(
        default=None,
        description="LangSmith API key for tracing"
    )
    langchain_project: str = Field(
        default="agentic-hiring-orchestrator",
        description="LangSmith project name"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    # ============================================================================
    # Pydantic Configuration
    # ============================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore unknown environment variables
    )

    @model_validator(mode='after')
    def validate_settings(self) -> 'Settings':
        """Validate cross-field constraints and provider-specific requirements."""
        # Validate LLM provider
        valid_providers = ["llamacpp-server", "openai", "anthropic"]
        if self.llm_provider not in valid_providers:
            raise ValueError(
                f"llm_provider must be one of {valid_providers}, "
                f"got '{self.llm_provider}'"
            )

        # Validate OpenAI configuration if selected
        if self.llm_provider == "openai":
            if not self.openai_api_key or self.openai_api_key == "your_openai_api_key_here":
                raise ValueError(
                    "openai_api_key must be set when llm_provider='openai'"
                )

        # Validate Anthropic configuration if selected
        if self.llm_provider == "anthropic":
            if not self.anthropic_api_key or self.anthropic_api_key == "your_anthropic_api_key_here":
                raise ValueError(
                    "anthropic_api_key must be set when llm_provider='anthropic'"
                )

        # Validate llama.cpp server URL format
        if self.llm_provider == "llamacpp-server":
            if not self.llamacpp_base_url.startswith(("http://", "https://")):
                raise ValueError(
                    f"llamacpp_base_url must be a valid URL, "
                    f"got '{self.llamacpp_base_url}'"
                )

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"log_level must be one of {valid_log_levels}, "
                f"got '{self.log_level}'"
            )

        # Validate output format
        valid_formats = ["json"]
        if self.output_format not in valid_formats:
            raise ValueError(
                f"output_format must be one of {valid_formats}, "
                f"got '{self.output_format}'"
            )

        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    This function uses LRU cache to ensure settings are loaded once
    and reused across the application, preventing redundant environment reads.

    Returns:
        Settings: Validated settings instance
    """
    return Settings()
