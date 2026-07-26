# Requirements — AWS Evolution (Runbook Guardian)

## Objetivo

Evolucionar Runbook Guardian desde un MVP local hacia una arquitectura híbrida AWS sin destruir, reemplazar ni desestabilizar la implementación local existente.

---

## Historias de usuario

### HU-AWS-001: Consulta con evidencia desde Bedrock
**Como** ingeniero on-call,
**quiero** que el agente busque en runbooks almacenados en AWS,
**para** obtener respuestas con evidencia verificable incluso cuando el corpus local no sea suficiente.

### HU-AWS-002: Fallback transparente
**Como** operador SRE,
**quiero** que si AWS no está disponible el sistema use automáticamente el motor local,
**para** garantizar continuidad operativa durante incidentes de red.

### HU-AWS-003: Trazabilidad de versiones
**Como** líder de plataforma,
**quiero** que cada respuesta indique la versión exacta del runbook (incluyendo S3 version ID),
**para** auditar que nunca se usó documentación obsoleta.

### HU-AWS-004: Infraestructura reproducible
**Como** DevOps,
**quiero** que toda la infraestructura AWS se gestione con CloudFormation,
**para** poder recrear o eliminar el entorno de forma controlada.

### HU-AWS-005: Control de costos
**Como** responsable de la cuenta AWS,
**quiero** que el entorno de desarrollo cueste menos de $5/mes,
**para** evitar sorpresas en la facturación durante la hackathon.

---

## Requerimientos funcionales

### REQ-AWS-001: Almacenamiento versionado
WHEN un runbook sea cargado a la fuente de conocimiento,
THE SYSTEM SHALL almacenarlo en un bucket S3 con versionamiento habilitado.

### REQ-AWS-002: Metadatos de indexación
WHEN un runbook sea indexado,
THE SYSTEM SHALL conservar metadatos de: id, versión, estado, propietario, fecha de revisión y hash de contenido.

### REQ-AWS-003: Recuperación semántica con Bedrock
WHEN el usuario realice una consulta en modo `bedrock`,
THE SYSTEM SHALL recuperar evidencia mediante Amazon Bedrock Knowledge Bases.

### REQ-AWS-004: Citaciones de Bedrock
WHEN Bedrock genere una respuesta,
THE SYSTEM SHALL devolver las citas asociadas a los fragmentos recuperados.

### REQ-AWS-005: Normalización de citas
WHEN una cita sea recibida desde Bedrock,
THE SYSTEM SHALL convertirla al modelo interno de evidencia y validar su vigencia.

### REQ-AWS-006: Exclusión de runbooks no vigentes
IF una fuente está marcada como `deprecated`, `archived` o `expired`,
THE SYSTEM SHALL excluirla como fuente autorizada.

### REQ-AWS-007: Abstención por falta de evidencia
IF la respuesta no contiene evidencia válida,
THE SYSTEM SHALL abstenerse de entregar instrucciones operativas.

### REQ-AWS-008: Bloqueo de acciones destructivas
IF la consulta o respuesta contiene una acción destructiva,
THE SYSTEM SHALL bloquear la acción y mostrar advertencia.

### REQ-AWS-009: Aprobación humana visible
IF una acción requiere aprobación,
THE SYSTEM SHALL mostrar explícitamente `HUMAN_APPROVAL_REQUIRED`.

### REQ-AWS-010: Prohibición de ejecución
THE SYSTEM SHALL NOT ejecutar comandos ni modificar recursos AWS.

### REQ-AWS-011: Fallback automático
IF Bedrock no está disponible y `RAG_PROVIDER=auto`,
THE SYSTEM SHALL activar el proveedor local automáticamente.

### REQ-AWS-012: Información de fallback visible
WHEN se active el fallback,
THE SYSTEM SHALL informar el proveedor utilizado y el motivo del cambio.

