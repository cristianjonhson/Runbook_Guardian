"""Servicio de seguridad — detección de acciones destructivas.

Escanea fragmentos de runbook para detectar comandos o acciones
potencialmente destructivas y marcarlos con WARNING.

El servicio NO elimina fragmentos, solo los marca para que el usuario
tome una decisión informada.
"""

import re

import structlog

from backend.models.query import RetrievalCandidate
from backend.utils.destructive_patterns import check_approval_required, check_destructive

logger = structlog.get_logger(__name__)


class SafetyCheckResult:
    """Resultado de la verificación de seguridad de un candidato."""

    def __init__(
        self,
        candidate: RetrievalCandidate,
        warnings: list[str],
        approval_required: bool = False,
        approval_reasons: list[str] | None = None,
    ):
        self.candidate = candidate
        self.warnings = warnings
        self.approval_required = approval_required
        self.approval_reasons = approval_reasons or []

    @property
    def has_warnings(self) -> bool:
        """Indica si el candidato tiene advertencias de seguridad."""
        return len(self.warnings) > 0


class SafetyService:
    """Detecta y marca acciones destructivas en fragmentos de runbook."""

    def __init__(self, extra_patterns: str | None = None):
        """Inicializa el servicio de seguridad.

        Args:
            extra_patterns: Regex adicional para patrones destructivos
                           (desde variable de entorno). Se suma a los
                           patrones por defecto.
        """
        self._extra_pattern: re.Pattern | None = None
        if extra_patterns:
            try:
                self._extra_pattern = re.compile(extra_patterns, re.IGNORECASE)
            except re.error as e:
                logger.warning("invalid_extra_patterns", error=str(e))

    def check_candidates(
        self,
        candidates: list[RetrievalCandidate],
    ) -> list[SafetyCheckResult]:
        """Verifica todos los candidatos por acciones destructivas.

        Args:
            candidates: Lista de candidatos validados por vigencia.

        Returns:
            Lista de SafetyCheckResult con warnings para cada candidato.
        """
        results: list[SafetyCheckResult] = []
        total_warnings = 0

        for candidate in candidates:
            warnings = self._check_single(candidate.text)
            approval_reasons = check_approval_required(candidate.text)
            results.append(SafetyCheckResult(
                candidate=candidate,
                warnings=warnings,
                approval_required=len(approval_reasons) > 0,
                approval_reasons=approval_reasons,
            ))
            total_warnings += len(warnings)

        logger.info(
            "safety_check_complete",
            candidates_count=len(candidates),
            candidates_with_warnings=sum(1 for r in results if r.has_warnings),
            total_warnings=total_warnings,
        )
        return results

    def check_text(self, text: str) -> list[str]:
        """Verifica un texto individual por acciones destructivas.

        Args:
            text: Texto a verificar.

        Returns:
            Lista de descripciones de acciones destructivas encontradas.
        """
        return self._check_single(text)

    def _check_single(self, text: str) -> list[str]:
        """Verifica un texto contra patrones destructivos.

        Args:
            text: Texto a analizar.

        Returns:
            Lista de warnings encontrados.
        """
        # Verificar patrones por defecto
        warnings = check_destructive(text)

        # Verificar patrones extra (desde configuración)
        if self._extra_pattern and self._extra_pattern.search(text):
            warnings.append("Matches additional configured destructive pattern")

        return warnings
