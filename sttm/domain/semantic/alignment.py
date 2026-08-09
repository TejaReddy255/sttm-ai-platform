"""Semantic alignment domain models for the STTM platform.

Semantic alignment represents the relationship between source and
target metadata attributes after semantic reasoning.

The model captures:

* Source and target attributes.
* Alignment decision.
* Semantic similarity.
* Business-term evidence.
* Data-type compatibility.
* Candidate-path evidence.
* Alternatives considered.
* Confidence and rationale.

The model does not contain Vertex AI implementation details.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sttm.core import (
    ConfidenceSource,
    MappingStatus,
    MappingType,
)


class SemanticAttribute(BaseModel):
    """Attribute participating in semantic alignment.

    Attributes:
        column_id: Metadata column identifier.
        column_name: Physical column name.
        table_id: Parent table identifier.
        table_name: Parent table name.
        data_type: Physical or canonical data type.
        description: Optional business description.
        business_terms: Business glossary terms associated with it.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    column_id: UUID

    column_name: str = Field(
        min_length=1,
    )

    table_id: UUID

    table_name: str = Field(
        min_length=1,
    )

    data_type: str = Field(
        min_length=1,
    )

    description: str | None = None

    business_terms: list[str] = Field(
        default_factory=list,
    )


class AlignmentEvidence(BaseModel):
    """Evidence supporting a semantic alignment decision.

    Attributes:
        evidence_type: Evidence category.
        description: Explanation of the evidence.
        score: Evidence strength.
        source: Origin of the evidence.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    evidence_type: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    source: ConfidenceSource


class AlignmentAlternative(BaseModel):
    """Alternative target candidate considered during alignment.

    Attributes:
        target: Alternative target attribute.
        score: Alignment score.
        rejection_reason: Reason it was not selected.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    target: SemanticAttribute

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    rejection_reason: str = Field(
        min_length=1,
    )


class SemanticAlignment(BaseModel):
    """Semantic alignment decision between source and target attributes.

    This is a domain-level representation of an AI-assisted semantic
    decision.

    Attributes:
        id: Alignment identifier.
        source: Source attribute.
        target: Target attribute.
        mapping_type: Mapping classification.
        status: Current mapping status.
        semantic_similarity: Semantic similarity score.
        structural_compatibility: Structural compatibility score.
        business_term_match: Business-term matching score.
        data_type_compatibility: Data-type compatibility score.
        candidate_path_score: Supporting path score.
        overall_confidence: Overall confidence.
        confidence_source: Source of confidence.
        evidence: Supporting evidence.
        alternatives: Alternative candidates considered.
        rationale: Human-readable reasoning summary.
        requires_review: Whether human review is required.
        created_at: Creation timestamp.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    id: UUID = Field(
        default_factory=uuid4,
    )

    source: SemanticAttribute

    target: SemanticAttribute

    mapping_type: MappingType

    status: MappingStatus

    semantic_similarity: float = Field(
        ge=0.0,
        le=1.0,
    )

    structural_compatibility: float = Field(
        ge=0.0,
        le=1.0,
    )

    business_term_match: float = Field(
        ge=0.0,
        le=1.0,
    )

    data_type_compatibility: float = Field(
        ge=0.0,
        le=1.0,
    )

    candidate_path_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    overall_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_source: ConfidenceSource

    evidence: list[AlignmentEvidence] = Field(
        min_length=1,
    )

    alternatives: list[AlignmentAlternative] = Field(
        default_factory=list,
    )

    rationale: str = Field(
        min_length=1,
    )

    requires_review: bool = False

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_alignment(self) -> Self:
        """Validate alignment consistency.

        Returns:
            Validated alignment.

        Raises:
            ValueError: If the alignment is inconsistent.
        """
        if (
            self.source.column_id
            == self.target.column_id
        ):
            raise ValueError(
                "Source and target attributes cannot be the same "
                "metadata column.",
            )

        if (
            self.status == MappingStatus.REJECTED
            and not self.rationale.strip()
        ):
            raise ValueError(
                "Rejected alignments require a rationale.",
            )

        if (
            self.overall_confidence < 0.60
            and not self.requires_review
        ):
            raise ValueError(
                "Alignments below 0.60 confidence must require "
                "human review.",
            )

        return self

    @property
    def is_high_confidence(self) -> bool:
        """Return whether alignment has high confidence.

        Returns:
            True when confidence is at least 0.85.
        """
        return self.overall_confidence >= 0.85

    @property
    def is_ambiguous(self) -> bool:
        """Return whether multiple candidates are close in score.

        Returns:
            True when the top alternatives are potentially ambiguous.
        """
        if not self.alternatives:
            return False

        best_alternative = max(
            self.alternatives,
            key=lambda item: item.score,
        )

        return (
            abs(
                self.overall_confidence
                - best_alternative.score,
            )
            <= 0.10
        )


class AlignmentSet(BaseModel):
    """Collection of semantic alignment decisions."""

    model_config = ConfigDict(
        extra="forbid",
    )

    alignments: list[SemanticAlignment] = Field(
        default_factory=list,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add(
        self,
        alignment: SemanticAlignment,
    ) -> None:
        """Add an alignment decision.

        Args:
            alignment: Alignment to add.

        Raises:
            ValueError: If an alignment for the same source-target
                pair already exists.
        """
        duplicate = any(
            item.source.column_id
            == alignment.source.column_id
            and item.target.column_id
            == alignment.target.column_id
            for item in self.alignments
        )

        if duplicate:
            raise ValueError(
                "An alignment already exists for this source-target pair.",
            )

        self.alignments.append(
            alignment,
        )

    def for_source(
        self,
        source_column_id: UUID,
    ) -> list[SemanticAlignment]:
        """Return alignments for a source column.

        Args:
            source_column_id: Source column identifier.

        Returns:
            Matching alignments.
        """
        return [
            alignment
            for alignment in self.alignments
            if alignment.source.column_id == source_column_id
        ]

    def for_target(
        self,
        target_column_id: UUID,
    ) -> list[SemanticAlignment]:
        """Return alignments for a target column.

        Args:
            target_column_id: Target column identifier.

        Returns:
            Matching alignments.
        """
        return [
            alignment
            for alignment in self.alignments
            if alignment.target.column_id == target_column_id
        ]

    def requiring_review(self) -> list[SemanticAlignment]:
        """Return alignments requiring human review.

        Returns:
            Review-required alignments.
        """
        return [
            alignment
            for alignment in self.alignments
            if alignment.requires_review
        ]


__all__ = [
    "AlignmentAlternative",
    "AlignmentEvidence",
    "AlignmentSet",
    "SemanticAlignment",
    "SemanticAttribute",
]