# AI-Assisted STTM Platform

An enterprise-oriented AI-assisted Source-to-Target Mapping (STTM) platform that transforms canonical metadata into validated logical mappings and a deterministic 16-column STTM artifact.

The platform sits between an upstream metadata extraction system and a downstream code-generation system.

## Run the mapping workbench

After creating a virtual environment and installing the project dependencies, start the Streamlit UI:

```powershell
.\.venv\Scripts\python.exe -m streamlit run sttm\ui\app.py
```

The workbench supports an approved `LogicalMappingIR` JSON upload, deterministic
STTM compilation, artifact download, and SQL/dbt generation. Use **Load guided demo**
to explore the complete workflow without connecting a source system.

---

## 1. System Context

```text
┌──────────────────────────────┐
│     UPSTREAM SYSTEM          │
│                              │
│     Metadata Extractor       │
│                              │
│ Source Metadata              │
│ Target Metadata              │
└──────────────┬───────────────┘
               │
               │ Canonical Metadata Contract
               ▼
┌───────────────────────────────────────────────────────────┐
│                 STTM AI PLATFORM                          │
│                                                           │
│  Metadata Foundation                                      │
│          ↓                                                │
│  Metadata Graph                                            │
│          ↓                                                │
│  Deterministic Analysis                                   │
│          ↓                                                │
│  AI Semantic Reasoning                                    │
│          ↓                                                │
│  Logical Mapping IR                                       │
│          ↓                                                │
│  Optimization                                             │
│          ↓                                                │
│  Validation                                               │
│          ↓                                                │
│  STTM Compiler                                             │
└─────────────────────────┬─────────────────────────────────┘
                          │
                          │ Validated Logical Mapping IR
                          │ + STTM Artifact
                          ▼
┌──────────────────────────────┐
│      DOWNSTREAM SYSTEM       │
│                              │
│       Code Generator        │
│                              │
│ SQL / PySpark / dbt / etc.  │
└──────────────────────────────┘
