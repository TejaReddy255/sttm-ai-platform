"""Structured logging infrastructure for the STTM platform.

The logging module provides:

- Consistent application logging.
- Correlation IDs for end-to-end workflow tracing.
- JSON logging for production environments.
- Human-readable logging for local development.
- Sensitive-data redaction.
- Context propagation for LangGraph and application runs.

The module intentionally avoids dependencies on Streamlit,
Vertex AI, LangGraph, or database infrastructure.
"""

from __future__ import annotations

import contextvars
import json
import logging
import re
import sys
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from sttm.config import Settings, get_settings


CORRELATION_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "sttm_correlation_id",
    default=None,
)

RUN_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "sttm_run_id",
    default=None,
)

USER_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "sttm_user_id",
    default=None,
)


_SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|"
    r"credential|private[_-]?key|access[_-]?token)",
    re.IGNORECASE,
)


class SensitiveDataRedactor:
    """Redact sensitive values from structured logging data."""

    REDACTED_VALUE = "***REDACTED***"

    def redact(
        self,
        value: Any,
    ) -> Any:
        """Recursively redact sensitive data.

        Args:
            value: Arbitrary value to sanitize.

        Returns:
            Sanitized value.
        """
        if isinstance(value, Mapping):
            return {
                str(key): (
                    self.REDACTED_VALUE
                    if _SENSITIVE_KEY_PATTERN.search(str(key))
                    else self.redact(item)
                )
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple, set)):
            return [
                self.redact(item)
                for item in value
            ]

        if isinstance(value, bytes):
            return "<bytes>"

        return value


class CorrelationContext:
    """Manage correlation and workflow context."""

    def __init__(
        self,
        *,
        correlation_id: str | None = None,
        run_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        """Initialize a correlation context.

        Args:
            correlation_id: Optional correlation identifier.
            run_id: Optional workflow execution identifier.
            user_id: Optional authenticated user identifier.
        """
        self.correlation_id = (
            correlation_id
            or str(uuid.uuid4())
        )
        self.run_id = run_id
        self.user_id = user_id

        self._correlation_token: contextvars.Token[str | None] | None = None
        self._run_token: contextvars.Token[str | None] | None = None
        self._user_token: contextvars.Token[str | None] | None = None

    def __enter__(self) -> CorrelationContext:
        """Activate the context.

        Returns:
            Active correlation context.
        """
        self._correlation_token = CORRELATION_ID.set(
            self.correlation_id,
        )

        self._run_token = RUN_ID.set(
            self.run_id,
        )

        self._user_token = USER_ID.set(
            self.user_id,
        )

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        """Restore the previous logging context.

        Args:
            exc_type: Exception type, if raised.
            exc_value: Exception instance, if raised.
            traceback: Exception traceback.
        """
        if self._correlation_token is not None:
            CORRELATION_ID.reset(
                self._correlation_token,
            )

        if self._run_token is not None:
            RUN_ID.reset(
                self._run_token,
            )

        if self._user_token is not None:
            USER_ID.reset(
                self._user_token,
            )


def get_correlation_id() -> str:
    """Return the current correlation ID.

    Returns:
        Current correlation ID, generating one when necessary.
    """
    correlation_id = CORRELATION_ID.get()

    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
        CORRELATION_ID.set(correlation_id)

    return correlation_id


def get_run_id() -> str | None:
    """Return the current workflow run ID.

    Returns:
        Current workflow run ID or None.
    """
    return RUN_ID.get()


def get_user_id() -> str | None:
    """Return the current user ID.

    Returns:
        Current user ID or None.
    """
    return USER_ID.get()


class ContextFilter(logging.Filter):
    """Inject STTM execution context into log records."""

    def filter(
        self,
        record: logging.LogRecord,
    ) -> bool:
        """Add correlation context to a log record.

        Args:
            record: Logging record.

        Returns:
            Always True.
        """
        record.correlation_id = get_correlation_id()
        record.run_id = get_run_id()
        record.user_id = get_user_id()

        return True


class StructuredFormatter(logging.Formatter):
    """Format records as structured JSON or text."""

    def __init__(
        self,
        *,
        json_format: bool,
        redact_sensitive_data: bool = True,
    ) -> None:
        """Initialize the formatter.

        Args:
            json_format: Whether to emit JSON.
            redact_sensitive_data: Whether sensitive fields are redacted.
        """
        super().__init__()

        self.json_format = json_format
        self.redact_sensitive_data = redact_sensitive_data
        self.redactor = SensitiveDataRedactor()

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        """Format a log record.

        Args:
            record: Python logging record.

        Returns:
            Formatted log message.
        """
        timestamp = datetime.now(
            timezone.utc,
        ).isoformat()

        message = record.getMessage()

        if self.redact_sensitive_data:
            message = self.redactor.redact(message)

        context = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "correlation_id": getattr(
                record,
                "correlation_id",
                None,
            ),
            "run_id": getattr(
                record,
                "run_id",
                None,
            ),
            "user_id": getattr(
                record,
                "user_id",
                None,
            ),
        }

        if record.exc_info:
            context["exception"] = self.formatException(
                record.exc_info,
            )

        if self.json_format:
            return json.dumps(
                context,
                default=str,
                ensure_ascii=False,
            )

        return self._format_text(context)

    @staticmethod
    def _format_text(
        context: Mapping[str, Any],
    ) -> str:
        """Format structured fields as readable text.

        Args:
            context: Structured logging context.

        Returns:
            Human-readable log message.
        """
        parts = [
            str(context["timestamp"]),
            str(context["level"]),
            f"[correlation_id={context['correlation_id']}]",
        ]

        if context.get("run_id"):
            parts.append(
                f"[run_id={context['run_id']}]",
            )

        if context.get("user_id"):
            parts.append(
                f"[user_id={context['user_id']}]",
            )

        parts.extend(
            [
                str(context["logger"]),
                str(context["message"]),
            ],
        )

        result = " ".join(parts)

        exception = context.get("exception")

        if exception:
            result = f"{result}\n{exception}"

        return result


