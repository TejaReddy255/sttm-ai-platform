"""Core primitives for the STTM platform.

The core package contains infrastructure-independent primitives
shared across the application, including:

- Enumerations
- Exception hierarchy
- Interfaces and protocols
- Logging abstractions
- Common execution metadata

Core modules must remain lightweight and must not depend on
domain-specific implementations, Vertex AI, Streamlit, or
database infrastructure.
"""

from .enum import (
    AgentType,
    AggregationType,
    AnalysisDecision,
    ArtifactType,
    AuditAction,
    CacheType,
    CardinalityEvidence,
    CardinalityType,
    ColumnRole,
    CompilerStage,
    ConfidenceLevel,
    ConfidenceSource,
    ConstraintType,
    DatabasePlatform,
    DependencyType,
    ExecutionMode,
    GrainLevel,
    GrainRelationship,
    JoinType,
    KnowledgeType,
    MappingStatus,
    MappingType,
    MetadataType,
    ObjectType,
    PathSelectionStatus,
    ProvenanceType,
    ReasoningMode,
    RelationshipSource,
    RelationshipType,
    ReviewStatus,
    SourceSystemType,
    TransformationType,
    ValidationCategory,
    ValidationSeverity,
    ValidationStatus,
    WorkflowNode,
    WorkflowStatus,
)

__all__ = [
    "AgentType", "AggregationType", "AnalysisDecision", "ArtifactType",
    "AuditAction", "CacheType", "CardinalityEvidence", "CardinalityType",
    "ColumnRole", "CompilerStage", "ConfidenceLevel", "ConfidenceSource",
    "ConstraintType", "DatabasePlatform", "DependencyType", "ExecutionMode",
    "GrainLevel", "GrainRelationship", "JoinType", "KnowledgeType",
    "MappingStatus", "MappingType", "MetadataType", "ObjectType",
    "PathSelectionStatus", "ProvenanceType", "ReasoningMode",
    "RelationshipSource", "RelationshipType", "ReviewStatus", "SourceSystemType",
    "TransformationType", "ValidationCategory", "ValidationSeverity",
    "ValidationStatus", "WorkflowNode", "WorkflowStatus",
]
