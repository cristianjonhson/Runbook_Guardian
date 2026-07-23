"""Modelos de dominio para Runbooks."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class RunbookMetadata(BaseModel):
    """Metadata extraída del YAML frontmatter de un runbook.

    Campos obligatorios según REQ-F-001:
    - title, service, version, last_reviewed, status
    """

    title: str = Field(..., description="Título del runbook.")
    service: str = Field(..., description="Servicio al que aplica.")
    version: str = Field(..., description="Versión semántica del runbook.")
    last_reviewed: date = Field(..., description="Fecha de última revisión (YYYY-MM-DD).")
    status: Literal["active", "deprecated", "draft"] = Field(
        ..., description="Estado del runbook."
    )
    file_path: str = Field(default="", description="Ruta relativa del archivo fuente.")


class RunbookSection(BaseModel):
    """Sección individual de un runbook (dividido por headers)."""

    heading: str = Field(..., description="Título del header (## o ###).")
    content: str = Field(..., description="Contenido textual de la sección.")
    line_start: int = Field(..., ge=0, description="Línea de inicio en el archivo fuente.")


class Runbook(BaseModel):
    """Modelo completo de un runbook parseado.

    Incluye metadata, secciones individuales y contenido raw.
    """

    metadata: RunbookMetadata
    sections: list[RunbookSection] = Field(
        default_factory=list, description="Secciones divididas por headers."
    )
    raw_content: str = Field(default="", description="Contenido Markdown completo sin frontmatter.")