### REQ-AWS-013: Correlation ID
WHEN una solicitud llegue a la API,
THE SYSTEM SHALL generar un correlation ID único para trazabilidad.

### REQ-AWS-014: Observabilidad segura
THE SYSTEM SHALL registrar métricas sin almacenar secretos ni contenido sensible.

### REQ-AWS-015: Eliminación controlada
THE SYSTEM SHALL permitir eliminar los recursos de desarrollo mediante la eliminación controlada de stacks CloudFormation.

### REQ-CFN-001: Change Set obligatorio
BEFORE un stack sea desplegado o actualizado,
THE SYSTEM SHALL crear y mostrar un Change Set para revisión humana.

### REQ-CFN-002: Validación de plantillas
WHEN una plantilla sea modificada,
THE SYSTEM SHALL validarla mediante cfn-lint y `aws cloudformation validate-template`.

### REQ-CFN-003: Capacidades IAM explícitas
IF una plantilla crea recursos IAM con nombres explícitos,
THE DEPLOYMENT SHALL requerir `CAPABILITY_NAMED_IAM`.

### REQ-CFN-004: Políticas de eliminación
WHEN un stack persistente sea creado,
THE SYSTEM SHALL configurar políticas explícitas de eliminación y reemplazo.

### REQ-CFN-005: Smoke tests post-deploy
WHEN se complete un despliegue,
THE SYSTEM SHALL verificar el estado final del stack y ejecutar smoke tests.

### REQ-CFN-006: Manejo de stacks fallidos
IF un stack entra en estado `ROLLBACK_COMPLETE` o `UPDATE_ROLLBACK_FAILED`,
THE SYSTEM SHALL detener el despliegue y mostrar un procedimiento seguro de recuperación.

### REQ-CFN-007: Drift detection
THE SYSTEM SHALL soportar detección de drift para recursos gestionados por CloudFormation.

---

## Requerimientos no funcionales

### REQ-AWS-NF-001: Presupuesto
- El entorno de desarrollo debe costar menos de $5 USD/mes.
- Debe poder reducirse a $0 eliminando el stack.

### REQ-AWS-NF-002: Latencia
- Consulta vía Bedrock: < 10 segundos (p95).
- Fallback a local: < 3 segundos.

### REQ-AWS-NF-003: Disponibilidad
- El sistema local debe funcionar al 100% sin AWS.
- AWS es un proveedor adicional, no un reemplazo.

### REQ-AWS-NF-004: Seguridad
- IAM con mínimo privilegio.
- Sin credenciales permanentes en CI/CD (OIDC).
- Sin acceso público a S3.
- HTTPS obligatorio.

### REQ-AWS-NF-005: Reproducibilidad
- Todo recurso creado desde CloudFormation.
- Todo entorno eliminable con un solo `delete-stack`.

---

## Criterios de aceptación

| ID | Criterio | Verificación |
|----|----------|-------------|
| AC-AWS-001 | Query en modo bedrock retorna citas con fuente y versión | Test E2E con Bedrock |
| AC-AWS-002 | Runbook deprecated excluido en modo bedrock | Test con runbook status=deprecated |
| AC-AWS-003 | Fallback activa si Bedrock timeout | Test simulando error de red |
| AC-AWS-004 | Respuesta indica provider_used y fallback_reason | Verificar JSON response |
| AC-AWS-005 | S3 bucket tiene versioning habilitado | aws s3api get-bucket-versioning |
| AC-AWS-006 | cfn-lint pasa sin errores | CI pipeline |
| AC-AWS-007 | Stack se crea correctamente | aws cloudformation describe-stacks |
| AC-AWS-008 | Stack se elimina sin errores (excepto Retain) | delete-stack test |
| AC-AWS-009 | Costo mensual < $5 USD | Cost Explorer + tags |
| AC-AWS-010 | Tests locales siguen pasando (54/54) | pytest en CI |
| AC-AWS-011 | Acción destructiva bloqueada en modo bedrock | Test con query peligrosa |
