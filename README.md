# Runbook Guardian

Agente seguro para asistir a equipos on-call durante incidentes, utilizando runbooks versionados como unica fuente autorizada.

## Problema

Durante un incidente, los operadores buscan documentacion bajo presion. Frecuentemente encuentran runbooks desactualizados, incompletos o sin contexto de version, aumentando el riesgo de ejecutar acciones incorrectas o destructivas.

## Solucion

Runbook Guardian es un agente RAG con controles deterministicos de seguridad que:

- Responde exclusivamente con evidencia extraida de runbooks versionados.
- Rechaza documentacion obsoleta o sin metadatos validos.
- Detecta y advierte sobre acciones destructivas (26 patrones).
- Requiere aprobacion humana para acciones criticas.
- Funciona en modo hibrido: local (ChromaDB) o cloud (Bedrock).
- Nunca ejecuta comandos ni modifica infraestructura.

## Demo en vivo

| Componente | URL |
|-----------|-----|
| Frontend (Cloud) | https://dtp3hvjjnnwh6.cloudfront.net |
| API Health | https://uilhc0pi4a.execute-api.us-east-1.amazonaws.com/dev/api/v1/health |

## Arquitectura

```
                    +-------------------+
                    |   Frontend        |
                    | (Streamlit local  |
                    |  o HTML/CloudFront)|
                    +--------+----------+
                             |
                    +--------v----------+
                    |   FastAPI / Lambda |
                    +--------+----------+
                             |
              +--------------+--------------+
              |                             |
    +---------v---------+       +-----------v-----------+
    | Local Retriever   |       | Bedrock Retriever     |
    | (ChromaDB +       |       | (Claude Haiku 4.5)    |
    | sentence-transformers)    |                       |
    +---------+---------+       +-----------+-----------+
              |                             |
              +-------------+---------------+
                            |
                  +---------v---------+
                  | Pipeline Seguridad|
                  | - Validation      |
                  | - Safety (26 pat) |
                  | - Approval check  |
                  +---------+---------+
                            |
                  +---------v---------+
                  | Respuesta con     |
                  | evidencia visible |
                  +-------------------+
```

## Stack tecnologico

| Componente | Tecnologia | Proposito |
|-----------|-----------|-----------|
| Backend | Python 3.11 / FastAPI | API REST con pipeline de seguridad |
| Frontend local | Streamlit | Interfaz para desarrollo y demo |
| Frontend cloud | HTML/JS + CloudFront | Interfaz estatica desplegada en AWS |
| Vector Store | ChromaDB | Busqueda semantica local |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Vectorizacion local de runbooks |
| IA Cloud | Amazon Bedrock (Claude Haiku 4.5) | Generacion de respuestas con contexto |
| Almacenamiento | Amazon S3 (versionado) | Runbooks en la nube con trazabilidad |
| Serverless | AWS Lambda + API Gateway | Backend en la nube ($0 free tier) |
| CDN | Amazon CloudFront | Frontend estatico global |
| IaC | CloudFormation + SAM | Infraestructura reproducible |
| CI/CD | GitHub Actions | Validacion automatica en PRs |
| Tests | pytest (54 tests, 85% cobertura) | Unitarios e integracion |
| Lint | ruff | Calidad de codigo |

## Estructura del proyecto

```
Runbook_Guardian/
├── backend/
│   ├── api/                  # Endpoints FastAPI (router, schemas, dependencies)
│   ├── services/             # Logica de negocio
│   │   ├── query_service.py          # Orquestador principal
│   │   ├── retrieval_service.py      # Busqueda semantica (ChromaDB)
│   │   ├── bedrock_retriever.py      # Integracion Bedrock
│   │   ├── fallback_router.py        # Circuit breaker local/bedrock/auto
│   │   ├── validation_service.py     # Vigencia de runbooks
│   │   └── safety_service.py         # Deteccion de acciones destructivas
│   ├── repositories/         # Acceso a datos (filesystem, ChromaDB)
│   ├── models/               # Modelos de dominio (Pydantic)
│   ├── utils/                # Parser markdown, patrones destructivos
│   ├── config.py             # Configuracion centralizada
│   ├── main.py               # App factory FastAPI
│   └── lambda_handler.py     # Handler para AWS Lambda
├── frontend/
│   ├── app.py                # Streamlit (ejecucion local)
│   └── static/               # HTML/JS para CloudFront (cloud)
├── data/
│   └── runbooks/             # 16 runbooks en espanol con YAML frontmatter
├── tests/
│   ├── unit/                 # 41 tests unitarios
│   └── integration/          # 13 tests de integracion
├── scripts/
│   ├── ingest_runbooks.py    # Indexar en ChromaDB
│   ├── demo_queries.py       # Script de demo (4 escenarios)
│   └── aws/                  # Upload S3, manifesto, validacion, sync
├── infrastructure/
│   ├── cloudformation/       # Stack base (S3 + IAM + CloudWatch)
│   └── sam/                  # Stack API (Lambda + API GW + CloudFront)
├── .kiro/                    # Steering, Specs, Hooks (Kiro IDE)
├── .github/workflows/        # CI/CD (PR validation, deploy)
├── requirements.txt          # Dependencias Python
├── pyproject.toml            # Configuracion de herramientas
└── docker-compose.yml        # Ejecucion local con Docker
```

