"""Repositorio para acceso a runbooks en el filesystem.

Lee y parsea archivos Markdown con YAML frontmatter desde el directorio
configurado en settings.runbooks_path.
"""

from pathlib import Path

import structlog

from backend.models.runbook import Runbook, RunbookMetadata
from backend.utils.markdown_parser import RunbookParseError, parse_runbook

logger = structlog.get_logger(__name__)


class RunbookRepository:
    """Acceso a runbooks almacenados como archivos Markdown en el filesystem."""

    def __init__(self, runbooks_path: Path):
        """Inicializa el repositorio.

        Args:
            runbooks_path: Directorio donde se almacenan los runbooks.
        """
        self._path = Path(runbooks_path)

    def list_all(self) -> list[Runbook]:
        """Lee y parsea todos los runbooks del directorio.

        Returns:
            Lista de Runbooks parseados correctamente.
            Los archivos con errores se omiten con un log de warning.
        """
        runbooks: list[Runbook] = []

        if not self._path.exists():
            logger.warning("runbooks_directory_not_found", path=str(self._path))
            return runbooks

        for file_path in sorted(self._path.glob("*.md")):
            try:
                runbook = parse_runbook(file_path)
                runbooks.append(runbook)
            except RunbookParseError as e:
                logger.warning(
                    "runbook_parse_error",
                    file=str(file_path),
                    reason=e.reason,
                )

        logger.info("runbooks_loaded", count=len(runbooks), path=str(self._path))
        return runbooks

    def get_by_service(self, service: str) -> list[Runbook]:
        """Filtra runbooks por nombre de servicio.

        Args:
            service: Nombre del servicio a buscar (case-insensitive).

        Returns:
            Lista de runbooks que coinciden con el servicio.
        """
        all_runbooks = self.list_all()
        return [
            rb for rb in all_runbooks
            if rb.metadata.service.lower() == service.lower()
        ]

    def get_by_file(self, file_name: str) -> Runbook | None:
        """Obtiene un runbook específico por nombre de archivo.

        Args:
            file_name: Nombre del archivo (ej: 'service-restart-nginx.md').

        Returns:
            El Runbook parseado o None si no existe o tiene errores.
        """
        file_path = self._path / file_name
        if not file_path.exists():
            return None

        try:
            return parse_runbook(file_path)
        except RunbookParseError as e:
            logger.warning("runbook_parse_error", file=file_name, reason=e.reason)
            return None

    def list_metadata(self) -> list[RunbookMetadata]:
        """Retorna solo la metadata de todos los runbooks (sin contenido).

        Returns:
            Lista de RunbookMetadata para listar runbooks disponibles.
        """
        return [rb.metadata for rb in self.list_all()]

    def count(self) -> int:
        """Cuenta archivos .md en el directorio de runbooks."""
        if not self._path.exists():
            return 0
        return len(list(self._path.glob("*.md")))
