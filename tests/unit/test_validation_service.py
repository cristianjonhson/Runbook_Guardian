"""Tests unitarios para ValidationService."""

from datetime import date

from backend.services.validation_service import ValidationService


class TestValidationService:
    """Tests para el servicio de validación de vigencia."""

    def setup_method(self):
        """Setup: crear instancia con 90 días de antigüedad máxima."""
        self.service = ValidationService(max_age_days=90)
        self.reference_date = date(2026, 7, 22)

    def test_validate_active_recent_returns_valid(
        self, sample_candidate_active
    ):
        """Runbook activo y con revisión reciente debe ser válido."""
        result = self.service.filter_valid(
            [sample_candidate_active], reference_date=self.reference_date
        )
        assert len(result.valid) == 1
        assert len(result.rejected) == 0
        assert result.valid[0].metadata.file_path == "service-restart-nginx.md"

    def test_validate_deprecated_returns_rejected(
        self, sample_candidate_deprecated
    ):
        """Runbook deprecated debe ser rechazado."""
        result = self.service.filter_valid(
            [sample_candidate_deprecated], reference_date=self.reference_date
        )
        assert len(result.valid) == 0
        assert len(result.rejected) == 1
        assert result.rejected[0].reason == "deprecated"
        assert result.rejected[0].source_file == "memory-leak-java.md"

    def test_validate_stale_returns_rejected(self, sample_candidate_stale):
        """Runbook sin revisión en >90 días debe ser rechazado."""
        result = self.service.filter_valid(
            [sample_candidate_stale], reference_date=self.reference_date
        )
        assert len(result.valid) == 0
        assert len(result.rejected) == 1
        assert "stale" in result.rejected[0].reason

    def test_validate_mixed_candidates_filters_correctly(
        self,
        sample_candidate_active,
        sample_candidate_deprecated,
        sample_candidate_stale,
    ):
        """Mezcla de candidatos filtra correctamente."""
        candidates = [
            sample_candidate_active,
            sample_candidate_deprecated,
            sample_candidate_stale,
        ]
        result = self.service.filter_valid(
            candidates, reference_date=self.reference_date
        )
        assert len(result.valid) == 1
        assert len(result.rejected) == 2

    def test_validate_empty_list_returns_empty(self):
        """Lista vacía retorna resultado vacío."""
        result = self.service.filter_valid([], reference_date=self.reference_date)
        assert len(result.valid) == 0
        assert len(result.rejected) == 0

    def test_validate_custom_max_age(self, sample_candidate_active):
        """Max age personalizado funciona correctamente."""
        # Con max_age=10, un runbook revisado hace 21 días es stale
        strict_service = ValidationService(max_age_days=10)
        result = strict_service.filter_valid(
            [sample_candidate_active], reference_date=self.reference_date
        )
        assert len(result.valid) == 0
        assert "stale" in result.rejected[0].reason
