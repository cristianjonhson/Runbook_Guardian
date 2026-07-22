# Project Structure — Runbook Guardian

## Estructura de carpetas

```
Runbook_Guardian/
├── .kiro/
│   ├── steering/           # Reglas y convenciones del proyecto
│   ├── specs/              # Especificaciones (requirements, design, tasks)
│   │   └── core-mvp/
│   ├── hooks/              # Hooks de automatización
│   └── settings/
│       └── mcp.json        # Configuración de servidores MCP
│
├── backend/
│   ├── __init__.py
│   ├── main.py             # Punto de entrada FastAPI, app factory
│   ├── config.py           # Settings con pydantic-settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py       # Router principal
│   │   ├── schemas.py      # Request/Response models (Pydantic)
│   │   └── dependencies.py # Inyección de dependencias
│   ├── services/
│   │   ├── __init__.py
│   │   ├── query_service.py      # Orquestación de consultas
│   │   ├── retrieval_service.py  # Búsqueda en vector store
│   │   ├── validation_service.py # Validación de vigencia
│   │   └── safety_service.py     # Detección de acciones destructivas
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── runbook_repository.py # Acceso a runbooks en filesystem
│   │   └── vector_repository.py  # Acceso a ChromaDB
│   ├── models/
│   │   ├── __init__.py
│   │   ├── runbook.py      # Modelo de dominio de runbook
│   │   └── query.py        # Modelo de consulta y respuesta
│   └── utils/
│       ├── __init__.py
│       ├── markdown_parser.py  # Parser de Markdown + YAML frontmatter
│       └── destructive_patterns.py  # Patrones de acciones peligrosas
│
├── frontend/
│   ├── app.py              # Aplicación Streamlit principal
│   ├── components/         # Componentes reutilizables de UI
│   └── assets/             # Recursos estáticos (logo, CSS)
│
├── data/
│   └── runbooks/           # Runbooks Markdown con YAML frontmatter
│       ├── high-cpu-linux.md
│       ├── disk-full-cleanup.md
│       ├── service-restart-nginx.md
│       ├── database-connection-pool.md
│       └── memory-leak-java.md
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Fixtures compartidos
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_validation_service.py
│   │   ├── test_safety_service.py
│   │   ├── test_markdown_parser.py
│   │   └── test_retrieval_service.py
│   └── integration/
│       ├── __init__.py
│       ├── test_query_endpoint.py
│       └── test_query_flow.py
│
├── scripts/
│   ├── ingest_runbooks.py  # Script para indexar runbooks en ChromaDB
│   ├── validate_runbooks.py # Validar metadatos de todos los runbooks
│   └── demo_queries.py     # Queries de ejemplo para la demo
│
├── infrastructure/         # CloudFormation templates (fase 2)
├── docs/                   # Documentación adicional, diagramas
│
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml
└── docker-compose.yml
```

## Convenciones de nombrado

- Archivos Python: `snake_case.py`
- Clases: `PascalCase`
- Funciones y variables: `snake_case`
- Constantes: `UPPER_SNAKE_CASE`
- Tests: `test_<modulo>_<caso>.py` o `test_<funcionalidad>.py`

## Separación por capas

```
API (routers, schemas) → Services (lógica de negocio) → Repositories (acceso a datos)
```

- Los routers NO contienen lógica de negocio.
- Los services NO acceden directamente a filesystem ni ChromaDB.
- Los repositories NO conocen FastAPI ni HTTP.
- La inyección de dependencias se maneja en `api/dependencies.py`.

## Ubicación de archivos por tipo

| Tipo | Ubicación |
|------|-----------|
| Endpoints API | `backend/api/` |
| Lógica de negocio | `backend/services/` |
| Acceso a datos | `backend/repositories/` |
| Modelos de dominio | `backend/models/` |
| Utilidades compartidas | `backend/utils/` |
| Tests unitarios | `tests/unit/` |
| Tests de integración | `tests/integration/` |
| Runbooks de datos | `data/runbooks/` |
| Scripts de operación | `scripts/` |
| Infraestructura | `infrastructure/` |
| Documentación | `docs/` |
| UI Streamlit | `frontend/` |
