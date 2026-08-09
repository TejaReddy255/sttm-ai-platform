"""Deterministic analysis domain package.

This package contains the domain contracts produced by deterministic
metadata analysis:

- Relationships
- Cardinality
- Grain
- Dependencies
- Candidate join paths

These models form the evidence layer consumed by semantic reasoning
and logical mapping planning.
"""

from .cardinality import (
    Cardinality,
    CardinalityEvidenceItem,
    CardinalityGraph,
)

from .candidate import (
    CandidatePath,
    CandidatePathScore,
    CandidatePathSet,
    JoinColumnPair,
    JoinStep,
)

from .dependency import (
    Dependency,
    DependencyColumn,
    DependencyEvidence,
    DependencyGraph,
)

from .grain import (
    Grain,
    GrainComparison,
    GrainEvidence,
    GrainGraph,
    GrainKeyColumn,
)

from .relationship import (
    Relationship,
    RelationshipColumnMapping,
    RelationshipEvidence,
    RelationshipGraph,
)

__all__ = [
    # Relationship
    "Relationship",
    "RelationshipColumnMapping",
    "RelationshipEvidence",
    "RelationshipGraph",

    # Cardinality
    "Cardinality",
    "CardinalityEvidenceItem",
    "CardinalityGraph",

    # Grain
    "Grain",
    "GrainComparison",
    "GrainEvidence",
    "GrainGraph",
    "GrainKeyColumn",

    # Dependency
    "Dependency",
    "DependencyColumn",
    "DependencyEvidence",
    "DependencyGraph",

    # Candidate paths
    "CandidatePath",
    "CandidatePathScore",
    "CandidatePathSet",
    "JoinColumnPair",
    "JoinStep",
]
