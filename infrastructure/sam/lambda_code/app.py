"""AWS Lambda handler ligero para Runbook Guardian.

Este handler NO usa sentence-transformers ni ChromaDB (demasiado grandes para Lambda).
En su lugar, invoca directamente Bedrock con los runbooks almacenados en S3
como contexto pre-cargado.

Para el MVP cloud: las queries van directo a Bedrock sin retrieval semántico local.
El retrieval local (ChromaDB) solo funciona cuando se ejecuta localmente.
"""

import json
import os
import re
from datetime import date

import boto3

# Configuración desde variables de entorno
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
BEDROCK_MAX_TOKENS = int(os.environ.get("BEDROCK_MAX_TOKENS", "500"))
BEDROCK_TEMPERATURE = float(os.environ.get("BEDROCK_TEMPERATURE", "0.1"))
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_RUNBOOKS_BUCKET", "")

# Patrones destructivos (subset para Lambda)
DESTRUCTIVE_PATTERNS = [
    (r"rm\s+-rf", "Eliminación recursiva forzada (rm -rf)"),
    (r"rm\s+-f", "Eliminación forzada (rm -f)"),
    (r"drop\s+database", "Eliminación de base de datos"),
    (r"drop\s+table", "Eliminación de tabla"),
    (r"delete\s+from", "Eliminación de registros"),
    (r"kill\s+-9", "Terminación forzada de proceso"),
    (r"kubectl\s+delete", "Eliminación de recurso Kubernetes"),
    (r"terraform\s+destroy", "Destrucción de infraestructura"),
    (r"aws\s+cloudformation\s+delete-stack", "Eliminación de stack"),
    (r"aws\s+s3\s+rb", "Eliminación de bucket S3"),
    (r"chmod\s+777", "Permisos abiertos a todos"),
    (r"shutdown\s+-h", "Apagado del sistema"),
]

SYSTEM_PROMPT = """Eres un asistente experto para equipos on-call de Runbook Guardian.
REGLAS ESTRICTAS:
1. Responde SOLO basándote en los runbooks proporcionados como contexto.
2. NUNCA inventes información que no esté en los runbooks.
3. Cita siempre la fuente (nombre del archivo y sección).
4. Si un paso implica una acción destructiva, marca con ADVERTENCIA.
5. Si no hay información relevante en los runbooks, di explícitamente que no tienes evidencia.
6. Responde en español.
7. Estructura la respuesta con pasos claros y numerados.
"""

# Cliente Bedrock (reutilizado entre invocaciones)
bedrock_client = None
# Cache de runbooks (se carga una vez por instancia de Lambda)
runbooks_cache = None


def get_bedrock_client():
    global bedrock_client
    if bedrock_client is None:
        bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    return bedrock_client


def load_runbooks_from_s3():
    """Carga runbooks desde S3 (se ejecuta una vez por cold start)."""
    global runbooks_cache
    if runbooks_cache is not None:
        return runbooks_cache

    if not S3_BUCKET:
        runbooks_cache = []
        return runbooks_cache

    s3 = boto3.client("s3", region_name=AWS_REGION)
    runbooks_cache = []

    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="runbooks/")
        for obj in response.get("Contents", []):
            if obj["Key"].endswith(".md"):
                body = s3.get_object(Bucket=S3_BUCKET, Key=obj["Key"])["Body"].read().decode("utf-8")
                runbooks_cache.append({
                    "key": obj["Key"],
                    "filename": obj["Key"].split("/")[-1],
                    "content": body[:3000],  # Limitar tamaño para el prompt
                })
    except Exception as e:
        print(f"Error loading runbooks from S3: {e}")

    return runbooks_cache


