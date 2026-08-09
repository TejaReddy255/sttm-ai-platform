"""Validation services for the Logical Mapping IR.

This module provides domain-level validation for the Logical Mapping
Intermediate Representation before it reaches downstream code
generators.

The validator checks structural and semantic invariants such as:

* Mapping sequence integrity.
* Target uniqueness.
* Source-column references.
* Join consistency.
* Expression-tree validity.
* Blocking validation rules.
* Human-review requirements.
* Confidence thresholds.

It does not validate generated SQL syntax. Dialect-specific
validation belongs to the compiler layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sttm.domain.ir.models import (
    IRNode,
    IRNodeType,
    IRStatus,
    LogicalMapping,
    LogicalMappingIR,
)


@dataclass(frozen=True)
class IRValidationFinding:
    """One validation finding.

    Attributes:
        code: Stable validation code.
        message: Human-readable message.
        blocking: Whether compilation must stop.
        mapping_id: Optional affected mapping.
        target_column_id: Optional affected target column.
    """

    code: str
    message: str
    blocking: bool = True
    mapping_id: UUID | None = None
    target_column_id: UUID | None = None


@dataclass
class IRValidationResult:
    """Result of validating a Logical Mapping IR.

    Attributes:
        findings: Validation findings.
    """

    findings: list[IRValidationFinding] = field(
        default_factory=list,
    )

    @property
    def valid(self) -> bool:
        """Return whether the IR is valid.

        Returns:
            True when no blocking findings exist.
        """
        return not self.blocking_findings

    @property
    def blocking_findings(self) -> list[IRValidationFinding]:
        """Return blocking findings.

        Returns:
            Blocking validation findings.
        """
        return [
            finding
            for finding in self.findings
            if finding.blocking
        ]

    @property
    def warnings(self) -> list[IRValidationFinding]:
        """Return non-blocking findings.

        Returns:
            Warning findings.
        """
        return [
            finding
            for finding in self.findings
            if not finding.blocking
        ]

    def add(
        self,
        finding: IRValidationFinding,
    ) -> None:
        """Add a validation finding.

        Args:
            finding: Finding to add.
        """
        self.findings.append(finding)


class LogicalMappingIRValidator:
    """Validate Logical Mapping IR before compilation."""

    MIN_COMPILATION_CONFIDENCE = 0.60

    def validate(
        self,
        ir: LogicalMappingIR,
    ) -> IRValidationResult:
        """Validate a complete Logical Mapping IR.

        Args:
            ir: Logical Mapping IR to validate.

        Returns:
            Validation result.
        """
        result = IRValidationResult()

        self._validate_document_status(
            ir,
            result,
        )

        self._validate_mapping_sequences(
            ir,
            result,
        )

        self._validate_target_uniqueness(
            ir,
            result,
        )

        self._validate_mappings(
            ir,
            result,
        )

        self._validate_global_joins(
            ir,
            result,
        )

        self._validate_blocking_rules(
            ir,
            result,
        )

        return result

    def assert_valid(
        self,
        ir: LogicalMappingIR,
    ) -> None:
        """Raise when the IR is not valid.

        Args:
            ir: Logical Mapping IR.

        Raises:
            ValueError: If blocking findings exist.
        """
        result = self.validate(ir)

        if not result.valid:
            messages = "\n".join(
                f"[{finding.code}] {finding.message}"
                for finding in result.blocking_findings
            )

            raise ValueError(
                "Logical Mapping IR validation failed:\n"
                f"{messages}",
            )

    def _validate_document_status(
        self,
        ir: LogicalMappingIR,
        result: IRValidationResult,
    ) -> None:
        """Validate document lifecycle status."""
        if ir.status not in {
            IRStatus.DRAFT,
            IRStatus.VALIDATED,
            IRStatus.APPROVED,
        }:
            result.add(
                IRValidationFinding(
                    code="IR-STATUS-001",
                    message=(
                        "IR cannot enter compilation validation from "
                        f"status {ir.status}."
                    ),
                ),
            )

    def _validate_mapping_sequences(
        self,
        ir: LogicalMappingIR,
        result: IRValidationResult,
    ) -> None:
        """Validate mapping sequence numbers."""
        sequences = [
            mapping.sequence
            for mapping in ir.mappings
        ]

        expected = list(
            range(
                1,
                len(sequences) + 1,
            ),
        )

        if sorted(sequences) != expected:
            result.add(
                IRValidationFinding(
                    code="IR-SEQUENCE-001",
                    message=(
                        "Mapping sequences must be unique, contiguous, "
                        "and start at one."
                    ),
                ),
            )

    def _validate_target_uniqueness(
        self,
        ir: LogicalMappingIR,
        result: IRValidationResult,
    ) -> None:
        """Ensure each target column has at most one mapping."""
        seen: set[UUID] = set()

        for mapping in ir.mappings:
            target_id = mapping.target.column_id

            if target_id in seen:
                result.add(
                    IRValidationFinding(
                        code="IR-TARGET-001",
                        message=(
                            "Multiple mappings exist for target column "
                            f"{mapping.target.column_name!r}."
                        ),
                        mapping_id=mapping.id,
                        target_column_id=target_id,
                    ),
                )

            seen.add(target_id)

    def _validate_mappings(
        self,
        ir: LogicalMappingIR,
        result: IRValidationResult,
    ) -> None:
        """Validate individual logical mappings."""
        for mapping in ir.mappings:
            self._validate_mapping(
                mapping,
                result,
            )

    def _validate_mapping(
        self,
        mapping: LogicalMapping,
        result: IRValidationResult,
    ) -> None:
        """Validate one logical mapping."""
        self._validate_mapping_confidence(
            mapping,
            result,
        )

        self._validate_expression(
            mapping,
            result,
        )

        self._validate_source_columns(
            mapping,
            result,
        )

        self._validate_joins(
            mapping,
            result,
        )

        self._validate_review_status(
            mapping,
            result,
        )

    def _validate_mapping_confidence(
        self,
        mapping: LogicalMapping,
        result: IRValidationResult,
    ) -> None:
        """Validate mapping confidence."""
        confidence = mapping.confidence.overall

        if confidence < self.MIN_COMPILATION_CONFIDENCE:
            result.add(
                IRValidationFinding(
                    code="IR-CONFIDENCE-001",
                    message=(
                        f"Mapping for target "
                        f"{mapping.target.column_name!r} has confidence "
                        f"{confidence:.2f}, below the minimum compilation "
                        f"threshold of "
                        f"{self.MIN_COMPILATION_CONFIDENCE:.2f}."
                    ),
                    mapping_id=mapping.id,
                    target_column_id=mapping.target.column_id,
                ),
            )

        elif confidence < 0.85:
            result.add(
                IRValidationFinding(
                    code="IR-CONFIDENCE-002",
                    message=(
                        f"Mapping for target "
                        f"{mapping.target.column_name!r} has moderate "
                        f"confidence ({confidence:.2f})."
                    ),
                    blocking=False,
                    mapping_id=mapping.id,
                    target_column_id=mapping.target.column_id,
                ),
            )

    def _validate_expression(
        self,
        mapping: LogicalMapping,
        result: IRValidationResult,
    ) -> None:
        """Validate the mapping expression tree."""
        expression = mapping.expression

        if expression.node_type == IRNodeType.TARGET_COLUMN:
            result.add(
                IRValidationFinding(
                    code="IR-EXPRESSION-001",
                    message=(
                        "A mapping expression cannot directly be a "
                        "TARGET_COLUMN node."
                    ),
                    mapping_id=mapping.id,
                    target_column_id=mapping.target.column_id,
                ),
            )

        self._validate_expression_node(
            expression,
            mapping,
            result,
        )

    def _validate_expression_node(
        self,
        node: IRNode,
        mapping: LogicalMapping,
        result: IRValidationResult,
    ) -> None:
        """Recursively validate an expression node."""
        if node.node_type == IRNodeType.SOURCE_COLUMN:
            if node.column is None:
                result.add(
                    IRValidationFinding(
                        code="IR-EXPRESSION-002",
                        message=(
                            "SOURCE_COLUMN node is missing its "
                            "column reference."
                        ),
                        mapping_id=mapping.id,
                        target_column_id=mapping.target.column_id,
                    ),
                )

        if node.node_type == IRNodeType.CONSTANT:
            if node.value is None:
                result.add(
                    IRValidationFinding(
                        code="IR-EXPRESSION-003",
                        message=(
                            "CONSTANT node must contain a value."
                        ),
                        mapping_id=mapping.id,
                        target_column_id=mapping.target.column_id,
                    ),
                )

        for child in node.children:
            self._validate_expression_node(
                child,
                mapping,
                result,
            )

    def _validate_source_columns(
        self,
        mapping: LogicalMapping,
        result: IRValidationResult,
    ) -> None:
        """Validate source-column references."""
        expression_columns = self._collect_expression_columns(
            mapping.expression,
        )

        declared_columns = {
            column.column_id
            for column in mapping.source_columns
        }

        missing = expression_columns - declared_columns

        for column_id in missing:
            result.add(
                IRValidationFinding(
                    code="IR-SOURCE-001",
                    message=(
                        "Expression references source column "
                        f"{column_id} that is not declared in "
                        "source_columns."
                    ),
                    mapping_id=mapping.id,
                    target_column_id=mapping.target.column_id,
                ),
            )

    def _collect_expression_columns(
        self,
        node: IRNode,
    ) -> set[UUID]:
        """Collect source columns from an expression tree."""
        result: set[UUID] = set()

        if (
            node.node_type == IRNodeType.SOURCE_COLUMN
            and node.column is not None
        ):
            result.add(
                node.column.column_id,
            )

        for child in node.children:
            result.update(
                self._collect_expression_columns(child),
            )

        return result

    def _validate_joins(
        self,
        mapping: LogicalMapping,
        result: IRValidationResult,
    ) -> None:
        """Validate joins attached to a mapping."""
        for join in mapping.joins:
            if (
                join.left_table_id
                == join.right_table_id
            ):
                result.add(
                    IRValidationFinding(
                        code="IR-JOIN-001",
                        message=(
                            "Join references the same table on both "
                            "sides."
                        ),
                        mapping_id=mapping.id,
                        target_column_id=mapping.target.column_id,
                    ),
                )

            if not join.conditions:
                result.add(
                    IRValidationFinding(
                        code="IR-JOIN-002",
                        message=(
                            "Join must contain at least one condition."
                        ),
                        mapping_id=mapping.id,
                        target_column_id=mapping.target.column_id,
                    ),
                )

    def _validate_global_joins(
        self,
        ir: LogicalMappingIR,
        result: IRValidationResult,
    ) -> None:
        """Validate document-level joins."""
        for join in ir.joins:
            if (
                join.left_table_id
                == join.right_table_id
            ):
                result.add(
                    IRValidationFinding(
                        code="IR-JOIN-003",
                        message=(
                            "Global join references the same table "
                            "on both sides."
                        ),
                    ),
                )

    def _validate_blocking_rules(
        self,
        ir: LogicalMappingIR,
        result: IRValidationResult,
    ) -> None:
        """Validate document-level blocking rules."""
        for rule in ir.validation_rules:
            if rule.blocking:
                result.add(
                    IRValidationFinding(
                        code="IR-VALIDATION-001",
                        message=(
                            f"Blocking validation rule "
                            f"{rule.rule_code!r} is attached to the IR."
                        ),
                    ),
                )

    def _validate_review_status(
        self,
        mapping: LogicalMapping,
        result: IRValidationResult,
    ) -> None:
        """Ensure low-confidence mappings do not bypass review."""
        if (
            mapping.requires_review
            and mapping.status
            in {
                IRStatus.VALIDATED,
                IRStatus.APPROVED,
                IRStatus.COMPILED,
            }
        ):
            result.add(
                IRValidationFinding(
                    code="IR-REVIEW-001",
                    message=(
                        f"Mapping for target "
                        f"{mapping.target.column_name!r} requires "
                        "human review but has already been marked "
                        f"{mapping.status}."
                    ),
                    mapping_id=mapping.id,
                    target_column_id=mapping.target.column_id,
                ),
            )


__all__ = [
    "IRValidationFinding",
    "IRValidationResult",
    "LogicalMappingIRValidator",
]