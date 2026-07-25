"""Tests de integración para el endpoint de consulta."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.fixture
def client():
    """Client síncrono para tests."""
    from fastapi.testclient import TestClient

    return TestClient(app)


class TestHealthEndpoint:
    """Tests para GET /api/v1/health."""

    def test_health_returns_200(self, client):
        """Health endpoint retorna 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_returns_expected_fields(self, client):
        """Health endpoint retorna campos esperados."""
        response = client.get("/api/v1/health")
        data = response.json()

        assert "status" in data
        assert "runbooks_indexed" in data
        assert "version" in data
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"

    def test_health_runbooks_indexed_is_integer(self, client):
        """runbooks_indexed es un entero."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert isinstance(data["runbooks_indexed"], int)


class TestRunbooksEndpoint:
    """Tests para GET /api/v1/runbooks."""

    def test_runbooks_returns_200(self, client):
        """Runbooks endpoint retorna 200."""
        response = client.get("/api/v1/runbooks")
        assert response.status_code == 200

    def test_runbooks_returns_list(self, client):
        """Runbooks endpoint retorna una lista."""
        response = client.get("/api/v1/runbooks")
        data = response.json()
        assert isinstance(data, list)

    def test_runbooks_items_have_expected_fields(self, client):
        """Cada runbook tiene los campos esperados."""
        response = client.get("/api/v1/runbooks")
        data = response.json()

        if data:  # Solo si hay runbooks
            item = data[0]
            assert "title" in item
            assert "service" in item
            assert "version" in item
            assert "last_reviewed" in item
            assert "status" in item
            assert "file_path" in item


class TestQueryEndpoint:
    """Tests para POST /api/v1/query."""

    def test_query_valid_returns_200(self, client):
        """Query válida retorna 200."""
        response = client.post(
            "/api/v1/query",
            json={"query": "nginx not responding"},
        )
        assert response.status_code == 200

    def test_query_returns_expected_structure(self, client):
        """Query retorna la estructura esperada."""
        response = client.post(
            "/api/v1/query",
            json={"query": "test query"},
        )
        data = response.json()

        assert "query" in data
        assert "results" in data
        assert "warnings" in data
        assert "rejected_sources" in data
        assert "metadata" in data
        assert data["query"] == "test query"

    def test_query_metadata_has_mode(self, client):
        """Metadata incluye mode (normal o fallback)."""
        response = client.post(
            "/api/v1/query",
            json={"query": "test"},
        )
        data = response.json()
        assert data["metadata"]["mode"] in ("normal", "fallback")

    def test_query_empty_returns_422(self, client):
        """Query vacía retorna 422."""
        response = client.post(
            "/api/v1/query",
            json={"query": ""},
        )
        assert response.status_code == 422

    def test_query_too_long_returns_422(self, client):
        """Query > 500 caracteres retorna 422."""
        response = client.post(
            "/api/v1/query",
            json={"query": "x" * 501},
        )
        assert response.status_code == 422

    def test_query_missing_field_returns_422(self, client):
        """Request sin campo query retorna 422."""
        response = client.post(
            "/api/v1/query",
            json={},
        )
        assert response.status_code == 422

    def test_query_results_have_evidence_fields(self, client):
        """Resultados incluyen campos de evidencia."""
        response = client.post(
            "/api/v1/query",
            json={"query": "nginx service restart"},
        )
        data = response.json()

        # Ya sea normal o fallback, si hay resultados deben tener estos campos
        for result in data.get("results", []):
            assert "text" in result
            assert "source_file" in result
            assert "version" in result
            assert "last_reviewed" in result
            assert "section" in result
            assert "similarity_score" in result
            assert "warnings" in result
