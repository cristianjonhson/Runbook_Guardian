"""Router principal de la API v1."""

import structlog
from fastapi import APIRouter, Depends

from backend.api.dependencies import (
    get_fallback_service,
    get_query_service,
    get_settings,
    get_vector_repository,
)
from backend.api.schemas import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
    RunbookSummary,
)
from backend.config import Settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verificar estado del sistema",
    description="Retorna el estado del backend, cantidad de runbooks indexados y versión.",
)
async def health_check(
    config: Settings = Depends(get_settings),
) -> HealthResponse:
    """Endpoint de salud.

    Retorna status, conteo de documentos indexados en ChromaDB, y versión.
    """
    try:
        vector_repo = get_vector_repository()
        indexed_count = vector_repo.count()
    except Exception:
        indexed_count = 0

    return HealthResponse(
        status="healthy",
        runbooks_indexed=indexed_count,
        version=config.app_version,
    )


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Consultar el agente",
    description=(
        "Envía una pregunta en lenguaje natural y recibe fragmentos de runbooks "
        "con evidencia visible, warnings de seguridad y fuentes rechazadas."
    ),
)
async def query_agent(
    request: QueryRequest,
) -> QueryResponse:
    """Endpoint principal de consulta.

    Flujo: retrieval → validación → seguridad → respuesta con evidencia.
    Si el sistema de retrieval falla, activa modo fallback.
    """
    try:
        query_service = get_query_service()
        response = query_service.process_query(query=request.query)
    except Exception as e:
        # Si retrieval falla, usar fallback
        logger.warning(
            "query_service_failed_using_fallback",
            error=str(e),
            query_length=len(request.query),
        )
        fallback_service = get_fallback_service()
        response = fallback_service.get_fallback_response(query=request.query)

    return response


@router.get(
    "/runbooks",
    response_model=list[RunbookSummary],
    summary="Listar runbooks disponibles",
    description="Retorna metadata de todos los runbooks indexados.",
)
async def list_runbooks() -> list[RunbookSummary]:
    """Lista los runbooks disponibles con su metadata."""
    from backend.api.dependencies import get_runbook_repository

    repo = get_runbook_repository()
    metadata_list = repo.list_metadata()

    return [
        RunbookSummary(
            title=m.title,
            service=m.service,
            version=m.version,
            last_reviewed=m.last_reviewed,
            status=m.status,
            file_path=m.file_path,
        )
        for m in metadata_list
    ]
