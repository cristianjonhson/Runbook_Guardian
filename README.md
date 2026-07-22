# Runbook Guardian

Agente seguro para asistir a equipos on-call durante incidentes, utilizando runbooks versionados como única fuente autorizada.

## Problema

Durante un incidente, los operadores pueden utilizar documentación desactualizada, incompleta o sin evidencia, aumentando el riesgo de ejecutar acciones incorrectas o destructivas.

## Solución

Runbook Guardian es un agente RAG con controles deterministas de seguridad que:

- Responde exclusivamente con evidencia extraída de runbooks versionados.
- Rechaza documentación obsoleta o sin metadatos válidos.
- Bloquea la sugerencia de acciones destructivas.
- Funciona sin conexión a servicios cloud (modo offline).

## Usuarios objetivo

- Ingenieros on-call
- DevOps / SRE
- Equipos de plataforma

## Stack técnico

| Componente | Tecnología |
|-----------|-----------|
| Backend | Python 3.11+ / FastAPI |
| Frontend | Streamlit |
| Vector Store | ChromaDB (local) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Runbooks | Markdown con metadatos YAML |
| Cloud (fase 2) | Amazon S3 + Amazon Bedrock |
| IaC (fase 2) | CloudFormation |
| CI/CD | GitHub Actions |

## Estructura del proyecto

```
├── backend/          # API FastAPI
├── frontend/         # Interfaz Streamlit
├── data/
│   └── runbooks/     # Runbooks en Markdown con YAML frontmatter
├── tests/            # Pruebas unitarias e integración
├── scripts/          # Scripts de utilidad
├── infrastructure/   # CloudFormation (fase 2)
├── docs/             # Documentación adicional
└── .kiro/            # Configuración Kiro (steering, specs, hooks, MCP)
```

## Inicio rápido

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar backend
uvicorn backend.main:app --reload --port 8000

# Ejecutar frontend (en otra terminal)
streamlit run frontend/app.py
```

## Variables de entorno

Copiar `.env.example` a `.env` y configurar los valores necesarios.

## Licencia

Este proyecto fue creado para la hackathon. Consultar reglas de propiedad intelectual del evento.
