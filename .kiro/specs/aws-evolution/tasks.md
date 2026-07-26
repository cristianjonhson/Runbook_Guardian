# Tasks — AWS Evolution (Runbook Guardian)

## Resumen

La evolución se divide en fases incrementales. Cada tarea es reversible y no rompe el MVP local.

---

## Fase A: Fundamentos (rama `infra/aws-foundation`)

- [ ] A1. Crear estructura CloudFormation (templates/, parameters/, scripts/)
- [ ] A2. Crear plantilla principal con S3 bucket versionado
- [ ] A3. Crear IAM role para acceso a Bedrock
- [ ] A4. Crear scripts de validación (validate.sh)
- [ ] A5. Crear script de create-change-set.sh
- [ ] A6. Crear script de execute-change-set.sh
- [ ] A7. Crear script de delete-stack.sh
- [ ] A8. Validar plantilla con cfn-lint
- [ ] A9. Crear parameters/dev.example.json
- [ ] A10. Documentar en infrastructure/cloudformation/README.md

---

## Fase B: Almacenamiento S3 (rama `infra/aws-foundation`)

- [ ] B1. Desplegar stack con S3 bucket (change set revisado)
- [ ] B2. Crear script de upload de runbooks a S3
- [ ] B3. Crear script de generación de manifiesto (runbook-manifest.json)
- [ ] B4. Subir los 16 runbooks a S3
- [ ] B5. Verificar versionamiento con aws s3api list-object-versions
- [ ] B6. Crear test de validación de metadatos S3

---

## Fase C: Integración Bedrock (rama `feature/aws-rag`)

- [ ] C1. Crear Protocol `RunbookRetriever` como interfaz abstracta
- [ ] C2. Refactorizar RetrievalService existente como `LocalRunbookRetriever`
- [ ] C3. Crear `BedrockRunbookRetriever` usando InvokeModel con contexto
- [ ] C4. Crear `FallbackRouter` con circuit breaker básico
- [ ] C5. Agregar RAG_PROVIDER a config.py
- [ ] C6. Actualizar QueryService para usar FallbackRouter
- [ ] C7. Actualizar dependencies.py con factory por provider
- [ ] C8. Crear CitationNormalizer para respuestas de Bedrock
- [ ] C9. Agregar tests unitarios con mocks de boto3
- [ ] C10. Verificar que tests locales siguen pasando (54/54)

---

## Fase D: Seguridad AWS (rama `feature/aws-safety`)

- [ ] D1. Agregar patrones destructivos AWS a destructive_patterns.py
- [ ] D2. Crear ManifestValidator (verifica vigencia contra manifiesto)
- [ ] D3. Extender RunbookMetadata con campos: id, owner, valid_until, content_hash
- [ ] D4. Agregar lógica de HUMAN_APPROVAL_REQUIRED
- [ ] D5. Agregar lógica de abstención (sin evidencia suficiente)
- [ ] D6. Crear tests para cada nuevo patrón y regla
- [ ] D7. Verificar que Bedrock Guardrails es solo complementario (no reemplaza reglas)

---

## Fase E: Fallback y resiliencia (rama `feature/aws-fallback`)

- [ ] E1. Implementar circuit breaker con estados (closed, open, half-open)
- [ ] E2. Configurar timeout para Bedrock (10s)
- [ ] E3. Clasificar errores: recuperables vs no recuperables
- [ ] E4. Agregar metadata de fallback al response (provider_used, fallback_reason)
- [ ] E5. Crear test de fallback simulando timeout
- [ ] E6. Crear test de fallback simulando error de auth
- [ ] E7. Verificar que modo local sigue funcionando al 100%

---

## Fase F: Observabilidad (rama `feature/aws-observability`)

- [ ] F1. Agregar correlation_id a cada request
- [ ] F2. Crear logs estructurados para decisiones AWS
- [ ] F3. Configurar CloudWatch Log Group en CloudFormation (7 días retención)
- [ ] F4. Definir métricas custom (QueryCount, FallbackCount, BlockedActionCount)
- [ ] F5. Crear test de que los logs no contienen secretos

---

## Fase G: CI/CD (rama `ci/aws-deployment`)