def load_runbooks_from_local():
    """Carga runbooks empaquetados en el Lambda zip."""
    global runbooks_cache
    if runbooks_cache is not None:
        return runbooks_cache

    runbooks_path = os.environ.get("RUNBOOKS_PATH", "/var/task/data/runbooks")
    runbooks_cache = []

    try:
        import os as _os
        for filename in sorted(_os.listdir(runbooks_path)):
            if filename.endswith(".md"):
                filepath = _os.path.join(runbooks_path, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()[:3000]
                runbooks_cache.append({
                    "key": f"runbooks/{filename}",
                    "filename": filename,
                    "content": content,
                })
    except Exception as e:
        print(f"Error loading local runbooks: {e}")

    return runbooks_cache


def check_destructive(text):
    """Verifica patrones destructivos en el texto."""
    warnings = []
    for pattern, desc in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(desc)
    return warnings


def invoke_bedrock(query, runbooks):
    """Invoca Bedrock con los runbooks como contexto."""
    # Construir contexto con TODOS los runbooks (16 * ~3KB = ~48KB, dentro del límite de 200K de Haiku)
    context_parts = []
    for i, rb in enumerate(runbooks, 1):
        context_parts.append(f"[Runbook {i}: {rb['filename']}]\n{rb['content']}\n")

    context = "\n---\n".join(context_parts)
    user_prompt = f"Consulta del operador: {query}\n\nRunbooks disponibles:\n\n{context}\n\nResponde basándote exclusivamente en los runbooks."

    client = get_bedrock_client()
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": BEDROCK_MAX_TOKENS,
        "temperature": BEDROCK_TEMPERATURE,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    })

    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def build_response(status_code, body):
    """Construye respuesta HTTP con CORS."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def handler(event, context):
    """Lambda handler principal."""
    http_method = event.get("httpMethod", event.get("requestContext", {}).get("http", {}).get("method", "GET"))
    path = event.get("path", event.get("rawPath", "/"))

    # CORS preflight
    if http_method == "OPTIONS":
        return build_response(200, {})

    # Health check
    if path.endswith("/health") and http_method == "GET":
        runbooks = load_runbooks_from_s3() or load_runbooks_from_local()
        return build_response(200, {
            "status": "healthy",
            "runbooks_indexed": len(runbooks),
            "version": "0.2.0-cloud",
            "provider": "bedrock",
        })

    # Runbooks list
    if path.endswith("/runbooks") and http_method == "GET":
        runbooks = load_runbooks_from_s3() or load_runbooks_from_local()
        return build_response(200, [{"file_path": r["filename"]} for r in runbooks])

    # Query
    if path.endswith("/query") and http_method == "POST":
        try:
            body = json.loads(event.get("body", "{}"))
            query = body.get("query", "").strip()

            if not query or len(query) > 500:
                return build_response(422, {"detail": "Query debe tener 1-500 caracteres"})

            # Cargar runbooks
            runbooks = load_runbooks_from_s3() or load_runbooks_from_local()

            if not runbooks:
                return build_response(200, {
                    "query": query,
                    "results": [],
                    "warnings": ["No hay runbooks disponibles"],
                    "rejected_sources": [],
                    "metadata": {"response_time_ms": 0, "total_candidates": 0, "mode": "error",
                                 "provider_requested": "bedrock", "provider_used": "none",
                                 "fallback_applied": False, "fallback_reason": None,
                                 "human_approval_required": False},
                })

            # Invocar Bedrock
            import time
            start = time.time()
            answer = invoke_bedrock(query, runbooks)
            elapsed_ms = int((time.time() - start) * 1000)

            # Verificar patrones destructivos en la respuesta
            warnings = check_destructive(answer)
            global_warnings = []
            if warnings:
                global_warnings.append(
                    f"La respuesta contiene acciones potencialmente destructivas: {', '.join(warnings)}. Verificar antes de ejecutar."
                )

            return build_response(200, {
                "query": query,
                "results": [{
                    "text": answer,
                    "source_file": "bedrock-synthesis",
                    "version": "cloud",
                    "last_reviewed": str(date.today()),
                    "section": "Respuesta generada",
                    "similarity_score": 0.0,
                    "warnings": warnings,
                }],
                "warnings": global_warnings,
                "rejected_sources": [],
                "metadata": {
                    "response_time_ms": elapsed_ms,
                    "total_candidates": len(runbooks),
                    "mode": "normal",
                    "provider_requested": "bedrock",
                    "provider_used": "bedrock",
                    "fallback_applied": False,
                    "fallback_reason": None,
                    "human_approval_required": len(warnings) > 0,
                },
            })

        except Exception as e:
            print(f"Error processing query: {e}")
            return build_response(200, {
                "query": body.get("query", ""),
                "results": [],
                "warnings": [f"Error del sistema: {str(e)[:100]}"],
                "rejected_sources": [],
                "metadata": {"response_time_ms": 0, "total_candidates": 0, "mode": "error",
                             "provider_requested": "bedrock", "provider_used": "none",
                             "fallback_applied": False, "fallback_reason": str(e)[:50],
                             "human_approval_required": False},
            })

    return build_response(404, {"detail": "Not found"})
