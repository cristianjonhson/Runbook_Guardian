"""Punto de entrada de la aplicación FastAPI — Runbook Guardian."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from backend.api.router import router
from backend.config import settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Precargar el modelo de embeddings al arrancar para evitar timeout en la primera query."""
    logger.info("startup_preloading_model", model=settings.embedding_model)
    try:
        from backend.api.dependencies import get_retrieval_service

        service = get_retrieval_service()
        service._get_model()
        logger.info("startup_model_loaded")
    except Exception as e:
        logger.warning("startup_model_load_failed", error=str(e))
    yield


def create_app() -> FastAPI:
    """Factory para crear la aplicación FastAPI."""
    app = FastAPI(
        title="Runbook Guardian",
        description=(
            "Agente seguro para asistir a equipos on-call durante incidentes, "
            "utilizando runbooks versionados como única fuente autorizada."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.include_router(router)

    return app


app = create_app()
