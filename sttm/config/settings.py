"""Application configuration for the STTM platform.

This module provides a single, strongly typed configuration object
for the application.

Configuration is loaded from environment variables and, when
available, a local ``.env`` file.

The module intentionally keeps infrastructure configuration in one
place so that application components do not access ``os.environ``
directly.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration.

    Configuration values are loaded from environment variables and
    optionally from a local ``.env`` file.

    Attributes:
        app_name: Logical application name.
        app_env: Runtime environment such as development or production.
        app_version: Application version.
        debug: Enables additional development diagnostics.
        data_dir: Base directory for local application data.
        artifact_dir: Directory for generated artifacts.
        log_dir: Directory for application logs.
        prompt_dir: Directory containing versioned prompt templates.
        database_url: SQLAlchemy database URL.
        sqlite_echo: Enables SQLAlchemy SQL logging.
        sqlite_foreign_keys: Enables SQLite foreign-key enforcement.
        google_cloud_project: Google Cloud project identifier.
        google_cloud_location: Vertex AI region.
        google_application_credentials: Optional ADC credential file.
        vertex_ai_enabled: Enables Vertex AI integration.
        vertex_ai_model: Gemini model used for semantic reasoning.
        vertex_ai_temperature: LLM temperature.
        vertex_ai_top_p: LLM top-p value.
        vertex_ai_max_output_tokens: Maximum generated tokens.
        vertex_ai_max_retries: Maximum Vertex AI retry attempts.
        vertex_ai_retry_min_seconds: Minimum retry delay.
        vertex_ai_retry_max_seconds: Maximum retry delay.
        ai_confidence_threshold: Minimum accepted AI confidence.
        ai_human_review_threshold: Confidence threshold for review.
        sttm_version: STTM contract version.
        sttm_column_count: Required number of exported STTM columns.
        langgraph_checkpoint_enabled: Enables workflow checkpoints.
        langgraph_max_retries: Maximum workflow retries.
        semantic_retrieval_enabled: Enables semantic retrieval.
        retrieval_top_k: Number of retrieved knowledge items.
        retrieval_min_score: Minimum retrieval similarity.
        cache_enabled: Enables application caching.
        prompt_cache_enabled: Enables prompt caching.
        embedding_cache_enabled: Enables embedding caching.
        ir_cache_enabled: Enables Logical Mapping IR caching.
        validation_enabled: Enables validation.
        validation_block_on_error: Blocks generation on validation errors.
        human_review_enabled: Enables human-review routing.
        log_level: Application logging level.
        log_format: Logging output format.
        log_include_timestamp: Includes timestamps in logs.
        log_include_correlation_id: Includes correlation IDs.
        observability_enabled: Enables observability.
        metrics_enabled: Enables metrics.
        tracing_enabled: Enables tracing.
        security_enabled: Enables security controls.
        redact_sensitive_log_data: Prevents sensitive data in logs.
        streamlit_server_port: Streamlit HTTP port.
        streamlit_server_address: Streamlit bind address.
        enable_sample_data: Enables development sample data.
        enable_debug_endpoints: Enables development-only endpoints.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    # ============================================================
    # Application
    # ============================================================

    app_name: str = Field(
        default="sttm-ai-platform",
        min_length=1,
    )

    app_env: str = Field(
        default="development",
        min_length=1,
    )

    app_version: str = Field(
        default="0.1.0",
        min_length=1,
    )

    debug: bool = False

    # ============================================================
    # Paths
    # ============================================================

    data_dir: Path = Path("./data")

    artifact_dir: Path = Path("./artifacts")

    log_dir: Path = Path("./logs")

    prompt_dir: Path = Path("./prompts")

    # ============================================================
    # Database
    # ============================================================

    database_url: str = "sqlite:///./data/sttm.db"

    sqlite_echo: bool = False

    sqlite_foreign_keys: bool = True

    # ============================================================
    # Google Cloud / Vertex AI
    # ============================================================

    google_cloud_project: str | None = None

    google_cloud_location: str = "us-central1"

    google_application_credentials: Path | None = None

    vertex_ai_enabled: bool = True

    # ============================================================
    # Gemini
    # ============================================================

    vertex_ai_model: str = "gemini-2.5-flash"

    vertex_ai_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
    )

    vertex_ai_top_p: float = Field(
        default=0.95,
        gt=0.0,
        le=1.0,
    )

    vertex_ai_max_output_tokens: int = Field(
        default=4096,
        gt=0,
    )

    # ============================================================
    # Vertex AI Retry
    # ============================================================

    vertex_ai_max_retries: int = Field(
        default=3,
        ge=0,
    )

    vertex_ai_retry_min_seconds: float = Field(
        default=1.0,
        ge=0.0,
    )

    vertex_ai_retry_max_seconds: float = Field(
        default=10.0,
        ge=0.0,
    )

    # ============================================================
    # Confidence
    # ============================================================

    ai_confidence_threshold: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
    )

    ai_human_review_threshold: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
    )

    # ============================================================
    # STTM
    # ============================================================

    sttm_version: str = "1.0"

    sttm_column_count: int = Field(
        default=16,
        gt=0,
    )

    # ============================================================
    # LangGraph
    # ============================================================

    langgraph_checkpoint_enabled: bool = True

    langgraph_max_retries: int = Field(
        default=2,
        ge=0,
    )

    # ============================================================
    # Semantic Retrieval
    # ============================================================

    semantic_retrieval_enabled: bool = True

    retrieval_top_k: int = Field(
        default=8,
        gt=0,
    )

    retrieval_min_score: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
    )

    # ============================================================
    # Caching
    # ============================================================

    cache_enabled: bool = True

    prompt_cache_enabled: bool = True

    embedding_cache_enabled: bool = True

    ir_cache_enabled: bool = True

    # ============================================================
    # Validation
    # ============================================================

    validation_enabled: bool = True

    validation_block_on_error: bool = True

    # ============================================================
    # Human Review
    # ============================================================

    human_review_enabled: bool = True

    # ============================================================
    # Logging
    # ============================================================

    log_level: str = "INFO"

    log_format: str = "text"

    log_include_timestamp: bool = True

    log_include_correlation_id: bool = True

    # ============================================================
    # Observability
    # ============================================================

    observability_enabled: bool = True

    metrics_enabled: bool = True

    tracing_enabled: bool = False

    # ============================================================
    # Security
    # ============================================================

    security_enabled: bool = True

    redact_sensitive_log_data: bool = True

    # ============================================================
    # Streamlit
    # ============================================================

    streamlit_server_port: int = Field(
        default=8501,
        ge=1,
        le=65535,
    )

    streamlit_server_address: str = "0.0.0.0"

    # ============================================================
    # Development
    # ============================================================

    enable_sample_data: bool = True

    enable_debug_endpoints: bool = False

    # ============================================================
    # Validators
    # ============================================================

    @field_validator("app_env")
    @classmethod
    def validate_app_environment(cls, value: str) -> str:
        """Validate the configured application environment.

        Args:
            value: Environment name.

        Returns:
            Normalized environment name.

        Raises:
            ValueError: If the environment is unsupported.
        """
        normalized = value.strip().lower()

        allowed = {
            "development",
            "test",
            "staging",
            "production",
        }

        if normalized not in allowed:
            raise ValueError(
                f"Unsupported application environment: {value!r}. "
                f"Expected one of: {sorted(allowed)}."
            )

        return normalized

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate and normalize the logging level.

        Args:
            value: Logging level.

        Returns:
            Uppercase logging level.

        Raises:
            ValueError: If the logging level is unsupported.
        """
        normalized = value.strip().upper()

        allowed = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        if normalized not in allowed:
            raise ValueError(
                f"Unsupported log level: {value!r}. "
                f"Expected one of: {sorted(allowed)}."
            )

        return normalized

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, value: str) -> str:
        """Validate the configured log format.

        Args:
            value: Logging format.

        Returns:
            Normalized logging format.

        Raises:
            ValueError: If the format is unsupported.
        """
        normalized = value.strip().lower()

        allowed = {"text", "json"}

        if normalized not in allowed:
            raise ValueError(
                f"Unsupported log format: {value!r}. "
                f"Expected one of: {sorted(allowed)}."
            )

        return normalized

    @field_validator("vertex_ai_retry_max_seconds")
    @classmethod
    def validate_retry_window(
        cls,
        value: float,
    ) -> float:
        """Validate that the maximum retry delay is positive.

        Args:
            value: Maximum retry delay.

        Returns:
            Validated retry delay.

        Raises:
            ValueError: If the value is not positive.
        """
        if value <= 0:
            raise ValueError(
                "vertex_ai_retry_max_seconds must be greater than zero."
            )

        return value

    @field_validator("sttm_column_count")
    @classmethod
    def validate_sttm_column_count(cls, value: int) -> int:
        """Validate the STTM external contract column count.

        Args:
            value: Number of exported STTM columns.

        Returns:
            Validated column count.

        Raises:
            ValueError: If the count is not exactly 16.
        """
        if value != 16:
            raise ValueError(
                "The STTM external contract requires exactly 16 columns."
            )

        return value

    @field_validator("google_cloud_project")
    @classmethod
    def normalize_google_project(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize the Google Cloud project identifier.

        Args:
            value: Google Cloud project identifier.

        Returns:
            Stripped project identifier or None.
        """
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None

    # ============================================================
    # Derived properties
    # ============================================================

    @property
    def is_production(self) -> bool:
        """Return whether the application runs in production.

        Returns:
            True when the configured environment is production.
        """
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Return whether the application runs in development.

        Returns:
            True when the configured environment is development.
        """
        return self.app_env == "development"

    @property
    def is_test(self) -> bool:
        """Return whether the application runs in tests.

        Returns:
            True when the configured environment is test.
        """
        return self.app_env == "test"

    def ensure_runtime_directories(self) -> None:
        """Create required local runtime directories.

        This method intentionally performs filesystem I/O only when
        explicitly called. Constructing ``Settings`` remains free of
        side effects.

        Raises:
            OSError: If a runtime directory cannot be created.
        """
        directories = (
            self.data_dir,
            self.artifact_dir,
            self.log_dir,
        )

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the application-wide settings singleton.

    Returns:
        Cached :class:`Settings` instance.

    Notes:
        The cache prevents repeatedly parsing environment variables
        throughout the application lifecycle. Tests can clear the
        cache using ``get_settings.cache_clear()``.
    """
    return Settings()