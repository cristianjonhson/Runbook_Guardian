"""Protocol para proveedores de retrieval de runbooks.

Define la interfaz común que deben implementar tanto el retriever local
(ChromaDB + sentence-transformers) como el retriever AWS (Bedrock).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from backend.models.query import RetrievalCandidate


@dataclass
class RetrievalResult:
    """Resultado de una operación de retrieval."""

    candidates: list[RetrievalCandidate] = field(default_factory=list)
    provider: str = "unknown"
    fallback_applied: bool = False
    fallback_reason: str | None = None
    error: str | None = None


class RunbookRetriever(Protocol):
    """Interfaz abstracta para proveedores de retrieval.

    Tanto LocalRunbookRetriever como BedrockRunbookRetriever
    deben implementar este Protocol.
    """

    @property
    def provider_name(self) -> str:
        """Nombre del proveedor (local, bedrock)."""
        ...

    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        """Recupera fragmentos relevantes del corpus de runbooks.

        Args:
            query: Texto de consulta del usuario.
            top_k: Número máximo de resultados.

        Returns:
            RetrievalResult con candidatos y metadata del proveedor.
        """
        ...