def configure_logging(
    settings: Settings | None = None,
) -> None:
    """Configure application-wide logging.

    The configuration is idempotent. Repeated calls replace the
    handlers installed by this function rather than creating
    duplicate log entries.

    Args:
        settings: Optional application settings.

    Raises:
        OSError: If the configured log directory cannot be created.
    """
    resolved_settings = settings or get_settings()

    root_logger = logging.getLogger()

    root_logger.setLevel(
        getattr(
            logging,
            resolved_settings.log_level,
        ),
    )

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    formatter = StructuredFormatter(
        json_format=resolved_settings.log_format == "json",
        redact_sensitive_data=(
            resolved_settings.redact_sensitive_log_data
        ),
    )

    context_filter = ContextFilter()

    console_handler = logging.StreamHandler(
        sys.stdout,
    )

    console_handler.setFormatter(
        formatter,
    )

    console_handler.addFilter(
        context_filter,
    )

    root_logger.addHandler(
        console_handler,
    )

    resolved_settings.log_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = (
        resolved_settings.log_dir
        / "sttm.log"
    )

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )

    file_handler.setFormatter(
        formatter,
    )

    file_handler.addFilter(
        context_filter,
    )

    root_logger.addHandler(
        file_handler,
    )

    logging.captureWarnings(True)


def get_logger(
    name: str,
) -> logging.Logger:
    """Return a configured logger.

    Args:
        name: Logger name, normally ``__name__``.

    Returns:
        Configured Python logger.
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    """Logger adapter supporting structured context fields."""

    def process(
        self,
        msg: Any,
        kwargs: dict[str, Any],
    ) -> tuple[Any, dict[str, Any]]:
        """Inject adapter context into the logging message.

        Args:
            msg: Original log message.
            kwargs: Logging keyword arguments.

        Returns:
            Processed message and keyword arguments.
        """
        extra = kwargs.setdefault(
            "extra",
            {},
        )

        if isinstance(self.extra, Mapping):
            extra.update(
                self.extra,
            )

        return msg, kwargs


def get_context_logger(
    name: str,
    **context: Any,
) -> LoggerAdapter:
    """Create a logger with additional structured context.

    Args:
        name: Logger name.
        **context: Additional structured logging fields.

    Returns:
        Logger adapter.
    """
    return LoggerAdapter(
        get_logger(name),
        context,
    )


class LoggingTimer:
    """Simple elapsed-time measurement for workflow operations."""

    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
    ) -> None:
        """Initialize the timer.

        Args:
            logger: Logger used for timing events.
            operation: Operation being measured.
        """
        self.logger = logger
        self.operation = operation
        self._start: datetime | None = None

    def __enter__(self) -> LoggingTimer:
        """Start timing.

        Returns:
            Active timer.
        """
        self._start = datetime.now(
            timezone.utc,
        )

        self.logger.debug(
            "operation_started",
            extra={
                "operation": self.operation,
            },
        )

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        """Finish timing and log elapsed duration.

        Args:
            exc_type: Exception type, if raised.
            exc_value: Exception instance, if raised.
            traceback: Exception traceback.
        """
        if self._start is None:
            return

        elapsed = (
            datetime.now(timezone.utc)
            - self._start
        ).total_seconds()

        level = (
            logging.ERROR
            if exc_type is not None
            else logging.DEBUG
        )

        self.logger.log(
            level,
            "operation_completed",
            extra={
                "operation": self.operation,
                "elapsed_seconds": elapsed,
                "success": exc_type is None,
            },
        )


__all__ = [
    "CORRELATION_ID",
    "RUN_ID",
    "USER_ID",
    "CorrelationContext",
    "ContextFilter",
    "SensitiveDataRedactor",
    "StructuredFormatter",
    "configure_logging",
    "get_correlation_id",
    "get_run_id",
    "get_user_id",
    "get_logger",
    "get_context_logger",
    "LoggerAdapter",
    "LoggingTimer",
]