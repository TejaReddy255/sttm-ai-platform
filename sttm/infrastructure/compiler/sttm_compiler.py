"""Deterministic compiler from Logical Mapping IR to the STTM contract."""

from __future__ import annotations

from sttm.domain.ir import (
    IRExpressionOperator,
    IRNode,
    IRNodeType,
    LogicalMapping,
    LogicalMappingIR,
)
from sttm.domain.ir import LogicalMappingIRValidator
from sttm.domain.sttm import STTMDocument, STTMRow, STTMValidator


class STTMCompiler:
    """Compile approved logical mappings into a portable STTM document.

    This class contains no AI calls and is intentionally deterministic so the
    STTM remains an auditable boundary between mapping decisions and code.
    """

    def __init__(
        self,
        ir_validator: LogicalMappingIRValidator | None = None,
        sttm_validator: STTMValidator | None = None,
    ) -> None:
        self._ir_validator = ir_validator or LogicalMappingIRValidator()
        self._sttm_validator = sttm_validator or STTMValidator()

    def compile(self, ir: LogicalMappingIR) -> STTMDocument:
        """Compile an approved, review-free IR into STTM rows."""
        self._ir_validator.assert_valid(ir)
        ir.validate_for_compilation()
        rows = [
            self._compile_mapping(ir, mapping)
            for mapping in sorted(ir.mappings, key=lambda item: item.sequence)
        ]
        document = STTMDocument(
            mapping_ir_id=ir.id,
            source_system=ir.source_system,
            target_system=ir.target_system,
            rows=rows,
        )
        self._sttm_validator.assert_valid(document)
        return document

    def _compile_mapping(self, ir: LogicalMappingIR, mapping: LogicalMapping) -> STTMRow:
        source_columns = ", ".join(
            f"{column.table_name}.{column.column_name}"
            for column in mapping.source_columns
        )
        source_tables = sorted({column.table_name for column in mapping.source_columns})
        source_table = ", ".join(source_tables) or "N/A"
        join_rule = " AND ".join(self._render_join(join) for join in mapping.joins or ir.joins)
        business_rule = "; ".join(str(identifier) for identifier in mapping.business_rule_ids)
        assumptions = mapping.comments or ""
        return STTMRow(
            source_system=ir.source_system,
            source_database=self._database_part(ir.source_model),
            source_schema=self._schema_part(ir.source_model),
            source_table=source_table,
            source_columns=source_columns or "N/A",
            target_system=ir.target_system,
            target_database=self._database_part(ir.target_model),
            target_schema=self._schema_part(ir.target_model),
            target_table=mapping.target.table_name,
            target_column=mapping.target.column_name,
            transformation_rule=self._render_expression(mapping.expression),
            join_rule=join_rule,
            filter_rule="",
            business_rule=business_rule,
            confidence=mapping.confidence.overall,
            assumptions=assumptions,
        )

    @staticmethod
    def _database_part(model: str) -> str:
        return model.split(".")[0] if "." in model else model

    @staticmethod
    def _schema_part(model: str) -> str:
        parts = model.split(".")
        return parts[1] if len(parts) > 1 else ""

    def _render_join(self, join: object) -> str:
        conditions = " AND ".join(
            f"{condition.left_column.table_name}.{condition.left_column.column_name} = "
            f"{condition.right_column.table_name}.{condition.right_column.column_name}"
            for condition in join.conditions
        )
        return f"{join.join_type.upper()} JOIN {join.right_table_name} ON {conditions}"

    def _render_expression(self, node: IRNode) -> str:
        if node.node_type == IRNodeType.SOURCE_COLUMN and node.column is not None:
            return f"{node.column.table_name}.{node.column.column_name}"
        if node.node_type == IRNodeType.CONSTANT:
            return self._render_literal(node.value)
        children = [self._render_expression(child) for child in node.children]
        operator = node.operator
        if operator == IRExpressionOperator.DIRECT:
            return children[0] if children else "DIRECT"
        if operator == IRExpressionOperator.CUSTOM:
            expression = node.parameters.get("expression")
            if not isinstance(expression, str) or not expression:
                raise ValueError(
                    "CUSTOM IR expressions require a non-empty 'expression' parameter.",
                )
            return expression
        binary = {
            IRExpressionOperator.ADD: "+", IRExpressionOperator.SUBTRACT: "-",
            IRExpressionOperator.MULTIPLY: "*", IRExpressionOperator.DIVIDE: "/",
            IRExpressionOperator.EQUALS: "=", IRExpressionOperator.NOT_EQUALS: "!=",
            IRExpressionOperator.AND: "AND", IRExpressionOperator.OR: "OR",
            IRExpressionOperator.GREATER_THAN: ">", IRExpressionOperator.LESS_THAN: "<",
            IRExpressionOperator.GREATER_THAN_OR_EQUAL: ">=",
            IRExpressionOperator.LESS_THAN_OR_EQUAL: "<=",
        }
        if operator in binary and len(children) == 2:
            return f"({children[0]} {binary[operator]} {children[1]})"
        if operator == IRExpressionOperator.CAST and children:
            data_type = node.parameters.get("data_type")
            if not isinstance(data_type, str) or not data_type:
                raise ValueError("CAST IR expressions require a 'data_type' parameter.")
            return f"CAST({children[0]} AS {data_type})"
        name = operator.value if operator is not None else node.node_type.value
        return f"{name}({', '.join(children)})"

    @staticmethod
    def _render_literal(value: str | int | float | bool | None) -> str:
        if isinstance(value, str):
            return "'" + value.replace("'", "''") + "'"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if value is None:
            return "NULL"
        return str(value)
