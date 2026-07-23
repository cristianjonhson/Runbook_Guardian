"""Schemas de request y response para la API."""

from datetime import date

from pydantic import BaseModel, Field


# --- Request ---


class QueryRequest(BaseModel):
    """Request para consulta al agente."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Pregunta en lenguaje natural sobre un incidente o síntoma.",
        examples=["El servicio nginx no responde, ¿qué hago?"],
    )


# --- Response: Query ---


class EvidenceFragment(BaseModel):
    """Fragmento de evidencia extraído de un runbook."""

    text: str = Field(..., description="Texto exacto del runbook (sin modificar).")
    source_file: str = Field(..., description="Nombre del archivo fuente.")
    version: str = Field(..., description="Versión del runbook.")
    last_reviewed: date = Field(..., description="Fecha de última revisión.")
    section: str = Field(..., description="Sección del runbook.")
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Score de similitud semántica."
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Advertencias de seguridad (acciones destructivas).",
    )


class RejectedSource(BaseModel):
    """Runbook rechazado por validación de vigencia."""

    source_file: str = Field(..., description="Nombre del archivo rechazado.")
    reason: str = Field(
        ...,
        description="Motivo del rechazo: deprecated, stale, missing_metadata.",
    )


class ResponseMetadata(BaseModel):
    """Metadata de la respuesta."""

    response_time_ms: int = Field(..., description="Tiempo de respuesta en ms.")
    total_candidates: int = Field(..., description="Total de candidatos evaluados.")
    mode: str = Field(
        default="normal",
        description="Modo de operación: normal o fallback.",
    )


class QueryResponse(BaseModel):
    """Response de una consulta al agente."""

    query: str = Field(..., description="Query original del usuario.")
    results: list[EvidenceFragment] = Field(
        default_factory=list, description="Fragmentos con evidencia."
    )
    warnings: list[str] = Field(
        default_factory=list, description="Advertencias globales."
    )
    rejected_sources: list[RejectedSource] = Field(
        default_factory=list, description="Fuentes rechazadas por validación."
    )
    metadata: ResponseMetadata


# --- Response: Health ---


class HealthResponse(BaseModel):
    """Response del endpoint de salud."""

    status: str = Field(default="healthy", description="Estado del sistema.")
    runbooks_indexed: int = Field(..., description="Cantidad de documentos indexados.")
    version: str = Field(..., description="Versión de la aplicación.")


# --- Response: Runbook List ---


class RunbookSummary(BaseModel):
    """Resumen de un runbook indexado."""

    title: str
    service: str
    version: str
    last_reviewed: date
    status: str
    file_path: str
