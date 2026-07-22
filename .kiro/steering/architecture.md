# Architecture — Runbook Guardian

## Estilo arquitectónico

Arquitectura por capas (Layered Architecture) con separación clara entre presentación, lógica de negocio y acceso a datos. Complementada con un pipeline determinista de validación y seguridad.

## Componentes principales

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Streamlit)                       │
│   Interfaz de usuario para consultas on-call                │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP (REST)
┌─────────────────────────▼───────────────────────────────────┐
│                    API Layer (FastAPI)                        │
│   Routers, Schemas, Validación de entrada                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                 Service Layer (Orquestación)                  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ QueryService │──│ Retrieval    │──│ Validation       │  │
│  │ (orquesta)   │  │ Service      │  │ Service          │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         │                                                    │
│  ┌──────▼───────────────────────────────────────────────┐   │
│  │ SafetyService (filtro de acciones destructivas)      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                Repository Layer (Datos)                       │
│                                                              │
│  ┌──────────────────┐    ┌──────────────────────────────┐   │
│  │ RunbookRepository│    │ VectorRepository (ChromaDB)  │   │
│  │ (filesystem)     │    │                              │   │
│  └──────────────────┘    └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Data Layer                                 │
│   data/runbooks/*.md    │    chroma_data/ (vector store)    │
└─────────────────────────────────────────────────────────────┘
```

## Responsabilidades por componente

| Componente | Responsabilidad |
|-----------|-----------------|
| `API Layer` | Recibir requests, validar input, serializar respuestas, manejar errores HTTP |
| `QueryService` | Orquestar el flujo completo: retrieval → validación → seguridad → respuesta |
| `RetrievalService` | Generar embeddings de la consulta, buscar similitud en ChromaDB |
| `ValidationService` | Verificar vigencia del runbook (estado, fecha, metadata obligatoria) |
| `SafetyService` | Detectar y bloquear acciones destructivas en fragmentos de respuesta |
| `RunbookRepository` | Leer y parsear runbooks del filesystem |
| `VectorRepository` | CRUD contra ChromaDB (indexar, buscar, eliminar) |
| `Frontend` | Interfaz visual, envío de consultas, presentación de respuestas con evidencia |

## Comunicación entre componentes

- Frontend → Backend: HTTP REST (JSON).
- API → Services: Llamadas directas (inyección de dependencias).
- Services → Repositories: Llamadas directas (inyección de dependencias).
- Repositories → Data: Filesystem (runbooks) y ChromaDB client (vectores).

## Flujo de datos (consulta)

```
1. Usuario envía query (POST /api/v1/query)
2. Router valida schema de entrada
3. QueryService recibe query validada
4. RetrievalService genera embedding y busca en ChromaDB (top-k=5)
5. Para cada resultado:
   a. ValidationService verifica vigencia (estado != deprecated, fecha < 90 días)
   b. SafetyService filtra acciones destructivas
6. QueryService construye respuesta con evidencia
7. Router serializa y retorna respuesta
```

## Dependencias permitidas

```
api/ → services/ → repositories/ → (filesystem, ChromaDB)
api/ → models/
services/ → models/
repositories/ → models/
utils/ ← (cualquier capa puede usar utils)
```

## Dependencias PROHIBIDAS

- `repositories/` NO puede importar de `api/` ni `services/`.
- `services/` NO puede importar de `api/`.
- `frontend/` NO puede importar de `backend/` (se comunican por HTTP).
- Ningún módulo puede importar secretos directamente; usar `config.py`.
- Ningún módulo puede ejecutar subprocesses o comandos del sistema.

## Decisiones técnicas clave

1. **RAG determinista sobre generativo**: No se usa LLM para generar texto. Se retorna el fragmento textual exacto del runbook. Esto garantiza trazabilidad y auditabilidad.
2. **Validación como pipeline**: Cada respuesta pasa por validación de vigencia Y seguridad antes de ser entregada. No hay bypass.
3. **Embeddings locales**: Se sacrifica calidad por independencia de servicios externos y funcionamiento offline.
4. **ChromaDB embebido**: Sin servidor separado. La persistencia es un directorio local.
5. **Sin caché en MVP**: Simplicidad sobre rendimiento. Se puede agregar después.
