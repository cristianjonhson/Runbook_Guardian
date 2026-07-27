"""Servicio de consulta — orquestador principal.

Coordina el flujo completo:
  1. Retrieval via FallbackRouter (local, bedrock, o auto).
  2. Validación: filtrar por vigencia (deprecated, stale).
  3. Seguridad: marcar acciones destructivas.
  4. Respuesta: construir QueryResponse con evidencia y metadata de proveedor.
"""

import time
import uuid

import structlog

from backend.api.schemas import (
    EvidenceFragment,
    QueryResponse,
    ResponseMetadata,
)
from backend.services.fallback_router import FallbackRouter
from backend.services.retriever_protocol import RetrievalResult
from backend.services.safety_service import SafetyService
from backend.services.validation_service import ValidationService

logger = structlog.get_logger(__name__)


class QueryService:
    """Orquestador del flujo de consulta al agente."""

    def __init__(
        self,
        fallback_router: FallbackRouter,
        validation_service: ValidationService,
        safety_service: SafetyService,
    ):
        """Inicializa el orquestador con sus dependencias.

        Args:
            fallback_router: Router que gestiona local/bedrock/auto.
            validation_service: Servicio de validación de vigencia.
            safety_service: Servicio de detección de acciones destructivas.
        """
        self._router = fallback_router
        self._validation = validation_service
        self._safety = safety_service

    def process_query(self, query: str, top_k: int = 5) -> QueryResponse:
        """Procesa una consulta completa a través del pipeline.

        Flujo: retrieval (via router) → validación → seguridad → respuesta.

        Args:
            query: Texto de consulta del usuario.
            top_k: Número máximo de candidatos a recuperar.

        Returns:
            QueryResponse con resultados, warnings y metadata de proveedor.
        """
        start_time = time.time()
        correlation_id = str(uuid.uuid4())[:8]

        # 1. Retrieval via FallbackRouter
        retrieval_result: RetrievalResult = self._router.retrieve(
            query=query, top_k=top_k
        )

        candidates = retrieval_result.candidates
        total_candidates = len(candidates)

        logger.info(
            "query_retrieval_complete",
            correlation_id=correlation_id,
            query_length=len(query),
            candidates_found=total_candidates,
            provider_requested=self._router.provider_name,
            provider_used=retrieval_result.provider,
            fallback_applied=retrieval_result.fallback_applied,
            fallback_reason=retrieval_result.fallback_reason,
        )

        # 2. Validación: filtrar por vigencia
        validation_result = self._validation.filter_valid(candidates)

        # 3. Seguridad: verificar acciones destructivas
        safety_results = self._safety.check_candidates(validation_result.valid)

        # 4. Construir respuesta
        results: list[EvidenceFragment] = []
        global_warnings: list[str] = []

        for safety_result in safety_results:
            candidate = safety_result.candidate
            fragment = EvidenceFragment(
                text=candidate.text,
                source_file=candidate.metadata.file_path,
                version=candidate.metadata.version,
                last_reviewed=candidate.metadata.last_reviewed,
                section=candidate.section,
                similarity_score=candidate.similarity_score,
                warnings=safety_result.warnings,
            )
            results.append(fragment)

            if safety_result.has_warnings:
                global_warnings.append(
                    f"El resultado de '{candidate.metadata.file_path}' contiene "
                    f"acciones potencialmente destructivas. Verificar antes de ejecutar."
                )

        # Calcular tiempo de respuesta
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Determinar modo
        mode = "normal"
        if retrieval_result.fallback_applied:
            mode = "fallback"
        elif retrieval_result.error:
            mode = "error"

        # Determinar si algún resultado requiere aprobación humana
        any_approval_required = any(
            sr.approval_required for sr in safety_results
        )

        response = QueryResponse(
            query=query,
            results=results,
            warnings=global_warnings,
            rejected_sources=validation_result.rejected,
            metadata=ResponseMetadata(
                response_time_ms=elapsed_ms,
                total_candidates=total_candidates,
                mode=mode,
                provider_requested=self._router.provider_name,
                provider_used=retrieval_result.provider,
                fallback_applied=retrieval_result.fallback_applied,
                fallback_reason=retrieval_result.fallback_reason,
                human_approval_required=any_approval_required,
            ),
        )

        logger.info(
            "query_processed",
            correlation_id=correlation_id,
            results_count=len(results),
            rejected_count=len(validation_result.rejected),
            warnings_count=len(global_warnings),
            response_time_ms=elapsed_ms,
            provider_used=retrieval_result.provider,
            mode=mode,
        )

        return response
