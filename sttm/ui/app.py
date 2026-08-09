"""Enterprise Streamlit workbench for the STTM compilation workflow."""

from __future__ import annotations

import json
from io import StringIO
from uuid import uuid4

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from sttm.application.services import STTMGenerationService
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
from sttm.domain.ir import LogicalMappingIRValidator
from sttm.infrastructure.codegen import DeterministicCodeGeneratorAgent
from sttm.infrastructure.compiler import STTMCompiler


st.set_page_config(
    page_title="STTM Workbench",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _apply_theme() -> None:
    """Apply the compact application visual system."""
    st.markdown(
        """
        <style>
          :root { --navy:#0B162A; --ink:#12233F; --muted:#66758E;
                  --line:#E4EAF2; --blue:#2563EB; --mint:#10B981;
                  --surface:#F7F9FC; }
          .stApp { background: var(--surface); color: var(--ink); }
          [data-testid="stSidebar"] { background:#0B162A; }
          [data-testid="stSidebar"] * { color:#EFF6FF; }
          .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
          .hero { background:linear-gradient(118deg,#0B162A 0%,#183B72 100%);
                  padding:2rem 2.2rem; border-radius:18px; color:white; margin-bottom:1.25rem; }
          .hero h1 { margin:0; font-size:2rem; letter-spacing:-0.03em; }
          .hero p { color:#D8E7FF; margin:.55rem 0 0; font-size:1rem; }
          .eyebrow { color:#7DD3FC; font-size:.72rem; font-weight:700;
                     letter-spacing:.12em; text-transform:uppercase; margin-bottom:.45rem; }
          .pipeline { display:flex; gap:.45rem; flex-wrap:wrap; margin-top:1.25rem; }
          .step { border:1px solid rgba(255,255,255,.22); border-radius:999px;
                  padding:.3rem .65rem; font-size:.78rem; color:#E8F1FF; }
          .step.active { background:#DBEAFE; color:#123265; border-color:#DBEAFE; }
          .section-title { font-size:1.05rem; font-weight:700; color:var(--ink); margin-bottom:.25rem; }
          .section-subtitle { color:var(--muted); margin-bottom:1rem; font-size:.9rem; }
          .notice { background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px;
                    padding:.75rem .9rem; color:#065F46; font-size:.87rem; }
          .stButton > button { border-radius:8px; font-weight:600; }
          .stButton > button[kind="primary"] { background:#2563EB; border-color:#2563EB; }
          .stButton > button[kind="primary"]:hover { background:#1D4ED8; border-color:#1D4ED8; }
          .stTabs [data-baseweb="tab-list"] { gap:1.25rem; }
          .stTabs [data-baseweb="tab"] { padding:0.7rem 0.2rem; font-weight:600; }
          .stTabs [aria-selected="true"] p { color:#2563EB; }
          .stTabs [data-testid="stTab"][aria-selected="true"] .react-aria-SelectionIndicator {
            background:#2563EB !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _demo_ir() -> LogicalMappingIR:
    """Create a high-confidence demo with no external data dependency."""
    source_table_id = uuid4()
    target_table_id = uuid4()
    source_columns = [
        IRColumnReference(
            column_id=uuid4(),
            column_name="CUSTOMER_ID",
            table_id=source_table_id,
            table_name="CRM_CUSTOMER",
            data_type="INTEGER",
        ),
        IRColumnReference(
            column_id=uuid4(),
            column_name="EMAIL_ADDRESS",
            table_id=source_table_id,
            table_name="CRM_CUSTOMER",
            data_type="VARCHAR",
        ),
        IRColumnReference(
            column_id=uuid4(),
            column_name="GIVEN_NAME",
            table_id=source_table_id,
            table_name="CRM_CUSTOMER",
            data_type="VARCHAR",
        ),
        IRColumnReference(
            column_id=uuid4(),
            column_name="FAMILY_NAME",
            table_id=source_table_id,
            table_name="CRM_CUSTOMER",
            data_type="VARCHAR",
        ),
    ]
    targets = [
        "CUSTOMER_KEY",
        "EMAIL",
        "FIRST_NAME",
        "LAST_NAME",
    ]
    confidence = IRConfidence(
        overall=0.95,
        semantic=0.95,
        structural=0.98,
        transformation=0.95,
        business_rule=0.90,
        validation=0.98,
        rationale="Demo mapping is supported by matching metadata names and types.",
    )
    mappings = [
        LogicalMapping(
            sequence=index,
            target=IRColumnReference(
                column_id=uuid4(),
                column_name=target,
                table_id=target_table_id,
                table_name="DIM_CUSTOMER",
                data_type=source.data_type,
            ),
            expression=IRNode(node_type=IRNodeType.SOURCE_COLUMN, column=source),
            source_columns=[source],
            confidence=confidence,
            lineage=IRLineage(
                source_columns=[source],
                transformation_summary=f"Direct mapping from {source.column_name}.",
            ),
            status=IRStatus.APPROVED,
        )
        for index, (source, target) in enumerate(zip(source_columns, targets), start=1)
    ]
    return LogicalMappingIR(
        source_system="CRM",
        target_system="ANALYTICS",
        source_model="CRM_DB.PUBLIC",
        target_model="ANALYTICS_DB.MART",
        mappings=mappings,
        confidence=confidence,
        status=IRStatus.APPROVED,
    )


def _init_state() -> None:
    """Initialize view state without generating artifacts implicitly."""
    defaults: dict[str, object] = {
        "ir": None,
        "sttm": None,
        "generated_code": None,
        "validation_findings": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _load_ir(raw_json: str) -> None:
    """Load JSON into the review-first session workflow."""
    ir = LogicalMappingIR.model_validate_json(raw_json)
    validation = LogicalMappingIRValidator().validate(ir)
    st.session_state.ir = ir
    st.session_state.sttm = None
    st.session_state.generated_code = None
    st.session_state.validation_findings = validation.findings


def _ir_summary(ir: LogicalMappingIR) -> pd.DataFrame:
    """Return an analyst-friendly mapping-review table."""
    return pd.DataFrame(
        [
            {
                "#": mapping.sequence,
                "Target": f"{mapping.target.table_name}.{mapping.target.column_name}",
                "Source columns": ", ".join(
                    f"{column.table_name}.{column.column_name}"
                    for column in mapping.source_columns
                ),
                "Confidence": f"{mapping.confidence.overall:.0%}",
                "Status": mapping.status.value,
                "Transformation": mapping.lineage.transformation_summary,
            }
            for mapping in sorted(ir.mappings, key=lambda item: item.sequence)
        ],
    )


def _sttm_csv() -> str:
    """Render the current STTM as a download-ready CSV."""
    sttm = st.session_state.sttm
    if sttm is None:
        return ""
    buffer = StringIO()
    pd.DataFrame([row.as_record() for row in sttm.rows]).to_csv(buffer, index=False)
    return buffer.getvalue()


def _compile_sttm() -> None:
    """Compile only after approved IR has been supplied by the user."""
    ir = st.session_state.ir
    if ir is None:
        st.warning("Load an approved Logical Mapping IR before compiling an STTM artifact.")
        return
    try:
        st.session_state.sttm = STTMGenerationService(compiler=STTMCompiler()).compile(ir).sttm
        st.session_state.generated_code = None
        st.success("STTM compiled and passed its validation gate.")
    except ValueError as error:
        st.error(f"Compilation blocked: {error}")


def _generate_code(language: str) -> None:
    """Generate implementation code strictly from the compiled STTM artifact."""
    sttm = st.session_state.sttm
    if sttm is None:
        st.warning("Compile the STTM artifact before generating implementation code.")
        return
    try:
        result = DeterministicCodeGeneratorAgent().generate(sttm, language)
        st.session_state.generated_code = result
        st.success(f"Generated {result.language} and passed the STTM compliance review.")
    except ValueError as error:
        st.error(f"Code generation blocked: {error}")


def _render_sidebar() -> None:
    """Render workflow status and guardrails."""
    with st.sidebar:
        st.markdown("## ◈ STTM")
        st.caption("Mapping intelligence workbench")
        st.divider()
        st.markdown("#### Workflow status")
        statuses = [
            ("1. Logical Mapping IR", st.session_state.ir is not None),
            ("2. STTM review", st.session_state.sttm is not None),
            ("3. Implementation code", st.session_state.generated_code is not None),
        ]
        for label, completed in statuses:
            icon = "●" if completed else "○"
            st.markdown(f"{icon} {label}")
        st.divider()
        st.markdown("#### Guardrails")
        st.caption("• Code generation only reads a compiled STTM artifact.")
        st.caption("• Low-confidence mappings are blocked upstream.")
        st.caption("• Artifacts remain downloadable and reviewable.")
        st.divider()
        st.caption("STTM AI Platform · v0.1.0")


def main() -> None:
    """Render the interactive STTM workbench."""
    _apply_theme()
    _init_state()
    _render_sidebar()

    st.markdown(
        """
        <section class="hero">
          <div class="eyebrow">Governed data engineering</div>
          <h1>Source-to-target mapping workbench</h1>
          <p>Review approved mapping decisions, compile a controlled STTM artifact,
          and generate implementation-ready code with traceable guardrails.</p>
          <div class="pipeline">
            <span class="step active">Logical Mapping IR</span>
            <span class="step">STTM Artifact</span>
            <span class="step">Implementation Code</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    ir = st.session_state.ir
    metric_columns = st.columns(4)
    metric_columns[0].metric("Mappings", ir.mapping_count if ir else "—")
    metric_columns[1].metric("IR confidence", f"{ir.confidence.overall:.0%}" if ir else "—")
    metric_columns[2].metric("STTM rows", len(st.session_state.sttm.rows) if st.session_state.sttm else "—")
    metric_columns[3].metric("Review state", "Ready" if ir and not ir.review_required else "Awaiting IR")

    tab_ir, tab_sttm, tab_code = st.tabs(
        ["1 · Mapping IR", "2 · STTM Review", "3 · Code Studio"],
    )

    with tab_ir:
        st.markdown('<div class="section-title">Bring an approved mapping decision</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Start from a sample mapping or upload a LogicalMappingIR JSON document.</div>',
            unsafe_allow_html=True,
        )
        action, download = st.columns([1, 2])
        if action.button("Load guided demo", type="primary", use_container_width=True):
            _load_ir(_demo_ir().model_dump_json())
            st.rerun()
        with download:
            demo_json = _demo_ir().model_dump_json(indent=2)
            st.download_button(
                "Download demo IR JSON",
                demo_json,
                file_name="demo_logical_mapping_ir.json",
                mime="application/json",
                use_container_width=True,
            )
        uploaded = st.file_uploader("Upload approved IR", type=["json"], label_visibility="collapsed")
        if uploaded is not None:
            try:
                _load_ir(uploaded.getvalue().decode("utf-8"))
                st.success("Logical Mapping IR loaded. Review it before compiling.")
            except (UnicodeDecodeError, ValidationError, ValueError) as error:
                st.error(f"Unable to load IR: {error}")

        if st.session_state.ir is None:
            st.info("No mapping is loaded. Load the guided demo or upload an approved IR to begin.")
        else:
            ir = st.session_state.ir
            findings = st.session_state.validation_findings
            if findings:
                st.warning(f"IR validation returned {len(findings)} finding(s). Review before compilation.")
                st.dataframe(
                    pd.DataFrame(
                        [{"Code": item.code, "Message": item.message, "Blocking": item.blocking} for item in findings],
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.markdown('<div class="notice">IR validation passed. This is the only input allowed into STTM compilation.</div>', unsafe_allow_html=True)
            st.dataframe(_ir_summary(ir), use_container_width=True, hide_index=True)
            with st.expander("View source IR JSON"):
                st.code(ir.model_dump_json(indent=2), language="json")

    with tab_sttm:
        st.markdown('<div class="section-title">Compile the reviewable mapping artifact</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">The STTM is a fixed 16-column handoff for reviewers and implementation teams.</div>',
            unsafe_allow_html=True,
        )
        st.button("Compile STTM", type="primary", on_click=_compile_sttm)
        if st.session_state.sttm is not None:
            sttm = st.session_state.sttm
            st.dataframe(
                pd.DataFrame([row.as_record() for row in sttm.rows]),
                use_container_width=True,
                hide_index=True,
            )
            json_column, csv_column = st.columns(2)
            json_column.download_button(
                "Download STTM JSON",
                sttm.model_dump_json(indent=2),
                file_name="sttm_document.json",
                mime="application/json",
                use_container_width=True,
            )
            csv_column.download_button(
                "Download STTM CSV",
                _sttm_csv(),
                file_name="sttm_document.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("Compile an approved IR to create the STTM review artifact.")

    with tab_code:
        st.markdown('<div class="section-title">Generate implementation code</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">This downstream step reads the compiled STTM only; it cannot reinterpret metadata or mapping intent.</div>',
            unsafe_allow_html=True,
        )
        language = st.selectbox(
            "Target format",
            options=("ansi_sql", "spark_sql", "dbt"),
            format_func=lambda value: {"ansi_sql": "ANSI SQL", "spark_sql": "Spark SQL", "dbt": "dbt model"}[value],
        )
        st.button("Generate code", type="primary", on_click=_generate_code, args=(language,))
        generated = st.session_state.generated_code
        if generated is not None:
            st.code(generated.content, language="sql")
            st.download_button(
                "Download generated code",
                generated.content,
                file_name=generated.filename,
                mime="text/plain",
                use_container_width=True,
            )
            st.caption(generated.explanation or "Generated from the approved STTM artifact.")
        else:
            st.info("Generate implementation code after compiling the STTM artifact.")


if __name__ == "__main__":
    main()
