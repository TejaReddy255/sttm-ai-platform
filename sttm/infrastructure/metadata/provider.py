"""Registry-backed metadata provider."""

from __future__ import annotations

from uuid import UUID

from sttm.domain.metadata import MetadataDocument
from sttm.infrastructure.metadata.base import MetadataExtractor
from sttm.infrastructure.metadata.registry import (
    MetadataExtractorRegistry,
)


class RegistryMetadataProvider:
    """Resolve a metadata extractor through a registry."""

    def __init__(
        self,
        registry: MetadataExtractorRegistry,
    ) -> None:
        """Initialize the provider.

        Args:
            registry: Metadata extractor registry.
        """
        self._registry = registry

    def get_metadata(
        self,
        source_system: str,
        model_name: str,
        *,
        job_id: UUID | None = None,
    ) -> MetadataDocument:
        """Extract metadata using the registered source adapter.

        The source-system value is used as the extractor key.

        Args:
            source_system: Registered source type.
            model_name: Model/schema/catalog name.
            job_id: Optional extraction job identifier.

        Returns:
            Canonical metadata document.
        """
        extractor: MetadataExtractor = self._registry.get(
            source_system,
        )

        return extractor.extract(
            source_system,
            model_name,
            job_id=job_id,
        )


__all__ = [
    "RegistryMetadataProvider",
]