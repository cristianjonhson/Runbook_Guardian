# Technical Stack — Runbook Guardian

## Lenguaje principal

- Python 3.11+
- Type hints obligatorios en interfaces públicas.
- Async/await para endpoints de API.

## Framework backend

- FastAPI 0.115+
- Pydantic v2 para validación de datos.
- Uvicorn como servidor ASGI.
- Estructura modular por capas (router → service → repository).

## Framework frontend

- Streamlit 1.41+
- Sin JavaScript custom.
- Comunicación con backend vía HTTP (requests).

## Base de datos / Almacenamiento

- Runbooks: archivos Markdown con YAML frontmatter en `data/runbooks/`.
- Vector store: ChromaDB 0.5+ (persistencia local en `chroma_data/`).
- No se usa base de datos relacional para el MVP.

## Embeddings

- Modelo: `all-MiniLM-L6-v2` (sentence-transformers).
- Ejecución local, sin llamadas a API externa.
- Dimensión: 384.

## Servicios cloud (fase 2, NO requeridos para MVP)

- Amazon S3 con versioning para almacenar runbooks.
- Amazon Bedrock para generación aumentada (post-MVP).

## Infraestructura como código

- CloudFormation (fase 2, después del MVP local).
- Archivos en `infrastructure/`.

## Herramientas de testing

- pytest + pytest-asyncio para tests.
- httpx para test client de FastAPI.
- pytest-cov para cobertura (mínimo 70%).
- Ruff para linting y formato.

## CI/CD

- GitHub Actions.
- Workflows: lint, test, build.
- No deploy automático en MVP.

## Restricciones técnicas

1. El sistema NUNCA ejecuta comandos en el host.
2. El sistema NUNCA modifica infraestructura.
3. El sistema NUNCA aprueba acciones sin intervención humana.
4. El sistema NUNCA responde sin evidencia textual de un runbook.
5. Todas las dependencias deben tener versión pinneada.
6. No se permiten llamadas a APIs externas en el path crítico del MVP.
7. El sistema debe funcionar completamente offline.

## Versiones pinneadas

Consultar `requirements.txt` para versiones exactas. No usar rangos abiertos.
