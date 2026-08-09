"""Controlled vocabularies for the STTM platform.

This module contains enums shared across domain, application,
validation, orchestration, and compiler layers.

Enums provide stable machine-readable values and prevent
inconsistent string literals throughout the application.
"""

from __future__ import annotations

from enum import StrEnum


class MetadataType(StrEnum):
    """Type of metadata object."""

    DATABASE = "database"
    SCHEMA = "schema"
    TABLE = "table"
    VIEW = "view"
    COLUMN = "column"
    CONSTRAINT = "constraint"
    INDEX = "index"


class SourceSystemType(StrEnum):
    """Type of upstream metadata source."""

    DATABASE = "database"
    FILE = "file"
    API = "api"
    UNKNOWN = "unknown"


class DatabasePlatform(StrEnum):
    """Supported database platforms."""

    ORACLE = "oracle"
    POSTGRESQL = "postgresql"
    SQL_SERVER = "sql_server"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    DATABRICKS = "databricks"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    UNKNOWN = "unknown"


class ObjectType(StrEnum):
    """Metadata object classification."""

    TABLE = "table"
    VIEW = "view"
    MATERIALIZED_VIEW = "materialized_view"
    FILE = "file"
    QUERY = "query"


class ColumnRole(StrEnum):
    """Semantic role of a column."""

    IDENTIFIER = "identifier"
    BUSINESS_KEY = "business_key"
    FOREIGN_KEY = "foreign_key"
    MEASURE = "measure"
    ATTRIBUTE = "attribute"
    DATE = "date"
    TIMESTAMP = "timestamp"
    FLAG = "flag"
    STATUS = "status"
    CODE = "code"
    DESCRIPTION = "description"
    AUDIT = "audit"
    UNKNOWN = "unknown"


class ConstraintType(StrEnum):
    """Database constraint type."""

    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    UNIQUE = "unique"
    CHECK = "check"
    NOT_NULL = "not_null"


class RelationshipType(StrEnum):
    """Relationship between metadata objects."""

    PRIMARY_KEY_FOREIGN_KEY = "primary_key_foreign_key"
    INFERRED_FOREIGN_KEY = "inferred_foreign_key"
    UNIQUE_KEY = "unique_key"
    BRIDGE = "bridge"
    SELF_REFERENCE = "self_reference"
    ASSOCIATION = "association"
    UNKNOWN = "unknown"


class RelationshipSource(StrEnum):
    """Origin of a relationship decision."""

    DECLARED = "declared"
    INFERRED = "inferred"
    AI = "ai"
    MANUAL = "manual"


class CardinalityType(StrEnum):
    """Relationship cardinality."""

    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_ONE = "N:1"
    MANY_TO_MANY = "N:N"
    UNKNOWN = "unknown"


class CardinalityEvidence(StrEnum):
    """Evidence supporting cardinality."""

    CONSTRAINT = "constraint"
    UNIQUE_CONSTRAINT = "unique_constraint"
    DATA_PROFILE = "data_profile"
    GRAPH_INFERENCE = "graph_inference"
    AI_INFERENCE = "ai_inference"
    MANUAL = "manual"


class GrainLevel(StrEnum):
    """Relative granularity classification."""

    ROW = "row"
    ENTITY = "entity"
    TRANSACTION = "transaction"
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    AGGREGATED = "aggregated"
    UNKNOWN = "unknown"


class GrainRelationship(StrEnum):
    """Relationship between source and target grain."""

    SAME = "same"
    TARGET_COARSER = "target_coarser"
    TARGET_FINER = "target_finer"
    INCOMPARABLE = "incomparable"
    UNKNOWN = "unknown"


class DependencyType(StrEnum):
    """Type of dependency between data objects."""

    COLUMN = "column"
    FUNCTIONAL = "functional"
    TRANSITIVE = "transitive"
    DERIVATION = "derivation"
    LOAD_ORDER = "load_order"


class MappingType(StrEnum):
    """Type of target-column mapping."""

    DIRECT = "direct"
    TRANSFORMED = "transformed"
    DERIVED = "derived"
    AGGREGATED = "aggregated"
    LOOKUP = "lookup"
    CONDITIONAL = "conditional"
    CONSTANT = "constant"
    DEFAULT = "default"
    UNMAPPED = "unmapped"


class MappingStatus(StrEnum):
    """Lifecycle status of a mapping."""

    DRAFT = "draft"
    ANALYZED = "analyzed"
    AI_REVIEWED = "ai_reviewed"
    VALIDATED = "validated"
    HUMAN_REVIEW = "human_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPILED = "compiled"


class TransformationType(StrEnum):
    """Supported transformation operations."""

    DIRECT = "direct"
    CAST = "cast"
    TRIM = "trim"
    UPPER = "upper"
    LOWER = "lower"
    NULL_HANDLING = "null_handling"
    COALESCE = "coalesce"
    CASE = "case"
    CONCAT = "concat"
    SUBSTRING = "substring"
    DATE_CONVERSION = "date_conversion"
    DATE_TRUNC = "date_trunc"
    ARITHMETIC = "arithmetic"
    LOOKUP = "lookup"
    JOIN = "join"
    FILTER = "filter"
    AGGREGATE = "aggregate"
    WINDOW = "window"
    DEDUPLICATION = "deduplication"
    DERIVATION = "derivation"
    CUSTOM_EXPRESSION = "custom_expression"


class AggregationType(StrEnum):
    """Supported aggregation operations."""

    SUM = "sum"
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    FIRST = "first"
    LAST = "last"


class JoinType(StrEnum):
    """Logical join types."""

    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"
    CROSS = "cross"
    SEMI = "semi"
    ANTI = "anti"


