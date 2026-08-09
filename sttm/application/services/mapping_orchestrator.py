"""Application orchestration for STTM mapping generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sttm.application.ports.code_generator import CodeGenerator
from sttm.application.ports.metadata import MetadataProvider
from sttm.application.ports.semantic_reasoning import (
    SemanticReasoningProvider,
)
from sttm.domain.ir import LogicalMappingIR
from sttm.domain.ir import LogicalMappingIRValidator


@dataclass(frozen=True)
class MappingRequest:
    """Request to generate mappings."""

    source_system: str
    target_system: str
    source_model: str
    target_model: str
    target_table_id: UUID
    mapping_job_id: UUID | None = None


@dataclass(frozen=True)
class MappingAnalysisResult:
    """Result produced by deterministic metadata analysis."""

    analysis_id: UUID
    relationship_graph: object
    cardinality_graph: object
    grain_graph: object
    dependency_graph: object
    candidate_paths: object


@dataclass(frozen=True)
class SemanticReasoningResult:
    """Result produced by semantic reasoning."""

    reasoning_id: UUID
    alignments: object
    intents: object
    business_rules: object
    transformation_plans: object
    conflicts: object


@dataclass(frozen=True)
class MappingGenerationResult:
    """Final result of the mapping workflow."""

    job_id: UUID
    analysis: MappingAnalysisResult
    reasoning: SemanticReasoningResult
    ir: LogicalMappingIR
    generated_at: datetime


class AnalysisProvider:
    """Application port for deterministic analysis."""

    def analyze(
        self,
        request: MappingRequest,
    ) -> MappingAnalysisResult:
        """Analyze metadata for a mapping request."""
        raise NotImplementedError


class MappingIRBuilder:
    """Application port for constructing Logical Mapping IR."""

    def build(
        self,
        request: MappingRequest,
        analysis: MappingAnalysisResult,
        reasoning: SemanticReasoningResult,
    ) -> LogicalMappingIR:
        """Build Logical Mapping IR."""
        raise NotImplementedError


class MappingOrchestrator:
    """Coordinate the STTM mapping workflow."""

    def __init__(
        self,
        analysis_provider: AnalysisProvider,
        semantic_provider: SemanticReasoningProvider,
        ir_builder: MappingIRBuilder,
        ir_validator: LogicalMappingIRValidator | None = None,
        metadata_provider: MetadataProvider | None = None,
        code_generator: CodeGenerator | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            analysis_provider: Deterministic analysis implementation.
            semantic_provider: Semantic reasoning implementation.
            ir_builder: Logical Mapping IR builder.
            ir_validator: IR validation service.
            metadata_provider: Optional metadata provider.
            code_generator: Optional downstream generator.
        """
        self._analysis_provider = analysis_provider
        self._semantic_provider = semantic_provider
        self._ir_builder = ir_builder
        self._ir_validator = (
            ir_validator
            or LogicalMappingIRValidator()
        )
        self._metadata_provider = metadata_provider
        self._code_generator = code_generator

    def generate(
        self,
        request: MappingRequest,
    ) -> MappingGenerationResult:
        """Generate and validate Logical Mapping IR.

        The workflow is:

            Metadata
                ↓
            Analysis
                ↓
            Semantic Reasoning
                ↓
            IR Construction
                ↓
            IR Validation

        Code generation happens after this boundary.
        """
        job_id = (
            request.mapping_job_id
            or uuid4()
        )

        analysis = self._analysis_provider.analyze(
            request,
        )

        reasoning = self._semantic_provider.reason(
            request,
            analysis,
        )

        ir = self._ir_builder.build(
            request,
            analysis,
            reasoning,
        )

        self._ir_validator.assert_valid(
            ir,
        )

        return MappingGenerationResult(
            job_id=job_id,
            analysis=analysis,
            reasoning=reasoning,
            ir=ir,
            generated_at=datetime.now(timezone.utc),
        )


__all__ = [
    "AnalysisProvider",
    "MappingAnalysisResult",
    "MappingGenerationResult",
    "MappingIRBuilder",
    "MappingOrchestrator",
    "MappingRequest",
    "SemanticReasoningResult",
]