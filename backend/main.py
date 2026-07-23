"""Punto de entrada de la aplicación FastAPI — Runbook Guardian."""

from fastapi import FastAPI

from backend.api.router import router
from backend.config import settings


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
    )

    app.include_router(router)

    return app


app = create_app()
