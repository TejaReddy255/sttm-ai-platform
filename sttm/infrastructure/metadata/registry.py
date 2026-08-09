"""Registry for metadata extraction adapters."""

from __future__ import annotations

from sttm.infrastructure.metadata.base import MetadataExtractor


class MetadataExtractorRegistry:
    """Registry of metadata extractors.

    The registry allows different metadata sources to be plugged into
    the same application workflow.

    Example:

        registry.register("oracle", oracle_extractor)
        registry.register("snowflake", snowflake_extractor)
        registry.register("csv", csv_extractor)
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._extractors: dict[str, MetadataExtractor] = {}

    def register(
        self,
        source_type: str,
        extractor: MetadataExtractor,
    ) -> None:
        """Register a metadata extractor.

        Args:
            source_type: Stable source-type identifier.
            extractor: Extractor implementation.

        Raises:
            ValueError: If source type is already registered.
        """
        normalized = source_type.strip().lower()

        if not normalized:
            raise ValueError(
                "source_type cannot be empty.",
            )

        if normalized in self._extractors:
            raise ValueError(
                f"Metadata extractor {source_type!r} "
                "is already registered.",
            )

        self._extractors[normalized] = extractor

    def replace(
        self,
        source_type: str,
        extractor: MetadataExtractor,
    ) -> None:
        """Replace an existing extractor.

        Args:
            source_type: Source-type identifier.
            extractor: Extractor implementation.
        """
        normalized = source_type.strip().lower()

        if not normalized:
            raise ValueError(
                "source_type cannot be empty.",
            )

        self._extractors[normalized] = extractor

    def get(
        self,
        source_type: str,
    ) -> MetadataExtractor:
        """Get an extractor for a source type.

        Args:
            source_type: Source-type identifier.

        Returns:
            Registered extractor.

        Raises:
            KeyError: If no extractor is registered.
        """
        normalized = source_type.strip().lower()

        try:
            return self._extractors[normalized]
        except KeyError as exc:
            available = ", ".join(
                sorted(self._extractors),
            )

            raise KeyError(
                f"No metadata extractor registered for "
                f"{source_type!r}. "
                f"Available extractors: {available or 'none'}",
            ) from exc

    def has(
        self,
        source_type: str,
    ) -> bool:
        """Check whether an extractor is registered.

        Args:
            source_type: Source-type identifier.

        Returns:
            True when registered.
        """
        return (
            source_type.strip().lower()
            in self._extractors
        )

    def source_types(self) -> list[str]:
        """Return registered source types.

        Returns:
            Sorted source-type identifiers.
        """
        return sorted(
            self._extractors,
        )