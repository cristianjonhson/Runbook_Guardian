---
title: "Errores HTTP 500 en la API"
service: "api-gateway"
version: "1.0.0"
last_reviewed: "2026-07-15"
status: "active"
---

## Síntomas

- Respuestas HTTP 500 Internal Server Error desde la API.
- Incremento súbito en la tasa de errores 5xx en el monitoreo.
- Clientes reportando fallos intermitentes o totales.
- Health checks del balanceador pasando pero endpoints funcionales fallando.
- Logs mostrando excepciones no capturadas o stack traces.

## Diagnóstico

1. Verificar tasa de errores en los últimos 5 minutos:
   ```
   grep "500" /var/log/api/access.log | tail -50
   ```

2. Revisar logs de la aplicación para excepciones:
   ```
   journalctl -u api-service --since "5 min ago" | grep -i "error\|exception\|traceback"
   ```

3. Verificar si el error es en un endpoint específico o generalizado:
   ```
   grep "500" /var/log/api/access.log | awk '{print $7}' | sort | uniq -c | sort -rn
   ```

4. Verificar estado de dependencias (base de datos, cache, servicios externos):
   ```
   curl -s http://localhost:8080/health/dependencies | python3 -m json.tool
   ```

5. Verificar uso de recursos del proceso:
   ```
   ps aux | grep api-service
   cat /proc/<PID>/status | grep -E "VmRSS|Threads"
   ```

## Resolución

1. Si el error es por una dependencia caída (DB, Redis, servicio externo):
   - Verificar y reiniciar la dependencia afectada.
   - La API debería recuperarse automáticamente.

2. Si el error es por un bug en un deploy reciente:
   ```
   # Verificar último deploy
   cat /var/log/deploy/last_deploy.log
   # Rollback si necesario
   ./scripts/rollback.sh
   ```

3. Si el error es por agotamiento de recursos (memoria, file descriptors):
   ```
   systemctl restart api-service
   ```

4. Si el error es por rate limiting o sobrecarga:
   ```
   # Verificar conexiones activas
   ss -s
   # Considerar escalar horizontalmente
   ```

5. Después de la resolución, verificar que los errores cesaron:
   ```
   watch -n 5 'grep "500" /var/log/api/access.log | wc -l'
   ```

## Escalamiento

- Si los errores persisten después de restart, escalar al equipo de desarrollo con los stack traces.
- Si el problema es de capacidad, coordinar con infraestructura para escalar.
- Si el error está en una dependencia externa, contactar al equipo responsable.

## Prevención

- Implementar circuit breakers para dependencias externas.
- Configurar alertas de tasa de errores al 1% del tráfico.
- Mantener logs estructurados con correlation IDs.
- Hacer canary deployments para detectar regresiones temprano.
- Revisar error budgets semanalmente.
