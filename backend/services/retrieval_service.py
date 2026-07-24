"""Servicio de retrieval — búsqueda semántica en runbooks.

Genera embeddings de la consulta usando sentence-transformers y busca
los fragmentos más similares en el vector store.
"""

from __future__ import annotations

from typing import Any

import structlog

from backend.models.query import RetrievalCandidate
from backend.models.runbook import RunbookMetadata
from backend.repositories.vector_repository import VectorRepository

logger = structlog.get_logger(__name__)


def _load_model(model_name: str):
    """Carga el modelo de sentence-transformers (lazy import).

    Permite que el módulo se importe sin tener torch/sentence-transformers
    disponibles, facilitando testing con mocks.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class RetrievalService:
    """Búsqueda semántica en el vector store de runbooks."""

    def __init__(
        self,
        vector_repository: VectorRepository,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        """Inicializa el servicio con el modelo de embeddings.

        Args:
            vector_repository: Repositorio de vectores (ChromaDB).
            model_name: Nombre del modelo sentence-transformers a usar.
        """
        self._vector_repo = vector_repository
        self._model_name = model_name
        self._model = None  # Lazy loaded
        logger.info("retrieval_service_initialized", model=model_name)

    def _get_model(self):
        """Lazy-loads the embedding model on first use."""
        if self._model is None:
            self._model = _load_model(self._model_name)
        return self._model

    def search(self, query: str, top_k: int = 5) -> list[RetrievalCandidate]:
        """Busca fragmentos de runbooks relevantes para la consulta.

        Args:
            query: Texto de consulta del usuario.
            top_k: Número máximo de resultados.

        Returns:
            Lista de RetrievalCandidate ordenados por similaridad descendente.
        """
        # Generar embedding de la consulta
        model = self._get_model()
        query_embedding = model.encode(query).tolist()

        # Buscar en ChromaDB
        results = self._vector_repo.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        # Convertir resultados a RetrievalCandidate
        candidates = []
        for result in results:
            candidate = self._result_to_candidate(result)
            if candidate:
                candidates.append(candidate)

        logger.info(
            "retrieval_search_complete",
            query_length=len(query),
            results_count=len(candidates),
        )
        return candidates

    def generate_embedding(self, text: str) -> list[float]:
        """Genera un embedding para un texto dado.

        Args:
            text: Texto a vectorizar.

        Returns:
            Vector de embedding como lista de floats.
        """
        model = self._get_model()
        return model.encode(text).tolist()

    def _result_to_candidate(self, result: dict[str, Any]) -> RetrievalCandidate | None:
        """Convierte un resultado del vector store a RetrievalCandidate.

        Args:
            result: Diccionario con id, document, metadata, similarity_score.

        Returns:
            RetrievalCandidate o None si la metadata es inválida.
        """
        metadata = result.get("metadata", {})

        try:
            runbook_metadata = RunbookMetadata(
                title=metadata.get("title", "Unknown"),
                service=metadata.get("service", "unknown"),
                version=metadata.get("version", "0.0.0"),
                last_reviewed=metadata.get("last_reviewed", "2020-01-01"),
                status=metadata.get("status", "active"),
                file_path=metadata.get("file_path", ""),
            )
        except Exception as e:
            logger.warning(
                "invalid_candidate_metadata",
                result_id=result.get("id"),
                error=str(e),
            )
            return None

        return RetrievalCandidate(
            text=result.get("document", ""),
            metadata=runbook_metadata,
            section=metadata.get("section", ""),
            similarity_score=result.get("similarity_score", 0.0),
            line_start=int(metadata.get("line_start", 0)),
        )
