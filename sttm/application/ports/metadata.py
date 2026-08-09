"""Metadata extraction application port."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sttm.domain.metadata import MetadataDocument


class MetadataProvider(Protocol):
    """Port for obtaining canonical metadata.

    Implementations may read metadata from:

    * JDBC/ODBC
    * Oracle
    * PostgreSQL
    * Snowflake
    * BigQuery
    * CSV
    * JSON
    * API sources
    * Previously extracted metadata
    """

    def get_metadata(
        self,
        source_system: str,
        model_name: str,
        *,
        job_id: UUID | None = None,
    ) -> MetadataDocument:
        """Return canonical metadata for a source model."""
        