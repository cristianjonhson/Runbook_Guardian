---
title: "Pipeline de Logs Bloqueado"
service: "observability"
version: "1.0.0"
last_reviewed: "2026-07-06"
status: "active"
---

## Síntomas

- Logs no apareciendo en el sistema centralizado (ELK, CloudWatch, Datadog).
- Gap de tiempo en la visualización de logs (últimos N minutos sin datos).
- Alertas basadas en logs no disparándose a pesar de errores activos.
- Agentes de logs (Fluentd, Filebeat, CloudWatch Agent) consumiendo disco.
- Buffer de logs local creciendo sin drenar.

## Diagnóstico

1. Verificar estado del agente de logs:
   ```
   systemctl status fluentd
   # o
   systemctl status filebeat
   ```

2. Verificar si el buffer local está creciendo:
   ```
   du -sh /var/log/fluentd-buffer/
   ls -la /var/lib/filebeat/registry/
   ```

3. Verificar conectividad con el destino:
   ```
   # Elasticsearch
   curl -s http://elasticsearch:9200/_cluster/health

   # CloudWatch
   aws logs describe-log-groups --limit 1
   ```

4. Verificar si hay errores en el agente:
   ```
   journalctl -u fluentd --since "10 min ago" | grep -i "error\|warn\|retry"
   ```

5. Verificar que los logs se están escribiendo localmente:
   ```
   tail -1 /var/log/app/application.log
   # Si el archivo no crece, el problema es la aplicación, no el pipeline
   ```

## Resolución

1. Si el agente de logs está caído, reiniciarlo:
   ```
   systemctl restart fluentd
   ```

2. Si el buffer está lleno, limpiar y reiniciar:
   ```
   # Hacer backup del buffer si los logs son importantes
   mv /var/log/fluentd-buffer/ /tmp/fluentd-buffer-backup/
   mkdir /var/log/fluentd-buffer/
   systemctl restart fluentd
   ```

3. Si Elasticsearch está con disco lleno, liberar espacio:
   ```
   # Eliminar índices viejos
   curl -X DELETE "elasticsearch:9200/logs-2026.06.*"
   ```

4. Si el problema es de autenticación/permisos con el destino:
   ```
   # Verificar credenciales del agente
   cat /etc/fluentd/fluent.conf | grep -A 5 "credentials\|access_key"
   ```

5. Verificar que los logs comienzan a fluir:
   ```
   # Generar un log de prueba
   logger "test-log-pipeline-$(date +%s)"
   # Verificar que aparece en el destino en < 60 segundos
   ```

## Escalamiento

- Si Elasticsearch está caído o saturado, escalar al equipo de observabilidad.
- Si el problema es de permisos/IAM, contactar al equipo de seguridad.
- Si los logs se están perdiendo (buffer overflow), priorizar como incidente de auditoría.

## Prevención

- Monitorear latencia del pipeline de logs (tiempo entre generación y disponibilidad).
- Configurar alertas de "no data" si un servicio deja de enviar logs por > 5 minutos.
- Implementar retry con backoff en los agentes.
- Mantener espacio suficiente para buffers locales (al menos 1GB).
- Rotar índices de Elasticsearch automáticamente con ILM.
