"""Dependency domain models for the STTM platform.

Dependency models describe deterministic dependencies between
metadata attributes.

The dependency layer supports:

* Direct column dependencies.
* Functional dependencies.
* Transitive dependencies.
* Derived-column dependencies.
* Transformation lineage.
* Downstream lineage generation.

The models intentionally describe dependency facts rather than
AI-generated business interpretations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sttm.core import (
    ConfidenceSource,
    DependencyType,
)


class DependencyColumn(BaseModel):
    """Column participating in a dependency.

    Attributes:
        column_id: Metadata column identifier.
        column_name: Column name.
        table_id: Parent table identifier.
        table_name: Parent table name.
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


class DependencyEvidence(BaseModel):
    """Evidence supporting a dependency.

    Attributes:
        evidence_type: Type of evidence.
        description: Human-readable explanation.
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
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    source: ConfidenceSource


class Dependency(BaseModel):
    """Canonical dependency relationship.

    A dependency expresses that one or more determinant columns
    influence or determine a dependent column.

    Examples:

        CUSTOMER_ID -> CUSTOMER_NAME

        ORDER_ID -> ORDER_DATE

        ORDER_ID -> CUSTOMER_ID -> CUSTOMER_REGION

    Attributes:
        id: Dependency identifier.
        determinant_columns: Columns determining the dependent value.
        dependent_column: Column whose value depends on the determinants.
        dependency_type: Dependency classification.
        evidence: Supporting evidence.
        confidence: Overall confidence.
        confidence_source: Source of confidence.
        transitive_depth: Depth for transitive dependencies.
        nullable_dependency: Whether the dependency can contain nulls.
        active: Whether dependency participates in analysis.
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

    determinant_columns: list[DependencyColumn] = Field(
        min_length=1,
    )

    dependent_column: DependencyColumn

    dependency_type: DependencyType

    evidence: list[DependencyEvidence] = Field(
        min_length=1,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_source: ConfidenceSource

    transitive_depth: int = Field(
        default=0,
        ge=0,
    )

    nullable_dependency: bool = False

    active: bool = True

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_dependency(self) -> Self:
        """Validate dependency consistency.

        Returns:
            Validated dependency.

        Raises:
            ValueError: If determinant and dependent columns conflict.
        """
        dependent_id = self.dependent_column.column_id

        if any(
            column.column_id == dependent_id
            for column in self.determinant_columns
        ):
            raise ValueError(
                "A dependent column cannot also be a determinant "
                "within the same dependency.",
            )

        if (
            self.dependency_type != DependencyType.TRANSITIVE
            and self.transitive_depth > 0
        ):
            raise ValueError(
                "transitive_depth must be zero for non-transitive "
                "dependencies.",
            )

        if (
            self.dependency_type == DependencyType.TRANSITIVE
            and self.transitive_depth < 1
        ):
            raise ValueError(
                "Transitive dependencies require transitive_depth "
                "greater than zero.",
            )

        return self

    @property
    def determinant_table_ids(self) -> set[UUID]:
        """Return tables containing determinant columns.

        Returns:
            Set of table identifiers.
        """
        return {
            column.table_id
            for column in self.determinant_columns
        }

    @property
    def is_cross_table(self) -> bool:
        """Return whether the dependency crosses tables.

        Returns:
            True when determinant and dependent columns span tables.
        """
        determinant_tables = self.determinant_table_ids

        return (
            self.dependent_column.table_id
            not in determinant_tables
        )

    @property
    def is_transitive(self) -> bool:
        """Return whether the dependency is transitive.

        Returns:
            True for transitive dependencies.
        """
        return (
            self.dependency_type
            == DependencyType.TRANSITIVE
        )


class DependencyGraph(BaseModel):
    """Graph of deterministic column dependencies."""

    model_config = ConfigDict(
        extra="forbid",
    )

    dependencies: list[Dependency] = Field(
        default_factory=list,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add(
        self,
        dependency: Dependency,
    ) -> None:
        """Add a dependency to the graph.

        Args:
            dependency: Dependency to add.

        Raises:
            ValueError: If an identical dependency already exists.
        """
        if self.contains(
            dependency,
        ):
            raise ValueError(
                "An equivalent dependency already exists.",
            )

        self.dependencies.append(
            dependency,
        )

    def contains(
        self,
        dependency: Dependency,
    ) -> bool:
        """Check whether an equivalent dependency exists.

        Args:
            dependency: Dependency to check.

        Returns:
            True when an equivalent dependency exists.
        """
        determinant_ids = {
            column.column_id
            for column in dependency.determinant_columns
        }

        for existing in self.dependencies:
            existing_determinants = {
                column.column_id
                for column in existing.determinant_columns
            }

            if (
                existing_determinants == determinant_ids
                and existing.dependent_column.column_id
                == dependency.dependent_column.column_id
                and existing.dependency_type
                == dependency.dependency_type
            ):
                return True

        return False

    def for_dependent(
        self,
        column_id: UUID,
    ) -> list[Dependency]:
        """Find dependencies for a dependent column.

        Args:
            column_id: Dependent column identifier.

        Returns:
            Dependencies targeting the specified column.
        """
        return [
            dependency
            for dependency in self.dependencies
            if dependency.dependent_column.column_id == column_id
        ]

    def for_determinant(
        self,
        column_id: UUID,
    ) -> list[Dependency]:
        """Find dependencies where a column is a determinant.

        Args:
            column_id: Determinant column identifier.

        Returns:
            Dependencies originating from the specified column.
        """
        return [
            dependency
            for dependency in self.dependencies
            if any(
                determinant.column_id == column_id
                for determinant in dependency.determinant_columns
            )
        ]

    def transitive_dependencies(self) -> list[Dependency]:
        """Return transitive dependencies.

        Returns:
            Transitive dependency collection.
        """
        return [
            dependency
            for dependency in self.dependencies
            if dependency.is_transitive
        ]

    def cross_table_dependencies(self) -> list[Dependency]:
        """Return dependencies spanning multiple tables.

        Returns:
            Cross-table dependencies.
        """
        return [
            dependency
            for dependency in self.dependencies
            if dependency.is_cross_table
        ]


__all__ = [
    "Dependency",
    "DependencyColumn",
    "DependencyEvidence",
    "DependencyGraph",
]