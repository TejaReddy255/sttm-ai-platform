"""Identifier generation utilities for the STTM platform.

The platform contains many entities that need stable identifiers,
including metadata objects, mappings, workflow executions, audit
records, validation results, and generated artifacts.

This module centralizes identifier generation so individual
components do not implement their own ID conventions.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Final


_UUID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[0-9a-f]{8}-"
    r"[0-9a-f]{4}-"
    r"[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-"
    r"[0-9a-f]{12}$",
    re.IGNORECASE,
)


class IDGenerator:
    """Generate UUID-based platform identifiers.

    UUID4 is used for identifiers that require uniqueness without
    relying on a central database sequence.

    The class is intentionally stateless and therefore safe to
    instantiate wherever dependency injection requires an ID
    generator.
    """

    def generate(self) -> str:
        """Generate a UUID4 identifier.

        Returns:
            UUID4 string.
        """
        return str(uuid.uuid4())

    def generate_prefixed(
        self,
        prefix: str,
    ) -> str:
        """Generate a prefixed UUID identifier.

        Args:
            prefix: Short entity prefix such as ``map`` or ``run``.

        Returns:
            Identifier in the form ``prefix_uuid``.

        Raises:
            ValueError: If the prefix is invalid.
        """
        normalized_prefix = normalize_prefix(prefix)

        return f"{normalized_prefix}_{self.generate()}"

    def generate_run_id(self) -> str:
        """Generate an identifier for a workflow execution.

        Returns:
            Workflow run identifier.
        """
        return self.generate_prefixed("run")

    def generate_mapping_id(self) -> str:
        """Generate an identifier for a mapping.

        Returns:
            Mapping identifier.
        """
        return self.generate_prefixed("map")

    def generate_metadata_id(self) -> str:
        """Generate an identifier for a metadata object.

        Returns:
            Metadata identifier.
        """
        return self.generate_prefixed("meta")

    def generate_validation_id(self) -> str:
        """Generate an identifier for a validation result.

        Returns:
            Validation identifier.
        """
        return self.generate_prefixed("val")

    def generate_artifact_id(self) -> str:
        """Generate an identifier for a generated artifact.

        Returns:
            Artifact identifier.
        """
        return self.generate_prefixed("artifact")

    def generate_audit_id(self) -> str:
        """Generate an identifier for an audit event.

        Returns:
            Audit event identifier.
        """
        return self.generate_prefixed("audit")


def normalize_prefix(prefix: str) -> str:
    """Normalize an identifier prefix.

    Prefixes are restricted to lowercase alphanumeric characters
    and underscores.

    Args:
        prefix: Raw identifier prefix.

    Returns:
        Normalized prefix.

    Raises:
        ValueError: If the prefix is empty or invalid.
    """
    normalized = prefix.strip().lower()

    if not normalized:
        raise ValueError(
            "Identifier prefix cannot be empty.",
        )

    if not re.fullmatch(
        r"[a-z][a-z0-9_]*",
        normalized,
    ):
        raise ValueError(
            "Identifier prefix must start with a lowercase letter "
            "and contain only lowercase letters, digits, and underscores.",
        )

    return normalized


def is_valid_uuid(value: str) -> bool:
    """Determine whether a value is a valid UUID4 string.

    Args:
        value: Candidate UUID.

    Returns:
        True when the value matches the UUID format and version.
    """
    if not _UUID_PATTERN.fullmatch(value):
        return False

    try:
        parsed = uuid.UUID(value)
    except ValueError:
        return False

    return parsed.version == 4


def is_valid_identifier(value: str) -> bool:
    """Determine whether a value is a valid platform identifier.

    Both plain UUIDs and prefixed UUIDs are accepted.

    Args:
        value: Candidate identifier.

    Returns:
        True when the identifier is valid.
    """
    if is_valid_uuid(value):
        return True

    parts = value.split("_", maxsplit=1)

    if len(parts) != 2:
        return False

    prefix, identifier = parts

    try:
        normalize_prefix(prefix)
    except ValueError:
        return False

    return is_valid_uuid(identifier)


def generate_correlation_id() -> str:
    """Generate an identifier for request correlation.

    Returns:
        UUID4 correlation identifier.
    """
    return str(uuid.uuid4())


def generate_timestamp_id(
    prefix: str,
) -> str:
    """Generate a time-aware identifier.

    The timestamp provides human-readable ordering information,
    while the UUID suffix maintains uniqueness.

    Args:
        prefix: Identifier prefix.

    Returns:
        Identifier containing UTC timestamp and UUID.

    Example:
        ``run_20260809T120000Z_a1b2c3...``
    """
    normalized_prefix = normalize_prefix(prefix)

    timestamp = datetime.now(
        timezone.utc,
    ).strftime("%Y%m%dT%H%M%SZ")

    return (
        f"{normalized_prefix}_"
        f"{timestamp}_"
        f"{uuid.uuid4()}"
    )


__all__ = [
    "IDGenerator",
    "generate_correlation_id",
    "generate_timestamp_id",
    "is_valid_identifier",
    "is_valid_uuid",
    "normalize_prefix",
]