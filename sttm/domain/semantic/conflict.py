"""Conflict resolution domain models for the STTM platform.

This module represents conflicts between competing mapping decisions,
business rules, transformation plans, metadata interpretations, or
other pieces of evidence.

Conflict resolution is deliberately modeled as a domain concern.
The actual resolution strategy may be implemented by deterministic
services, Vertex AI agents, or human reviewers.

No conflict should be silently discarded.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sttm.core import (
    ConfidenceSource,
    ReviewStatus,
)


class ConflictType(StrEnum):
    """Types of conflicts that can occur during STTM reasoning."""

    SEMANTIC = "SEMANTIC"
    BUSINESS_RULE = "BUSINESS_RULE"
    TRANSFORMATION = "TRANSFORMATION"
    CARDINALITY = "CARDINALITY"
    GRAIN = "GRAIN"
    RELATIONSHIP = "RELATIONSHIP"
    DATA_TYPE = "DATA_TYPE"
    MAPPING = "MAPPING"
    SOURCE_PRIORITY = "SOURCE_PRIORITY"


class ConflictSeverity(StrEnum):
    """Severity of a detected conflict."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ResolutionMethod(StrEnum):
    """Method used to resolve a conflict."""

    DETERMINISTIC = "DETERMINISTIC"
    AI = "AI"
    HUMAN = "HUMAN"
    CONSENSUS = "CONSENSUS"
    UNRESOLVED = "UNRESOLVED"


class ConflictEvidence(BaseModel):
    """Evidence participating in a conflict.

    Attributes:
        evidence_id: Evidence identifier.
        source_type: Type of source.
        source_id: Optional source identifier.
        statement: Statement made by the evidence source.
        score: Evidence confidence.
        authoritative: Whether the source is authoritative.
        priority: Evidence priority.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    evidence_id: UUID = Field(
        default_factory=uuid4,
    )

    source_type: str = Field(
        min_length=1,
    )

    source_id: str | None = None

    statement: str = Field(
        min_length=1,
    )

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    authoritative: bool = False

    priority: int = Field(
        default=100,
        ge=1,
    )


class ConflictResolution(BaseModel):
    """Resolution decision for a conflict.

    Attributes:
        method: Resolution method.
        selected_evidence_id: Evidence supporting the resolution.
        resolution_statement: Explanation of the decision.
        rationale: Detailed rationale.
        confidence: Resolution confidence.
        reviewer_id: Human reviewer when applicable.
        resolved_at: Resolution timestamp.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    method: ResolutionMethod

    selected_evidence_id: UUID | None = None

    resolution_statement: str = Field(
        min_length=1,
    )

    rationale: str = Field(
        min_length=1,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reviewer_id: str | None = None

    resolved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_resolution(self) -> ConflictResolution:
        """Validate resolution consistency.

        Returns:
            Validated resolution.

        Raises:
            ValueError: If resolution metadata is inconsistent.
        """
        if (
            self.method == ResolutionMethod.HUMAN
            and not self.reviewer_id
        ):
            raise ValueError(
                "Human conflict resolution requires reviewer_id.",
            )

        if (
            self.method == ResolutionMethod.UNRESOLVED
            and self.selected_evidence_id is not None
        ):
            raise ValueError(
                "An unresolved conflict cannot select evidence.",
            )

        return self


class Conflict(BaseModel):
    """Canonical conflict between competing STTM decisions.

    Attributes:
        id: Conflict identifier.
        conflict_type: Type of conflict.
        severity: Conflict severity.
        subject_id: Identifier of affected domain object.
        subject_type: Type of affected domain object.
        subject_name: Human-readable subject.
        description: Conflict description.
        evidence: Competing evidence.
        resolution: Optional resolution.
        review_status: Human review state.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    id: UUID = Field(
        default_factory=uuid4,
    )

    conflict_type: ConflictType

    severity: ConflictSeverity

    subject_id: UUID

    subject_type: str = Field(
        min_length=1,
    )

    subject_name: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    evidence: list[ConflictEvidence] = Field(
        min_length=2,
    )

    resolution: ConflictResolution | None = None

    review_status: ReviewStatus = (
        ReviewStatus.NOT_REQUIRED
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_conflict(self) -> Conflict:
        """Validate conflict state.

        Returns:
            Validated conflict.

        Raises:
            ValueError: If the conflict state is inconsistent.
        """
        if (
            self.resolution is not None
            and self.review_status
            == ReviewStatus.PENDING
        ):
            raise ValueError(
                "A resolved conflict cannot remain in PENDING "
                "review status.",
            )

        if (
            self.severity
            in {
                ConflictSeverity.HIGH,
                ConflictSeverity.CRITICAL,
            }
            and self.resolution is None
            and self.review_status
            == ReviewStatus.NOT_REQUIRED
        ):
            raise ValueError(
                "High and critical unresolved conflicts require "
                "human review.",
            )

        return self

    @property
    def is_resolved(self) -> bool:
        """Return whether the conflict has been resolved.

        Returns:
            True when a resolution exists.
        """
        return self.resolution is not None

    @property
    def requires_human_review(self) -> bool:
        """Return whether human review is required.

        Returns:
            True when human intervention is required.
        """
        return self.review_status in {
            ReviewStatus.PENDING,
            ReviewStatus.REJECTED,
        } or (
            not self.is_resolved
            and self.severity
            in {
                ConflictSeverity.HIGH,
                ConflictSeverity.CRITICAL,
            }
        )

    @property
    def strongest_evidence(self) -> ConflictEvidence:
        """Return the highest-priority evidence.

        Returns:
            Highest-priority evidence item.
        """
        return max(
            self.evidence,
            key=lambda item: (
                item.authoritative,
                item.priority * -1,
                item.score,
            ),
        )


class ConflictSet(BaseModel):
    """Collection of conflicts produced during mapping analysis."""

    model_config = ConfigDict(
        extra="forbid",
    )

    conflicts: list[Conflict] = Field(
        default_factory=list,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add(
        self,
        conflict: Conflict,
    ) -> None:
        """Add a conflict.

        Args:
            conflict: Conflict to add.

        Raises:
            ValueError: If the same conflict already exists.
        """
        if any(
            existing.id == conflict.id
            for existing in self.conflicts
        ):
            raise ValueError(
                f"Conflict {conflict.id} already exists.",
            )

        self.conflicts.append(conflict)

    def unresolved(self) -> list[Conflict]:
        """Return unresolved conflicts.

        Returns:
            Unresolved conflicts.
        """
        return [
            conflict
            for conflict in self.conflicts
            if not conflict.is_resolved
        ]

    def critical(self) -> list[Conflict]:
        """Return critical conflicts.

        Returns:
            Critical conflicts.
        """
        return [
            conflict
            for conflict in self.conflicts
            if conflict.severity
            == ConflictSeverity.CRITICAL
        ]

    def requiring_review(self) -> list[Conflict]:
        """Return conflicts requiring human review.

        Returns:
            Review-required conflicts.
        """
        return [
            conflict
            for conflict in self.conflicts
            if conflict.requires_human_review
        ]

    @property
    def has_blocking_conflicts(self) -> bool:
        """Return whether unresolved critical conflicts exist.

        Returns:
            True when the set contains unresolved critical conflicts.
        """
        return any(
            conflict.severity
            == ConflictSeverity.CRITICAL
            and not conflict.is_resolved
            for conflict in self.conflicts
        )


__all__ = [
    "Conflict",
    "ConflictEvidence",
    "ConflictResolution",
    "ConflictSet",
    "ConflictSeverity",
    "ConflictType",
    "ResolutionMethod",
]