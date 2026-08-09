"""Transformation planning domain models for the STTM platform.

A transformation plan describes how source attributes are converted
into a target attribute.

The plan is an intermediate domain contract between semantic
reasoning and the Logical Mapping IR.

It is intentionally independent of any target execution technology.

The same transformation plan can therefore be compiled into:

* ANSI SQL
* Oracle SQL
* PostgreSQL SQL
* Snowflake SQL
* BigQuery SQL
* Databricks SQL
* PySpark
* Spark SQL
* dbt

The transformation planner does not execute transformations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sttm.core import (
    ConfidenceSource,
    ReviewStatus,
)


class TransformationOperation(StrEnum):
    """Supported logical transformation operations."""

    DIRECT = "DIRECT"
    CAST = "CAST"
    RENAME = "RENAME"
    TRIM = "TRIM"
    UPPER = "UPPER"
    LOWER = "LOWER"
    NULL_HANDLING = "NULL_HANDLING"
    DEFAULT_VALUE = "DEFAULT_VALUE"
    CASE = "CASE"
    CONDITIONAL = "CONDITIONAL"
    CONCATENATION = "CONCATENATION"
    SPLIT = "SPLIT"
    SUBSTRING = "SUBSTRING"
    DATE_CONVERSION = "DATE_CONVERSION"
    DATE_ARITHMETIC = "DATE_ARITHMETIC"
    NUMERIC_ARITHMETIC = "NUMERIC_ARITHMETIC"
    AGGREGATION = "AGGREGATION"
    WINDOW = "WINDOW"
    LOOKUP = "LOOKUP"
    DEDUPLICATION = "DEDUPLICATION"
    FILTER = "FILTER"
    DISTINCT = "DISTINCT"
    COALESCE = "COALESCE"
    CUSTOM_EXPRESSION = "CUSTOM_EXPRESSION"


class TransformationAttribute(BaseModel):
    """Attribute consumed or produced by a transformation.

    Attributes:
        column_id: Metadata column identifier.
        column_name: Column name.
        table_id: Parent table identifier.
        table_name: Parent table name.
        data_type: Data type.
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


class TransformationStep(BaseModel):
    """One operation in a transformation pipeline.

    Steps are ordered and form a logical expression tree/sequence
    that will eventually be translated by a compiler.

    Attributes:
        id: Transformation step identifier.
        sequence: One-based execution sequence.
        operation: Logical transformation operation.
        expression: Optional logical expression.
        input_attributes: Attributes consumed by the operation.
        output_alias: Optional output alias.
        parameters: Operation parameters.
        description: Human-readable explanation.
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

    operation: TransformationOperation

    expression: str | None = None

    input_attributes: list[TransformationAttribute] = Field(
        default_factory=list,
    )

    output_alias: str | None = None

    parameters: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict,
    )

    description: str = Field(
        min_length=1,
    )


class TransformationEvidence(BaseModel):
    """Evidence supporting a transformation decision.

    Attributes:
        evidence_type: Evidence category.
        description: Explanation.
        score: Evidence strength.
        source: Evidence origin.
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


