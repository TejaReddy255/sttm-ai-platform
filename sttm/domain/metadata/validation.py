"""Validation services for canonical STTM metadata.

This module validates the structural integrity of the canonical
metadata contract before metadata enters graph construction and
deterministic analysis.

The validator checks metadata facts only. It does not attempt to
infer business meaning or perform AI reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from sttm.core import (
    ConstraintType,
    ValidationSeverity,
)
from sttm.domain.metadata.models import (
    ColumnModel,
    ConstraintModel,
    DatabaseModel,
    MetadataDocument,
    SchemaModel,
    TableModel,
)


@dataclass(frozen=True, slots=True)
class MetadataValidationIssue:
    """A single metadata validation issue.

    Attributes:
        code: Stable validation code.
        severity: Issue severity.
        message: Human-readable explanation.
        object_type: Type of affected metadata object.
        object_name: Name of affected metadata object.
        path: Logical path to the affected object.
    """

    code: str
    severity: ValidationSeverity
    message: str
    object_type: str | None = None
    object_name: str | None = None
    path: str | None = None


@dataclass(slots=True)
class MetadataValidationReport:
    """Complete metadata validation result.

    Attributes:
        issues: Validation issues discovered.
        checked_databases: Number of databases checked.
        checked_schemas: Number of schemas checked.
        checked_tables: Number of tables checked.
        checked_columns: Number of columns checked.
    """

    issues: list[MetadataValidationIssue] = field(
        default_factory=list,
    )

    checked_databases: int = 0
    checked_schemas: int = 0
    checked_tables: int = 0
    checked_columns: int = 0

    @property
    def has_errors(self) -> bool:
        """Return whether blocking errors exist.

        Returns:
            True when at least one ERROR or BLOCKER exists.
        """
        return any(
            issue.severity
            in {
                ValidationSeverity.ERROR,
                ValidationSeverity.BLOCKER,
            }
            for issue in self.issues
        )

    @property
    def has_warnings(self) -> bool:
        """Return whether warnings exist.

        Returns:
            True when at least one warning exists.
        """
        return any(
            issue.severity == ValidationSeverity.WARNING
            for issue in self.issues
        )

    @property
    def is_valid(self) -> bool:
        """Return whether metadata passed validation.

        Returns:
            True when no blocking issues exist.
        """
        return not self.has_errors

    @property
    def error_count(self) -> int:
        """Return the number of blocking issues.

        Returns:
            Number of errors and blockers.
        """
        return sum(
            issue.severity
            in {
                ValidationSeverity.ERROR,
                ValidationSeverity.BLOCKER,
            }
            for issue in self.issues
        )

    @property
    def warning_count(self) -> int:
        """Return the number of warnings.

        Returns:
            Number of warnings.
        """
        return sum(
            issue.severity == ValidationSeverity.WARNING
            for issue in self.issues
        )


class MetadataValidator:
    """Validate canonical metadata before graph construction.

    The validator is deliberately deterministic. It should never
    invoke an LLM.

    Validation is organized into:

    1. Document validation.
    2. Database validation.
    3. Schema validation.
    4. Table validation.
    5. Column validation.
    6. Constraint validation.
    7. Index validation.
    8. Cross-object reference validation.
    """

    _VALID_IDENTIFIER_PATTERN: Final[str] = (
        r"^[A-Za-z_][A-Za-z0-9_$#]*$"
    )

    def validate(
        self,
        document: MetadataDocument,
    ) -> MetadataValidationReport:
        """Validate a canonical metadata document.

        Args:
            document: Canonical metadata document.

        Returns:
            Complete validation report.
        """
        report = MetadataValidationReport()

        self._validate_document(
            document,
            report,
        )

        for database in document.databases:
            report.checked_databases += 1

            self._validate_database(
                database,
                report,
            )

            for schema in database.schemas:
                report.checked_schemas += 1

                self._validate_schema(
                    schema,
                    report,
                )

                for table in schema.tables:
                    report.checked_tables += 1

                    self._validate_table(
                        database,
                        schema,
                        table,
                        report,
                    )

                    report.checked_columns += len(
                        table.columns,
                    )

                    self._validate_columns(
                        table,
                        report,
                    )

                    self._validate_constraints(
                        database,
                        schema,
                        table,
                        report,
                    )

                    self._validate_indexes(
                        table,
                        report,
                    )

        return report

    def validate_or_raise(
        self,
        document: MetadataDocument,
    ) -> MetadataValidationReport:
        """Validate metadata and raise if blocking issues exist.

        Args:
            document: Metadata document.

        Returns:
            Successful validation report.

        Raises:
            ValueError: If blocking metadata issues are discovered.
        """
        report = self.validate(document)

        if report.has_errors:
            messages = "; ".join(
                issue.message
                for issue in report.issues
                if issue.severity
                in {
                    ValidationSeverity.ERROR,
                    ValidationSeverity.BLOCKER,
                }
            )

            raise ValueError(
                f"Metadata validation failed: {messages}",
            )

        return report

    def _validate_document(
        self,
        document: MetadataDocument,
        report: MetadataValidationReport,
    ) -> None:
        """Validate document-level metadata.

        Args:
            document: Metadata document.
            report: Mutable validation report.
        """
        if not document.databases:
            self._add_issue(
                report,
                code="META-DOC-001",
                severity=ValidationSeverity.BLOCKER,
                message="Metadata document contains no databases.",
                object_type="metadata_document",
                object_name=str(document.id),
            )

        if not document.source_system.name.strip():
            self._add_issue(
                report,
                code="META-DOC-002",
                severity=ValidationSeverity.BLOCKER,
                message="Source system name cannot be empty.",
                object_type="source_system",
                object_name=str(document.source_system.id),
            )

    def _validate_database(
        self,
        database: DatabaseModel,
        report: MetadataValidationReport,
    ) -> None:
        """Validate a database.

        Args:
            database: Database model.
            report: Mutable validation report.
        """
        self._validate_identifier(
            value=database.name,
            object_type="database",
            object_name=database.name,
            path=f"database.{database.name}",
            report=report,
        )

        if not database.schemas:
            self._add_issue(
                report,
                code="META-DB-001",
                severity=ValidationSeverity.WARNING,
                message=(
                    f"Database {database.name!r} contains no schemas."
                ),
                object_type="database",
                object_name=database.name,
            )

    def _validate_schema(
        self,
        schema: SchemaModel,
        report: MetadataValidationReport,
    ) -> None:
        """Validate a schema.

        Args:
            schema: Schema model.
            report: Mutable validation report.
        """
        self._validate_identifier(
            value=schema.name,
            object_type="schema",
            object_name=schema.name,
            path=f"schema.{schema.name}",
            report=report,
        )

        if not schema.tables:
            self._add_issue(
                report,
                code="META-SCHEMA-001",
                severity=ValidationSeverity.WARNING,
                message=(
                    f"Schema {schema.name!r} contains no tables."
                ),
                object_type="schema",
                object_name=schema.name,
            )

    def _validate_table(
        self,
        database: DatabaseModel,
        schema: SchemaModel,
        table: TableModel,
        report: MetadataValidationReport,
    ) -> None:
        """Validate table-level metadata.

        Args:
            database: Parent database.
            schema: Parent schema.
            table: Table model.
            report: Mutable validation report.
        """
        path = (
            f"{database.name}."
            f"{schema.name}."
            f"{table.name}"
        )

        self._validate_identifier(
            value=table.name,
            object_type="table",
            object_name=table.name,
            path=path,
            report=report,
        )

        if not table.columns:
            self._add_issue(
                report,
                code="META-TABLE-001",
                severity=ValidationSeverity.BLOCKER,
                message=(
                    f"Table {path!r} contains no columns."
                ),
                object_type="table",
                object_name=table.name,
                path=path,
            )

        if not table.fully_qualified_name.strip():
            self._add_issue(
                report,
                code="META-TABLE-002",
                severity=ValidationSeverity.BLOCKER,
                message=(
                    f"Table {path!r} has no fully qualified name."
                ),
                object_type="table",
                object_name=table.name,
                path=path,
            )

    def _validate_columns(
        self,
        table: TableModel,
        report: MetadataValidationReport,
    ) -> None:
        """Validate columns within a table.

        Args:
            table: Table model.
            report: Mutable validation report.
        """
        seen_ordinals: set[int] = set()

        for column in table.columns:
            self._validate_column(
                table,
                column,
                report,
            )

            if column.ordinal_position in seen_ordinals:
                self._add_issue(
                    report,
                    code="META-COL-001",
                    severity=ValidationSeverity.BLOCKER,
                    message=(
                        f"Duplicate ordinal position "
                        f"{column.ordinal_position} in "
                        f"table {table.name!r}."
                    ),
                    object_type="column",
                    object_name=column.name,
                    path=(
                        f"{table.name}.{column.name}"
                    ),
                )

            seen_ordinals.add(
                column.ordinal_position,
            )

        ordinals = [
            column.ordinal_position
            for column in table.columns
        ]

        if ordinals and min(ordinals) != 1:
            self._add_issue(
                report,
                code="META-COL-002",
                severity=ValidationSeverity.WARNING,
                message=(
                    f"Column ordinal positions for table "
                    f"{table.name!r} do not start at 1."
                ),
                object_type="table",
                object_name=table.name,
            )

    def _validate_column(
        self,
        table: TableModel,
        column: ColumnModel,
        report: MetadataValidationReport,
    ) -> None:
        """Validate an individual column.

        Args:
            table: Parent table.
            column: Column model.
            report: Mutable validation report.
        """
        path = f"{table.name}.{column.name}"

        self._validate_identifier(
            value=column.name,
            object_type="column",
            object_name=column.name,
            path=path,
            report=report,
        )

        if not column.data_type.strip():
            self._add_issue(
                report,
                code="META-COL-003",
                severity=ValidationSeverity.BLOCKER,
                message=(
                    f"Column {path!r} has no data type."
                ),
                object_type="column",
                object_name=column.name,
                path=path,
            )

        if column.precision is not None and column.scale is not None:
            if column.scale > column.precision:
                self._add_issue(
                    report,
                    code="META-COL-004",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"Column {path!r} has scale greater than "
                        "precision."
                    ),
                    object_type="column",
                    object_name=column.name,
                    path=path,
                )

        statistics = column.statistics

        if statistics is not None:
            if (
                statistics.row_count is not None
                and statistics.null_count is not None
                and statistics.null_count > statistics.row_count
            ):
                self._add_issue(
                    report,
                    code="META-COL-005",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"Column {path!r} has null_count greater "
                        "than row_count."
                    ),
                    object_type="column",
                    object_name=column.name,
                    path=path,
                )

    def _validate_constraints(
        self,
        database: DatabaseModel,
        schema: SchemaModel,
        table: TableModel,
        report: MetadataValidationReport,
    ) -> None:
        """Validate table constraints and FK references.

        Args:
            database: Parent database.
            schema: Parent schema.
            table: Table model.
            report: Mutable validation report.
        """
        local_columns = {
            column.name.casefold()
            for column in table.columns
        }

        for constraint in table.constraints:
            self._validate_constraint(
                database,
                schema,
                table,
                constraint,
                local_columns,
                report,
            )

    def _validate_constraint(
        self,
        database: DatabaseModel,
        schema: SchemaModel,
        table: TableModel,
        constraint: ConstraintModel,
        local_columns: set[str],
        report: MetadataValidationReport,
    ) -> None:
        """Validate one constraint.

        Args:
            database: Parent database.
            schema: Parent schema.
            table: Parent table.
            constraint: Constraint model.
            local_columns: Known local column names.
            report: Mutable validation report.
        """
        for column in constraint.columns:
            if column.column_name.casefold() not in local_columns:
                self._add_issue(
                    report,
                    code="META-CON-001",
                    severity=ValidationSeverity.BLOCKER,
                    message=(
                        f"Constraint {constraint.name!r} references unknown "
                        f"column {column.column_name!r} on table {table.name!r}."
                    ),
                    object_type="constraint",
                    object_name=constraint.name,
                    path=f"{database.name}.{schema.name}.{table.name}",
                )

        if constraint.constraint_type != ConstraintType.FOREIGN_KEY:
            return

        if not constraint.referenced_table or not constraint.referenced_columns:
            self._add_issue(
                report,
                code="META-CON-002",
                severity=ValidationSeverity.BLOCKER,
                message=(
                    f"Foreign key {constraint.name!r} is missing its referenced "
                    "table or columns."
                ),
                object_type="constraint",
                object_name=constraint.name,
            )
            return

        referenced_schema = constraint.referenced_schema or schema.name
        referenced = next(
            (
                candidate
                for candidate in database.schemas
                if candidate.name.casefold() == referenced_schema.casefold()
            ),
            None,
        )
        referenced_table = (
            referenced.get_table(constraint.referenced_table)
            if referenced is not None
            else None
        )
        if referenced_table is None:
            self._add_issue(
                report,
                code="META-CON-003",
                severity=ValidationSeverity.BLOCKER,
                message=(
                    f"Foreign key {constraint.name!r} references unknown table "
                    f"{referenced_schema}.{constraint.referenced_table}."
                ),
                object_type="constraint",
                object_name=constraint.name,
            )
            return

        referenced_names = {
            column.name.casefold()
            for column in referenced_table.columns
        }
        for name in constraint.referenced_columns:
            if name.casefold() not in referenced_names:
                self._add_issue(
                    report,
                    code="META-CON-004",
                    severity=ValidationSeverity.BLOCKER,
                    message=(
                        f"Foreign key {constraint.name!r} references unknown "
                        f"column {name!r} on table {referenced_table.name!r}."
                    ),
                    object_type="constraint",
                    object_name=constraint.name,
                )

    def _validate_indexes(
        self,
        table: TableModel,
        report: MetadataValidationReport,
    ) -> None:
        """Validate index column references."""
        known_columns = {column.name.casefold() for column in table.columns}
        for index in table.indexes:
            for index_column in index.columns:
                if index_column.column_name.casefold() not in known_columns:
                    self._add_issue(
                        report,
                        code="META-IDX-001",
                        severity=ValidationSeverity.BLOCKER,
                        message=(
                            f"Index {index.name!r} references unknown column "
                            f"{index_column.column_name!r} on table {table.name!r}."
                        ),
                        object_type="index",
                        object_name=index.name,
                        path=table.name,
                    )

    def _validate_identifier(
        self,
        *,
        value: str,
        object_type: str,
        object_name: str,
        path: str,
        report: MetadataValidationReport,
    ) -> None:
        """Warn on names that may need quoted identifiers downstream."""
        import re

        if not re.match(self._VALID_IDENTIFIER_PATTERN, value):
            self._add_issue(
                report,
                code="META-NAME-001",
                severity=ValidationSeverity.WARNING,
                message=(
                    f"{object_type.title()} name {value!r} is not a portable "
                    "unquoted SQL identifier."
                ),
                object_type=object_type,
                object_name=object_name,
                path=path,
            )

    @staticmethod
    def _add_issue(
        report: MetadataValidationReport,
        *,
        code: str,
        severity: ValidationSeverity,
        message: str,
        object_type: str | None = None,
        object_name: str | None = None,
        path: str | None = None,
    ) -> None:
        """Append a structured validation issue."""
        report.issues.append(
            MetadataValidationIssue(
                code=code,
                severity=severity,
                message=message,
                object_type=object_type,
                object_name=object_name,
                path=path,
            ),
        )


__all__ = [
    "MetadataValidationIssue",
    "MetadataValidationReport",
    "MetadataValidator",
]
