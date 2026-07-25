"""Servicio de consulta — orquestador principal.

Coordina el flujo completo:
  1. Retrieval: buscar fragmentos similares en vector store.
  2. Validación: filtrar por vigencia (deprecated, stale).
  3. Seguridad: marcar acciones destructivas.
  4. Respuesta: construir QueryResponse con evidencia.
"""

import time

import structlog

from backend.api.schemas import (
    EvidenceFragment,
    QueryResponse,
    ResponseMetadata,
)
from backend.services.retrieval_service import RetrievalService
from backend.services.safety_service import SafetyService
from backend.services.validation_service import ValidationService

logger = structlog.get_logger(__name__)


class QueryService:
    """Orquestador del flujo de consulta al agente."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        validation_service: ValidationService,
        safety_service: SafetyService,
    ):
        """Inicializa el orquestador con sus dependencias.

        Args:
            retrieval_service: Servicio de búsqueda semántica.
            validation_service: Servicio de validación de vigencia.
            safety_service: Servicio de detección de acciones destructivas.
        """
        self._retrieval = retrieval_service
        self._validation = validation_service
        self._safety = safety_service

    def process_query(self, query: str, top_k: int = 5) -> QueryResponse:
        """Procesa una consulta completa a través del pipeline.

        Flujo: retrieval → validación → seguridad → respuesta.

        Args:
            query: Texto de consulta del usuario.
            top_k: Número máximo de candidatos a recuperar.

        Returns:
            QueryResponse con resultados, warnings y metadata.
        """
        start_time = time.time()

        # 1. Retrieval: buscar fragmentos similares
        candidates = self._retrieval.search(query=query, top_k=top_k)
        total_candidates = len(candidates)

        logger.info(
            "query_retrieval_complete",
            query_length=len(query),
            candidates_found=total_candidates,
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

            # Agregar warnings globales si hay acciones destructivas
            if safety_result.has_warnings:
                global_warnings.append(
                    f"El resultado de '{candidate.metadata.file_path}' contiene "
                    f"acciones potencialmente destructivas. Verificar antes de ejecutar."
                )

        # Calcular tiempo de respuesta
        elapsed_ms = int((time.time() - start_time) * 1000)

        response = QueryResponse(
            query=query,
            results=results,
            warnings=global_warnings,
            rejected_sources=validation_result.rejected,
            metadata=ResponseMetadata(
                response_time_ms=elapsed_ms,
                total_candidates=total_candidates,
                mode="normal",
            ),
        )

        logger.info(
            "query_processed",
            results_count=len(results),
            rejected_count=len(validation_result.rejected),
            warnings_count=len(global_warnings),
            response_time_ms=elapsed_ms,
        )

        return response
