"""Intent domain models for the STTM platform.

The intent domain represents the business and transformation intent
associated with a target attribute.

Intent reasoning is distinct from semantic alignment:

    Alignment:
        Which source attributes are related to this target?

    Intent:
        What does the target attribute represent and what operation
        is required to produce it?

The actual AI implementation is intentionally outside this module.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sttm.core import (
    ConfidenceSource,
    ReasoningMode,
)


class IntentAttribute(BaseModel):
    """Attribute used as part of intent analysis.

    Attributes:
        column_id: Metadata column identifier.
        column_name: Column name.
        table_id: Parent table identifier.
        table_name: Parent table name.
        data_type: Attribute data type.
        description: Optional business description.
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


class IntentEvidence(BaseModel):
    """Evidence supporting an intent classification.

    Attributes:
        evidence_type: Evidence category.
        description: Evidence explanation.
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


class IntentCandidate(BaseModel):
    """Candidate interpretation of a target attribute.

    Attributes:
        intent_type: Candidate intent classification.
        description: Human-readable interpretation.
        score: Candidate confidence.
        selected: Whether this candidate was selected.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    intent_type: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    selected: bool = False


class IntentDecision(BaseModel):
    """Intent decision for a target attribute.

    The intent decision is consumed by alignment, business-rule
    resolution, transformation planning, and the logical mapping IR.

    Attributes:
        id: Intent decision identifier.
        target: Target attribute.
        intent_type: Selected intent classification.
        business_definition: Business meaning inferred or supplied.
        transformation_required: Whether transformation is required.
        aggregation_required: Whether aggregation is required.
        lookup_required: Whether a lookup/reference operation is required.
        filtering_required: Whether filtering is required.
        conditional_logic_required: Whether conditional logic is required.
        source_attributes: Attributes known to participate in the intent.
        candidates: Alternative intent interpretations.
        evidence: Supporting evidence.
        confidence: Overall intent confidence.
        confidence_source: Source of confidence.
        reasoning_mode: Reasoning mode used.
        rationale: Explanation of the decision.
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

    target: IntentAttribute

    intent_type: str = Field(
        min_length=1,
    )

    business_definition: str = Field(
        min_length=1,
    )

    transformation_required: bool = False

    aggregation_required: bool = False

    lookup_required: bool = False

    filtering_required: bool = False

    conditional_logic_required: bool = False

    source_attributes: list[IntentAttribute] = Field(
        default_factory=list,
    )

    candidates: list[IntentCandidate] = Field(
        min_length=1,
    )

    evidence: list[IntentEvidence] = Field(
        min_length=1,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_source: ConfidenceSource

    reasoning_mode: ReasoningMode

    rationale: str = Field(
        min_length=1,
    )

    requires_review: bool = False

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_intent(self) -> IntentDecision:
        """Validate the intent decision.

        Returns:
            Validated intent decision.

        Raises:
            ValueError: If intent metadata is inconsistent.
        """
        selected_candidates = [
            candidate
            for candidate in self.candidates
            if candidate.selected
        ]

        if len(selected_candidates) != 1:
            raise ValueError(
                "Exactly one intent candidate must be selected.",
            )

        selected = selected_candidates[0]

        if selected.intent_type != self.intent_type:
            raise ValueError(
                "Selected intent candidate must match intent_type.",
            )

        if (
            self.confidence < 0.60
            and not self.requires_review
        ):
            raise ValueError(
                "Intent decisions below 0.60 confidence must "
                "require human review.",
            )

        if (
            self.aggregation_required
            and not self.transformation_required
        ):
            raise ValueError(
                "Aggregation-required intent must also require "
                "a transformation.",
            )

        return self

    @property
    def is_direct(self) -> bool:
        """Return whether no transformation is required.

        Returns:
            True when the intent is direct.
        """
        return not self.transformation_required

    @property
    def requires_complex_logic(self) -> bool:
        """Return whether complex transformation logic is needed.

        Returns:
            True when lookup, filtering, aggregation, or conditional
            logic is required.
        """
        return (
            self.aggregation_required
            or self.lookup_required
            or self.filtering_required
            or self.conditional_logic_required
        )


class IntentSet(BaseModel):
    """Collection of target-column intent decisions."""

    model_config = ConfigDict(
        extra="forbid",
    )

    decisions: list[IntentDecision] = Field(
        default_factory=list,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add(
        self,
        decision: IntentDecision,
    ) -> None:
        """Add an intent decision.

        Args:
            decision: Intent decision to add.

        Raises:
            ValueError: If the target already has an intent decision.
        """
        if any(
            item.target.column_id == decision.target.column_id
            for item in self.decisions
        ):
            raise ValueError(
                "An intent decision already exists for this target.",
            )

        self.decisions.append(
            decision,
        )

    def for_target(
        self,
        target_column_id: UUID,
    ) -> IntentDecision | None:
        """Find the intent decision for a target column.

        Args:
            target_column_id: Target column identifier.

        Returns:
            Matching intent decision or None.
        """
        return next(
            (
                decision
                for decision in self.decisions
                if decision.target.column_id == target_column_id
            ),
            None,
        )

    def requiring_review(self) -> list[IntentDecision]:
        """Return decisions requiring human review.

        Returns:
            Review-required intent decisions.
        """
        return [
            decision
            for decision in self.decisions
            if decision.requires_review
        ]


__all__ = [
    "IntentAttribute",
    "IntentCandidate",
    "IntentDecision",
    "IntentEvidence",
    "IntentSet",
]