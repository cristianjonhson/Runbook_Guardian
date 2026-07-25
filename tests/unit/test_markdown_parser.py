"""Tests unitarios para el markdown parser."""

from pathlib import Path

import pytest

from backend.utils.markdown_parser import RunbookParseError, parse_runbook


class TestMarkdownParser:
    """Tests para el parser de Markdown con YAML frontmatter."""

    def test_parse_valid_runbook(self, tmp_runbooks_dir):
        """Parsea correctamente un runbook válido."""
        runbook = parse_runbook(tmp_runbooks_dir / "valid-runbook.md")

        assert runbook.metadata.title == "Valid Runbook"
        assert runbook.metadata.service == "test-service"
        assert runbook.metadata.version == "1.0.0"
        assert runbook.metadata.status == "active"
        assert runbook.metadata.file_path == "valid-runbook.md"
        assert len(runbook.sections) == 3
        assert runbook.sections[0].heading == "Symptoms"
        assert runbook.sections[1].heading == "Diagnosis"
        assert runbook.sections[2].heading == "Resolution"

    def test_parse_runbook_sections_have_content(self, tmp_runbooks_dir):
        """Las secciones contienen el texto correcto."""
        runbook = parse_runbook(tmp_runbooks_dir / "valid-runbook.md")

        assert "Service is down" in runbook.sections[0].content
        assert "Check logs" in runbook.sections[1].content
        assert "Restart service" in runbook.sections[2].content

    def test_parse_runbook_sections_have_line_start(self, tmp_runbooks_dir):
        """Las secciones tienen line_start >= 0."""
        runbook = parse_runbook(tmp_runbooks_dir / "valid-runbook.md")

        for section in runbook.sections:
            assert section.line_start >= 0

    def test_parse_deprecated_runbook(self, tmp_runbooks_dir):
        """Parsea correctamente un runbook deprecated."""
        runbook = parse_runbook(tmp_runbooks_dir / "deprecated-runbook.md")

        assert runbook.metadata.status == "deprecated"
        assert runbook.metadata.service == "old-service"

    def test_parse_missing_frontmatter_raises_error(self, tmp_runbooks_dir):
        """Archivo sin frontmatter lanza RunbookParseError."""
        with pytest.raises(RunbookParseError) as exc_info:
            parse_runbook(tmp_runbooks_dir / "no-frontmatter.md")

        assert "Missing required frontmatter" in str(exc_info.value)

    def test_parse_nonexistent_file_raises_error(self):
        """Archivo inexistente lanza RunbookParseError."""
        with pytest.raises(RunbookParseError) as exc_info:
            parse_runbook(Path("/nonexistent/file.md"))

        assert "does not exist" in str(exc_info.value)

    def test_parse_non_markdown_file_raises_error(self, tmp_path):
        """Archivo no .md lanza RunbookParseError."""
        txt_file = tmp_path / "file.txt"
        txt_file.write_text("content")

        with pytest.raises(RunbookParseError) as exc_info:
            parse_runbook(txt_file)

        assert "not a Markdown file" in str(exc_info.value)

    def test_parse_invalid_status_raises_error(self, tmp_path):
        """Status inválido lanza RunbookParseError."""
        bad_file = tmp_path / "bad-status.md"
        bad_file.write_text(
            """---
title: "Bad"
service: "svc"
version: "1.0.0"
last_reviewed: "2026-01-01"
status: "invalid_status"
---

## Content
Text here.
"""
        )

        with pytest.raises(RunbookParseError) as exc_info:
            parse_runbook(bad_file)

        assert "Invalid status" in str(exc_info.value)

    def test_parse_raw_content_excludes_frontmatter(self, tmp_runbooks_dir):
        """raw_content no incluye el frontmatter YAML."""
        runbook = parse_runbook(tmp_runbooks_dir / "valid-runbook.md")

        assert "---" not in runbook.raw_content.split("\n")[0]
        assert "title:" not in runbook.raw_content
        assert "## Symptoms" in runbook.raw_content
