"""Core interfaces and protocols for the STTM platform.

This module defines stable contracts between architectural layers.

Implementations may live in infrastructure-specific packages,
but application and domain code should depend on these contracts
rather than concrete implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel


RequestT = TypeVar("RequestT", bound=BaseModel)
ResponseT = TypeVar("ResponseT", bound=BaseModel)
EntityT = TypeVar("EntityT", bound=BaseModel)
IdentifierT = TypeVar("IdentifierT")


class MetadataParser(Protocol):
    """Contract for an upstream metadata parser.

    A parser converts a source-specific metadata representation into
    the platform's canonical metadata model.

    Implementations may support databases, CSV files, Excel files,
    APIs, or other metadata sources.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the parser's unique name.

        Returns:
            Parser name.
        """

    @abstractmethod
    def supports(self, source: Any) -> bool:
        """Determine whether this parser supports the input.

        Args:
            source: Source metadata input.

        Returns:
            True when this parser can process the input.
        """

    @abstractmethod
    def parse(self, source: Any) -> BaseModel:
        """Parse source metadata into a canonical representation.

        Args:
            source: Source metadata input.

        Returns:
            Canonical metadata model.
        """


class AnalysisEngine(Protocol[RequestT, ResponseT]):
    """Generic contract for deterministic analysis engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the engine's unique name.

        Returns:
            Engine name.
        """

    @abstractmethod
    def analyze(self, request: RequestT) -> ResponseT:
        """Perform deterministic analysis.

        Args:
            request: Typed analysis request.

        Returns:
            Typed analysis response.
        """


class SemanticAgent(Protocol[RequestT, ResponseT]):
    """Contract for an AI semantic reasoning agent."""

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Return the semantic agent type.

        Returns:
            Agent type identifier.
        """

    @abstractmethod
    def reason(self, request: RequestT) -> ResponseT:
        """Execute semantic reasoning.

        Args:
            request: Structured agent request.

        Returns:
            Structured semantic decision.
        """


class KnowledgeProvider(Protocol):
    """Contract for enterprise knowledge retrieval."""

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[BaseModel]:
        """Search enterprise knowledge.

        Args:
            query: Semantic or textual search query.
            top_k: Maximum number of results.
            filters: Optional metadata filters.

        Returns:
            Retrieved knowledge records.
        """


class Repository(Protocol[EntityT, IdentifierT]):
    """Generic repository contract.

    The repository pattern isolates persistence infrastructure from
    domain and application services.
    """

    def get(
        self,
        entity_id: IdentifierT,
    ) -> EntityT | None:
        """Retrieve an entity by identifier.

        Args:
            entity_id: Entity identifier.

        Returns:
            Entity if found, otherwise None.
        """

    def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[EntityT]:
        """List entities.

        Args:
            limit: Maximum number of entities.
            offset: Pagination offset.

        Returns:
            Matching entities.
        """

    def add(self, entity: EntityT) -> EntityT:
        """Persist a new entity.

        Args:
            entity: Entity to persist.

        Returns:
            Persisted entity.
        """

    def update(self, entity: EntityT) -> EntityT:
        """Update an existing entity.

        Args:
            entity: Entity to update.

        Returns:
            Updated entity.
        """

    def delete(self, entity_id: IdentifierT) -> None:
        """Delete an entity.

        Args:
            entity_id: Entity identifier.
        """


class Validator(Protocol[RequestT, ResponseT]):
    """Contract for validation components."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return validator name.

        Returns:
            Validator name.
        """

    @abstractmethod
    def validate(self, request: RequestT) -> ResponseT:
        """Validate a request.

        Args:
            request: Object to validate.

        Returns:
            Structured validation result.
        """


class Compiler(Protocol[RequestT, ResponseT]):
    """Contract for deterministic artifact compilers."""

    @property
    @abstractmethod
    def artifact_type(self) -> str:
        """Return the compiler's artifact type.

        Returns:
            Artifact type.
        """

    @abstractmethod
    def compile(self, request: RequestT) -> ResponseT:
        """Compile validated input into an artifact.

        Args:
            request: Compiler input.

        Returns:
            Generated artifact representation.
        """


