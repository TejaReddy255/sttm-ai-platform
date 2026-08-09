"""Application layer for the STTM platform.

The application layer coordinates use cases and workflow execution.

It sits between the domain layer and infrastructure adapters.

Architecture:

    Infrastructure
          ↓
    Application Services
          ↓
        Domain

This package exposes:

* Mapping orchestration and services
* Application-level request/response types

It does not expose:

* Infrastructure adapters
* Streamlit UI code
* LangGraph or Vertex AI internals
"""

from .services import (
    AnalysisProvider,
    MappingAnalysisResult,
    MappingGenerationResult,
    MappingIRBuilder,
    MappingOrchestrator,
    MappingRequest,
    SemanticReasoningResult,
    STTMGenerationResult,
    STTMGenerationService,
)

__all__ = [
    # Mapping services
    "AnalysisProvider",
    "MappingAnalysisResult",
    "MappingGenerationResult",
    "MappingIRBuilder",
    "MappingOrchestrator",
    "MappingRequest",
    "SemanticReasoningResult",
    "STTMGenerationResult",
    "STTMGenerationService",
]
