"""Exception hierarchy for the STTM platform.

The exception hierarchy provides a stable error contract across
domain, application, infrastructure, AI, workflow, validation,
and compiler components.

Application code should raise the most specific STTM exception
available rather than generic ``Exception`` instances.
"""

from __future__ import annotations

from typing import Any


class STTMError(Exception):
    """Base exception for all expected STTM platform errors.

    Attributes:
        message: Human-readable description of the failure.
        code: Stable machine-readable error code.
        details: Optional structured diagnostic information.
    """

    default_code = "STTM_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize an STTM platform exception.

        Args:
            message: Human-readable error description.
            code: Optional machine-readable error code.
            details: Optional structured diagnostic information.
        """
        self.message = message
        self.code = code or self.default_code
        self.details = details or {}

        super().__init__(message)

    def __str__(self) -> str:
        """Return the human-readable exception message.

        Returns:
            Exception message.
        """
        return self.message


class ConfigurationError(STTMError):
    """Raised when application configuration is invalid."""

    default_code = "CONFIGURATION_ERROR"


class DependencyError(STTMError):
    """Raised when a required application dependency is unavailable."""

    default_code = "DEPENDENCY_ERROR"


class MetadataError(STTMError):
    """Base exception for metadata-related failures."""

    default_code = "METADATA_ERROR"


class MetadataContractError(MetadataError):
    """Raised when upstream metadata violates the input contract."""

    default_code = "METADATA_CONTRACT_ERROR"


class MetadataNormalizationError(MetadataError):
    """Raised when metadata cannot be normalized."""

    default_code = "METADATA_NORMALIZATION_ERROR"


class MetadataValidationError(MetadataError):
    """Raised when canonical metadata fails validation."""

    default_code = "METADATA_VALIDATION_ERROR"


class GraphError(STTMError):
    """Base exception for metadata graph failures."""

    default_code = "GRAPH_ERROR"


class GraphConstructionError(GraphError):
    """Raised when the metadata graph cannot be constructed."""

    default_code = "GRAPH_CONSTRUCTION_ERROR"


class GraphTraversalError(GraphError):
    """Raised when graph traversal fails."""

    default_code = "GRAPH_TRAVERSAL_ERROR"


class AnalysisError(STTMError):
    """Base exception for deterministic analysis failures."""

    default_code = "ANALYSIS_ERROR"


class RelationshipAnalysisError(AnalysisError):
    """Raised when relationship analysis fails."""

    default_code = "RELATIONSHIP_ANALYSIS_ERROR"


class CardinalityAnalysisError(AnalysisError):
    """Raised when cardinality analysis fails."""

    default_code = "CARDINALITY_ANALYSIS_ERROR"


class GrainAnalysisError(AnalysisError):
    """Raised when grain analysis fails."""

    default_code = "GRAIN_ANALYSIS_ERROR"


class DependencyAnalysisError(AnalysisError):
    """Raised when dependency analysis fails."""

    default_code = "DEPENDENCY_ANALYSIS_ERROR"


class CandidatePathError(AnalysisError):
    """Raised when candidate join-path generation fails."""

    default_code = "CANDIDATE_PATH_ERROR"


class SemanticReasoningError(STTMError):
    """Base exception for AI semantic reasoning failures."""

    default_code = "SEMANTIC_REASONING_ERROR"


class VertexAIError(SemanticReasoningError):
    """Raised for Vertex AI integration failures."""

    default_code = "VERTEX_AI_ERROR"


class VertexAIConfigurationError(VertexAIError):
    """Raised when Vertex AI configuration is invalid."""

    default_code = "VERTEX_AI_CONFIGURATION_ERROR"


class VertexAITimeoutError(VertexAIError):
    """Raised when a Vertex AI request times out."""

    default_code = "VERTEX_AI_TIMEOUT_ERROR"


class VertexAIRetryExhaustedError(VertexAIError):
    """Raised when all Vertex AI retry attempts are exhausted."""

    default_code = "VERTEX_AI_RETRY_EXHAUSTED"


class VertexAIResponseError(VertexAIError):
    """Raised when a Vertex AI response is malformed or unusable."""

    default_code = "VERTEX_AI_RESPONSE_ERROR"


class PromptError(SemanticReasoningError):
    """Raised for prompt loading or rendering failures."""

    default_code = "PROMPT_ERROR"


class SemanticAlignmentError(SemanticReasoningError):
    """Raised when semantic alignment cannot be resolved."""

    default_code = "SEMANTIC_ALIGNMENT_ERROR"


class BusinessRuleResolutionError(SemanticReasoningError):
    """Raised when a business rule cannot be resolved."""

    default_code = "BUSINESS_RULE_RESOLUTION_ERROR"


class TransformationPlanningError(SemanticReasoningError):
    """Raised when transformation planning fails."""

    default_code = "TRANSFORMATION_PLANNING_ERROR"


class ConflictResolutionError(SemanticReasoningError):
    """Raised when conflicting semantic decisions cannot be resolved."""

    default_code = "CONFLICT_RESOLUTION_ERROR"


class PlanningError(STTMError):
    """Base exception for logical planning failures."""

    default_code = "PLANNING_ERROR"


class IRValidationError(PlanningError):
    """Raised when the Logical Mapping IR is structurally invalid."""

    default_code = "IR_VALIDATION_ERROR"


class OptimizationError(PlanningError):
    """Raised when IR optimization fails."""

    default_code = "OPTIMIZATION_ERROR"


class ExecutionPlanningError(PlanningError):
    """Raised when execution planning fails."""

    default_code = "EXECUTION_PLANNING_ERROR"


class ValidationError(STTMError):
    """Base exception for validation failures."""

    default_code = "VALIDATION_ERROR"


class BlockingValidationError(ValidationError):
    """Raised when validation contains one or more blockers."""

    default_code = "BLOCKING_VALIDATION_ERROR"


class CompilationError(STTMError):
    """Base exception for artifact compilation failures."""

    default_code = "COMPILATION_ERROR"


class STTMCompilationError(CompilationError):
    """Raised when the 16-column STTM cannot be generated."""

    default_code = "STTM_COMPILATION_ERROR"


class ArtifactGenerationError(CompilationError):
    """Raised when an output artifact cannot be generated."""

    default_code = "ARTIFACT_GENERATION_ERROR"


class UnsupportedArtifactError(CompilationError):
    """Raised when an unsupported artifact type is requested."""

    default_code = "UNSUPPORTED_ARTIFACT_ERROR"


class RepositoryError(STTMError):
    """Base exception for persistence failures."""

    default_code = "REPOSITORY_ERROR"


class RepositoryNotFoundError(RepositoryError):
    """Raised when a requested entity does not exist."""

    default_code = "REPOSITORY_NOT_FOUND"


class RepositoryConflictError(RepositoryError):
    """Raised when a persistence operation violates uniqueness."""

    default_code = "REPOSITORY_CONFLICT"


class TransactionError(RepositoryError):
    """Raised when a database transaction fails."""

    default_code = "TRANSACTION_ERROR"


class WorkflowError(STTMError):
    """Base exception for LangGraph workflow failures."""

    default_code = "WORKFLOW_ERROR"


class WorkflowStateError(WorkflowError):
    """Raised when workflow state is invalid."""

    default_code = "WORKFLOW_STATE_ERROR"


class WorkflowRoutingError(WorkflowError):
    """Raised when workflow routing cannot determine the next node."""

    default_code = "WORKFLOW_ROUTING_ERROR"


class HumanReviewRequired(STTMError):
    """Raised when a decision must be reviewed by a human.

    This exception represents a controlled business state rather
    than an unexpected system failure.
    """

    default_code = "HUMAN_REVIEW_REQUIRED"