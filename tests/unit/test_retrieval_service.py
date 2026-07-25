"""Tests unitarios para RetrievalService (con mock de VectorRepository)."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from backend.services.retrieval_service import RetrievalService


class TestRetrievalService:
    """Tests para el servicio de retrieval con mocks."""

    def setup_method(self):
        """Setup: crear instancia con vector repo mockeado."""
        self.mock_vector_repo = MagicMock()
        # No cargar el modelo real; mockeamos _get_model
        self.service = RetrievalService(
            vector_repository=self.mock_vector_repo,
            model_name="test-model",
        )
        # Mock del modelo de embeddings
        self.mock_model = MagicMock()
        self.mock_model.encode.return_value = MagicMock(
            tolist=MagicMock(return_value=[0.1] * 384)
        )
        self.service._model = self.mock_model

    def test_search_returns_candidates(self):
        """Search retorna candidatos del vector store."""
        self.mock_vector_repo.search.return_value = [
            {
                "id": "nginx__resolution",
                "document": "systemctl restart nginx",
                "metadata": {
                    "title": "Restart Nginx",
                    "service": "nginx",
                    "version": "1.2.0",
                    "last_reviewed": "2026-07-01",
                    "status": "active",
                    "file_path": "service-restart-nginx.md",
                    "section": "Resolution",
                    "line_start": 15,
                },
                "similarity_score": 0.85,
            }
        ]

        results = self.service.search("nginx not responding")

        assert len(results) == 1
        assert results[0].text == "systemctl restart nginx"
        assert results[0].metadata.service == "nginx"
        assert results[0].similarity_score == 0.85
        assert results[0].section == "Resolution"

    def test_search_empty_results(self):
        """Search con resultados vacíos retorna lista vacía."""
        self.mock_vector_repo.search.return_value = []

        results = self.service.search("nonexistent query")

        assert results == []

    def test_search_calls_model_encode(self):
        """Search llama al modelo para generar embedding."""
        self.mock_vector_repo.search.return_value = []

        self.service.search("test query")

        self.mock_model.encode.assert_called_once_with("test query")

    def test_search_calls_vector_repo_with_embedding(self):
        """Search pasa el embedding al vector repository."""
        self.mock_vector_repo.search.return_value = []

        self.service.search("test query", top_k=3)

        self.mock_vector_repo.search.assert_called_once_with(
            query_embedding=[0.1] * 384,
            top_k=3,
        )

    def test_search_skips_invalid_metadata(self):
        """Candidatos con metadata inválida se omiten."""
        self.mock_vector_repo.search.return_value = [
            {
                "id": "bad",
                "document": "some text",
                "metadata": {"title": "Bad", "status": "invalid_status"},
                "similarity_score": 0.5,
            }
        ]

        results = self.service.search("query")

        # Debería omitir el resultado con status inválido
        assert len(results) == 0

    def test_generate_embedding_returns_list(self):
        """generate_embedding retorna lista de floats."""
        result = self.service.generate_embedding("test text")

        assert isinstance(result, list)
        assert len(result) == 384