## Requisitos

### Ejecucion local

- Python 3.11
- pip

### Ejecucion cloud

- AWS CLI v2
- AWS SAM CLI
- Cuenta AWS con acceso a Bedrock (Claude Haiku 4.5)
- Perfil AWS con permisos de admin

## Inicio rapido (local)

```bash
# 1. Clonar repositorio
git clone https://github.com/cristianjonhson/Runbook_Guardian.git
cd Runbook_Guardian

# 2. Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Indexar runbooks en ChromaDB
python scripts/ingest_runbooks.py

# 5. Ejecutar backend
uvicorn backend.main:app --port 8000

# 6. Ejecutar frontend (otra terminal)
streamlit run frontend/app.py
```

Abrir http://localhost:8501

## Configuracion

Copiar `.env.example` a `.env` y ajustar:

```bash
# Modo de operacion
RAG_PROVIDER=local          # local | bedrock | auto

# AWS (solo para modo bedrock/auto)
AWS_PROFILE=admin
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0
S3_RUNBOOKS_BUCKET=runbook-guardian-source-087786573283-dev
```

## Modos de operacion

| Modo | Descripcion | Requisitos |
|------|-------------|-----------|
| `local` | ChromaDB + sentence-transformers (default) | Solo Python |
| `bedrock` | Bedrock Claude Haiku. Error si falla. | AWS credentials |
| `auto` | Intenta Bedrock, fallback automatico a local | AWS credentials (opcional) |

## API Endpoints

| Metodo | Path | Descripcion |
|--------|------|-------------|
| GET | `/api/v1/health` | Estado del sistema y runbooks indexados |
| POST | `/api/v1/query` | Consulta al agente con evidencia |
| GET | `/api/v1/runbooks` | Lista de runbooks disponibles |

### Ejemplo de consulta

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "nginx no responde, que hago?"}'
```

## Runbooks incluidos (16)

| Servicio | Runbook | Estado |
|----------|---------|--------|
| nginx | Reinicio del servicio | active |
| linux | Alto consumo CPU | active |
| linux | Disco lleno | active |
| postgresql | Pool de conexiones | active |
| postgresql | Reinicio de BD | active |
| api-gateway | Errores HTTP 500 | active |
| deployment | Rollback de despliegue | active |
| message-queue | Backlog en cola | active |
| microservices | Timeouts entre servicios | active |
| security | Expiracion certificado SSL | active |
| redis | Memoria llena | active |
| kubernetes | Pod CrashLoopBackOff | active |
| networking | Fallo DNS | active |
| load-balancer | Targets no saludables | active |
| observability | Pipeline de logs bloqueado | active |
| java | Memory leak (deprecated) | deprecated |

## Tests

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Con cobertura
python -m pytest tests/ --cov=backend --cov-fail-under=70

# Lint
ruff check --config pyproject.toml backend/ tests/ scripts/
```

## Despliegue en AWS

### Stack base (S3 + IAM)

```bash
cd infrastructure/cloudformation/scripts
./validate.sh
./create-change-set.sh
# Revisar cambios, luego:
CHANGE_SET_NAME=<nombre> ./execute-change-set.sh
```

### Stack API (Lambda + CloudFront)

```bash
source .venv/bin/activate
export AWS_PROFILE=admin
cd infrastructure/sam
sam build --template-file template.yaml --build-dir .aws-sam/build
sam deploy --template-file .aws-sam/build/template.yaml \
  --stack-name runbook-guardian-api-dev \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --resolve-s3 --no-confirm-changeset
```

### Subir runbooks a S3

```bash
python scripts/aws/upload_runbooks.py --bucket runbook-guardian-source-087786573283-dev
```

## Seguridad

- El sistema NUNCA ejecuta comandos.
- El sistema NUNCA modifica infraestructura.
- 26 patrones destructivos detectados (rm -rf, DROP DATABASE, kubectl delete, etc.).
- 7 patrones de aprobacion humana requerida.
- Documentacion obsoleta (deprecated o >90 dias) es rechazada.
- IAM con minimo privilegio.
- S3 con Block Public Access y versionamiento.
- Sin credenciales en el repositorio.

## Costos estimados (AWS)

| Servicio | Costo mensual |
|----------|--------------|
| Lambda | $0 (free tier) |
| API Gateway | $0 (free tier) |
| S3 | < $0.01 |
| CloudFront | ~$0.50 |
| Bedrock (Haiku) | ~$0.002/query |
| CloudWatch | < $0.50 |
| **Total** | **< $2/mes** |


## Autor

Cristian Jonhson Alvarez
