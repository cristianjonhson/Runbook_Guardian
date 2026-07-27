---
title: "Rollback de Despliegue"
service: "deployment-pipeline"
version: "2.0.0"
last_reviewed: "2026-07-08"
status: "active"
---

## Síntomas

- Incremento de errores inmediatamente después de un despliegue.
- Degradación de rendimiento tras la última release.
- Funcionalidad crítica rota después del deploy.
- Alertas de SLO disparadas post-deploy.
- Usuarios reportando comportamiento inesperado.

## Diagnóstico

1. Confirmar que el problema coincide con el último deploy:
   ```
   # Verificar hora del último despliegue
   cat /var/log/deploy/last_deploy.log
   # Comparar con inicio de los errores en monitoreo
   ```

2. Identificar qué cambió en el deploy:
   ```
   git log --oneline HEAD~5..HEAD
   ```

3. Verificar si el rollback es la acción correcta:
   - ¿El problema empezó exactamente con el deploy?
   - ¿Hay una corrección rápida disponible (hotfix)?
   - ¿El rollback puede causar incompatibilidad de datos?

4. Verificar versión actualmente desplegada:
   ```
   curl -s http://localhost:8080/health | jq .version
   ```

## Resolución

1. Ejecutar rollback a la versión anterior:
   ```
   # Con Docker/Kubernetes
   kubectl rollout undo deployment/api-service

   # Con scripts de deploy
   ./scripts/deploy.sh --version <version-anterior>
   ```

2. Verificar que el rollback fue exitoso:
   ```
   curl -s http://localhost:8080/health | jq .version
   kubectl rollout status deployment/api-service
   ```

3. Verificar que los errores cesaron:
   ```
   # Monitorear tasa de errores por 5 minutos
   watch -n 10 'curl -s http://localhost:8080/metrics | grep http_errors_total'
   ```

4. Comunicar el rollback al equipo:
   - Notificar en el canal de incidentes.
   - Documentar la razón del rollback.
   - Crear ticket para investigar la causa raíz.

5. ADVERTENCIA: NO hacer rollback si:
   - Hubo migraciones de base de datos irreversibles.
   - Se cambió el formato de datos en cache/queue.
   - Otros servicios ya dependen de la nueva versión.

## Escalamiento

- Si el rollback falla, escalar al equipo de plataforma.
- Si hay migraciones de datos involucradas, coordinar con el equipo DBA.
- Si múltiples servicios fueron desplegados, coordinar rollback en orden inverso.

## Prevención

- Implementar canary deployments (10% de tráfico primero).
- Configurar rollback automático si error rate > 5% post-deploy.
- Mantener migraciones de datos reversibles siempre que sea posible.
- Hacer deploy en horarios de bajo tráfico.
- Tener runbook de rollback por servicio documentado.
