"""Core primitives for the STTM platform.

The core package contains infrastructure-independent primitives
shared across the application, including:

- Enumerations
- Exception hierarchy
- Interfaces and protocols
- Logging abstractions
- Common execution metadata

Core modules must remain lightweight and must not depend on
domain-specific implementations, Vertex AI, Streamlit, or
database infrastructure.
"""

__all__: list[str] = []