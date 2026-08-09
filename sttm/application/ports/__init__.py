"""Application ports for the STTM platform.

Ports define the contracts between the application layer and
external adapters.

Upstream:
    MetadataProvider

Downstream:
    CodeGenerator
"""

from .code_generator import (
    CodeGeneratorAgent,
    GeneratedCode,
)

from .metadata import (
    MetadataProvider,
)
from .sttm_compiler import STTMCompilerPort

__all__ = [
    "CodeGeneratorAgent",
    "GeneratedCode",
    "MetadataProvider",
    "STTMCompilerPort",
]
