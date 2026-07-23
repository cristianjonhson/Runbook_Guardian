"""Parser de archivos Markdown con YAML frontmatter.

Extrae metadata del frontmatter y divide el contenido en secciones
basándose en los headers (## y ###).
"""

import re
from datetime import date
from pathlib import Path

import frontmatter

from backend.models.runbook import Runbook, RunbookMetadata, RunbookSection

# Regex para detectar headers Markdown de nivel 2 o 3
HEADER_PATTERN = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)

# Campos obligatorios en el frontmatter
REQUIRED_FIELDS = {"title", "service", "version", "last_reviewed", "status"}
VALID_STATUSES = {"active", "deprecated", "draft"}


class RunbookParseError(Exception):
    """Error al parsear un runbook."""

    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Error parsing '{file_path}': {reason}")


def parse_runbook(file_path: Path) -> Runbook:
    """Parsea un archivo Markdown con YAML frontmatter y retorna un Runbook.

    Args:
        file_path: Ruta al archivo .md del runbook.

    Returns:
        Runbook con metadata, secciones y contenido raw.

    Raises:
        RunbookParseError: Si el archivo no tiene frontmatter válido o faltan campos.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise RunbookParseError(str(file_path), "File does not exist")

    if not file_path.suffix == ".md":
        raise RunbookParseError(str(file_path), "File is not a Markdown file")

    raw_text = file_path.read_text(encoding="utf-8")

    # Parsear frontmatter YAML
    post = frontmatter.loads(raw_text)
    fm_data = dict(post.metadata)

    # Validar campos obligatorios
    missing = REQUIRED_FIELDS - set(fm_data.keys())
    if missing:
        raise RunbookParseError(
            str(file_path),
            f"Missing required frontmatter fields: {sorted(missing)}",
        )

    # Validar status
    status = fm_data.get("status", "")
    if status not in VALID_STATUSES:
        raise RunbookParseError(
            str(file_path),
            f"Invalid status '{status}'. Must be one of: {sorted(VALID_STATUSES)}",
        )

    # Normalizar last_reviewed a date
    last_reviewed = fm_data["last_reviewed"]
    if isinstance(last_reviewed, str):
        try:
            last_reviewed = date.fromisoformat(last_reviewed)
        except ValueError as e:
            raise RunbookParseError(
                str(file_path),
                f"Invalid last_reviewed date format: {e}",
            ) from e

    # Construir metadata
    metadata = RunbookMetadata(
        title=str(fm_data["title"]),
        service=str(fm_data["service"]),
        version=str(fm_data["version"]),
        last_reviewed=last_reviewed,
        status=status,
        file_path=file_path.name,
    )

    # Extraer contenido sin frontmatter
    content = post.content.strip()

    # Dividir en secciones
    sections = _split_into_sections(content, raw_text)

    return Runbook(
        metadata=metadata,
        sections=sections,
        raw_content=content,
    )


def _split_into_sections(content: str, raw_text: str) -> list[RunbookSection]:
    """Divide el contenido Markdown en secciones basándose en headers.

    Args:
        content: Contenido sin frontmatter.
        raw_text: Texto completo (para calcular líneas absolutas).

    Returns:
        Lista de RunbookSection con heading, content y line_start.
    """
    lines = content.split("\n")
    sections: list[RunbookSection] = []

    # Calcular offset de línea del contenido dentro del archivo raw
    # (las líneas del frontmatter + delimitadores)
    raw_lines = raw_text.split("\n")
    content_offset = 0
    in_frontmatter = False
    for i, line in enumerate(raw_lines):
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
            else:
                content_offset = i + 1
                break

    current_heading = ""
    current_content_lines: list[str] = []
    current_line_start = content_offset

    for i, line in enumerate(lines):
        match = HEADER_PATTERN.match(line)
        if match:
            # Guardar sección anterior si existe
            if current_heading:
                section_content = "\n".join(current_content_lines).strip()
                if section_content:
                    sections.append(
                        RunbookSection(
                            heading=current_heading,
                            content=section_content,
                            line_start=current_line_start,
                        )
                    )

            # Iniciar nueva sección
            current_heading = match.group(2).strip()
            current_content_lines = []
            current_line_start = content_offset + i
        else:
            current_content_lines.append(line)

    # Guardar última sección
    if current_heading:
        section_content = "\n".join(current_content_lines).strip()
        if section_content:
            sections.append(
                RunbookSection(
                    heading=current_heading,
                    content=section_content,
                    line_start=current_line_start,
                )
            )

    return sections
