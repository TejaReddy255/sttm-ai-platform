"""Logical Mapping Intermediate Representation for the STTM platform.

The Logical Mapping IR is the canonical contract between semantic
reasoning and downstream code generation.

The IR is intentionally execution-engine agnostic.

It describes:

* Source and target attributes.
* Relationships and joins.
* Transformation expressions.
* Business rules.
* Execution dependencies.
* Validation requirements.
* Confidence.
* Lineage.
* Versioning.

Compilers translate this IR into concrete artifacts such as:

* ANSI SQL
* Oracle SQL
* PostgreSQL SQL
* Snowflake SQL
* BigQuery SQL
* Databricks SQL
* PySpark
* Spark SQL
* dbt
* Fixed 16-column STTM

No compiler-specific syntax should be stored in the IR.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IRNodeType(StrEnum):
    """Types of logical transformation nodes."""

    SOURCE_COLUMN = "SOURCE_COLUMN"
    TARGET_COLUMN = "TARGET_COLUMN"
    CONSTANT = "CONSTANT"
    FUNCTION = "FUNCTION"
    CAST = "CAST"
    CASE = "CASE"
    CONDITION = "CONDITION"
    JOIN = "JOIN"
    FILTER = "FILTER"
    AGGREGATION = "AGGREGATION"
    WINDOW = "WINDOW"
    LOOKUP = "LOOKUP"
    COALESCE = "COALESCE"
    NULL_HANDLER = "NULL_HANDLER"
    EXPRESSION = "EXPRESSION"


class IRExpressionOperator(StrEnum):
    """Technology-neutral expression operators."""

    DIRECT = "DIRECT"
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    MODULO = "MODULO"

    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"

    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"

    LIKE = "LIKE"
    IN = "IN"
    BETWEEN = "BETWEEN"

    CONCAT = "CONCAT"

    UPPER = "UPPER"
    LOWER = "LOWER"
    TRIM = "TRIM"

    COALESCE = "COALESCE"

    CAST = "CAST"

    CASE = "CASE"

    SUM = "SUM"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    MIN = "MIN"
    MAX = "MAX"
    AVG = "AVG"

    ROW_NUMBER = "ROW_NUMBER"
    RANK = "RANK"
    DENSE_RANK = "DENSE_RANK"

    CUSTOM = "CUSTOM"


class IRValidationSeverity(StrEnum):
    """Severity levels for IR validation findings."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    BLOCKER = "BLOCKER"


class IRStatus(StrEnum):
    """Lifecycle status of an IR document."""

    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPILED = "COMPILED"


class IRSourceReference(BaseModel):
    """Reference to an upstream domain decision.

    Attributes:
        reference_type: Type of upstream object.
        reference_id: Object identifier.
        description: Optional description.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    reference_type: str = Field(
        min_length=1,
    )

    reference_id: UUID

    description: str | None = None


class IRColumnReference(BaseModel):
    """Technology-neutral column reference.

    Attributes:
        column_id: Canonical metadata column identifier.
        column_name: Physical column name.
        table_id: Parent table identifier.
        table_name: Parent table name.
        data_type: Canonical data type.
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


