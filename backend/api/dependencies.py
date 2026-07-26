"""Inyección de dependencias para la API.

Centraliza la creación de servicios para facilitar testing (mock) y
mantener los routers libres de lógica de inicialización.
"""

from functools import lru_cache
from pathlib import Path

import structlog

from backend.config import Settings, settings

logger = structlog.get_logger(__name__)


def get_settings() -> Settings:
    """Retorna la instancia de configuración."""
    return settings


@lru_cache(maxsize=1)
def get_runbook_repository():
    """Crea y cachea el RunbookRepository."""
    from backend.repositories.runbook_repository import RunbookRepository

    return RunbookRepository(runbooks_path=settings.runbooks_path)


@lru_cache(maxsize=1)
def get_vector_repository():
    """Crea y cachea el VectorRepository."""
    from backend.repositories.vector_repository import VectorRepository

    return VectorRepository(
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
    )


@lru_cache(maxsize=1)
def get_retrieval_service():
    """Crea y cachea el RetrievalService (ChromaDB local)."""
    from backend.services.retrieval_service import RetrievalService

    return RetrievalService(
        vector_repository=get_vector_repository(),
        model_name=settings.embedding_model,
    )


@lru_cache(maxsize=1)
def get_local_retriever():
    """Crea y cachea el LocalRunbookRetriever."""
    from backend.services.local_retriever import LocalRunbookRetriever

    return LocalRunbookRetriever(retrieval_service=get_retrieval_service())


@lru_cache(maxsize=1)
def get_bedrock_retriever():
    """Crea el BedrockRunbookRetriever (None si RAG_PROVIDER=local)."""
    if settings.rag_provider == "local":
        return None

    from backend.services.bedrock_retriever import BedrockRunbookRetriever

    return BedrockRunbookRetriever(
        model_id=settings.bedrock_model_id,
        region=settings.aws_region,
        max_tokens=settings.bedrock_max_tokens,
        temperature=settings.bedrock_temperature,
        timeout_seconds=settings.bedrock_timeout_seconds,
    )


@lru_cache(maxsize=1)
def get_fallback_router():
    """Crea y cachea el FallbackRouter según RAG_PROVIDER."""
    from backend.services.fallback_router import FallbackRouter

    return FallbackRouter(
        local_retriever=get_local_retriever(),
        bedrock_retriever=get_bedrock_retriever(),
        provider=settings.rag_provider,
    )


@lru_cache(maxsize=1)
def get_validation_service():
    """Crea y cachea el ValidationService."""
    from backend.services.validation_service import ValidationService

    return ValidationService(max_age_days=settings.runbook_max_age_days)


@lru_cache(maxsize=1)
def get_safety_service():
    """Crea y cachea el SafetyService."""
    from backend.services.safety_service import SafetyService

    return SafetyService(extra_patterns=settings.destructive_patterns)


@lru_cache(maxsize=1)
def get_query_service():
    """Crea y cachea el QueryService (orquestador con FallbackRouter)."""
    from backend.services.query_service import QueryService

    return QueryService(
        fallback_router=get_fallback_router(),
        validation_service=get_validation_service(),
        safety_service=get_safety_service(),
    )


@lru_cache(maxsize=1)
def get_fallback_service():
    """Crea y cachea el FallbackService (respuestas precomputadas)."""
    from backend.services.fallback_service import FallbackService

    fallback_file = Path("data/fallback_responses.json")
    return FallbackService(fallback_file=fallback_file if fallback_file.exists() else None)
