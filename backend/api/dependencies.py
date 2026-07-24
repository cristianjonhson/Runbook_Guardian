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
    """Crea y cachea el RetrievalService."""
    from backend.services.retrieval_service import RetrievalService

    return RetrievalService(
        vector_repository=get_vector_repository(),
        model_name=settings.embedding_model,
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
    """Crea y cachea el QueryService (orquestador)."""
    from backend.services.query_service import QueryService

    return QueryService(
        retrieval_service=get_retrieval_service(),
        validation_service=get_validation_service(),
        safety_service=get_safety_service(),
    )


@lru_cache(maxsize=1)
def get_fallback_service():
    """Crea y cachea el FallbackService."""
    from backend.services.fallback_service import FallbackService

    fallback_file = Path("data/fallback_responses.json")
    return FallbackService(fallback_file=fallback_file if fallback_file.exists() else None)
