# AWS — Runbook Guardian

## Región

- Región principal: `us-east-1` (N. Virginia).
- Justificación: disponibilidad completa de Amazon Bedrock, Knowledge Bases, Claude Haiku y Titan Embeddings.
- No usar múltiples regiones para el MVP.

## Servicios AWS permitidos

| Servicio | Uso |
|----------|-----|
| Amazon S3 | Almacenamiento versionado de runbooks |
| Amazon Bedrock | Knowledge Bases + Foundation Models |
| AWS Lambda | API serverless (fase posterior) |
| Amazon API Gateway | Exposición REST (fase posterior) |
| AWS IAM | Roles y políticas de mínimo privilegio |
| Amazon CloudWatch | Logs y métricas |
| AWS CloudFormation | Infraestructura como código |
| AWS Systems Manager Parameter Store | Parámetros no sensibles |

## Servicios fuera de alcance (MVP)

- Amazon ECS / EKS / Fargate (no contenerizar frontend aún).
- Amazon RDS / DynamoDB (sin base relacional).
- Amazon Cognito (sin autenticación de usuarios).
- AWS Step Functions.
- Amazon SageMaker.
- AWS WAF (considerar post-MVP).

## Convención de nombres

```
{proyecto}-{recurso}-{entorno}
```

Ejemplos:
- `runbook-guardian-source-dev` (bucket S3)
- `runbook-guardian-query-dev` (Lambda)
- `runbook-guardian-api-dev` (API Gateway)
- `runbook-guardian-dev` (stack CloudFormation)

## Estrategia de etiquetas

Todos los recursos deben tener como mínimo:

```yaml
Tags:
  - Key: Project
    Value: runbook-guardian
  - Key: Environment
    Value: dev
  - Key: ManagedBy
    Value: cloudformation
  - Key: Owner
    Value: platform-team
  - Key: CostCenter
    Value: hackathon
```

## Gestión de variables y secretos

- Variables no sensibles: CloudFormation Parameters + SSM Parameter Store.
- Variables sensibles (API keys, tokens): Secrets Manager o GitHub Secrets.
- NUNCA hardcodear secretos en templates ni código.
- Usar `${VARIABLE}` en `.env` y references en CloudFormation.

## Políticas IAM

- Mínimo privilegio siempre.
- No usar `*` en Resource salvo CloudWatch Logs.
- Roles específicos por servicio (Lambda, Bedrock KB).
- No crear usuarios IAM; usar roles con OIDC para CI/CD.
- Documentar cada permiso con comentario de justificación.

## Cifrado

- S3: SSE-S3 (aws:kms innecesario para el MVP, agrega costo).
- CloudWatch Logs: cifrado por defecto.
- Tráfico: HTTPS obligatorio (S3 bucket policy).

## Bloqueo de acceso público

- Todos los buckets S3: Block Public Access habilitado (las 4 opciones).
- API Gateway: sin autenticación para MVP local, API key si se expone.
- Lambda: sin URL pública directa (solo via API Gateway).

## Entornos permitidos

- `dev`: único entorno para el MVP.
- `demo`: alias del mismo entorno si se necesita para la presentación.
- No crear `staging` ni `production` durante la hackathon.

## Política de eliminación

- Los stacks de desarrollo PUEDEN eliminarse después de la demo.
- Los buckets S3 con datos usan `DeletionPolicy: Retain` para evitar pérdida accidental.
- Todos los demás recursos usan `DeletionPolicy: Delete`.
- Vaciar buckets manualmente antes de eliminar stacks retenidos.

## Reglas de despliegue

1. No desplegar sin revisar el Change Set.
2. No ejecutar Change Sets automáticamente desde CI.
3. Usar OIDC para autenticación de GitHub Actions.
4. Verificar estado del stack después de cada operación.
5. No modificar recursos CloudFormation manualmente.
6. Ejecutar smoke tests después de cada despliegue.
