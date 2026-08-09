"""Application use case for the post-reasoning compilation boundary."""

from __future__ import annotations

from dataclasses import dataclass

from sttm.application.ports.code_generator import CodeGeneratorAgent, GeneratedCode
from sttm.application.ports.sttm_compiler import STTMCompilerPort
from sttm.domain.ir import LogicalMappingIR
from sttm.domain.sttm import STTMDocument


@dataclass(frozen=True)
class STTMGenerationResult:
    """A compiled STTM artifact and, optionally, its implementation code."""

    sttm: STTMDocument
    generated_code: GeneratedCode | None = None


class STTMGenerationService:
    """Keep compilation and code generation downstream of semantic reasoning.

    The service only accepts a LogicalMappingIR.  It cannot receive raw
    metadata, preventing downstream generators from making mapping decisions.
    """

    def __init__(
        self,
        compiler: STTMCompilerPort,
        code_generator: CodeGeneratorAgent | None = None,
    ) -> None:
        self._compiler = compiler
        self._code_generator = code_generator

    def compile(self, ir: LogicalMappingIR) -> STTMGenerationResult:
        """Compile an approved IR into an STTM document."""
        return STTMGenerationResult(sttm=self._compiler.compile(ir))

    def generate_code(
        self,
        ir: LogicalMappingIR,
        target_language: str,
    ) -> STTMGenerationResult:
        """Compile IR first, then generate implementation code from STTM."""
        if self._code_generator is None:
            raise ValueError("No downstream CodeGeneratorAgent has been configured.")
        sttm = self._compiler.compile(ir)
        return STTMGenerationResult(
            sttm=sttm,
            generated_code=self._code_generator.generate(sttm, target_language),
        )


__all__ = ["STTMGenerationResult", "STTMGenerationService"]
