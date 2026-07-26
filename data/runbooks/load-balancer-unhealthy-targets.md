---
title: "Targets No Saludables en el Balanceador de Carga"
service: "load-balancer"
version: "1.0.0"
last_reviewed: "2026-07-17"
status: "active"
---

## Síntomas

- Balanceador reportando targets/backends como "unhealthy".
- Tráfico concentrándose en pocos backends saludables.
- Incremento de latencia por menor capacidad disponible.
- Alertas de "No healthy targets" o "All targets unhealthy".
- Errores 503 si todos los targets están fuera de servicio.

## Diagnóstico

1. Verificar estado de los targets en el balanceador:
   ```
   # AWS ALB
   aws elbv2 describe-target-health --target-group-arn <arn>

   # Nginx upstream
   curl http://localhost/nginx_status
   ```

2. Verificar health check del servicio directamente:
   ```
   curl -v http://<target-ip>:<port>/health
   ```

3. Verificar que el servicio está corriendo en los targets:
   ```
   ssh <target-ip> "systemctl status api-service"
   ```

4. Verificar conectividad de red entre balanceador y targets:
   ```
   # Desde el balanceador o una instancia en la misma red
   nc -zv <target-ip> <port>
   ```

5. Revisar si el health check está configurado correctamente:
   ```
   # Verificar path, puerto, timeouts y thresholds
   aws elbv2 describe-target-groups --target-group-arn <arn> | jq '.TargetGroups[0].HealthCheckPath'
   ```

## Resolución

1. Si el servicio está caído en los targets, reiniciarlo:
   ```
   ssh <target-ip> "systemctl restart api-service"
   ```

2. Si el health check path está incorrecto, corregirlo:
   ```
   aws elbv2 modify-target-group --target-group-arn <arn> --health-check-path /health
   ```

3. Si es problema de seguridad de red (security groups/firewalls):
   ```
   # Verificar que el security group permite tráfico del balanceador
   aws ec2 describe-security-groups --group-id <sg-id>
   ```

4. Si los targets están respondiendo lento (timeout del health check):
   ```
   # Incrementar timeout del health check
   aws elbv2 modify-target-group --target-group-arn <arn> --health-check-timeout-seconds 10
   ```

5. Verificar que los targets vuelven a estado healthy:
   ```
   watch -n 5 'aws elbv2 describe-target-health --target-group-arn <arn>'
   ```

## Escalamiento

- Si todos los targets están unhealthy, esto es un incidente crítico — escalar inmediatamente.
- Si el problema es de red/security groups, contactar al equipo de infraestructura.
- Si los servicios no arrancan, coordinar con el equipo de desarrollo.

## Prevención

- Configurar health checks con timeouts y thresholds apropiados.
- Mantener mínimo 2 targets saludables por zona de disponibilidad.
- Implementar graceful shutdown que desregistra del balanceador antes de apagar.
- Monitorear conteo de targets saludables con alertas cuando < N mínimo.
- Probar failover regularmente.
