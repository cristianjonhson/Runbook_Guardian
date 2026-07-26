# CloudFormation — Runbook Guardian

## Uso obligatorio

Toda infraestructura AWS del proyecto debe gestionarse mediante CloudFormation.
No se permite crear recursos manualmente excepto durante pruebas exploratorias que deben eliminarse inmediatamente.

## Formato de plantillas

- YAML (no JSON).
- Indentación: 2 espacios.
- Comentarios para decisiones no obvias.

## Convención de stacks

```
runbook-guardian-{entorno}
```

Para el MVP: un solo stack `runbook-guardian-dev`.
Fragmentar en nested stacks solo si la plantilla supera 500 líneas o tiene dependencias circulares.

## Estructura de archivos

```
infrastructure/cloudformation/
├── templates/
│   └── main.yaml           # Plantilla principal (o única para MVP)
├── parameters/
│   └── dev.example.json    # Parámetros de ejemplo (sin secretos)
├── scripts/
│   ├── validate.sh         # cfn-lint + validate-template
│   ├── create-change-set.sh
│   ├── execute-change-set.sh
│   └── delete-stack.sh
└── README.md
```

## Parámetros

- Usar `Parameters` para valores que varían entre entornos.
- Definir `AllowedValues` cuando el rango es limitado.
- Definir `Default` para valores no sensibles.
- NUNCA poner secretos como parámetros por defecto.
- Usar `NoEcho: true` para valores sensibles pasados en deploy.

## Mappings y Conditions

- Usar `Mappings` para valores que dependen de región o entorno.
- Usar `Conditions` para recursos opcionales (ej: alarmas solo en prod).
- No abusar de Conditions para el MVP; simplicidad primero.

## Outputs

- Exportar valores necesarios para otros stacks o scripts.
- Formato: `{StackName}{ResourceType}{Nombre}`.
- Ejemplos: `S3BucketName`, `S3BucketArn`, `KnowledgeBaseId`, `LambdaArn`.

## Change Sets (obligatorio)

Flujo para todo despliegue:

```
1. cfn-lint templates/*.yaml
2. aws cloudformation validate-template
3. aws cloudformation create-change-set
4. Revisión humana del change set
5. aws cloudformation execute-change-set (con aprobación)
6. aws cloudformation wait stack-*-complete
7. Verificar outputs
8. Smoke tests
```

NUNCA usar `aws cloudformation deploy` directamente (omite la revisión del change set).

## Validación

Antes de crear un change set:

```bash
# Validación estática
cfn-lint infrastructure/cloudformation/templates/*.yaml

# Validación AWS
aws cloudformation validate-template \
  --template-body file://infrastructure/cloudformation/templates/main.yaml
```

## DeletionPolicy

| Tipo de recurso | DeletionPolicy | Justificación |
|----------------|---------------|---------------|
| S3 Bucket (datos) | Retain | Evitar pérdida accidental de runbooks |
| IAM Roles | Delete | Recreables sin pérdida |
| Lambda | Delete | Recreable desde código |
| API Gateway | Delete | Recreable |
| CloudWatch Logs | Delete | Logs de desarrollo no son permanentes |
| Knowledge Base | Delete | Reconfigurable |

## UpdateReplacePolicy

- S3 Bucket: `Retain` (un replace no debe eliminar datos).
- Otros recursos: `Delete` (default).

## Protección de terminación

- Para el MVP dev: NO habilitar termination protection (necesitamos poder eliminar fácilmente).
- Para producción futura: habilitar en stacks persistentes.

## CAPABILITY_NAMED_IAM

- Requerido cuando la plantilla crea roles IAM con nombres explícitos.
- Documentar en el README y en los scripts de deploy.
- El workflow de CI debe incluirlo explícitamente.

## Rollback

- CloudFormation hace rollback automático en caso de fallo.
- No deshabilitar rollback (`--disable-rollback`) en desarrollo.
- Si un stack queda en `ROLLBACK_COMPLETE`: eliminar y recrear.
- Si queda en `UPDATE_ROLLBACK_FAILED`: seguir procedimiento manual documentado.

## Drift Detection

- Ejecutar `detect-stack-drift` después de cambios manuales sospechosos.
- No corregir drift automáticamente.
- Documentar cualquier drift encontrado.
- Frecuencia: antes de cada deploy, no automático.

## Custom Resources

- Evitar siempre que exista alternativa nativa.
- Si es necesario: Lambda-backed, idempotente, con timeout < 60s.
- Documentar razón de uso.
- Manejar correctamente DELETE para limpieza.

## Prohibiciones

- No modificar recursos administrados por CloudFormation desde la consola.
- No usar macros de terceros no verificadas.
- No crear stacks duplicados del mismo entorno.
- No ejecutar change sets sin revisión humana.
- Runbook Guardian NO puede crear, modificar ni eliminar stacks.
