"""Canonical metadata domain models for the STTM platform.

The models in this module define the normalized metadata contract
consumed by the STTM reasoning pipeline.

The upstream metadata extraction layer is responsible for converting
Oracle, PostgreSQL, SQL Server, Snowflake, CSV, Excel, or other source
formats into these canonical models.

These models deliberately contain metadata facts only. They do not
contain AI decisions, transformation plans, or generated SQL.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sttm.core import (
    ConstraintType,
    DatabasePlatform,
    MetadataType,
    ObjectType,
    SourceSystemType,
)


class DomainModel(BaseModel):
    """Base model for STTM domain objects."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=False,
    )


class MetadataIdentifier(DomainModel):
    """Stable identifier for a metadata object."""

    id: UUID = Field(
        default_factory=uuid4,
        description="Globally unique metadata object identifier.",
    )

    metadata_type: MetadataType = Field(
        description="Type of metadata object represented by the identifier.",
    )


class SourceLocation(DomainModel):
    """Location information for an upstream metadata object."""

    system_name: str = Field(
        min_length=1,
        description="Logical source-system name.",
    )

    platform: DatabasePlatform | None = Field(
        default=None,
        description="Database platform when applicable.",
    )

    connection_name: str | None = Field(
        default=None,
        description="Logical connection identifier.",
    )

    database_name: str | None = Field(
        default=None,
        description="Database name.",
    )

    schema_name: str | None = Field(
        default=None,
        description="Schema name.",
    )

    object_name: str | None = Field(
        default=None,
        description="Physical object name.",
    )


class MetadataStatistics(DomainModel):
    """Optional profiling statistics associated with metadata."""

    row_count: int | None = Field(
        default=None,
        ge=0,
        description="Observed row count.",
    )

    distinct_count: int | None = Field(
        default=None,
        ge=0,
        description="Observed distinct value count.",
    )

    null_count: int | None = Field(
        default=None,
        ge=0,
        description="Observed null value count.",
    )

    null_ratio: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Observed null ratio.",
    )

    uniqueness_ratio: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Observed uniqueness ratio.",
    )

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        """Validate internally consistent profiling counts.

        Returns:
            Validated statistics model.

        Raises:
            ValueError: If counts are inconsistent.
        """
        if (
            self.row_count is not None
            and self.distinct_count is not None
            and self.distinct_count > self.row_count
        ):
            raise ValueError(
                "distinct_count cannot exceed row_count.",
            )

        if (
            self.row_count is not None
            and self.null_count is not None
            and self.null_count > self.row_count
        ):
            raise ValueError(
                "null_count cannot exceed row_count.",
            )

        if (
            self.row_count is not None
            and self.null_count is not None
            and self.distinct_count is not None
            and self.distinct_count > self.row_count - self.null_count
        ):
            raise ValueError(
                "distinct_count cannot exceed non-null row count.",
            )

        return self


