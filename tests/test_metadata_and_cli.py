"""Tests for metadata adapters and the runnable command-line application."""

from __future__ import annotations

from sttm.cli import main
from sttm.infrastructure.metadata import InMemoryMetadataExtractor, MetadataExtractorRegistry


def test_metadata_registry_accepts_in_memory_adapter() -> None:
    extractor = InMemoryMetadataExtractor()
    registry = MetadataExtractorRegistry()

    registry.register("memory", extractor)

    assert registry.get("memory") is extractor
    assert registry.has("MEMORY")


def test_cli_check_command() -> None:
    assert main(["check"]) == 0
