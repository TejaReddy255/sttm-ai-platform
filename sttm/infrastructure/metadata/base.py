"""Technology-neutral contracts for metadata extraction adapters."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sttm.domain.metadata import MetadataDocument


class MetadataExtractor(Protocol):
    """Extract canonical metadata for one source technology or source type."""

    def extract(
        self,
        source_system: str,
        model_name: str,
        *,
        job_id: UUID | None = None,
    ) -> MetadataDocument:
        """Return canonical metadata for the requested logical model."""
        ...


class MetadataExtractorProvider(Protocol):
    """Application-facing provider for canonical metadata documents."""

    def get_metadata(
        self,
        source_system: str,
        model_name: str,
        *,
        job_id: UUID | None = None,
    ) -> MetadataDocument:
        """Return canonical metadata for a source and model."""
        ...


__all__ = ["MetadataExtractor", "MetadataExtractorProvider"]
