# Requirements — AWS Deployment (Fase 2)

> **NOTA:** Esta spec es un placeholder para post-MVP. No implementar hasta que el MVP local esté completo y validado.

## Objetivo

Integrar Amazon S3 (runbooks versionados) y Amazon Bedrock (mejora de retrieval) como segunda fase del proyecto.

## Alcance previsto

1. Almacenamiento de runbooks en S3 con versioning habilitado.
2. Sincronización S3 → local para modo offline.
3. Integración con Amazon Bedrock para embeddings de mayor calidad.
4. CloudFormation template para despliegue.
5. GitHub Actions workflow para deploy.

## Rama asociada

`infra/aws-deployment`

## Prerrequisitos

- MVP local 100% funcional.
- Tests pasando.
- Demo ensayada offline.

## Estado

PENDIENTE — No iniciar hasta completar core-mvp y frontend.