class IRNode(BaseModel):
    """Node in a logical transformation expression tree.

    IR nodes form the technology-neutral transformation tree.

    Examples:

        SOURCE_COLUMN
             │
             ▼
          FUNCTION
             │
             ▼
          TARGET_COLUMN

    Attributes:
        id: Node identifier.
        node_type: Type of node.
        operator: Optional logical operator.
        column: Optional column reference.
        value: Optional literal value.
        children: Child expression nodes.
        parameters: Operator parameters.
        alias: Optional logical alias.
        description: Human-readable explanation.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: UUID = Field(
        default_factory=uuid4,
    )

    node_type: IRNodeType

    operator: IRExpressionOperator | None = None

    column: IRColumnReference | None = None

    value: str | int | float | bool | None = None

    children: list[IRNode] = Field(
        default_factory=list,
    )

    parameters: dict[
        str,
        str | int | float | bool | None,
    ] = Field(
        default_factory=dict,
    )

    alias: str | None = None

    description: str | None = None

    @model_validator(mode="after")
    def validate_node(self) -> Self:
        """Validate IR node semantics.

        Returns:
            Validated node.

        Raises:
            ValueError: If node structure is invalid.
        """
        column_nodes = {
            IRNodeType.SOURCE_COLUMN,
            IRNodeType.TARGET_COLUMN,
        }

        if (
            self.node_type in column_nodes
            and self.column is None
        ):
            raise ValueError(
                f"{self.node_type} node requires a column reference.",
            )

        if (
            self.node_type == IRNodeType.SOURCE_COLUMN
            and self.children
        ):
            raise ValueError(
                "SOURCE_COLUMN nodes cannot contain children.",
            )

        if (
            self.node_type == IRNodeType.CONSTANT
            and self.value is None
        ):
            raise ValueError(
                "CONSTANT nodes require a value.",
            )

        if (
            self.node_type
            in {
                IRNodeType.FUNCTION,
                IRNodeType.EXPRESSION,
                IRNodeType.CONDITION,
                IRNodeType.CASE,
            }
            and self.operator is None
        ):
            raise ValueError(
                f"{self.node_type} nodes require an operator.",
            )

        return self


class IRJoinCondition(BaseModel):
    """Technology-neutral join condition.

    Attributes:
        left_column: Left join column.
        right_column: Right join column.
        operator: Comparison operator.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    left_column: IRColumnReference

    right_column: IRColumnReference

    operator: IRExpressionOperator = (
        IRExpressionOperator.EQUALS
    )


class IRJoin(BaseModel):
    """Logical join definition.

    Attributes:
        id: Join identifier.
        left_table_id: Left table.
        left_table_name: Left table name.
        right_table_id: Right table.
        right_table_name: Right table name.
        join_type: Logical join type.
        conditions: Join predicates.
        relationship_reference: Supporting relationship.
        cardinality_reference: Supporting cardinality.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: UUID = Field(
        default_factory=uuid4,
    )

    left_table_id: UUID

    left_table_name: str = Field(
        min_length=1,
    )

    right_table_id: UUID

    right_table_name: str = Field(
        min_length=1,
    )

    join_type: str = Field(
        min_length=1,
    )

    conditions: list[IRJoinCondition] = Field(
        min_length=1,
    )

    relationship_reference: UUID | None = None

    cardinality_reference: UUID | None = None

    @model_validator(mode="after")
    def validate_join(self) -> Self:
        """Validate join structure.

        Returns:
            Validated join.

        Raises:
            ValueError: If the join is invalid.
        """
        if (
            self.left_table_id
            == self.right_table_id
        ):
            raise ValueError(
                "A logical join cannot join a table to itself.",
            )

        return self


class IRValidationRule(BaseModel):
    """Validation rule attached to an IR mapping.

    Attributes:
        id: Validation rule identifier.
        rule_code: Stable rule code.
        description: Rule description.
        expression: Technology-neutral validation expression.
        severity: Severity if validation fails.
        blocking: Whether failure blocks compilation.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: UUID = Field(
        default_factory=uuid4,
    )

    rule_code: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    expression: str = Field(
        min_length=1,
    )

    severity: IRValidationSeverity

    blocking: bool = False


