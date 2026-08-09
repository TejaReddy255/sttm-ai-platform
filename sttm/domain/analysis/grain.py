"""Grain domain models for the STTM platform.

Grain describes the business-level uniqueness represented by a
dataset, table, or transformation.

Examples:

    CUSTOMER
        grain = one row per customer

    ORDER
        grain = one row per order

    ORDER_LINE
        grain = one row per order line

    MONTHLY_CUSTOMER_SALES
        grain = one row per customer per month

Grain analysis is deterministic wherever possible and provides
evidence to the transformation planner and AI semantic layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sttm.core import (
    ConfidenceSource,
    GrainLevel,
    GrainRelationship,
)


class GrainKeyColumn(BaseModel):
    """Column participating in a grain definition.

    Attributes:
        column_id: Metadata column identifier.
        column_name: Physical column name.
        ordinal_position: Position within the grain key.
        is_primary_key: Whether the column is a declared PK column.
        uniqueness_score: Optional observed uniqueness score.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    column_id: UUID

    column_name: str = Field(
        min_length=1,
    )

    ordinal_position: int = Field(
        ge=1,
    )

    is_primary_key: bool = False

    uniqueness_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


class GrainEvidence(BaseModel):
    """Evidence supporting a grain determination.

    Attributes:
        evidence_type: Type of evidence.
        description: Human-readable explanation.
        score: Evidence strength.
        columns: Columns supporting the evidence.
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
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    columns: list[GrainKeyColumn] = Field(
        default_factory=list,
    )


class Grain(BaseModel):
    """Canonical grain definition for a dataset.

    Attributes:
        id: Grain identifier.
        table_id: Table represented by the grain.
        table_name: Table name.
        level: Grain classification.
        grain_description: Human-readable grain statement.
        key_columns: Columns defining the grain.
        evidence: Evidence supporting the grain.
        confidence: Overall confidence.
        confidence_source: Source of confidence calculation.
        row_count: Optional observed row count.
        distinct_grain_count: Optional observed distinct grain count.
        is_unique: Whether the grain key is empirically unique.
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

    table_id: UUID

    table_name: str = Field(
        min_length=1,
    )

    level: GrainLevel

    grain_description: str = Field(
        min_length=1,
    )

    key_columns: list[GrainKeyColumn] = Field(
        min_length=1,
    )

    evidence: list[GrainEvidence] = Field(
        min_length=1,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_source: ConfidenceSource

    row_count: int | None = Field(
        default=None,
        ge=0,
    )

    distinct_grain_count: int | None = Field(
        default=None,
        ge=0,
    )

    is_unique: bool = False

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_grain(self) -> Self:
        """Validate grain consistency.

        Returns:
            Validated grain.

        Raises:
            ValueError: If grain statistics are inconsistent.
        """
        if (
            self.row_count is not None
            and self.distinct_grain_count is not None
            and self.distinct_grain_count > self.row_count
        ):
            raise ValueError(
                "distinct_grain_count cannot exceed row_count.",
            )

        if (
            self.is_unique
            and self.row_count is not None
            and self.distinct_grain_count is not None
            and self.distinct_grain_count != self.row_count
        ):
            raise ValueError(
                "A unique grain must have distinct_grain_count "
                "equal to row_count.",
            )

        return self

    @property
    def average_evidence_score(self) -> float:
        """Return average evidence score.

        Returns:
            Average score between zero and one.
        """
        if not self.evidence:
            return 0.0

        return sum(
            evidence.score
            for evidence in self.evidence
        ) / len(self.evidence)

    @property
    def key_column_names(self) -> list[str]:
        """Return grain key column names.

        Returns:
            Ordered column names.
        """
        return [
            column.column_name
            for column in sorted(
                self.key_columns,
                key=lambda item: item.ordinal_position,
            )
        ]


class GrainComparison(BaseModel):
    """Comparison between source and target grain.

    This model is particularly important for determining whether a
    mapping requires joins, aggregation, deduplication, or other
    transformations.

    Attributes:
        id: Comparison identifier.
        source_grain_id: Source grain.
        target_grain_id: Target grain.
        relationship: Grain relationship.
        source_grain_description: Source grain description.
        target_grain_description: Target grain description.
        aggregation_required: Whether source data must be rolled up.
        expansion_risk: Whether target grain may expand source rows.
        deduplication_required: Whether duplicate elimination may be needed.
        confidence: Confidence in comparison.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: UUID = Field(
        default_factory=uuid4,
    )

    source_grain_id: UUID

    target_grain_id: UUID

    relationship: GrainRelationship

    source_grain_description: str = Field(
        min_length=1,
    )

    target_grain_description: str = Field(
        min_length=1,
    )

    aggregation_required: bool = False

    expansion_risk: bool = False

    deduplication_required: bool = False

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    rationale: str = Field(
        min_length=1,
    )

    @property
    def requires_transformation(self) -> bool:
        """Return whether grain mismatch requires transformation.

        Returns:
            True when aggregation or deduplication is required.
        """
        return (
            self.aggregation_required
            or self.deduplication_required
        )


class GrainGraph(BaseModel):
    """Collection of grain definitions and comparisons."""

    model_config = ConfigDict(
        extra="forbid",
    )

    grains: list[Grain] = Field(
        default_factory=list,
    )

    comparisons: list[GrainComparison] = Field(
        default_factory=list,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add_grain(
        self,
        grain: Grain,
    ) -> None:
        """Add a grain definition.

        Args:
            grain: Grain to add.

        Raises:
            ValueError: If a grain already exists for the table.
        """
        existing = self.for_table(
            grain.table_id,
        )

        if existing is not None:
            raise ValueError(
                f"Grain for table {grain.table_id} already exists.",
            )

        self.grains.append(grain)

    def add_comparison(
        self,
        comparison: GrainComparison,
    ) -> None:
        """Add a grain comparison.

        Args:
            comparison: Grain comparison to add.
        """
        self.comparisons.append(
            comparison,
        )

    def for_table(
        self,
        table_id: UUID,
    ) -> Grain | None:
        """Find the grain associated with a table.

        Args:
            table_id: Table identifier.

        Returns:
            Grain or None.
        """
        return next(
            (
                grain
                for grain in self.grains
                if grain.table_id == table_id
            ),
            None,
        )

    def comparison(
        self,
        source_grain_id: UUID,
        target_grain_id: UUID,
    ) -> GrainComparison | None:
        """Find a source-to-target grain comparison.

        Args:
            source_grain_id: Source grain identifier.
            target_grain_id: Target grain identifier.

        Returns:
            Matching comparison or None.
        """
        return next(
            (
                item
                for item in self.comparisons
                if (
                    item.source_grain_id == source_grain_id
                    and item.target_grain_id == target_grain_id
                )
            ),
            None,
        )


__all__ = [
    "Grain",
    "GrainComparison",
    "GrainEvidence",
    "GrainGraph",
    "GrainKeyColumn",
]