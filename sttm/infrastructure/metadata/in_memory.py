"""In-memory metadata adapter for local development and tests."""

from __future__ import annotations

from uuid import UUID

from sttm.domain.metadata import MetadataDocument


class InMemoryMetadataExtractor:
    """Serve pre-validated canonical metadata without external I/O."""

    def __init__(self) -> None:
        self._documents: dict[tuple[str, str], MetadataDocument] = {}

    def register(
        self,
        source_system: str,
        model_name: str,
        document: MetadataDocument,
    ) -> None:
        """Register metadata for an exact source-system/model pair."""
        key = self._key(source_system, model_name)
        if key in self._documents:
            raise ValueError(
                f"Metadata is already registered for {source_system!r}/{model_name!r}.",
            )
        self._documents[key] = document

    def extract(
        self,
        source_system: str,
        model_name: str,
        *,
        job_id: UUID | None = None,
    ) -> MetadataDocument:
        """Return the registered document; job ID is accepted for port parity."""
        del job_id
        key = self._key(source_system, model_name)
        try:
            return self._documents[key]
        except KeyError as exc:
            raise KeyError(
                f"No metadata is registered for {source_system!r}/{model_name!r}.",
            ) from exc

    @staticmethod
    def _key(source_system: str, model_name: str) -> tuple[str, str]:
        source = source_system.strip().casefold()
        model = model_name.strip().casefold()
        if not source or not model:
            raise ValueError("source_system and model_name cannot be empty.")
        return source, model


__all__ = ["InMemoryMetadataExtractor"]
