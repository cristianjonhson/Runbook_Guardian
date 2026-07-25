"""Tests unitarios para SafetyService."""

from backend.services.safety_service import SafetyService


class TestSafetyService:
    """Tests para el servicio de detección de acciones destructivas."""

    def setup_method(self):
        """Setup: crear instancia sin patrones extra."""
        self.service = SafetyService()

    # --- Tests por patrón destructivo ---

    def test_detect_rm_rf(self):
        """Detecta rm -rf."""
        warnings = self.service.check_text("Run rm -rf /tmp/logs/ to clean")
        assert any("rm -rf" in w.lower() for w in warnings)

    def test_detect_rm_f(self):
        """Detecta rm -f."""
        warnings = self.service.check_text("Use rm -f old_file.log")
        assert any("rm -f" in w.lower() for w in warnings)

    def test_detect_drop_database(self):
        """Detecta DROP DATABASE."""
        warnings = self.service.check_text("Execute: drop database production")
        assert any("drop database" in w.lower() for w in warnings)

    def test_detect_drop_table(self):
        """Detecta DROP TABLE."""
        warnings = self.service.check_text("Run drop table users")
        assert any("drop table" in w.lower() for w in warnings)

    def test_detect_delete_from(self):
        """Detecta DELETE FROM."""
        warnings = self.service.check_text("Execute delete from sessions")
        assert any("delete from" in w.lower() for w in warnings)

    def test_detect_truncate(self):
        """Detecta TRUNCATE."""
        warnings = self.service.check_text("TRUNCATE the logs table")
        assert any("truncate" in w.lower() for w in warnings)

    def test_detect_kill_9(self):
        """Detecta kill -9."""
        warnings = self.service.check_text("kill -9 12345")
        assert any("kill -9" in w.lower() for w in warnings)

    def test_detect_terraform_destroy(self):
        """Detecta terraform destroy."""
        warnings = self.service.check_text("Run terraform destroy")
        assert any("terraform destroy" in w.lower() for w in warnings)

    def test_detect_kubectl_delete(self):
        """Detecta kubectl delete."""
        warnings = self.service.check_text("kubectl delete pod my-pod")
        assert any("kubectl delete" in w.lower() for w in warnings)

    def test_detect_chmod_777(self):
        """Detecta chmod 777."""
        warnings = self.service.check_text("chmod 777 /var/www")
        assert any("chmod 777" in w.lower() for w in warnings)

    def test_detect_iptables_flush(self):
        """Detecta iptables -F."""
        warnings = self.service.check_text("iptables -F to clear rules")
        assert any("iptables -f" in w.lower() for w in warnings)

    def test_detect_shutdown(self):
        """Detecta shutdown -h."""
        warnings = self.service.check_text("shutdown -h now")
        assert any("shutdown" in w.lower() for w in warnings)

    def test_detect_halt(self):
        """Detecta halt."""
        warnings = self.service.check_text("Run halt to stop the system")
        assert any("halt" in w.lower() for w in warnings)

    def test_detect_format_c(self):
        """Detecta format C:."""
        warnings = self.service.check_text("format c: drive")
        assert any("format" in w.lower() for w in warnings)

    def test_detect_aws_force(self):
        """Detecta aws --force."""
        warnings = self.service.check_text("aws s3 rm --force bucket")
        assert any("aws" in w.lower() and "force" in w.lower() for w in warnings)

    # --- Tests de texto seguro ---

    def test_safe_text_no_warnings(self):
        """Texto seguro no genera warnings."""
        safe_texts = [
            "systemctl status nginx",
            "Check the logs in /var/log/syslog",
            "curl -I http://localhost/health",
            "SELECT count(*) FROM users;",
            "ps aux | grep java",
            "top -bn1 | head -20",
        ]
        for text in safe_texts:
            warnings = self.service.check_text(text)
            assert warnings == [], f"Unexpected warning for safe text: '{text}'"

    # --- Tests con candidatos ---

    def test_check_candidates_safe(self, sample_candidate_safe):
        """Candidato seguro no tiene warnings."""
        results = self.service.check_candidates([sample_candidate_safe])
        assert len(results) == 1
        assert not results[0].has_warnings
        assert results[0].warnings == []

    def test_check_candidates_destructive(self, sample_candidate_destructive):
        """Candidato destructivo tiene warnings."""
        results = self.service.check_candidates([sample_candidate_destructive])
        assert len(results) == 1
        assert results[0].has_warnings
        assert len(results[0].warnings) >= 2  # rm -rf AND kill -9

    def test_check_candidates_mixed(
        self, sample_candidate_safe, sample_candidate_destructive
    ):
        """Mezcla de candidatos procesa correctamente."""
        results = self.service.check_candidates(
            [sample_candidate_safe, sample_candidate_destructive]
        )
        assert len(results) == 2
        assert not results[0].has_warnings
        assert results[1].has_warnings

    # --- Tests con patrones extra ---

    def test_extra_patterns(self):
        """Patrones extra configurables funcionan."""
        service = SafetyService(extra_patterns=r"dangerous_command")
        warnings = service.check_text("Run dangerous_command here")
        assert len(warnings) > 0
