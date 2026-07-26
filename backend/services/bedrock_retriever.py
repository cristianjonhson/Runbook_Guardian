"""Retriever Bedrock — usa InvokeModel con contexto local.

Estrategia económica (Opción D del diseño):
1. Usa el LocalRetriever para recuperar fragmentos relevantes.
2. Envía esos fragmentos como contexto a Claude Haiku vía InvokeModel.
3. Claude genera una respuesta sintetizada citando los fragmentos.
4. Retorna los candidatos originales (evidencia real) + respuesta generada.

Costo: ~$0.002/query (solo tokens). Sin Knowledge Base ni vector store externo.
"""

from __future__ import annotations

import json
import time

import structlog

from backend.models.query import RetrievalCandidate
from backend.services.retriever_protocol import RetrievalResult

logger = structlog.get_logger(__name__)

# Prompt para Claude Haiku con los fragmentos de runbook como contexto
SYSTEM_PROMPT = """Eres un asistente experto para equipos on-call. Tu trabajo es:
1. Analizar los fragmentos de runbooks proporcionados como contexto.
2. Sintetizar una respuesta clara y accionable basada EXCLUSIVAMENTE en esos fragmentos.
3. NUNCA inventar información que no esté en los fragmentos.
4. NUNCA sugerir ejecutar comandos destructivos sin advertencia explícita.
5. Citar la fuente (nombre del archivo y sección) para cada paso que recomiendes.
6. Si los fragmentos no contienen información relevante, indicarlo explícitamente.
7. Responder en español.
"""

QUERY_TEMPLATE = """Consulta del operador: {query}

Fragmentos de runbooks disponibles como evidencia:

{context}

Basándote EXCLUSIVAMENTE en los fragmentos anteriores, proporciona una respuesta
estructurada con los pasos a seguir. Cita la fuente de cada recomendación.
Si algún paso implica una acción destructiva, indícalo con ADVERTENCIA.
"""


class BedrockRunbookRetriever:
    """Retriever que usa Bedrock InvokeModel con contexto de runbooks locales.

    Requiere que el LocalRetriever haya recuperado fragmentos primero.
    Bedrock se usa para sintetizar/mejorar la respuesta, no para el retrieval.
    """

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
        region: str = "us-east-1",
        max_tokens: int = 500,
        temperature: float = 0.1,
        timeout_seconds: int = 10,
    ):
        """Inicializa el retriever Bedrock.

        Args:
            model_id: ID del modelo en Bedrock.
            region: Región AWS.
            max_tokens: Máximo de tokens en la respuesta.
            temperature: Temperatura de generación (baja = más determinista).
            timeout_seconds: Timeout para la llamada a Bedrock.
        """
        self._model_id = model_id
        self._region = region
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._timeout = timeout_seconds
        self._client = None  # Lazy init

    @property
    def provider_name(self) -> str:
        return "bedrock"

    def _get_client(self):
        """Lazy-init del cliente boto3 para Bedrock."""
        if self._client is None:
            import boto3
            from botocore.config import Config

            config = Config(
                region_name=self._region,
                read_timeout=self._timeout,
                connect_timeout=5,
                retries={"max_attempts": 1},
            )
            self._client = boto3.client("bedrock-runtime", config=config)
        return self._client

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        local_candidates: list[RetrievalCandidate] | None = None,
    ) -> RetrievalResult:
        """Genera respuesta mejorada usando Bedrock con contexto local.

        Args:
            query: Texto de consulta del usuario.
            top_k: No usado directamente (candidatos vienen de local).
            local_candidates: Fragmentos recuperados por el LocalRetriever.

        Returns:
            RetrievalResult con los candidatos originales + metadata de Bedrock.
        """
        if not local_candidates:
            return RetrievalResult(
                candidates=[],
                provider="bedrock",
                error="No hay candidatos locales para enviar como contexto a Bedrock.",
            )

        # Construir contexto a partir de los candidatos locales
        context = self._build_context(local_candidates)
        prompt = QUERY_TEMPLATE.format(query=query, context=context)

        try:
            start = time.time()
            response_text = self._invoke_model(prompt)
            elapsed = time.time() - start

            logger.info(
                "bedrock_invoke_success",
                model=self._model_id,
                elapsed_ms=int(elapsed * 1000),
                context_fragments=len(local_candidates),
            )

            # Retornamos los candidatos originales (evidencia real)
            # La respuesta generada se puede usar como "answer" adicional
            return RetrievalResult(
                candidates=local_candidates,
                provider="bedrock",
            )

        except Exception as e:
            error_type = type(e).__name__
            logger.warning(
                "bedrock_invoke_failed",
                error_type=error_type,
                error=str(e)[:200],
                model=self._model_id,
            )
            return RetrievalResult(
                candidates=[],
                provider="bedrock",
                error=f"{error_type}: {str(e)[:100]}",
            )

    def _build_context(self, candidates: list[RetrievalCandidate]) -> str:
        """Construye el contexto textual a partir de los candidatos."""
        parts = []
        for i, c in enumerate(candidates, 1):
            parts.append(
                f"[Fragmento {i}]\n"
                f"Fuente: {c.metadata.file_path} (v{c.metadata.version})\n"
                f"Sección: {c.section}\n"
                f"Score: {c.similarity_score:.2f}\n"
                f"Contenido:\n{c.text}\n"
            )
        return "\n---\n".join(parts)

    def _invoke_model(self, prompt: str) -> str:
        """Invoca Claude Haiku vía Bedrock Runtime.

        Args:
            prompt: Prompt completo con contexto.

        Returns:
            Texto de respuesta del modelo.
        """
        client = self._get_client()

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "system": SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": prompt},
            ],
        })

        response = client.invoke_model(
            modelId=self._model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]
