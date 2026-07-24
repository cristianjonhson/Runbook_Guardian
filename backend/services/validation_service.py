"""Servicio de validación — verificación de vigencia de runbooks.

Filtra candidatos de retrieval según reglas deterministas:
- Rechaza runbooks con status 'deprecated'.
- Rechaza runbooks con last_reviewed mayor a N días.
- Rechaza runbooks sin metadata obligatoria.
"""

from datetime import date, timedelta

import structlog

from backend.api.schemas import RejectedSource
from backend.models.query import RetrievalCandidate

logger = structlog.get_logger(__name__)


class ValidationResult:
    """Resultado de la validación de candidatos."""

    def __init__(
        self,
        valid: list[RetrievalCandidate],
        rejected: list[RejectedSource],
    ):
        self.valid = valid
        self.rejected = rejected


class ValidationService:
    """Valida la vigencia de runbooks antes de presentarlos al usuario."""

    def __init__(self, max_age_days: int = 90):
        """Inicializa el servicio de validación.

        Args:
            max_age_days: Máximo número de días desde last_reviewed para considerar vigente.
        """
        self._max_age_days = max_age_days

    def filter_valid(
        self,
        candidates: list[RetrievalCandidate],
        reference_date: date | None = None,
    ) -> ValidationResult:
        """Filtra candidatos por vigencia y retorna válidos + rechazados.

        Args:
            candidates: Lista de candidatos del retrieval.
            reference_date: Fecha de referencia (default: hoy). Útil para testing.

        Returns:
            ValidationResult con listas de válidos y rechazados.
        """
        if reference_date is None:
            reference_date = date.today()

        valid: list[RetrievalCandidate] = []
        rejected: list[RejectedSource] = []

        for candidate in candidates:
            rejection_reason = self._check_candidate(candidate, reference_date)

            if rejection_reason:
                rejected.append(
                    RejectedSource(
                        source_file=candidate.metadata.file_path,
                        reason=rejection_reason,
                    )
                )
                logger.info(
                    "candidate_rejected",
                    file=candidate.metadata.file_path,
                    reason=rejection_reason,
                )
            else:
                valid.append(candidate)

        logger.info(
            "validation_complete",
            valid_count=len(valid),
            rejected_count=len(rejected),
        )
        return ValidationResult(valid=valid, rejected=rejected)

    def _check_candidate(
        self,
        candidate: RetrievalCandidate,
        reference_date: date,
    ) -> str | None:
        """Verifica si un candidato cumple los criterios de vigencia.

        Returns:
            Motivo de rechazo (string) o None si es válido.
        """
        metadata = candidate.metadata

        # Verificar status deprecated
        if metadata.status == "deprecated":
            return "deprecated"

        # Verificar status draft (no se presenta a usuarios)
        if metadata.status == "draft":
            return "draft"

        # Verificar antigüedad
        cutoff_date = reference_date - timedelta(days=self._max_age_days)
        if metadata.last_reviewed < cutoff_date:
            days_old = (reference_date - metadata.last_reviewed).days
            return f"stale (last reviewed {days_old} days ago, max allowed: {self._max_age_days})"

        # Verificar campos obligatorios
        if not metadata.title or not metadata.service or not metadata.version:
            return "missing_metadata"

        return None