class TransformationPlan(BaseModel):
    """Complete logical transformation plan for a target attribute.

    Attributes:
        id: Transformation plan identifier.
        target: Target attribute.
        source_attributes: Source attributes consumed by the plan.
        operations: Ordered transformation steps.
        business_rule_ids: Business rules applied.
        alignment_id: Semantic alignment supporting the plan.
        intent_id: Intent decision supporting the plan.
        candidate_path_id: Join path supporting source acquisition.
        expression: Final logical expression.
        grain_preserved: Whether target grain is preserved.
        aggregation_required: Whether aggregation is performed.
        deduplication_required: Whether deduplication is performed.
        filter_required: Whether filtering is performed.
        confidence: Overall confidence.
        confidence_source: Confidence origin.
        evidence: Supporting evidence.
        review_status: Human review state.
        rationale: Explanation.
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

    target: TransformationAttribute

    source_attributes: list[TransformationAttribute] = Field(
        default_factory=list,
    )

    operations: list[TransformationStep] = Field(
        min_length=1,
    )

    business_rule_ids: list[UUID] = Field(
        default_factory=list,
    )

    alignment_id: UUID | None = None

    intent_id: UUID | None = None

    candidate_path_id: UUID | None = None

    expression: str = Field(
        min_length=1,
    )

    grain_preserved: bool = True

    aggregation_required: bool = False

    deduplication_required: bool = False

    filter_required: bool = False

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_source: ConfidenceSource

    evidence: list[TransformationEvidence] = Field(
        min_length=1,
    )

    review_status: ReviewStatus = (
        ReviewStatus.NOT_REQUIRED
    )

    rationale: str = Field(
        min_length=1,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        """Validate transformation-plan consistency.

        Returns:
            Validated transformation plan.

        Raises:
            ValueError: If the plan is inconsistent.
        """
        sequences = [
            step.sequence
            for step in self.operations
        ]

        expected = list(
            range(
                1,
                len(sequences) + 1,
            ),
        )

        if sequences != expected:
            raise ValueError(
                "Transformation step sequences must be contiguous "
                "and start at one.",
            )

        if (
            self.aggregation_required
            and self.grain_preserved
        ):
            # Aggregation can preserve grain when the aggregation
            # produces exactly the target grain. Therefore this is
            # intentionally not rejected.
            pass

        if (
            self.confidence < 0.60
            and self.review_status == ReviewStatus.NOT_REQUIRED
        ):
            raise ValueError(
                "Transformation plans below 0.60 confidence "
                "require human review.",
            )

        if (
            self.aggregation_required
            and not any(
                step.operation
                == TransformationOperation.AGGREGATION
                for step in self.operations
            )
        ):
            raise ValueError(
                "aggregation_required is true but no AGGREGATION "
                "operation exists.",
            )

        if (
            self.deduplication_required
            and not any(
                step.operation
                in {
                    TransformationOperation.DEDUPLICATION,
                    TransformationOperation.DISTINCT,
                }
                for step in self.operations
            )
        ):
            raise ValueError(
                "deduplication_required is true but no deduplication "
                "operation exists.",
            )

        return self

    @property
    def requires_review(self) -> bool:
        """Return whether the plan requires human review.

        Returns:
            True when review is required.
        """
        return self.review_status in {
            ReviewStatus.PENDING,
            ReviewStatus.REJECTED,
        }

    @property
    def operation_types(self) -> list[TransformationOperation]:
        """Return ordered transformation operations.

        Returns:
            Ordered operations.
        """
        return [
            step.operation
            for step in self.operations
        ]

    @property
    def is_direct_mapping(self) -> bool:
        """Return whether the plan is a direct mapping.

        Returns:
            True when the only operation is DIRECT.
        """
        return (
            len(self.operations) == 1
            and self.operations[0].operation
            == TransformationOperation.DIRECT
        )


class TransformationPlanSet(BaseModel):
    """Collection of transformation plans for a mapping job."""

    model_config = ConfigDict(
        extra="forbid",
    )

    plans: list[TransformationPlan] = Field(
        default_factory=list,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add(
        self,
        plan: TransformationPlan,
    ) -> None:
        """Add a transformation plan.

        Args:
            plan: Transformation plan to add.

        Raises:
            ValueError: If a plan already exists for the target.
        """
        if any(
            existing.target.column_id
            == plan.target.column_id
            for existing in self.plans
        ):
            raise ValueError(
                "A transformation plan already exists for target "
                f"{plan.target.column_name!r}.",
            )

        self.plans.append(plan)

    def for_target(
        self,
        target_column_id: UUID,
    ) -> TransformationPlan | None:
        """Find a plan for a target column.

        Args:
            target_column_id: Target column identifier.

        Returns:
            Matching transformation plan or None.
        """
        return next(
            (
                plan
                for plan in self.plans
                if plan.target.column_id == target_column_id
            ),
            None,
        )

    def requiring_review(self) -> list[TransformationPlan]:
        """Return plans requiring human review.

        Returns:
            Review-required plans.
        """
        return [
            plan
            for plan in self.plans
            if plan.requires_review
        ]

    def aggregation_plans(self) -> list[TransformationPlan]:
        """Return plans requiring aggregation.

        Returns:
            Aggregation plans.
        """
        return [
            plan
            for plan in self.plans
            if plan.aggregation_required
        ]

    def direct_mappings(self) -> list[TransformationPlan]:
        """Return plans that require no transformation.

        Returns:
            Direct mapping plans.
        """
        return [
            plan
            for plan in self.plans
            if plan.is_direct_mapping
        ]


__all__ = [
    "TransformationAttribute",
    "TransformationEvidence",
    "TransformationOperation",
    "TransformationPlan",
    "TransformationPlanSet",
    "TransformationStep",
]