- [ ] G1. Crear .github/workflows/pull-request.yml (lint, test, cfn-lint)
- [ ] G2. Crear .github/workflows/deploy-dev.yml (change set + manual execution)
- [ ] G3. Crear .github/workflows/delete-dev-stack.yml (manual, con confirmación)
- [ ] G4. Configurar OIDC para GitHub Actions ↔ AWS
- [ ] G5. Documentar procedimiento de deploy

---

## Fase H: Demo AWS (rama `docs/aws-demo`)

- [ ] H1. Crear script de demo AWS (3 escenarios: exitosa, destructiva, fallback)
- [ ] H2. Actualizar docs/demo-guide.md con flujo AWS
- [ ] H3. Ensayar demo < 5 minutos
- [ ] H4. Verificar que demo funciona sin AWS (fallback)

---

## Detalle por tarea (Fase A — prioritaria)

### A1: Crear estructura CloudFormation

**Objetivo:** Directorio organizado para templates y scripts.
**Archivos:**
- `infrastructure/cloudformation/templates/main.yaml`
- `infrastructure/cloudformation/parameters/dev.example.json`
- `infrastructure/cloudformation/scripts/validate.sh`
- `infrastructure/cloudformation/scripts/create-change-set.sh`
- `infrastructure/cloudformation/scripts/execute-change-set.sh`
- `infrastructure/cloudformation/scripts/delete-stack.sh`
- `infrastructure/cloudformation/README.md`
**Dependencias:** Ninguna.
**Criterio:** Directorios creados, scripts ejecutables.
**Rama:** `infra/aws-foundation`

### A2: Crear plantilla principal con S3

**Objetivo:** Template YAML con bucket S3 versionado, cifrado, block public access.
**Archivos:** `infrastructure/cloudformation/templates/main.yaml`
**Dependencias:** A1.
**Criterio:** `cfn-lint` pasa, `validate-template` pasa.
**Rama:** `infra/aws-foundation`

### A3: Crear IAM role para Bedrock

**Objetivo:** Role con permisos mínimos para invocar Bedrock y leer S3.
**Archivos:** `infrastructure/cloudformation/templates/main.yaml` (agregar recurso)
**Dependencias:** A2.
**Criterio:** Role con mínimo privilegio, CAPABILITY_NAMED_IAM documentado.
**Rama:** `infra/aws-foundation`

### C1: Crear Protocol RunbookRetriever

**Objetivo:** Interfaz abstracta que permite intercambiar proveedores.
**Archivos:** `backend/services/retriever_protocol.py`
**Dependencias:** Ninguna (no rompe lo existente).
**Criterio:** Protocol definido, LocalRetriever lo implementa.
**Rama:** `feature/aws-rag`

### C3: Crear BedrockRunbookRetriever

**Objetivo:** Implementación que usa InvokeModel con contexto de ChromaDB.
**Archivos:** `backend/services/bedrock_retriever.py`
**Dependencias:** C1, C2, boto3.
**Criterio:** Envía fragmentos locales como contexto a Haiku, retorna respuesta generada.
**Rama:** `feature/aws-rag`

### C4: Crear FallbackRouter

**Objetivo:** Circuit breaker que redirige a local si Bedrock falla.
**Archivos:** `backend/services/fallback_router.py`
**Dependencias:** C1, C3.
**Criterio:** auto mode funciona: Bedrock OK → usa Bedrock. Bedrock timeout → usa local.
**Rama:** `feature/aws-rag`

---

## Orden de implementación recomendado

```
Fase A (fundamentos CFN) → desplegar S3
    ↓
Fase B (upload runbooks) → verificar versionamiento
    ↓
Fase C (Bedrock integration) → queries vía Bedrock
    ↓
Fase D (seguridad AWS) → patrones + manifiesto
    ↓
Fase E (fallback) → circuit breaker
    ↓
Fase F (observabilidad) → logs + métricas
    ↓
Fase G (CI/CD) → workflows automáticos
    ↓
Fase H (demo) → presentación final
```

## Notas de costo

- Fase A-B: $0 (solo S3 con < 1MB de datos).
- Fase C: ~$0.002/query (solo tokens de Haiku).
- Fase D-H: $0 adicional (lógica en código, no recursos nuevos).
- **Total estimado de la evolución completa: < $2/mes en uso activo.**
