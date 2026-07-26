# Cost Control — Runbook Guardian

## Principio

El MVP debe costar menos de $5 USD/mes en desarrollo activo y $0 cuando no se use.
Todos los recursos deben poder eliminarse completamente para detener costos.

## Entorno único

- Solo un entorno de desarrollo (`dev`).
- No crear staging ni producción durante la hackathon.
- Un solo stack de CloudFormation.

## Modelos de IA (selección por costo)

| Modelo | Uso | Costo aproximado | Justificación |
|--------|-----|-----------------|---------------|
| `amazon.titan-embed-text-v2:0` | Embeddings para Knowledge Base | ~$0.0001/1K tokens | Más económico que Cohere |
| `anthropic.claude-3-haiku-20240307-v1:0` | Generación de respuestas | ~$0.00025/1K input, $0.00125/1K output | Modelo más económico de Claude, suficiente para MVP |

**No usar:**
- Claude Sonnet/Opus (10-75x más caro).
- Modelos de OpenAI (requiere marketplace).
- Modelos custom (innecesarios para MVP).

## Límites de consultas

- Máximo 5 fragmentos recuperados por consulta (top_k=5).
- Máximo respuesta de 500 tokens de salida.
- Máximo 1000 tokens de entrada (prompt + contexto).
- No implementar cache en MVP, pero diseñar para agregarlo después.

## S3

- Un solo bucket para desarrollo.
- Lifecycle: versiones no actuales se eliminan después de 30 días.
- No usar Glacier ni Intelligent-Tiering (innecesario con 16 archivos).
- Cifrado SSE-S3 (sin costo adicional vs KMS que cobra por request).

## Lambda

- Memoria: 256MB (mínimo necesario para boto3 + lógica).
- Timeout: 30 segundos máximo.
- Free tier: 1M requests/mes + 400,000 GB-seconds.
- Para el MVP con < 100 queries/día, costo = $0.

## API Gateway

- REST API (no HTTP API si necesitamos features de throttling).
- Free tier: 1M requests/mes por 12 meses.
- Sin custom domain (innecesario para demo).

## CloudWatch

- Retención de logs: 7 días para desarrollo.
- No crear dashboards custom (usar consola directa).
- No crear alarmas que envíen a SNS (evitar costos de notificación).
- Alarmas solo en métricas gratuitas (Lambda errors, API 5xx).

## Bedrock Knowledge Base

- Sincronización manual (no programada).
- Solo sincronizar cuando se agregen o modifiquen runbooks.
- Vector store: usar la opción gestionada por Bedrock (sin servidor adicional).
  - OpenSearch Serverless tiene costo mínimo (~$0.24/hora por OCU).
  - **Alternativa más económica**: Pinecone free tier o S3-based retrieval sin vector store dedicado.
  - **Recomendación MVP**: Evaluar si Amazon Bedrock Knowledge Bases con vector store managed justifica el costo. Si no, usar retrieval directo con Bedrock sin Knowledge Base (InvokeModel con contexto inline).

## Estrategia de eliminación

Después de la demo/hackathon:

```bash
# 1. Vaciar bucket S3 (versiones incluidas)
aws s3 rm s3://runbook-guardian-source-dev --recursive
aws s3api delete-objects --bucket runbook-guardian-source-dev \
  --delete "$(aws s3api list-object-versions --bucket runbook-guardian-source-dev --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"

# 2. Eliminar stack
aws cloudformation delete-stack --stack-name runbook-guardian-dev
aws cloudformation wait stack-delete-complete --stack-name runbook-guardian-dev

# 3. Eliminar bucket retenido (si DeletionPolicy=Retain)
aws s3 rb s3://runbook-guardian-source-dev --force
```

## Etiquetas de costo

Todos los recursos deben tener:
```yaml
CostCenter: hackathon
Environment: dev
```

Esto permite filtrar en Cost Explorer para verificar el gasto real.

## Revisión obligatoria

Antes de cada despliegue, verificar:
- ¿Estoy creando un recurso con costo por hora (OpenSearch, NAT Gateway, etc.)?
- ¿La retención de logs es la mínima necesaria?
- ¿El modelo seleccionado es el más económico que cumple la necesidad?
- ¿Puedo eliminar todo con un solo `delete-stack`?

## Presupuesto estimado (activo)

| Servicio | Estimación/mes |
|----------|---------------|
| S3 (16 archivos) | < $0.01 |
| Bedrock Embeddings | < $0.10 (pocas sincronizaciones) |
| Bedrock Generation (Haiku) | < $0.50 (< 200 queries demo) |
| Lambda | $0.00 (free tier) |
| API Gateway | $0.00 (free tier) |
| CloudWatch (7 días) | < $0.50 |
| Vector Store (si managed) | $0 - $5 (depende de opción) |
| **Total** | **< $5/mes** |

## Presupuesto cuando no se usa

Si no se hacen consultas y no hay sincronizaciones: **$0/mes** (excepto si hay un vector store serverless con costo mínimo por hora).

## Alerta de costos

Crear un Budget Alert en AWS (manual, no en CloudFormation):
- Umbral: $10/mes.
- Acción: notificación por email.
- No es parte del stack del proyecto.
