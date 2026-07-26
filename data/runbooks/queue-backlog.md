---
title: "Backlog en Cola de Mensajes"
service: "message-queue"
version: "1.0.0"
last_reviewed: "2026-07-14"
status: "active"
---

## Síntomas

- Cola de mensajes creciendo sin procesarse (backlog > 10,000 mensajes).
- Consumidores sin procesar mensajes o procesando muy lentamente.
- Latencia de procesamiento de mensajes incrementando.
- Alertas de profundidad de cola disparadas.
- Servicios downstream no recibiendo eventos esperados.

## Diagnóstico

1. Verificar profundidad actual de la cola:
   ```
   # RabbitMQ
   rabbitmqctl list_queues name messages consumers

   # SQS
   aws sqs get-queue-attributes --queue-url <URL> --attribute-names ApproximateNumberOfMessages
   ```

2. Verificar estado de los consumidores:
   ```
   # Verificar si los workers están corriendo
   systemctl status queue-worker
   ps aux | grep worker
   ```

3. Revisar tasa de procesamiento vs tasa de ingreso:
   ```
   # Mensajes publicados vs consumidos por minuto
   rabbitmqctl list_queues name message_stats.publish_details.rate message_stats.deliver_details.rate
   ```

4. Verificar logs de los consumidores por errores:
   ```
   journalctl -u queue-worker --since "10 min ago" | grep -i "error\|failed\|timeout"
   ```

5. Verificar si hay mensajes envenenados (poison messages):
   ```
   # Revisar dead letter queue
   rabbitmqctl list_queues name messages | grep dead-letter
   ```

## Resolución

1. Si los consumidores están caídos, reiniciarlos:
   ```
   systemctl restart queue-worker
   ```

2. Si necesita más capacidad de procesamiento, escalar workers:
   ```
   # Incrementar número de workers
   kubectl scale deployment queue-worker --replicas=5
   ```

3. Si hay mensajes envenenados bloqueando la cola:
   ```
   # Mover mensajes problemáticos a dead letter queue
   rabbitmqctl purge_queue <nombre-cola-muerta>
   ```

4. Si el productor está generando tráfico anómalo:
   ```
   # Identificar el productor
   rabbitmqctl list_connections | grep <publisher-app>
   # Considerar rate limiting temporal
   ```

5. Monitorear que el backlog disminuye:
   ```
   watch -n 30 'rabbitmqctl list_queues name messages | grep <cola-afectada>'
   ```

## Escalamiento

- Si el backlog sigue creciendo con workers escalados, escalar al equipo de la aplicación productora.
- Si hay mensajes corruptos, coordinar con el equipo de desarrollo para parseo de errores.
- Si el broker está saturado (memoria/disco), escalar al equipo de infraestructura.

## Prevención

- Configurar alertas de profundidad de cola > 1,000 mensajes.
- Implementar auto-scaling de consumidores basado en backlog.
- Configurar dead letter queues para mensajes fallidos.
- Establecer TTL en mensajes para evitar acumulación infinita.
- Monitorear ratio publicación/consumo y alertar en desbalance > 2x.
