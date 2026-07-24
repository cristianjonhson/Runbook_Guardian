"""Repositorio para acceso al vector store (ChromaDB).

Gestiona la indexación y búsqueda de documentos embedidos en ChromaDB
usando persistencia local.
"""

from pathlib import Path
from typing import Any

import chromadb
import structlog

logger = structlog.get_logger(__name__)


class VectorRepository:
    """Wrapper sobre ChromaDB para indexar y buscar documentos de runbooks."""

    def __init__(
        self,
        persist_dir: Path,
        collection_name: str = "runbooks",
    ):
        """Inicializa el repositorio con ChromaDB persistent client.

        Args:
            persist_dir: Directorio para persistencia de ChromaDB.
            collection_name: Nombre de la colección de vectores.
        """
        self._persist_dir = Path(persist_dir)
        self._collection_name = collection_name
        self._client = chromadb.PersistentClient(path=str(self._persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "vector_repository_initialized",
            persist_dir=str(self._persist_dir),
            collection=self._collection_name,
        )

    def index(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        """Indexa documentos con sus embeddings y metadata en ChromaDB.

        Args:
            ids: Identificadores únicos por documento.
            documents: Textos originales de los fragmentos.
            metadatas: Metadata asociada a cada documento.
            embeddings: Vectores de embedding pre-calculados.
        """
        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        logger.info("documents_indexed", count=len(ids))

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Busca los documentos más similares al embedding de consulta.

        Args:
            query_embedding: Vector de embedding de la consulta.
            top_k: Número máximo de resultados a retornar.

        Returns:
            Lista de diccionarios con keys: id, document, metadata, distance.
            Ordenados de mayor a menor similitud.
        """
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.count() or top_k),
            include=["documents", "metadatas", "distances"],
        )

        items: list[dict[str, Any]] = []
        if not results["ids"] or not results["ids"][0]:
            return items

        for i, doc_id in enumerate(results["ids"][0]):
            # ChromaDB distance con cosine: distance = 1 - similarity
            distance = results["distances"][0][i] if results["distances"] else 0.0
            similarity = 1.0 - distance

            items.append({
                "id": doc_id,
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "similarity_score": max(0.0, min(1.0, similarity)),
            })

        return items

    def count(self) -> int:
        """Retorna el número de documentos en la colección."""
        return self._collection.count()

    def reset(self) -> None:
        """Elimina todos los documentos de la colección.

        Útil para re-indexación completa.
        """
        self._client.delete_collection(self._collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("vector_collection_reset", collection=self._collection_name)
