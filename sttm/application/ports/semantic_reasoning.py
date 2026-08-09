"""Semantic reasoning application port.

This port separates the application workflow from the AI reasoning
implementation.

The concrete adapter may use:

* Vertex AI
* Gemini
* LangGraph
* deterministic rules
* a mock implementation for tests

The application layer must depend only on this contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from sttm.application.services.mapping_orchestrator import (
        MappingAnalysisResult,
        MappingRequest,
        SemanticReasoningResult,
    )


class SemanticReasoningProvider(Protocol):
    """Port for semantic reasoning.

    The provider receives deterministic analysis and produces semantic
    decisions.

    It must not perform downstream code generation.
    """

    def reason(
        self,
        request: MappingRequest,
        analysis: MappingAnalysisResult,
    ) -> SemanticReasoningResult:
        """Produce semantic reasoning results.

        Args:
            request: Mapping request.
            analysis: Deterministic analysis evidence.

        Returns:
            Semantic reasoning result.
        """
        ...
