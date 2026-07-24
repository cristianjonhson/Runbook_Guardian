"""Servicio de fallback — respuestas precomputadas.

Proporciona respuestas predeterminadas cuando el sistema de retrieval
falla (ChromaDB no disponible, embeddings fallan, etc.).

Las respuestas se cargan desde un archivo JSON de configuración.
"""

import json
from datetime import date
from pathlib import Path

import structlog

from backend.api.schemas import (
    EvidenceFragment,
    QueryResponse,
    RejectedSource,
    ResponseMetadata,
)

logger = structlog.get_logger(__name__)

# Respuestas precomputadas para queries conocidas de demo
DEFAULT_FALLBACK_RESPONSES: dict[str, dict] = {
    "nginx": {
        "text": (
            "1. Verificar estado: systemctl status nginx\n"
            "2. Revisar logs: tail -50 /var/log/nginx/error.log\n"
            "3. Validar configuración: nginx -t\n"
            "4. Reload: systemctl reload nginx\n"
            "5. Si falla reload, restart: systemctl restart nginx"
        ),
        "source_file": "service-restart-nginx.md",
        "version": "1.2.0",
        "section": "Resolution",
    },
    "cpu": {
        "text": (
            "1. Identificar proceso: ps aux --sort=-%cpu | head -10\n"
            "2. Verificar carga: uptime\n"
            "3. Si proceso no crítico, reducir prioridad: renice +10 -p <PID>\n"
            "4. Si no responde: kill -15 <PID>"
        ),
        "source_file": "high-cpu-linux.md",
        "version": "1.3.0",
        "section": "Resolution",
    },
    "disco": {
        "text": (
            "1. Verificar uso: df -h\n"
            "2. Encontrar archivos grandes: du -sh /* | sort -rh | head -10\n"
            "3. Limpiar cache de paquetes: apt-get clean\n"
            "4. Limpiar journals: journalctl --vacuum-time=3d\n"
            "5. Eliminar temporales viejos: find /tmp -type f -atime +7 -delete"
        ),
        "source_file": "disk-full-cleanup.md",
        "version": "2.1.0",
        "section": "Resolution",
    },
    "disk": {
        "text": (
            "1. Check usage: df -h\n"
            "2. Find large files: du -sh /* | sort -rh | head -10\n"
            "3. Clean package cache: apt-get clean\n"
            "4. Clean journals: journalctl --vacuum-time=3d\n"
            "5. Remove old temp files: find /tmp -type f -atime +7 -delete"
        ),
        "source_file": "disk-full-cleanup.md",
        "version": "2.1.0",
        "section": "Resolution",
    },
    "database": {
        "text": (
            "1. Verificar conexiones: SELECT count(*) FROM pg_stat_activity;\n"
            "2. Ver máximo permitido: SHOW max_connections;\n"
            "3. Terminar idle: SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE state = 'idle' AND query_start < now() - interval '10 minutes';\n"
            "4. Reiniciar aplicación si necesario: systemctl restart <app-service>"
        ),
        "source_file": "database-connection-pool.md",
        "version": "1.0.0",
        "section": "Resolution",
    },
}


class FallbackService:
    """Proporciona respuestas precomputadas como fallback."""

    def __init__(self, fallback_file: Path | None = None):
        """Inicializa el servicio de fallback.

        Args:
            fallback_file: Ruta al archivo JSON con respuestas adicionales (opcional).
        """
        self._responses = dict(DEFAULT_FALLBACK_RESPONSES)

        if fallback_file and fallback_file.exists():
            try:
                extra = json.loads(fallback_file.read_text(encoding="utf-8"))
                self._responses.update(extra)
                logger.info("fallback_responses_loaded", file=str(fallback_file))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("fallback_file_load_error", error=str(e))

    def get_fallback_response(self, query: str) -> QueryResponse:
        """Genera una respuesta de fallback basada en keywords en la query.

        Args:
            query: Texto de consulta del usuario.

        Returns:
            QueryResponse con modo fallback y la mejor respuesta precomputada disponible.
        """
        query_lower = query.lower()

        # Buscar la mejor coincidencia por keywords
        best_match = None
        for keyword, response_data in self._responses.items():
            if keyword in query_lower:
                best_match = response_data
                break

        results: list[EvidenceFragment] = []
        if best_match:
            results.append(
                EvidenceFragment(
                    text=best_match["text"],
                    source_file=best_match["source_file"],
                    version=best_match["version"],
                    last_reviewed=date.today(),
                    section=best_match["section"],
                    similarity_score=0.0,  # No hay score real en fallback
                    warnings=[],
                )
            )

        response = QueryResponse(
            query=query,
            results=results,
            warnings=["Sistema en modo fallback. Los resultados pueden ser limitados."],
            rejected_sources=[],
            metadata=ResponseMetadata(
                response_time_ms=0,
                total_candidates=0,
                mode="fallback",
            ),
        )

        logger.info(
            "fallback_response_generated",
            query_length=len(query),
            has_results=len(results) > 0,
        )
        return response
