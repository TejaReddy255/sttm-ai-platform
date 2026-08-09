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

from .validation import (
    IRValidationFinding,
    IRValidationResult,
    LogicalMappingIRValidator,
)

__all__ = [
    # IR models
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

    # IR validation
    "IRValidationFinding",
    "IRValidationResult",
    "LogicalMappingIRValidator",
]