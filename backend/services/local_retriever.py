"""Retriever local — adapta RetrievalService existente al Protocol.

Wrapper que hace que el RetrievalService existente (ChromaDB + sentence-transformers)
implemente el RunbookRetriever Protocol para uso en el FallbackRouter.
"""

import structlog

from backend.services.retrieval_service import RetrievalService
from backend.services.retriever_protocol import RetrievalResult

logger = structlog.get_logger(__name__)


class LocalRunbookRetriever:
    """Retriever local usando ChromaDB y sentence-transformers.

    Adapta el RetrievalService existente al RunbookRetriever Protocol.
    """

    def __init__(self, retrieval_service: RetrievalService):
        """Inicializa con el servicio de retrieval existente.

        Args:
            retrieval_service: Instancia del RetrievalService (ChromaDB).
        """
        self._service = retrieval_service

    @property
    def provider_name(self) -> str:
        return "local"

    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        """Recupera fragmentos usando búsqueda semántica local.

        Args:
            query: Texto de consulta.
            top_k: Máximo de resultados.

        Returns:
            RetrievalResult con candidatos del vector store local.
        """
        try:
            candidates = self._service.search(query=query, top_k=top_k)
            return RetrievalResult(
                candidates=candidates,
                provider="local",
            )
        except Exception as e:
            logger.error("local_retriever_failed", error=str(e))
            return RetrievalResult(
                candidates=[],
                provider="local",
                error=str(e),
            )
