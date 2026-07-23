"""Router principal de la API v1."""

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_settings
from backend.api.schemas import HealthResponse
from backend.config import Settings

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

    Retorna status, conteo de documentos indexados en ChromaDB, y versión de la app.
    Por ahora retorna 0 runbooks hasta que se implemente el vector store.
    """
    return HealthResponse(
        status="healthy",
        runbooks_indexed=0,  # Se actualizará cuando VectorRepository esté implementado
        version=config.app_version,
    )
