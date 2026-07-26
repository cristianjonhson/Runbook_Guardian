"""Fallback Router — enrutamiento inteligente entre proveedores RAG.

Soporta tres modos:
- local: usa exclusivamente el retriever local.
- bedrock: usa Bedrock. Si falla, retorna error (sin fallback).
- auto: intenta Bedrock, si falla usa local automáticamente.

Incluye circuit breaker básico para evitar llamadas repetidas a un servicio caído.
"""

from __future__ import annotations

import time
from enum import Enum

import structlog

from backend.models.query import RetrievalCandidate
from backend.services.bedrock_retriever import BedrockRunbookRetriever
from backend.services.local_retriever import LocalRunbookRetriever
from backend.services.retriever_protocol import RetrievalResult

logger = structlog.get_logger(__name__)


class RAGProvider(str, Enum):
    """Proveedores RAG disponibles."""

    LOCAL = "local"
    BEDROCK = "bedrock"
    AUTO = "auto"


class CircuitState(str, Enum):
    """Estados del circuit breaker."""

    CLOSED = "closed"  # Normal, permite llamadas
    OPEN = "open"  # Abierto, bloquea llamadas (fallo reciente)
    HALF_OPEN = "half_open"  # Permite una llamada de prueba


class FallbackRouter:
    """Router que dirige queries al proveedor apropiado con fallback.

    Implementa el RunbookRetriever Protocol y gestiona el routing entre
    proveedores local y Bedrock según la configuración.
    """

    def __init__(
        self,
        local_retriever: LocalRunbookRetriever,
        bedrock_retriever: BedrockRunbookRetriever | None = None,
        provider: str = "local",
        circuit_failure_threshold: int = 3,
        circuit_recovery_seconds: int = 60,
    ):
        """Inicializa el router con los retrievers disponibles.

        Args:
            local_retriever: Retriever local (siempre disponible).
            bedrock_retriever: Retriever Bedrock (puede ser None si no configurado).
            provider: Modo de operación (local, bedrock, auto).
            circuit_failure_threshold: Fallos consecutivos para abrir el circuito.
            circuit_recovery_seconds: Segundos para intentar de nuevo tras abrir.
        """
        self._local = local_retriever
        self._bedrock = bedrock_retriever
        self._provider = RAGProvider(provider)

        # Circuit breaker state
        self._circuit_state = CircuitState.CLOSED
        self._failure_count = 0
        self._failure_threshold = circuit_failure_threshold
        self._recovery_seconds = circuit_recovery_seconds
        self._last_failure_time: float = 0

    @property
    def provider_name(self) -> str:
        return self._provider.value

    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        """Enruta la consulta al proveedor configurado con fallback.

        Args:
            query: Texto de consulta.
            top_k: Máximo de resultados.

        Returns:
            RetrievalResult con información del proveedor usado y fallback.
        """
        if self._provider == RAGProvider.LOCAL:
            return self._retrieve_local(query, top_k)

        if self._provider == RAGProvider.BEDROCK:
            return self._retrieve_bedrock(query, top_k, fallback=False)

        # AUTO mode
        return self._retrieve_auto(query, top_k)

    def _retrieve_local(self, query: str, top_k: int) -> RetrievalResult:
        """Usa exclusivamente el retriever local."""
        result = self._local.retrieve(query, top_k)
        result.provider = "local"
        return result

    def _retrieve_bedrock(
        self, query: str, top_k: int, fallback: bool = False
    ) -> RetrievalResult:
        """Usa Bedrock. Opcionalmente permite fallback."""
        if self._bedrock is None:
            if fallback:
                return self._fallback_to_local(query, top_k, "BEDROCK_NOT_CONFIGURED")
            return RetrievalResult(
                candidates=[],
                provider="bedrock",
                error="Bedrock retriever no configurado.",
            )

        # Verificar circuit breaker
        if self._is_circuit_open():
            if fallback:
                return self._fallback_to_local(query, top_k, "CIRCUIT_BREAKER_OPEN")
            return RetrievalResult(
                candidates=[],
                provider="bedrock",
                error="Circuit breaker abierto. Bedrock temporalmente no disponible.",
            )

        # Primero obtener candidatos locales (contexto para Bedrock)
        local_result = self._local.retrieve(query, top_k)

        if not local_result.candidates:
            # Sin contexto local, Bedrock no puede generar respuesta útil
            return RetrievalResult(
                candidates=[],
                provider="bedrock",
                error="Sin candidatos locales para contexto de Bedrock.",
            )

        # Invocar Bedrock con los candidatos como contexto
        result = self._bedrock.retrieve(
            query=query,
            top_k=top_k,
            local_candidates=local_result.candidates,
        )

        if result.error:
            self._record_failure()
            if fallback:
                return self._fallback_to_local(query, top_k, self._classify_error(result.error))
            return result

        self._record_success()
        return result

    def _retrieve_auto(self, query: str, top_k: int) -> RetrievalResult:
        """Modo auto: intenta Bedrock, fallback a local si falla."""
        return self._retrieve_bedrock(query, top_k, fallback=True)

    def _fallback_to_local(
        self, query: str, top_k: int, reason: str
    ) -> RetrievalResult:
        """Activa fallback al retriever local."""
        logger.info("fallback_activated", reason=reason)
        result = self._local.retrieve(query, top_k)
        result.fallback_applied = True
        result.fallback_reason = reason
        result.provider = "local"
        return result

    def _is_circuit_open(self) -> bool:
        """Verifica si el circuit breaker está abierto."""
        if self._circuit_state == CircuitState.CLOSED:
            return False

        if self._circuit_state == CircuitState.OPEN:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self._recovery_seconds:
                self._circuit_state = CircuitState.HALF_OPEN
                logger.info("circuit_breaker_half_open")
                return False
            return True

        # HALF_OPEN: permite una llamada de prueba
        return False

    def _record_failure(self):
        """Registra un fallo de Bedrock."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self._failure_threshold:
            self._circuit_state = CircuitState.OPEN
            logger.warning(
                "circuit_breaker_opened",
                failure_count=self._failure_count,
                recovery_seconds=self._recovery_seconds,
            )

    def _record_success(self):
        """Registra un éxito de Bedrock."""
        self._failure_count = 0
        if self._circuit_state != CircuitState.CLOSED:
            self._circuit_state = CircuitState.CLOSED
            logger.info("circuit_breaker_closed")

    def _classify_error(self, error: str) -> str:
        """Clasifica el error para el campo fallback_reason."""
        error_lower = error.lower()
        if "timeout" in error_lower or "timed out" in error_lower:
            return "BEDROCK_TIMEOUT"
        if "credential" in error_lower or "auth" in error_lower or "access denied" in error_lower:
            return "BEDROCK_AUTH_ERROR"
        if "throttl" in error_lower or "rate" in error_lower:
            return "BEDROCK_THROTTLED"
        if "not found" in error_lower or "not configured" in error_lower:
            return "BEDROCK_NOT_CONFIGURED"
        if "region" in error_lower:
            return "BEDROCK_REGION_ERROR"
        return "BEDROCK_UNKNOWN_ERROR"
