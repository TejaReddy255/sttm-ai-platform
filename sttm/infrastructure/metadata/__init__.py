"""Metadata infrastructure adapters.

This package contains adapters that obtain metadata from external
systems and expose it as the canonical STTM MetadataDocument.
"""

from .base import (
    MetadataExtractor,
    MetadataExtractorProvider,
)
from .in_memory import (
    InMemoryMetadataExtractor,
)
from .registry import (
    MetadataExtractorRegistry,
)

__all__ = [
    "MetadataExtractor",
    "MetadataExtractorProvider",
    "InMemoryMetadataExtractor",
    "MetadataExtractorRegistry",
]