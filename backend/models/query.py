"""Modelos de dominio para consultas y resultados de retrieval."""

from pydantic import BaseModel, Field

from backend.models.runbook import RunbookMetadata


class RetrievalCandidate(BaseModel):
    """Candidato retornado por el vector store tras búsqueda semántica.

    Representa un fragmento de runbook con su score de similitud
    antes de pasar por validación y filtros de seguridad.
    """

    text: str = Field(..., description="Texto del fragmento del runbook.")
    metadata: RunbookMetadata = Field(..., description="Metadata del runbook fuente.")
    section: str = Field(..., description="Nombre de la sección del runbook.")
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Score de similitud coseno."
    )
    line_start: int = Field(default=0, ge=0, description="Línea de inicio del fragmento.")
