"""Application port for deterministic IR-to-STTM compilation."""

from __future__ import annotations

from typing import Protocol

from sttm.domain.ir import LogicalMappingIR
from sttm.domain.sttm import STTMDocument


class STTMCompilerPort(Protocol):
    """Compile a validated logical mapping into the portable STTM contract."""

    def compile(self, ir: LogicalMappingIR) -> STTMDocument:
        """Create an STTM artifact from an approved Logical Mapping IR."""
        ...


__all__ = ["STTMCompilerPort"]
