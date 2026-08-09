"""Logical Mapping Intermediate Representation domain package.

The IR package contains the technology-neutral contracts exchanged
between the semantic reasoning layer and downstream compilers.

The IR must remain independent of:

* SQL dialects
* PySpark
* dbt
* Streamlit
* Vertex AI
* LangGraph
* Database implementations
"""

from .models import (
    IRColumnReference,
    IRConfidence,
    IRExpressionOperator,
    IRJoin,
    IRJoinCondition,
    IRLineage,
    IRNode,
    IRNodeType,
    IRSourceReference,
    IRStatus,
    IRValidationRule,
    IRValidationSeverity,
    LogicalMapping,
    LogicalMappingIR,
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