class ColumnModel(DomainModel):
    """Canonical representation of a database or file column."""

    id: UUID = Field(
        default_factory=uuid4,
        description="Globally unique column identifier.",
    )

    name: str = Field(
        min_length=1,
        description="Physical column name.",
    )

    ordinal_position: int = Field(
        ge=1,
        description="One-based column position.",
    )

    data_type: str = Field(
        min_length=1,
        description="Physical source data type.",
    )

    normalized_data_type: str | None = Field(
        default=None,
        description="Canonical normalized data type.",
    )

    length: int | None = Field(
        default=None,
        ge=0,
        description="Character or binary length where applicable.",
    )

    precision: int | None = Field(
        default=None,
        ge=0,
        description="Numeric precision where applicable.",
    )

    scale: int | None = Field(
        default=None,
        ge=0,
        description="Numeric scale where applicable.",
    )

    nullable: bool = True

    default_expression: str | None = Field(
        default=None,
        description="Database-defined default expression.",
    )

    comment: str | None = Field(
        default=None,
        description="Database or metadata comment.",
    )

    is_primary_key: bool = False

    is_foreign_key: bool = False

    is_unique: bool = False

    is_indexed: bool = False

    statistics: MetadataStatistics | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate and normalize a column name.

        Args:
            value: Physical column name.

        Returns:
            Stripped column name.

        Raises:
            ValueError: If the name is blank.
        """
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Column name cannot be blank.",
            )

        return normalized


class ConstraintColumn(DomainModel):
    """Column participation within a constraint."""

    column_name: str = Field(
        min_length=1,
    )

    ordinal_position: int = Field(
        ge=1,
    )


class ConstraintModel(DomainModel):
    """Database constraint metadata."""

    id: UUID = Field(
        default_factory=uuid4,
    )

    name: str = Field(
        min_length=1,
    )

    constraint_type: ConstraintType

    columns: list[ConstraintColumn] = Field(
        min_length=1,
    )

    referenced_schema: str | None = None

    referenced_table: str | None = None

    referenced_columns: list[str] = Field(
        default_factory=list,
    )

    expression: str | None = None

    enabled: bool = True

    validated: bool | None = None

    @model_validator(mode="after")
    def validate_foreign_key(self) -> Self:
        """Validate foreign-key-specific fields.

        Returns:
            Validated constraint.

        Raises:
            ValueError: If FK metadata is incomplete or inconsistent.
        """
        if self.constraint_type == ConstraintType.FOREIGN_KEY:
            if not self.referenced_table:
                raise ValueError(
                    "Foreign-key constraints require referenced_table.",
                )

            if not self.referenced_columns:
                raise ValueError(
                    "Foreign-key constraints require referenced_columns.",
                )

            if len(self.columns) != len(self.referenced_columns):
                raise ValueError(
                    "Foreign-key column count must match referenced column count.",
                )

        return self


class IndexColumn(DomainModel):
    """Column participation within an index."""

    column_name: str = Field(
        min_length=1,
    )

    ordinal_position: int = Field(
        ge=1,
    )

    descending: bool = False


class IndexModel(DomainModel):
    """Database index metadata."""

    id: UUID = Field(
        default_factory=uuid4,
    )

    name: str = Field(
        min_length=1,
    )

    columns: list[IndexColumn] = Field(
        min_length=1,
    )

    unique: bool = False

    clustered: bool | None = None

    partial: bool = False

    predicate: str | None = None

    enabled: bool = True


class TableModel(DomainModel):
    """Canonical representation of a table or view."""

    id: UUID = Field(
        default_factory=uuid4,
    )

    name: str = Field(
        min_length=1,
    )

    object_type: ObjectType = ObjectType.TABLE

    fully_qualified_name: str = Field(
        min_length=1,
    )

    comment: str | None = None

    columns: list[ColumnModel] = Field(
        min_length=1,
    )

    constraints: list[ConstraintModel] = Field(
        default_factory=list,
    )

    indexes: list[IndexModel] = Field(
        default_factory=list,
    )

    statistics: MetadataStatistics | None = None

    @model_validator(mode="after")
    def validate_columns(self) -> Self:
        """Validate table columns and constraints.

        Returns:
            Validated table model.

        Raises:
            ValueError: If column metadata is inconsistent.
        """
        column_names = [
            column.name.casefold()
            for column in self.columns
        ]

        if len(column_names) != len(set(column_names)):
            raise ValueError(
                f"Duplicate columns detected in table {self.name!r}.",
            )

        column_name_set = set(column_names)

        for constraint in self.constraints:
            for column in constraint.columns:
                if column.column_name.casefold() not in column_name_set:
                    raise ValueError(
                        f"Constraint {constraint.name!r} references unknown "
                        f"column {column.column_name!r}.",
                    )

        for index in self.indexes:
            for column in index.columns:
                if column.column_name.casefold() not in column_name_set:
                    raise ValueError(
                        f"Index {index.name!r} references unknown "
                        f"column {column.column_name!r}.",
                    )

        return self

    def get_column(
        self,
        column_name: str,
    ) -> ColumnModel | None:
        """Find a column case-insensitively.

        Args:
            column_name: Column name.

        Returns:
            Matching column or None.
        """
        normalized = column_name.casefold()

        return next(
            (
                column
                for column in self.columns
                if column.name.casefold() == normalized
            ),
            None,
        )

    def primary_key_columns(self) -> list[ColumnModel]:
        """Return columns participating in primary keys.

        Returns:
            Primary-key columns.
        """
        return [
            column
            for column in self.columns
            if column.is_primary_key
        ]

    def foreign_key_columns(self) -> list[ColumnModel]:
        """Return columns participating in foreign keys.

        Returns:
            Foreign-key columns.
        """
        return [
            column
            for column in self.columns
            if column.is_foreign_key
        ]


class SchemaModel(DomainModel):
    """Canonical representation of a database schema."""

    id: UUID = Field(
        default_factory=uuid4,
    )

    name: str = Field(
        min_length=1,
    )

    database_name: str | None = None

    comment: str | None = None

    tables: list[TableModel] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_tables(self) -> Self:
        """Ensure table names are unique within the schema.

        Returns:
            Validated schema.

        Raises:
            ValueError: If duplicate tables exist.
        """
        names = [
            table.name.casefold()
            for table in self.tables
        ]

        if len(names) != len(set(names)):
            raise ValueError(
                f"Duplicate table names detected in schema {self.name!r}.",
            )

        return self

    def get_table(
        self,
        table_name: str,
    ) -> TableModel | None:
        """Find a table case-insensitively.

        Args:
            table_name: Table name.

        Returns:
            Matching table or None.
        """
        normalized = table_name.casefold()

        return next(
            (
                table
                for table in self.tables
                if table.name.casefold() == normalized
            ),
            None,
        )


class DatabaseModel(DomainModel):
    """Canonical representation of a database."""

    id: UUID = Field(
        default_factory=uuid4,
    )

    name: str = Field(
        min_length=1,
    )

    platform: DatabasePlatform

    version: str | None = None

    schemas: list[SchemaModel] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_schemas(self) -> Self:
        """Ensure schema names are unique within the database.

        Returns:
            Validated database.

        Raises:
            ValueError: If duplicate schemas exist.
        """
        names = [
            schema.name.casefold()
            for schema in self.schemas
        ]

        if len(names) != len(set(names)):
            raise ValueError(
                f"Duplicate schema names detected in database {self.name!r}.",
            )

        return self


class SourceSystemModel(DomainModel):
    """Canonical representation of an upstream metadata source."""

    id: UUID = Field(
        default_factory=uuid4,
    )

    name: str = Field(
        min_length=1,
    )

    source_type: SourceSystemType

    description: str | None = None

    location: SourceLocation | None = None

    databases: list[DatabaseModel] = Field(
        default_factory=list,
    )

    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    extractor_name: str | None = None

    extractor_version: str | None = None


class MetadataDocument(DomainModel):
    """Complete canonical metadata document.

    This is the primary input contract for the STTM reasoning
    pipeline.
    """

    id: UUID = Field(
        default_factory=uuid4,
    )

    source_system: SourceSystemModel

    databases: list[DatabaseModel] = Field(
        min_length=1,
    )

    metadata_version: str = Field(
        default="1.0",
        min_length=1,
    )

    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    extraction_run_id: UUID = Field(
        default_factory=uuid4,
    )

    @model_validator(mode="after")
    def validate_document(self) -> Self:
        """Validate document-level metadata consistency.

        Returns:
            Validated metadata document.

        Raises:
            ValueError: If document metadata is inconsistent.
        """
        database_ids = [
            database.id
            for database in self.databases
        ]

        if len(database_ids) != len(set(database_ids)):
            raise ValueError(
                "Duplicate database IDs detected.",
            )

        names = [
            database.name.casefold()
            for database in self.databases
        ]

        if len(names) != len(set(names)):
            raise ValueError(
                "Duplicate database names detected.",
            )

        return self

    def find_table(
        self,
        *,
        database_name: str,
        schema_name: str,
        table_name: str,
    ) -> TableModel | None:
        """Find a table in the canonical metadata document.

        Args:
            database_name: Database name.
            schema_name: Schema name.
            table_name: Table name.

        Returns:
            Matching table or None.
        """
        database = next(
            (
                item
                for item in self.databases
                if item.name.casefold()
                == database_name.casefold()
            ),
            None,
        )

        if database is None:
            return None

        schema = next(
            (
                item
                for item in database.schemas
                if item.name.casefold()
                == schema_name.casefold()
            ),
            None,
        )

        if schema is None:
            return None

        return schema.get_table(table_name)

    def all_tables(self) -> list[TableModel]:
        """Return every table across all databases and schemas.

        Returns:
            Flat list of tables.
        """
        return [
            table
            for database in self.databases
            for schema in database.schemas
            for table in schema.tables
        ]

    def all_columns(self) -> list[ColumnModel]:
        """Return every column in the document.

        Returns:
            Flat list of columns.
        """
        return [
            column
            for table in self.all_tables()
            for column in table.columns
        ]