"""Canonical metadata domain models.

This package defines the platform's canonical representation of
upstream metadata.

The canonical model is the contract between the upstream metadata
extractor and the STTM reasoning pipeline.
"""

from .models import (
    ColumnModel,
    ConstraintColumn,
    ConstraintModel,
    DatabaseModel,
    DomainModel,
    IndexColumn,
    IndexModel,
    MetadataDocument,
    MetadataIdentifier,
    MetadataStatistics,
    SchemaModel,
    SourceLocation,
    SourceSystemModel,
    TableModel,
)
from .validation import (
    MetadataValidationIssue,
    MetadataValidationReport,
    MetadataValidator,
)

__all__ = [
    "ColumnModel",
    "ConstraintColumn",
    "ConstraintModel",
    "DatabaseModel",
    "DomainModel",
    "IndexColumn",
    "IndexModel",
    "MetadataDocument",
    "MetadataIdentifier",
    "MetadataStatistics",
    "MetadataValidationIssue",
    "MetadataValidationReport",
    "MetadataValidator",
    "SchemaModel",
    "SourceLocation",
    "SourceSystemModel",
    "TableModel",
]
