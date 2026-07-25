"""Fixtures compartidos para tests."""

import tempfile
from datetime import date
from pathlib import Path

import pytest

from backend.models.query import RetrievalCandidate
from backend.models.runbook import RunbookMetadata


@pytest.fixture
def sample_metadata_active() -> RunbookMetadata:
    """Metadata de un runbook activo y reciente."""
    return RunbookMetadata(
        title="Restart Nginx Service",
        service="nginx",
        version="1.2.0",
        last_reviewed=date(2026, 7, 1),
        status="active",
        file_path="service-restart-nginx.md",
    )


@pytest.fixture
def sample_metadata_deprecated() -> RunbookMetadata:
    """Metadata de un runbook deprecated."""
    return RunbookMetadata(
        title="Old Java Process",
        service="java-applications",
        version="1.1.0",
        last_reviewed=date(2025, 1, 15),
        status="deprecated",
        file_path="memory-leak-java.md",
    )


@pytest.fixture
def sample_metadata_stale() -> RunbookMetadata:
    """Metadata de un runbook sin revisión reciente (>90 días)."""
    return RunbookMetadata(
        title="Ancient Process",
        service="legacy",
        version="0.0.1",
        last_reviewed=date(2025, 1, 1),
        status="active",
        file_path="ancient-process.md",
    )


@pytest.fixture
def sample_candidate_active(sample_metadata_active) -> RetrievalCandidate:
    """Candidato de retrieval activo."""
    return RetrievalCandidate(
        text="systemctl reload nginx",
        metadata=sample_metadata_active,
        section="Resolution",
        similarity_score=0.85,
        line_start=15,
    )


@pytest.fixture
def sample_candidate_deprecated(sample_metadata_deprecated) -> RetrievalCandidate:
    """Candidato de retrieval deprecated."""
    return RetrievalCandidate(
        text="Restart java service",
        metadata=sample_metadata_deprecated,
        section="Resolution",
        similarity_score=0.8,
        line_start=20,
    )


@pytest.fixture
def sample_candidate_stale(sample_metadata_stale) -> RetrievalCandidate:
    """Candidato de retrieval stale."""
    return RetrievalCandidate(
        text="Follow old procedure",
        metadata=sample_metadata_stale,
        section="Steps",
        similarity_score=0.7,
        line_start=5,
    )


@pytest.fixture
def sample_candidate_destructive(sample_metadata_active) -> RetrievalCandidate:
    """Candidato con acción destructiva."""
    return RetrievalCandidate(
        text="If all else fails, run rm -rf /tmp/logs/* and kill -9 the process",
        metadata=sample_metadata_active,
        section="Resolution",
        similarity_score=0.75,
        line_start=30,
    )


@pytest.fixture
def sample_candidate_safe(sample_metadata_active) -> RetrievalCandidate:
    """Candidato sin acciones destructivas."""
    return RetrievalCandidate(
        text="Check status with systemctl status nginx and review logs",
        metadata=sample_metadata_active,
        section="Diagnosis",
        similarity_score=0.9,
        line_start=8,
    )


@pytest.fixture
def tmp_runbooks_dir():
    """Directorio temporal con runbooks de prueba."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)

        # Runbook válido
        (path / "valid-runbook.md").write_text(
            """---
title: "Valid Runbook"
service: "test-service"
version: "1.0.0"
last_reviewed: "2026-07-01"
status: "active"
---

## Symptoms

- Service is down

## Diagnosis

1. Check logs

## Resolution

1. Restart service
""",
            encoding="utf-8",
        )

        # Runbook sin frontmatter
        (path / "no-frontmatter.md").write_text(
            "# No Frontmatter\n\nJust content without YAML.",
            encoding="utf-8",
        )

        # Runbook deprecated
        (path / "deprecated-runbook.md").write_text(
            """---
title: "Deprecated Runbook"
service: "old-service"
version: "0.1.0"
last_reviewed: "2024-01-01"
status: "deprecated"
---

## Steps

Old steps here.
""",
            encoding="utf-8",
        )

        yield path
