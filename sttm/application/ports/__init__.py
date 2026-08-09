"""Application ports for the STTM platform.

Ports define the contracts between the application layer and
external adapters.

Upstream:
    MetadataProvider

Downstream:
    CodeGenerator
"""

from .code_generator import (
    CodeGenerator,
    GeneratedArtifact,
)

from .metadata import (
    MetadataProvider,
)

__all__ = [
    "CodeGenerator",
    "GeneratedArtifact",
    "MetadataProvider",
]