"""Code-generation application port."""

from __future__ import annotations

from typing import Protocol

from sttm.domain.ir import LogicalMappingIR


class GeneratedArtifact:
    """Generated downstream artifact.

    Concrete generators can extend this contract later with
    artifact-specific metadata.
    """

    def __init__(
        self,
        *,
        artifact_type: str,
        filename: str,
        content: str,
    ) -> None:
        self.artifact_type = artifact_type
        self.filename = filename
        self.content = content


class CodeGenerator(Protocol):
    """Port implemented by downstream code generators.

    The generator receives ONLY validated Logical Mapping IR.

    It must not perform semantic reasoning or metadata discovery.
    """

    def generate(
        self,
        ir: LogicalMappingIR,
    ) -> GeneratedArtifact:
        """Generate an artifact from Logical Mapping IR."""
        ...