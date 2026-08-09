"""Candidate join-path domain models for the STTM platform.

A candidate path represents a possible deterministic route between
tables through the metadata relationship graph.

The Candidate Path Generator is responsible for enumerating and
ranking paths. The semantic reasoning layer consumes these paths
when determining the most appropriate source-to-target mapping.

This module contains domain contracts only. It does not implement
graph traversal algorithms.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sttm.core import (
    CardinalityType,
    JoinType,
    PathSelectionStatus,
)


class JoinColumnPair(BaseModel):
    """Column pair used by a join step.

    Attributes:
        left_column_id: Left-side column identifier.
        left_column_name: Left-side column name.
        right_column_id: Right-side column identifier.
        right_column_name: Right-side column name.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    left_column_id: UUID

    left_column_name: str = Field(
        min_length=1,
    )

    right_column_id: UUID

    right_column_name: str = Field(
        min_length=1,
    )


class JoinStep(BaseModel):
    """One join operation within a candidate path.

    Attributes:
        id: Join-step identifier.
        sequence: One-based sequence number.
        left_table_id: Left table identifier.
        left_table_name: Left table name.
        right_table_id: Right table identifier.
        right_table_name: Right table name.
        join_type: Join type.
        join_columns: Column pairs used by the join.
        relationship_id: Supporting relationship.
        cardinality: Known cardinality, if available.
        fanout_risk: Whether this join can cause row multiplication.
        aggregation_required: Whether aggregation may be needed.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: UUID = Field(
        default_factory=uuid4,
    )

    sequence: int = Field(
        ge=1,
    )

    left_table_id: UUID

    left_table_name: str = Field(
        min_length=1,
    )

    right_table_id: UUID

    right_table_name: str = Field(
        min_length=1,
    )

    join_type: JoinType

    join_columns: list[JoinColumnPair] = Field(
        min_length=1,
    )

    relationship_id: UUID | None = None

    cardinality: CardinalityType | None = None

    fanout_risk: bool = False

    aggregation_required: bool = False

    @model_validator(mode="after")
    def validate_join_step(self) -> Self:
        """Validate join-step consistency.

        Returns:
            Validated join step.

        Raises:
            ValueError: If the join references the same table.
        """
        if self.left_table_id == self.right_table_id:
            raise ValueError(
                "A join step cannot join a table to itself.",
            )

        return self


class CandidatePathScore(BaseModel):
    """Detailed scoring information for a candidate path.

    Attributes:
        relationship_score: Relationship evidence score.
        cardinality_score: Cardinality quality score.
        grain_score: Grain compatibility score.
        dependency_score: Dependency alignment score.
        path_length_score: Score based on number of joins.
        fanout_penalty: Penalty for fanout risk.
        ambiguity_penalty: Penalty for ambiguous relationships.
        total_score: Final normalized score.
        rationale: Explanation of the score.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    relationship_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    cardinality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    grain_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    dependency_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    path_length_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    fanout_penalty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    ambiguity_penalty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    total_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    rationale: str = Field(
        min_length=1,
    )


