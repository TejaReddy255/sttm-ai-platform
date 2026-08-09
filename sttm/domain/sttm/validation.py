"""Validation for the stable STTM handoff boundary."""

from __future__ import annotations

from dataclasses import dataclass, field

from sttm.domain.sttm.models import STTM_COLUMNS, STTMDocument


@dataclass(frozen=True)
class STTMValidationFinding:
    """A stable STTM validation finding."""

    code: str
    message: str
    blocking: bool = True


@dataclass
class STTMValidationResult:
    """Outcome of validating an STTM document."""

    findings: list[STTMValidationFinding] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not any(finding.blocking for finding in self.findings)


class STTMValidator:
    """Validate the artifact without knowing a downstream SQL dialect."""

    MIN_CODEGEN_CONFIDENCE = 0.60

    def validate(self, document: STTMDocument) -> STTMValidationResult:
        result = STTMValidationResult()
        if document.column_count != 16 or len(STTM_COLUMNS) != 16:
            result.findings.append(
                STTMValidationFinding(
                    "STTM-SCHEMA-001",
                    "The STTM contract must have exactly 16 columns.",
                ),
            )
        for row in document.rows:
            if row.confidence < self.MIN_CODEGEN_CONFIDENCE:
                result.findings.append(
                    STTMValidationFinding(
                        "STTM-CONFIDENCE-001",
                        f"Target {row.target_table}.{row.target_column} is below "
                        "the code-generation confidence threshold.",
                    ),
                )
        return result

    def assert_valid(self, document: STTMDocument) -> None:
        result = self.validate(document)
        if not result.valid:
            message = "\n".join(
                f"[{item.code}] {item.message}"
                for item in result.findings
                if item.blocking
            )
            raise ValueError(f"STTM validation failed:\n{message}")


__all__ = ["STTMValidationFinding", "STTMValidationResult", "STTMValidator"]
