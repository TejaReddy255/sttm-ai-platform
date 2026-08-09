"""Application port for the downstream Code Generator Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sttm.domain.sttm import STTMDocument


@dataclass(frozen=True)
class GeneratedCode:
    """Code produced by the Code Generator Agent.

    Attributes:
        language: Target implementation language.
        filename: Suggested output filename.
        content: Generated source code.
        explanation: Agent-generated explanation of the implementation.
    """

    language: str
    filename: str
    content: str
    explanation: str | None = None


class CodeGeneratorAgent(Protocol):
    """Port implemented by the downstream AI code-generation agent.

    Input:
        STTMDocument

    Output:
        GeneratedCode

    The implementation may use Gemini/Vertex AI and an agentic
    workflow, but those dependencies must not leak into the
    application or domain layers.
    """

    def generate(
        self,
        sttm: STTMDocument,
        target_language: str,
    ) -> GeneratedCode:
        """Generate implementation code from STTM."""
        ...