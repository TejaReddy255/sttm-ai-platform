"""Relationship domain models for the STTM platform.

This module represents relationships discovered between metadata
objects.

Relationships may be:

- Declared through database constraints.
- Inferred from metadata evidence.
- Suggested by AI.
- Confirmed by a human.

The relationship model records both the conclusion and its evidence
so downstream reasoning can remain explainable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sttm.core import (
    RelationshipSource,
    RelationshipType,
)


class RelationshipColumnMapping(BaseModel):
    """Column-level correspondence within a relationship.

    Attributes:
        source_column_id: Source-side column identifier.
        target_column_id: Target-side column identifier.
        source_column_name: Source column name.
        target_column_name: Target column name.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    source_column_id: UUID

    target_column_id: UUID

    source_column_name: str = Field(
        min_length=1,
    )

    target_column_name: str = Field(
        min_length=1,
    )


class RelationshipEvidence(BaseModel):
    """Evidence supporting a relationship decision.

    Attributes:
        source: Origin of the relationship evidence.
        rule_name: Deterministic rule that produced the evidence.
        score: Evidence confidence between zero and one.
        explanation: Human-readable explanation.
        constraint_name: Supporting database constraint.
        column_mappings: Column-level evidence.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    source: RelationshipSource

    rule_name: str | None = None

    score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    explanation: str = Field(
        min_length=1,
    )

    constraint_name: str | None = None

    column_mappings: list[RelationshipColumnMapping] = Field(
        default_factory=list,
    )


class Relationship(BaseModel):
    """Canonical relationship between two metadata objects.

    A relationship is a graph-level fact used by cardinality,
    grain, dependency, candidate-path, and semantic reasoning
    components.

    Attributes:
        id: Relationship identifier.
        source_table_id: Source table identifier.
        target_table_id: Target table identifier.
        source_table_name: Source table name.
        target_table_name: Target table name.
        relationship_type: Relationship classification.
        source: Origin of the relationship.
        evidence: Supporting evidence.
        bidirectional: Whether traversal is logically bidirectional.
        active: Whether the relationship participates in analysis.
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

    source_table_id: UUID

    target_table_id: UUID

    source_table_name: str = Field(
        min_length=1,
    )

    target_table_name: str = Field(
        min_length=1,
    )

    relationship_type: RelationshipType

    source: RelationshipSource

    evidence: list[RelationshipEvidence] = Field(
        min_length=1,
    )

    bidirectional: bool = True

    active: bool = True

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_relationship(self) -> Self:
        """Validate relationship consistency.

        Returns:
            Validated relationship.

        Raises:
            ValueError: If relationship metadata is inconsistent.
        """
        if self.source_table_id == self.target_table_id:
            if (
                self.relationship_type
                != RelationshipType.SELF_REFERENCE
            ):
                raise ValueError(
                    "A relationship between the same table must "
                    "be classified as SELF_REFERENCE.",
                )

        if self.source == RelationshipSource.DECLARED:
            if not any(
                evidence.source
                == RelationshipSource.DECLARED
                for evidence in self.evidence
            ):
                raise ValueError(
                    "Declared relationships require declared evidence.",
                )

        return self

    @property
    def average_evidence_score(self) -> float:
        """Calculate the average evidence score.

        Returns:
            Average evidence score between zero and one.
        """
        if not self.evidence:
            return 0.0

        return sum(
            item.score
            for item in self.evidence
        ) / len(self.evidence)

    @property
    def strongest_evidence(self) -> RelationshipEvidence | None:
        """Return the strongest supporting evidence.

        Returns:
            Evidence with the highest score, or None.
        """
        if not self.evidence:
            return None

        return max(
            self.evidence,
            key=lambda item: item.score,
        )


class RelationshipGraph(BaseModel):
    """Collection of relationships discovered in metadata.

    This is the domain representation consumed by downstream
    deterministic engines.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    relationships: list[Relationship] = Field(
        default_factory=list,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add(
        self,
        relationship: Relationship,
    ) -> None:
        """Add a relationship to the graph.

        Duplicate relationship IDs are rejected.

        Args:
            relationship: Relationship to add.

        Raises:
            ValueError: If the relationship ID already exists.
        """
        if any(
            item.id == relationship.id
            for item in self.relationships
        ):
            raise ValueError(
                f"Relationship {relationship.id} already exists.",
            )

        self.relationships.append(
            relationship,
        )

    def between(
        self,
        source_table_id: UUID,
        target_table_id: UUID,
    ) -> list[Relationship]:
        """Find relationships between two tables.

        Args:
            source_table_id: Source table ID.
            target_table_id: Target table ID.

        Returns:
            Matching relationships.
        """
        return [
            relationship
            for relationship in self.relationships
            if (
                relationship.source_table_id
                == source_table_id
                and relationship.target_table_id
                == target_table_id
            )
            or (
                relationship.bidirectional
                and relationship.source_table_id
                == target_table_id
                and relationship.target_table_id
                == source_table_id
            )
        ]

    def for_table(
        self,
        table_id: UUID,
    ) -> list[Relationship]:
        """Find all relationships connected to a table.

        Args:
            table_id: Table identifier.

        Returns:
            Connected relationships.
        """
        return [
            relationship
            for relationship in self.relationships
            if (
                relationship.source_table_id == table_id
                or relationship.target_table_id == table_id
            )
        ]

    def active_relationships(self) -> list[Relationship]:
        """Return only active relationships.

        Returns:
            Active relationships.
        """
        return [
            relationship
            for relationship in self.relationships
            if relationship.active
        ]


__all__ = [
    "Relationship",
    "RelationshipColumnMapping",
    "RelationshipEvidence",
    "RelationshipGraph",
]