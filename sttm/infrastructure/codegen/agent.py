"""Deterministic planner, generator, and reviewer for downstream SQL code.

An LLM-backed adapter can implement the same application port later.  This
baseline is deliberately deterministic: it provides a safe runnable path and
enforces STTM compliance before model-dependent generation is introduced.
"""

from __future__ import annotations

from collections import defaultdict

from sttm.application.ports.code_generator import CodeGeneratorAgent, GeneratedCode
from sttm.domain.sttm import STTMDocument, STTMValidator


class DeterministicCodeGeneratorAgent(CodeGeneratorAgent):
    """Generate ANSI SQL or dbt models solely from a validated STTM document."""

    _LANGUAGES = {"ansi_sql", "sql", "spark_sql", "dbt"}

    def __init__(self, validator: STTMValidator | None = None) -> None:
        self._validator = validator or STTMValidator()

    def generate(self, sttm: STTMDocument, target_language: str) -> GeneratedCode:
        self._validator.assert_valid(sttm)
        language = target_language.strip().lower()
        if language not in self._LANGUAGES:
            supported = ", ".join(sorted(self._LANGUAGES))
            raise ValueError(
                f"Unsupported target language {target_language!r}. Supported: {supported}.",
            )
        statements = [
            self._render_table(table, rows, language)
            for table, rows in self._group_rows(sttm).items()
        ]
        content = "\n\n".join(statements) + "\n"
        self._review(sttm, content)
        filename = "model.sql" if language == "dbt" else "generated_mapping.sql"
        return GeneratedCode(
            language=language,
            filename=filename,
            content=content,
            explanation=(
                "Generated deterministically from a validated STTM artifact; "
                "no semantic decisions were made during code generation."
            ),
        )

    @staticmethod
    def _group_rows(sttm: STTMDocument) -> dict[str, list[object]]:
        grouped: dict[str, list[object]] = defaultdict(list)
        for row in sttm.rows:
            grouped[row.target_table].append(row)
        return dict(grouped)

    def _render_table(self, target_table: str, rows: list[object], language: str) -> str:
        columns = ",\n    ".join(row.target_column for row in rows)
        expressions = ",\n    ".join(
            f"{row.transformation_rule} AS {row.target_column}"
            for row in rows
        )
        source_tables = sorted(
            {
                table.strip()
                for row in rows
                for table in row.source_table.split(",")
                if table.strip() and table.strip() != "N/A"
            },
        )
        if not source_tables:
            raise ValueError(f"Target {target_table!r} has no usable source table.")
        joins = [row.join_rule for row in rows if row.join_rule]
        from_clause = f"FROM {source_tables[0]}"
        if joins:
            from_clause += "\n" + "\n".join(dict.fromkeys(joins))
        elif len(source_tables) > 1:
            from_clause += "\nCROSS JOIN " + "\nCROSS JOIN ".join(source_tables[1:])
        filters = [row.filter_rule for row in rows if row.filter_rule]
        where_clause = "\nWHERE " + " AND ".join(dict.fromkeys(filters)) if filters else ""
        select_sql = f"SELECT\n    {expressions}\n{from_clause}{where_clause}"
        if language == "dbt":
            return f"{{{{ config(materialized='table') }}}}\n\n{select_sql};"
        return f"INSERT INTO {target_table} (\n    {columns}\n)\n{select_sql};"

    @staticmethod
    def _review(sttm: STTMDocument, content: str) -> None:
        """Hard gate: every STTM target must appear in the generated SQL."""
        missing = [
            f"{row.target_table}.{row.target_column}"
            for row in sttm.rows
            if row.target_column not in content
        ]
        if missing:
            raise ValueError(
                "Generated code failed STTM compliance review: missing "
                + ", ".join(missing),
            )
