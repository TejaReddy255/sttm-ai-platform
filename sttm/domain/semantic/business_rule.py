"""Business rule domain models for the STTM platform.

Business rules describe explicit or inferred business logic that
must be applied when producing target attributes.

Rules may originate from:

* Enterprise policies.
* Business glossary definitions.
* Transformation catalogs.
* Historical STTM mappings.
* User-provided rules.
* AI-assisted rule resolution.
* Human-approved decisions.

The models in this module represent business-rule decisions only.
Rule execution belongs to the transformation and compiler layers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sttm.core import (
    ConfidenceSource,
    ReviewStatus,
)


class BusinessRuleAttribute(BaseModel):
    """Attribute referenced by a business rule.

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


class BusinessRuleEvidence(BaseModel):
    """Evidence supporting a business rule.

    Attributes:
        source_type: Type of source providing the evidence.
        source_id: Optional source identifier.
        description: Evidence description.
        score: Evidence strength.
        authoritative: Whether the source is authoritative.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    source_type: str = Field(
        min_length=1,
    )

    source_id: str | None = None

    description: str = Field(
        min_length=1,
    )

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    authoritative: bool = False


class BusinessRuleConflict(BaseModel):
    """Conflict between two business rules.

    Attributes:
        conflicting_rule_id: ID of the conflicting rule.
        description: Explanation of the conflict.
        resolution: Resolution, when known.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    conflicting_rule_id: UUID

    description: str = Field(
        min_length=1,
    )

    resolution: str | None = None


class BusinessRule(BaseModel):
    """Canonical business rule.

    Attributes:
        id: Rule identifier.
        rule_code: Stable human-readable rule code.
        name: Rule name.
        description: Business description.
        expression: Machine-readable rule expression when available.
        natural_language_rule: Human-readable rule statement.
        source_attributes: Attributes consumed by the rule.
        target_attributes: Attributes produced or affected by the rule.
        priority: Rule priority.
        mandatory: Whether the rule must be applied.
        active: Whether the rule is active.
        evidence: Supporting sources.
        conflicts: Conflicting rules.
        confidence: Overall confidence.
        confidence_source: Confidence origin.
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

    rule_code: str = Field(
        min_length=1,
    )

    name: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    expression: str | None = None

    natural_language_rule: str = Field(
        min_length=1,
    )

    source_attributes: list[BusinessRuleAttribute] = Field(
        default_factory=list,
    )

    target_attributes: list[BusinessRuleAttribute] = Field(
        default_factory=list,
    )

    priority: int = Field(
        default=100,
        ge=1,
    )

    mandatory: bool = False

    active: bool = True

    evidence: list[BusinessRuleEvidence] = Field(
        min_length=1,
    )

    conflicts: list[BusinessRuleConflict] = Field(
        default_factory=list,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    confidence_source: ConfidenceSource

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
    def validate_rule(self) -> BusinessRule:
        """Validate business-rule consistency.

        Returns:
            Validated business rule.

        Raises:
            ValueError: If the rule is inconsistent.
        """
        if not self.source_attributes and not self.target_attributes:
            raise ValueError(
                "A business rule must reference at least one "
                "source or target attribute.",
            )

        if self.mandatory and not self.active:
            raise ValueError(
                "A mandatory business rule cannot be inactive.",
            )

        if (
            self.confidence < 0.60
            and self.review_status == ReviewStatus.NOT_REQUIRED
        ):
            raise ValueError(
                "Low-confidence business rules require human review.",
            )

        return self

    @property
    def requires_review(self) -> bool:
        """Return whether human review is required.

        Returns:
            True when review is required.
        """
        return self.review_status in {
            ReviewStatus.PENDING,
            ReviewStatus.REJECTED,
        }

    @property
    def has_conflicts(self) -> bool:
        """Return whether the rule conflicts with another rule.

        Returns:
            True when conflicts exist.
        """
        return bool(self.conflicts)

    @property
    def authoritative_evidence(self) -> list[BusinessRuleEvidence]:
        """Return authoritative supporting evidence.

        Returns:
            Authoritative evidence items.
        """
        return [
            evidence
            for evidence in self.evidence
            if evidence.authoritative
        ]


class BusinessRuleSet(BaseModel):
    """Collection of business rules applicable to a mapping request."""

    model_config = ConfigDict(
        extra="forbid",
    )

    rules: list[BusinessRule] = Field(
        default_factory=list,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add(
        self,
        rule: BusinessRule,
    ) -> None:
        """Add a business rule.

        Args:
            rule: Rule to add.

        Raises:
            ValueError: If the rule code already exists.
        """
        if any(
            existing.rule_code == rule.rule_code
            for existing in self.rules
        ):
            raise ValueError(
                f"Business rule {rule.rule_code!r} already exists.",
            )

        self.rules.append(rule)

    def active_rules(self) -> list[BusinessRule]:
        """Return active rules.

        Returns:
            Active business rules.
        """
        return [
            rule
            for rule in self.rules
            if rule.active
        ]

    def mandatory_rules(self) -> list[BusinessRule]:
        """Return mandatory rules ordered by priority.

        Returns:
            Mandatory rules, highest priority first.
        """
        return sorted(
            [
                rule
                for rule in self.rules
                if rule.active and rule.mandatory
            ],
            key=lambda rule: rule.priority,
        )

    def for_target(
        self,
        target_column_id: UUID,
    ) -> list[BusinessRule]:
        """Return rules affecting a target column.

        Args:
            target_column_id: Target column identifier.

        Returns:
            Applicable business rules.
        """
        return [
            rule
            for rule in self.rules
            if any(
                attribute.column_id == target_column_id
                for attribute in rule.target_attributes
            )
        ]

    def for_source(
        self,
        source_column_id: UUID,
    ) -> list[BusinessRule]:
        """Return rules consuming a source column.

        Args:
            source_column_id: Source column identifier.

        Returns:
            Applicable business rules.
        """
        return [
            rule
            for rule in self.rules
            if any(
                attribute.column_id == source_column_id
                for attribute in rule.source_attributes
            )
        ]

    def conflicting_rules(self) -> list[BusinessRule]:
        """Return rules that have unresolved conflicts.

        Returns:
            Rules containing conflicts.
        """
        return [
            rule
            for rule in self.rules
            if rule.has_conflicts
        ]

    def requiring_review(self) -> list[BusinessRule]:
        """Return rules requiring human review.

        Returns:
            Rules requiring review.
        """
        return [
            rule
            for rule in self.rules
            if rule.requires_review
        ]


__all__ = [
    "BusinessRule",
    "BusinessRuleAttribute",
    "BusinessRuleConflict",
    "BusinessRuleEvidence",
    "BusinessRuleSet",
]