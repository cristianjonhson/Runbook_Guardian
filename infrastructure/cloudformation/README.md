# CloudFormation — Runbook Guardian

## Descripción

Infraestructura AWS del proyecto Runbook Guardian gestionada mediante CloudFormation.

## Stack: `runbook-guardian-dev`

### Recursos creados

| Recurso | Tipo | DeletionPolicy | Descripción |
|---------|------|---------------|-------------|
| S3 Bucket | `AWS::S3::Bucket` | Retain | Almacenamiento versionado de runbooks |
| Bucket Policy | `AWS::S3::BucketPolicy` | Delete | HTTPS obligatorio |
| IAM Role | `AWS::IAM::Role` | Delete | Permisos para Bedrock + S3 read |
| Log Group | `AWS::Logs::LogGroup` | Delete | Logs de aplicación (7 días) |

### Prerrequisitos

- AWS CLI v2 configurada con credenciales válidas.
- `cfn-lint` instalado (`pip install cfn-lint`).
- Región con soporte para Bedrock: `us-east-1`.

### Estructura

```
infrastructure/cloudformation/
├── templates/
│   └── main.yaml              # Plantilla principal
├── parameters/
│   └── dev.example.json       # Parámetros de ejemplo
├── scripts/
│   ├── validate.sh            # Validación cfn-lint + AWS
│   ├── create-change-set.sh   # Crear change set (sin ejecutar)
│   ├── execute-change-set.sh  # Ejecutar change set (con confirmación)
│   └── delete-stack.sh        # Eliminar stack (con confirmación)
└── README.md
```

## Uso

### 1. Validar plantillas

```bash
cd infrastructure/cloudformation/scripts
./validate.sh
```

### 2. Crear Change Set (revisión)

```bash
./create-change-set.sh
```

Esto muestra qué recursos se crearán/modificarán sin ejecutar nada.

### 3. Ejecutar Change Set (despliegue)

```bash
CHANGE_SET_NAME=changeset-20260725-120000 ./execute-change-set.sh
```

Requiere confirmación interactiva (`yes`).

### 4. Eliminar Stack (limpieza)

```bash
./delete-stack.sh
```

Requiere escribir `DELETE` para confirmar. El bucket S3 queda retenido.

## Parámetros

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| ProjectName | runbook-guardian | Nombre base para recursos |
| Environment | dev | Entorno (dev, demo) |
| BedrockModelId | anthropic.claude-3-haiku-20240307-v1:0 | Modelo de generación |
| BedrockEmbeddingModelId | amazon.titan-embed-text-v2:0 | Modelo de embeddings |
| LogRetentionDays | 7 | Retención de logs |

## Outputs

| Output | Descripción |
|--------|-------------|
| S3BucketName | Nombre del bucket de runbooks |
| S3BucketArn | ARN del bucket |
| BedrockInvokeRoleArn | ARN del rol para invocar Bedrock |
| LogGroupName | Nombre del log group |
| StackRegion | Región del stack |

## Capacidades requeridas

Este stack crea roles IAM con nombre explícito, por lo que requiere:

```
--capabilities CAPABILITY_NAMED_IAM
```

## Notas de costo

- S3: < $0.01/mes (16 archivos de texto).
- CloudWatch Logs: < $0.50/mes (7 días retención).
- IAM: sin costo.
- **Total del stack: < $1/mes.**

## Eliminación del bucket retenido

Si necesitas eliminar completamente el bucket después de eliminar el stack:

```bash
# Vaciar todas las versiones
BUCKET=runbook-guardian-source-<account-id>-dev
aws s3api list-object-versions --bucket $BUCKET \
  --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' \
  --output json | aws s3api delete-objects --bucket $BUCKET --delete file:///dev/stdin

# Eliminar delete markers
aws s3api list-object-versions --bucket $BUCKET \
  --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' \
  --output json | aws s3api delete-objects --bucket $BUCKET --delete file:///dev/stdin

# Eliminar bucket vacío
aws s3 rb s3://$BUCKET
```