class Cache(Protocol):
    """Contract for application caches."""

    def get(self, key: str) -> Any | None:
        """Retrieve a cached value.

        Args:
            key: Cache key.

        Returns:
            Cached value or None.
        """

    def set(
        self,
        key: str,
        value: Any,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        """Store a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl_seconds: Optional time-to-live.
        """

    def delete(self, key: str) -> None:
        """Delete a cached value.

        Args:
            key: Cache key.
        """

    def clear(self) -> None:
        """Clear the cache."""


class UnitOfWork(ABC):
    """Abstract transaction boundary.

    Application services use this interface instead of depending
    directly on SQLAlchemy sessions.
    """

    @abstractmethod
    def __enter__(self) -> UnitOfWork:
        """Start a unit of work.

        Returns:
            Active unit of work.
        """

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        """Complete or roll back the unit of work.

        Args:
            exc_type: Exception type, if an exception occurred.
            exc_value: Exception instance, if applicable.
            traceback: Exception traceback.
        """

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""


class EventPublisher(Protocol):
    """Contract for publishing application events."""

    def publish(
        self,
        event_name: str,
        payload: dict[str, Any],
    ) -> None:
        """Publish an application event.

        Args:
            event_name: Event identifier.
            payload: Structured event payload.
        """


class IDGenerator(Protocol):
    """Contract for generating stable identifiers."""

    def generate(self) -> str:
        """Generate a unique identifier.

        Returns:
            Generated identifier.
        """


class Clock(Protocol):
    """Contract for obtaining current time.

    Keeping time behind an interface makes timestamp-dependent
    business logic deterministic in unit tests.
    """

    def now(self) -> Any:
        """Return the current application time.

        Returns:
            Current timestamp.
        """


class PromptRenderer(Protocol):
    """Contract for rendering versioned AI prompts."""

    def render(
        self,
        template_name: str,
        variables: dict[str, Any],
    ) -> str:
        """Render a prompt template.

        Args:
            template_name: Versioned prompt template identifier.
            variables: Template variables.

        Returns:
            Rendered prompt.
        """


class LLMClient(Protocol):
    """Provider-independent contract for LLM execution."""

    def generate(
        self,
        prompt: str,
        *,
        response_model: type[ResponseT],
        temperature: float = 0.0,
        max_output_tokens: int | None = None,
    ) -> ResponseT:
        """Generate a structured LLM response.

        Args:
            prompt: Fully rendered prompt.
            response_model: Pydantic response schema.
            temperature: Model temperature.
            max_output_tokens: Maximum output token count.

        Returns:
            Parsed structured model response.
        """


class GraphService(Protocol):
    """Contract for metadata graph operations."""

    def add_node(
        self,
        node_id: str,
        attributes: dict[str, Any],
    ) -> None:
        """Add a graph node.

        Args:
            node_id: Unique node identifier.
            attributes: Node attributes.
        """

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        attributes: dict[str, Any],
    ) -> None:
        """Add a graph edge.

        Args:
            source_id: Source node identifier.
            target_id: Target node identifier.
            attributes: Edge attributes.
        """

    def shortest_path(
        self,
        source_id: str,
        target_id: str,
    ) -> Sequence[str]:
        """Find the shortest graph path.

        Args:
            source_id: Source node identifier.
            target_id: Target node identifier.

        Returns:
            Ordered node identifiers forming the path.
        """

    def detect_cycles(self) -> Sequence[Sequence[str]]:
        """Detect cycles in the graph.

        Returns:
            Detected cycles.
        """


class ConfidenceCalculator(Protocol):
    """Contract for combining evidence into confidence scores."""

    def calculate(
        self,
        evidence: Sequence[float],
        *,
        weights: Sequence[float] | None = None,
    ) -> float:
        """Calculate an overall confidence score.

        Args:
            evidence: Individual evidence scores between zero and one.
            weights: Optional weights corresponding to evidence.

        Returns:
            Overall confidence score.
        """


class ArtifactStore(Protocol):
    """Contract for storing generated artifacts."""

    def save(
        self,
        artifact_name: str,
        content: bytes,
        *,
        content_type: str,
    ) -> str:
        """Persist an artifact.

        Args:
            artifact_name: Artifact filename.
            content: Artifact bytes.
            content_type: MIME type.

        Returns:
            Artifact location or identifier.
        """

    def delete(self, artifact_id: str) -> None:
        """Delete an artifact.

        Args:
            artifact_id: Artifact identifier.
        """


class MetricsCollector(Protocol):
    """Contract for collecting application metrics."""

    def increment(
        self,
        name: str,
        *,
        value: int = 1,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Increment a metric.

        Args:
            name: Metric name.
            value: Increment amount.
            tags: Optional metric dimensions.
        """

    def observe(
        self,
        name: str,
        value: float,
        *,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Record an observed numeric value.

        Args:
            name: Metric name.
            value: Numeric measurement.
            tags: Optional metric dimensions.
        """


class HealthChecker(Protocol):
    """Contract for infrastructure health checks."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the health-check name.

        Returns:
            Health-check identifier.
        """

    @abstractmethod
    def check(self) -> bool:
        """Check component health.

        Returns:
            True when the component is healthy.
        """


class Service(ABC):
    """Base class for application services.

    This class provides a lightweight lifecycle abstraction for
    services that may require explicit startup and shutdown.

    Concrete services are not required to inherit from this class;
    protocols are preferred when structural typing is sufficient.
    """

    def start(self) -> None:
        """Start the service.

        The default implementation is intentionally a no-op.
        """

    def stop(self) -> None:
        """Stop the service.

        The default implementation is intentionally a no-op.
        """

    def health_check(self) -> bool:
        """Return service health.

        Returns:
            True by default because the base service has no
            external dependencies.
        """
        return True