class IRConfidence(BaseModel):
    """Confidence information associated with an IR mapping.

    Attributes:
        overall: Overall confidence.
        semantic: Semantic confidence.
        structural: Structural confidence.
        transformation: Transformation confidence.
        business_rule: Business-rule confidence.
        validation: Validation confidence.
        rationale: Explanation.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    overall: float = Field(
        ge=0.0,
        le=1.0,
    )

    semantic: float = Field(
        ge=0.0,
        le=1.0,
    )

    structural: float = Field(
        ge=0.0,
        le=1.0,
    )

    transformation: float = Field(
        ge=0.0,
        le=1.0,
    )

    business_rule: float = Field(
        ge=0.0,
        le=1.0,
    )

    validation: float = Field(
        ge=0.0,
        le=1.0,
    )

    rationale: str = Field(
        min_length=1,
    )


class IRLineage(BaseModel):
    """Lineage information attached to an IR mapping.

    Attributes:
        source_columns: Source columns contributing to target.
        upstream_references: References to upstream domain decisions.
        transformation_summary: Human-readable transformation summary.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    source_columns: list[IRColumnReference] = Field(
        default_factory=list,
    )

    upstream_references: list[IRSourceReference] = Field(
        default_factory=list,
    )

    transformation_summary: str = Field(
        min_length=1,
    )