class CandidatePath(BaseModel):
    """A possible route between source and target tables.

    Candidate paths are deterministic alternatives presented to the
    semantic reasoning layer.

    Attributes:
        id: Candidate path identifier.
        source_table_id: Starting table.
        source_table_name: Starting table name.
        target_table_id: Destination table.
        target_table_name: Destination table name.
        join_steps: Ordered join sequence.
        score: Detailed path score.
        selection_status: Current path status.
        max_depth: Maximum traversal depth used to discover it.
        cycle_free: Whether the path contains no repeated tables.
        complete: Whether the path reaches the requested target.
        generated_at: Creation timestamp.
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

    source_table_name: str = Field(
        min_length=1,
    )

    target_table_id: UUID

    target_table_name: str = Field(
        min_length=1,
    )

    join_steps: list[JoinStep] = Field(
        min_length=1,
    )

    score: CandidatePathScore

    selection_status: PathSelectionStatus = (
        PathSelectionStatus.CANDIDATE
    )

    max_depth: int = Field(
        ge=1,
    )

    cycle_free: bool = True

    complete: bool = True

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_path(self) -> Self:
        """Validate candidate path structure.

        Returns:
            Validated candidate path.

        Raises:
            ValueError: If the path is structurally invalid.
        """
        if not self.join_steps:
            raise ValueError(
                "Candidate path must contain at least one join step.",
            )

        sequences = [
            step.sequence
            for step in self.join_steps
        ]

        if sequences != list(
            range(
                1,
                len(sequences) + 1,
            ),
        ):
            raise ValueError(
                "Join-step sequence numbers must be contiguous "
                "and start at one.",
            )

        first_step = self.join_steps[0]
        last_step = self.join_steps[-1]

        if first_step.left_table_id != self.source_table_id:
            raise ValueError(
                "First join step must start from source_table_id.",
            )

        if last_step.right_table_id != self.target_table_id:
            raise ValueError(
                "Last join step must end at target_table_id.",
            )

        for previous, current in zip(
            self.join_steps,
            self.join_steps[1:],
        ):
            if previous.right_table_id != current.left_table_id:
                raise ValueError(
                    "Candidate path contains disconnected join steps.",
                )

        if self.max_depth < len(self.join_steps):
            raise ValueError(
                "max_depth cannot be less than the number of join steps.",
            )

        if self.source_table_id == self.target_table_id:
            raise ValueError(
                "Source and target tables must be different.",
            )

        return self

    @property
    def length(self) -> int:
        """Return the number of joins in the path.

        Returns:
            Number of join steps.
        """
        return len(self.join_steps)

    @property
    def table_ids(self) -> list[UUID]:
        """Return ordered table identifiers in the path.

        Returns:
            Table IDs from source to target.
        """
        if not self.join_steps:
            return [
                self.source_table_id,
            ]

        return [
            self.source_table_id,
            *[
                step.right_table_id
                for step in self.join_steps
            ],
        ]

    @property
    def table_names(self) -> list[str]:
        """Return ordered table names in the path.

        Returns:
            Table names from source to target.
        """
        if not self.join_steps:
            return [
                self.source_table_name,
            ]

        return [
            self.source_table_name,
            *[
                step.right_table_name
                for step in self.join_steps
            ],
        ]

    @property
    def has_fanout_risk(self) -> bool:
        """Return whether any join has fanout risk.

        Returns:
            True when at least one join can multiply rows.
        """
        return any(
            step.fanout_risk
            for step in self.join_steps
        )

    @property
    def requires_aggregation(self) -> bool:
        """Return whether any join requires aggregation.

        Returns:
            True when aggregation may be required.
        """
        return any(
            step.aggregation_required
            for step in self.join_steps
        )

    @property
    def total_score(self) -> float:
        """Return the final candidate path score.

        Returns:
            Normalized path score.
        """
        return self.score.total_score


class CandidatePathSet(BaseModel):
    """Collection of candidate paths for a source-target request."""

    model_config = ConfigDict(
        extra="forbid",
    )

    source_table_id: UUID

    target_table_id: UUID

    paths: list[CandidatePath] = Field(
        default_factory=list,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    selected_path_id: UUID | None = None

    def add(
        self,
        path: CandidatePath,
    ) -> None:
        """Add a candidate path.

        Args:
            path: Candidate path to add.

        Raises:
            ValueError: If the path does not belong to this set.
        """
        if (
            path.source_table_id
            != self.source_table_id
        ):
            raise ValueError(
                "Candidate path source does not match the path set.",
            )

        if (
            path.target_table_id
            != self.target_table_id
        ):
            raise ValueError(
                "Candidate path target does not match the path set.",
            )

        if any(
            existing.id == path.id
            for existing in self.paths
        ):
            raise ValueError(
                f"Candidate path {path.id} already exists.",
            )

        self.paths.append(path)

    def ranked(
        self,
    ) -> list[CandidatePath]:
        """Return paths ranked by descending score.

        Returns:
            Ranked candidate paths.
        """
        return sorted(
            self.paths,
            key=lambda path: (
                path.total_score,
                -path.length,
            ),
            reverse=True,
        )

    def best(
        self,
    ) -> CandidatePath | None:
        """Return the highest-ranked path.

        Returns:
            Best path or None when no candidates exist.
        """
        ranked = self.ranked()

        return ranked[0] if ranked else None

    def select(
        self,
        path_id: UUID,
    ) -> CandidatePath:
        """Select a candidate path.

        Args:
            path_id: Candidate path identifier.

        Returns:
            Selected candidate path.

        Raises:
            ValueError: If the path cannot be selected.
        """
        path = next(
            (
                candidate
                for candidate in self.paths
                if candidate.id == path_id
            ),
            None,
        )

        if path is None:
            raise ValueError(
                f"Candidate path {path_id} was not found.",
            )

        for candidate in self.paths:
            candidate.selection_status = (
                PathSelectionStatus.CANDIDATE
            )

        path.selection_status = (
            PathSelectionStatus.SELECTED
        )

        self.selected_path_id = path.id

        return path


__all__ = [
    "CandidatePath",
    "CandidatePathScore",
    "CandidatePathSet",
    "JoinColumnPair",
    "JoinStep",
]