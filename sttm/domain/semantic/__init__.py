"""Semantic reasoning domain package.

This package contains domain contracts for AI-assisted STTM
reasoning.

The semantic domain is intentionally independent of:

* Vertex AI
* LangGraph
* Streamlit
* SQLite
* Prompt templates
* Model-specific SDKs

Infrastructure and orchestration layers consume these contracts.
"""

from .alignment import (
    AlignmentAlternative,
    AlignmentEvidence,
    AlignmentSet,
    SemanticAlignment,
    SemanticAttribute,
)

from .business_rule import (
    BusinessRule,
    BusinessRuleAttribute,
    BusinessRuleConflict,
    BusinessRuleEvidence,
    BusinessRuleSet,
)

from .conflict import (
    Conflict,
    ConflictEvidence,
    ConflictResolution,
    ConflictSet,
    ConflictSeverity,
    ConflictType,
    ResolutionMethod,
)

from .intent import (
    IntentAttribute,
    IntentCandidate,
    IntentDecision,
    IntentEvidence,
    IntentSet,
)

from .transformation import (
    TransformationAttribute,
    TransformationEvidence,
    TransformationOperation,
    TransformationPlan,
    TransformationPlanSet,
    TransformationStep,
)

__all__ = [
    # Alignment
    "AlignmentAlternative",
    "AlignmentEvidence",
    "AlignmentSet",
    "SemanticAlignment",
    "SemanticAttribute",

    # Intent
    "IntentAttribute",
    "IntentCandidate",
    "IntentDecision",
    "IntentEvidence",
    "IntentSet",

    # Business rules
    "BusinessRule",
    "BusinessRuleAttribute",
    "BusinessRuleConflict",
    "BusinessRuleEvidence",
    "BusinessRuleSet",

    # Transformation
    "TransformationAttribute",
    "TransformationEvidence",
    "TransformationOperation",
    "TransformationPlan",
    "TransformationPlanSet",
    "TransformationStep",

    # Conflict resolution
    "Conflict",
    "ConflictEvidence",
    "ConflictResolution",
    "ConflictSet",
    "ConflictSeverity",
    "ConflictType",
    "ResolutionMethod",
]