class LogicalMapping(BaseModel):
    """Logical mapping for one target attribute.

    This is the atomic mapping unit in the Logical Mapping IR.

    Attributes:
        id: Mapping identifier.
        sequence: Execution sequence.
        target: Target attribute.
        expression: Root transformation expression.
        source_columns: Directly referenced source columns.
        joins: Joins required to acquire source data.
        business_rule_ids: Business rules applied.
        upstream_references: Supporting upstream decisions.
        validation_rules: Mapping-specific validation.
        confidence: Mapping confidence.
        lineage: Lineage information.
        comments: Compiler-facing comments.
        status: Mapping status.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    id: UUID = Field(
        default_factory=uuid4,
    )

    sequence: int = Field(
        ge=1,
    )

    target: IRColumnReference

    expression: IRNode

    source_columns: list[IRColumnReference] = Field(
        default_factory=list,
    )

    joins: list[IRJoin] = Field(
        default_factory=list,
    )

    business_rule_ids: list[UUID] = Field(
        default_factory=list,
    )

    upstream_references: list[IRSourceReference] = Field(
        default_factory=list,
    )

    validation_rules: list[IRValidationRule] = Field(
        default_factory=list,
    )

    confidence: IRConfidence

    lineage: IRLineage

    comments: str | None = None

    status: IRStatus = IRStatus.DRAFT

    @model_validator(mode="after")
    def validate_mapping(self) -> Self:
        """Validate logical mapping consistency.

        Returns:
            Validated logical mapping.

        Raises:
            ValueError: If the expression is inconsistent.
        """
        if (
            self.expression.node_type
            == IRNodeType.TARGET_COLUMN
        ):
            raise ValueError(
                "Mapping expression cannot be a TARGET_COLUMN node.",
            )

        if (
            self.confidence.overall < 0.60
            and self.status
            in {
                IRStatus.VALIDATED,
                IRStatus.APPROVED,
                IRStatus.COMPILED,
            }
        ):
            raise ValueError(
                "Low-confidence mappings cannot be marked "
                "validated, approved, or compiled.",
            )

        return self

    @property
    def requires_review(self) -> bool:
        """Return whether this mapping should receive human review.

        Returns:
            True when confidence is below the approval threshold.
        """
        return self.confidence.overall < 0.85

    @property
    def is_direct_mapping(self) -> bool:
        """Return whether this mapping is a direct source mapping.

        Returns:
            True when expression is a source-column reference.
        """
        return (
            self.expression.node_type
            == IRNodeType.SOURCE_COLUMN
        )


class LogicalMappingIR(BaseModel):
    """Complete Logical Mapping Intermediate Representation.

    The document is the canonical handoff between reasoning and
    code generation.

    Attributes:
        id: IR document identifier.
        version: Semantic version of the IR schema.
        mapping_version: Business mapping version.
        source_system: Source system name.
        target_system: Target system name.
        source_model: Source model/database/schema.
        target_model: Target model/database/schema.
        mappings: Target-column mappings.
        joins: Global joins.
        validation_rules: Document-level validations.
        confidence: Overall document confidence.
        status: Document lifecycle status.
        lineage: Document lineage references.
        metadata: Additional non-executable metadata.
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

    version: str = Field(
        default="1.0.0",
        pattern=r"^\d+\.\d+\.\d+$",
    )

    mapping_version: int = Field(
        default=1,
        ge=1,
    )

    source_system: str = Field(
        min_length=1,
    )

    target_system: str = Field(
        min_length=1,
    )

    source_model: str = Field(
        min_length=1,
    )

    target_model: str = Field(
        min_length=1,
    )

    mappings: list[LogicalMapping] = Field(
        min_length=1,
    )

    joins: list[IRJoin] = Field(
        default_factory=list,
    )

    validation_rules: list[IRValidationRule] = Field(
        default_factory=list,
    )

    confidence: IRConfidence

    status: IRStatus = IRStatus.DRAFT

    lineage: list[IRSourceReference] = Field(
        default_factory=list,
    )

    metadata: dict[
        str,
        str | int | float | bool | None,
    ] = Field(
        default_factory=dict,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_document(self) -> Self:
        """Validate IR document consistency.

        Returns:
            Validated IR document.

        Raises:
            ValueError: If mapping sequences or references are invalid.
        """
        sequences = [
            mapping.sequence
            for mapping in self.mappings
        ]

        expected = list(
            range(
                1,
                len(sequences) + 1,
            ),
        )

        if sorted(sequences) != expected:
            raise ValueError(
                "Mapping sequence numbers must be unique, contiguous, "
                "and start at one.",
            )

        mapping_ids = {
            mapping.id
            for mapping in self.mappings
        }

        if len(mapping_ids) != len(self.mappings):
            raise ValueError(
                "Logical mapping IDs must be unique.",
            )

        if (
            self.status
            in {
                IRStatus.VALIDATED,
                IRStatus.APPROVED,
                IRStatus.COMPILED,
            }
            and any(
                mapping.status == IRStatus.DRAFT
                for mapping in self.mappings
            )
        ):
            raise ValueError(
                "A validated IR cannot contain draft mappings.",
            )

        return self

    @property
    def mapping_count(self) -> int:
        """Return the number of target mappings.

        Returns:
            Mapping count.
        """
        return len(self.mappings)

    @property
    def review_required(self) -> bool:
        """Return whether human review is required.

        Returns:
            True when one or more mappings require review.
        """
        return any(
            mapping.requires_review
            for mapping in self.mappings
        )

    @property
    def has_blocking_validation_rules(self) -> bool:
        """Return whether blocking validations exist.

        Returns:
            True when at least one validation is blocking.
        """
        return any(
            rule.blocking
            for rule in self.validation_rules
        )

    def mapping_for_target(
        self,
        target_column_id: UUID,
    ) -> LogicalMapping | None:
        """Find mapping for a target column.

        Args:
            target_column_id: Target column identifier.

        Returns:
            Matching logical mapping or None.
        """
        return next(
            (
                mapping
                for mapping in self.mappings
                if mapping.target.column_id
                == target_column_id
            ),
            None,
        )

    def validate_for_compilation(self) -> None:
        """Validate that the IR is ready for compilation.

        Raises:
            ValueError: If the IR cannot safely be compiled.
        """
        if self.status not in {
            IRStatus.VALIDATED,
            IRStatus.APPROVED,
        }:
            raise ValueError(
                "IR must be VALIDATED or APPROVED before compilation.",
            )

        if self.review_required:
            raise ValueError(
                "IR contains mappings requiring human review.",
            )

        if self.has_blocking_validation_rules:
            raise ValueError(
                "IR contains blocking validation rules.",
            )

        if any(
            mapping.confidence.overall < 0.60
            for mapping in self.mappings
        ):
            raise ValueError(
                "IR contains mappings below the minimum confidence "
                "threshold.",
            )


__all__ = [
    "IRColumnReference",
    "IRConfidence",
    "IRExpressionOperator",
    "IRJoin",
    "IRJoinCondition",
    "IRLineage",
    "IRNode",
    "IRNodeType",
    "IRSourceReference",
    "IRStatus",
    "IRValidationRule",
    "IRValidationSeverity",
    "LogicalMapping",
    "LogicalMappingIR",
]