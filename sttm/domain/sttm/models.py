"""The portable, reviewable STTM artifact produced from a mapping IR.

This module deliberately models documentation and implementation intent, not
SQL.  Execution engines belong strictly downstream of this contract.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


STTM_COLUMNS: tuple[str, ...] = (
    "source_system",
    "source_database",
    "source_schema",
    "source_table",
    "source_columns",
    "target_system",
    "target_database",
    "target_schema",
    "target_table",
    "target_column",
    "transformation_rule",
    "join_rule",
    "filter_rule",
    "business_rule",
    "confidence",
    "assumptions",
)


class STTMRow(BaseModel):
    """One target-column mapping in the external 16-column STTM contract."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_system: str = Field(min_length=1)
    source_database: str = Field(default="")
    source_schema: str = Field(default="")
    source_table: str = Field(min_length=1)
    source_columns: str = Field(min_length=1)
    target_system: str = Field(min_length=1)
    target_database: str = Field(default="")
    target_schema: str = Field(default="")
    target_table: str = Field(min_length=1)
    target_column: str = Field(min_length=1)
    transformation_rule: str = Field(min_length=1)
    join_rule: str = Field(default="")
    filter_rule: str = Field(default="")
    business_rule: str = Field(default="")
    confidence: float = Field(ge=0.0, le=1.0)
    assumptions: str = Field(default="")

    def as_record(self) -> dict[str, str | float]:
        """Return fields in the stable external-column order."""
        return {column: getattr(self, column) for column in STTM_COLUMNS}


class STTMDocument(BaseModel):
    """A compiled STTM artifact ready for human review or code generation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    version: str = Field(default="1.0", min_length=1)
    mapping_ir_id: UUID
    source_system: str = Field(min_length=1)
    target_system: str = Field(min_length=1)
    rows: list[STTMRow] = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_target_columns(self) -> STTMDocument:
        """Reject duplicate target mappings in the same target table."""
        targets = [(row.target_table.casefold(), row.target_column.casefold()) for row in self.rows]
        if len(targets) != len(set(targets)):
            raise ValueError("An STTM document cannot map a target column more than once.")
        return self

    @property
    def column_count(self) -> int:
        """Return the fixed width of the external STTM contract."""
        return len(STTM_COLUMNS)


__all__ = ["STTM_COLUMNS", "STTMDocument", "STTMRow"]