class PathSelectionStatus(StrEnum):
    """Status of a candidate join path."""

    CANDIDATE = "candidate"
    SELECTED = "selected"
    REJECTED = "rejected"
    AMBIGUOUS = "ambiguous"


class AnalysisDecision(StrEnum):
    """Outcome of deterministic analysis."""

    DETERMINED = "determined"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_APPLICABLE = "not_applicable"


class ReasoningMode(StrEnum):
    """Mode used to produce a semantic decision."""

    DETERMINISTIC = "deterministic"
    AI = "ai"
    HYBRID = "hybrid"
    HUMAN = "human"


class AgentType(StrEnum):
    """Semantic reasoning agent types."""

    INTENT = "intent"
    ALIGNMENT = "alignment"
    BUSINESS_RULE = "business_rule"
    TRANSFORMATION = "transformation"
    CONFLICT_RESOLUTION = "conflict_resolution"


class ConfidenceLevel(StrEnum):
    """Human-readable confidence classification."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ConfidenceSource(StrEnum):
    """Origin of a confidence score."""

    DETERMINISTIC = "deterministic"
    AI = "ai"
    HYBRID = "hybrid"
    HUMAN = "human"


class ValidationSeverity(StrEnum):
    """Validation message severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class ValidationStatus(StrEnum):
    """Overall validation status."""

    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"
    BLOCKED = "blocked"
    NOT_RUN = "not_run"


class ValidationCategory(StrEnum):
    """Validation category."""

    METADATA = "metadata"
    RELATIONSHIP = "relationship"
    CARDINALITY = "cardinality"
    GRAIN = "grain"
    DEPENDENCY = "dependency"
    TRANSFORMATION = "transformation"
    BUSINESS_RULE = "business_rule"
    IR = "ir"
    COMPILER = "compiler"
    STTM = "sttm"


class ReviewStatus(StrEnum):
    """Human-review lifecycle status."""

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ProvenanceType(StrEnum):
    """Origin of a domain decision or artifact."""

    UPSTREAM_METADATA = "upstream_metadata"
    DETERMINISTIC_ENGINE = "deterministic_engine"
    KNOWLEDGE_BASE = "knowledge_base"
    AI_AGENT = "ai_agent"
    HUMAN_REVIEW = "human_review"
    SYSTEM_GENERATED = "system_generated"


class KnowledgeType(StrEnum):
    """Enterprise knowledge source type."""

    BUSINESS_GLOSSARY = "business_glossary"
    ONTOLOGY = "ontology"
    TRANSFORMATION_CATALOG = "transformation_catalog"
    HISTORICAL_STTM = "historical_sttm"
    POLICY = "policy"
    EXAMPLE = "example"
    FEEDBACK = "feedback"


class ArtifactType(StrEnum):
    """Supported generated artifact types."""

    STTM_CSV = "sttm_csv"
    STTM_EXCEL = "sttm_excel"
    LOGICAL_MAPPING_IR = "logical_mapping_ir"
    ANSI_SQL = "ansi_sql"
    PYSPARK = "pyspark"
    SPARK_SQL = "spark_sql"
    DBT = "dbt"
    LINEAGE = "lineage"
    DOCUMENTATION = "documentation"


class CompilerStage(StrEnum):
    """Stages of the artifact compiler."""

    LOAD_IR = "load_ir"
    VALIDATE_IR = "validate_ir"
    OPTIMIZE = "optimize"
    EXPAND_MAPPINGS = "expand_mappings"
    RENDER_EXPRESSIONS = "render_expressions"
    GENERATE_ARTIFACT = "generate_artifact"
    VALIDATE_ARTIFACT = "validate_artifact"
    EXPORT = "export"


class WorkflowStatus(StrEnum):
    """LangGraph workflow execution status."""

    CREATED = "created"
    RUNNING = "running"
    WAITING_FOR_REVIEW = "waiting_for_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowNode(StrEnum):
    """Canonical workflow node identifiers."""

    INPUT_VALIDATION = "input_validation"
    CANONICAL_METADATA = "canonical_metadata"
    METADATA_GRAPH = "metadata_graph"
    RELATIONSHIP_ANALYSIS = "relationship_analysis"
    CARDINALITY_ANALYSIS = "cardinality_analysis"
    GRAIN_ANALYSIS = "grain_analysis"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    CANDIDATE_PATHS = "candidate_paths"
    AMBIGUITY_DETECTION = "ambiguity_detection"
    INTENT = "intent"
    ALIGNMENT = "alignment"
    BUSINESS_RULES = "business_rules"
    TRANSFORMATION = "transformation"
    CONFLICT_RESOLUTION = "conflict_resolution"
    IR_BUILDER = "ir_builder"
    OPTIMIZER = "optimizer"
    VALIDATION = "validation"
    CONFIDENCE = "confidence"
    HUMAN_REVIEW = "human_review"
    COMPILER = "compiler"
    ARTIFACT_GENERATION = "artifact_generation"


class ExecutionMode(StrEnum):
    """Workflow execution mode."""

    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    BATCH = "batch"


class CacheType(StrEnum):
    """Cache categories."""

    PROMPT = "prompt"
    EMBEDDING = "embedding"
    LLM_RESPONSE = "llm_response"
    METADATA = "metadata"
    GRAPH = "graph"
    IR = "ir"
    ARTIFACT = "artifact"


class AuditAction(StrEnum):
    """Auditable platform actions."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ANALYZE = "analyze"
    GENERATE = "generate"
    VALIDATE = "validate"
    APPROVE = "approve"
    REJECT = "reject"
    COMPILE = "compile"
    EXECUTE = "execute"