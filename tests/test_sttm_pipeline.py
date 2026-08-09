"""Executable contract tests for the IR → STTM → code-generation boundary."""

from __future__ import annotations

from uuid import uuid4

from sttm.domain.ir import (
    IRColumnReference,
    IRConfidence,
    IRLineage,
    IRNode,
    IRNodeType,
    IRStatus,
    LogicalMapping,
    LogicalMappingIR,
)
from sttm.domain.sttm import STTMDocument, STTMRow, STTMValidator
from sttm.application.services.sttm_generation import STTMGenerationService
from sttm.infrastructure.codegen import DeterministicCodeGeneratorAgent
from sttm.infrastructure.compiler import STTMCompiler


def _confidence() -> IRConfidence:
    return IRConfidence(
        overall=0.95,
        semantic=0.95,
        structural=0.95,
        transformation=0.95,
        business_rule=0.95,
        validation=0.95,
        rationale="Confirmed by source and target metadata.",
    )


def test_approved_ir_compiles_to_sttm_and_sql() -> None:
    source = IRColumnReference(
        column_id=uuid4(),
        column_name="CUSTOMER_ID",
        table_id=uuid4(),
        table_name="CUSTOMER",
        data_type="INTEGER",
    )
    target = IRColumnReference(
        column_id=uuid4(),
        column_name="CUSTOMER_KEY",
        table_id=uuid4(),
        table_name="DIM_CUSTOMER",
        data_type="INTEGER",
    )
    mapping = LogicalMapping(
        sequence=1,
        target=target,
        expression=IRNode(node_type=IRNodeType.SOURCE_COLUMN, column=source),
        source_columns=[source],
        confidence=_confidence(),
        lineage=IRLineage(
            source_columns=[source],
            transformation_summary="Direct customer key mapping.",
        ),
        status=IRStatus.APPROVED,
    )
    ir = LogicalMappingIR(
        source_system="CRM",
        target_system="WAREHOUSE",
        source_model="CRM_DB.PUBLIC",
        target_model="WH_DB.DW",
        mappings=[mapping],
        confidence=_confidence(),
        status=IRStatus.APPROVED,
    )

    result = STTMGenerationService(
        compiler=STTMCompiler(),
        code_generator=DeterministicCodeGeneratorAgent(),
    ).generate_code(ir, "ansi_sql")
    sttm = result.sttm
    assert result.generated_code is not None
    generated = result.generated_code

    assert sttm.column_count == 16
    assert sttm.rows[0].source_columns == "CUSTOMER.CUSTOMER_ID"
    assert "INSERT INTO DIM_CUSTOMER" in generated.content
    assert "CUSTOMER.CUSTOMER_ID AS CUSTOMER_KEY" in generated.content


def test_low_confidence_sttm_is_a_hard_codegen_gate() -> None:
    document = STTMDocument(
        mapping_ir_id="00000000-0000-0000-0000-000000000001",
        source_system="CRM",
        target_system="WAREHOUSE",
        rows=[
            STTMRow(
                source_system="CRM",
                source_table="CUSTOMER",
                source_columns="CUSTOMER.ID",
                target_system="WAREHOUSE",
                target_table="DIM_CUSTOMER",
                target_column="CUSTOMER_KEY",
                transformation_rule="CUSTOMER.ID",
                confidence=0.59,
            ),
        ],
    )

    result = STTMValidator().validate(document)

    assert not result.valid
    assert result.findings[0].code == "STTM-CONFIDENCE-001"
