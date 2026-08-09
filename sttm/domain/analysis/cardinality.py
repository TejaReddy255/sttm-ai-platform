"""Cardinality domain models for the STTM platform.

Cardinality describes the multiplicity between two metadata
entities. It is consumed by grain analysis, candidate-path
generation, transformation planning, validation, and semantic
reasoning.

The model preserves the evidence used to determine cardinality so
that downstream decisions remain explainable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sttm.core import (
    CardinalityEvidence,
    CardinalityType,
    ConfidenceSource,
)


class CardinalityEvidenceItem(BaseModel):
    """Evidence supporting a cardinality decision.

    Attributes:
        evidence_type: Type of evidence.
        description: Human-readable evidence description.
        score: Evidence strength between zero and one.
        observed_left_count: Optional distinct count on the left side.
        observed_right_count: Optional distinct count on the right side.
        observed_left_rows: Optional row count on the left side.
        observed_right_rows: Optional row count on the right side.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    evidence_type: CardinalityEvidence

    description: str = Field(
        min_length=1,
    )

    score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    observed_left_count: int | None = Field(
        default=None,
        ge=0,
    )

    observed_right_count: int | None = Field(
        default=None,
        ge=0,
    )

    observed_left_rows: int | None = Field(
        default=None,
        ge=0,
    )

    observed_right_rows: int | None = Field(
        default=None,
        ge=0,
    )


class Cardinality(BaseModel):
    """Canonical cardinality relationship.

    Attributes:
        id: Cardinality identifier.
        relationship_id: Relationship being classified.
        left_table_id: Left-side table identifier.
        right_table_id: Right-side table identifier.
        cardinality: Determined cardinality.
        evidence: Supporting evidence.
        confidence: Overall confidence score.
        confidence_source: Origin of the confidence calculation.
        bridge_table_id: Optional bridge table for N:N relationships.
        aggregation_required: Whether aggregation may be required.
        fanout_risk: Whether the relationship presents fanout risk.
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

    relationship_id: UUID

    left_table_id: UUID

    right_table_id: UUID

    cardinality: CardinalityType

    evidence: list[CardinalityEvidenceItem] = Field(
        min_length=1,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_source: ConfidenceSource

    bridge_table_id: UUID | None = None

    aggregation_required: bool = False

    fanout_risk: bool = False

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_cardinality(self) -> Self:
        """Validate cardinality-specific constraints.

        Returns:
            Validated cardinality.

        Raises:
            ValueError: If cardinality metadata is inconsistent.
        """
        if (
            self.cardinality == CardinalityType.MANY_TO_MANY
            and self.bridge_table_id is None
        ):
            self.fanout_risk = True

        if (
            self.cardinality
            in {
                CardinalityType.ONE_TO_MANY,
                CardinalityType.MANY_TO_ONE,
                CardinalityType.MANY_TO_MANY,
            }
            and not self.aggregation_required
        ):
            # Aggregation is not necessarily required for every
            # many-side relationship, so this remains a warning
            # signal rather than an error.
            pass

        return self

    @property
    def average_evidence_score(self) -> float:
        """Calculate average evidence strength.

        Returns:
            Average evidence score.
        """
        if not self.evidence:
            return 0.0

        return sum(
            item.score
            for item in self.evidence
        ) / len(self.evidence)

    @property
    def is_many_to_many(self) -> bool:
        """Return whether this is an N:N relationship.

        Returns:
            True for N:N cardinality.
        """
        return (
            self.cardinality
            == CardinalityType.MANY_TO_MANY
        )

    @property
    def is_one_to_many(self) -> bool:
        """Return whether this is a 1:N relationship.

        Returns:
            True for 1:N cardinality.
        """
        return (
            self.cardinality
            == CardinalityType.ONE_TO_MANY
        )

    @property
    def requires_attention(self) -> bool:
        """Return whether downstream planning should inspect this relationship.

        Returns:
            True when fanout or aggregation concerns exist.
        """
        return (
            self.fanout_risk
            or self.aggregation_required
            or self.cardinality == CardinalityType.UNKNOWN
        )


class CardinalityGraph(BaseModel):
    """Collection of cardinality classifications."""

    model_config = ConfigDict(
        extra="forbid",
    )

    cardinalities: list[Cardinality] = Field(
        default_factory=list,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add(
        self,
        cardinality: Cardinality,
    ) -> None:
        """Add a cardinality classification.

        Args:
            cardinality: Cardinality to add.

        Raises:
            ValueError: If the ID already exists.
        """
        if any(
            item.id == cardinality.id
            for item in self.cardinalities
        ):
            raise ValueError(
                f"Cardinality {cardinality.id} already exists.",
            )

        self.cardinalities.append(
            cardinality,
        )

    def for_relationship(
        self,
        relationship_id: UUID,
    ) -> Cardinality | None:
        """Find cardinality for a relationship.

        Args:
            relationship_id: Relationship identifier.

        Returns:
            Matching cardinality or None.
        """
        return next(
            (
                item
                for item in self.cardinalities
                if item.relationship_id == relationship_id
            ),
            None,
        )

    def for_table(
        self,
        table_id: UUID,
    ) -> list[Cardinality]:
        """Return cardinalities involving a table.

        Args:
            table_id: Table identifier.

        Returns:
            Matching cardinality classifications.
        """
        return [
            item
            for item in self.cardinalities
            if (
                item.left_table_id == table_id
                or item.right_table_id == table_id
            )
        ]

    def fanout_relationships(self) -> list[Cardinality]:
        """Return relationships with fanout risk.

        Returns:
            Cardinalities marked as fanout-risk.
        """
        return [
            item
            for item in self.cardinalities
            if item.fanout_risk
        ]

    def aggregation_relationships(self) -> list[Cardinality]:
        """Return relationships where aggregation may be required.

        Returns:
            Cardinalities requiring aggregation attention.
        """
        return [
            item
            for item in self.cardinalities
            if item.aggregation_required
        ]


__all__ = [
    "Cardinality",
    "CardinalityEvidenceItem",
    "CardinalityGraph",
]