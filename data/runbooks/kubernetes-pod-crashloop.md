---
title: "Pod en CrashLoopBackOff en Kubernetes"
service: "kubernetes"
version: "1.0.0"
last_reviewed: "2026-07-16"
status: "active"
---

## Síntomas

- Pod en estado CrashLoopBackOff (reiniciando continuamente).
- Servicio no disponible a pesar de tener pods programados.
- Eventos mostrando "Back-off restarting failed container".
- Restart count del pod incrementando.
- Logs del contenedor mostrando errores de arranque.

## Diagnóstico

1. Verificar estado del pod:
   ```
   kubectl get pods -n <namespace> | grep <pod-name>
   kubectl describe pod <pod-name> -n <namespace>
   ```

2. Revisar logs del contenedor (incluyendo el último crash):
   ```
   kubectl logs <pod-name> -n <namespace> --previous
   kubectl logs <pod-name> -n <namespace>
   ```

3. Verificar eventos del pod:
   ```
   kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name> --sort-by=.lastTimestamp
   ```

4. Verificar si es problema de recursos:
   ```
   kubectl top pod <pod-name> -n <namespace>
   kubectl describe node <node-name> | grep -A 5 "Allocated resources"
   ```

5. Verificar configuración del pod (envvars, secrets, configmaps):
   ```
   kubectl get pod <pod-name> -n <namespace> -o yaml | grep -A 3 "env\|configMap\|secret"
   ```

## Resolución

1. Si el error es por una variable de entorno faltante o incorrecta:
   ```
   kubectl edit configmap <configmap-name> -n <namespace>
   kubectl rollout restart deployment <deployment-name> -n <namespace>
   ```

2. Si es por un secret que no existe:
   ```
   kubectl get secrets -n <namespace>
   # Crear o actualizar el secret faltante
   kubectl create secret generic <secret-name> --from-literal=key=value -n <namespace>
   ```

3. Si es OOMKilled (memoria insuficiente):
   ```
   # Incrementar límites de memoria
   kubectl patch deployment <name> -n <namespace> -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"limits":{"memory":"512Mi"}}}]}}}}'
   ```

4. Si es por imagen no encontrada o pull error:
   ```
   kubectl describe pod <pod-name> -n <namespace> | grep -A 3 "Events"
   # Verificar que la imagen existe y los credentials son correctos
   ```

5. Si es por health check fallido (liveness probe):
   ```
   # Verificar configuración del probe
   kubectl get pod <pod-name> -n <namespace> -o yaml | grep -A 10 "livenessProbe"
   # Considerar incrementar initialDelaySeconds
   ```

## Escalamiento

- Si el pod sigue crasheando después de corregir configuración, escalar al equipo de desarrollo.
- Si es un problema de recursos del nodo, contactar al equipo de infraestructura.
- Si el crash es por un bug en la imagen, coordinar rollback con el equipo de release.

## Prevención

- Configurar liveness y readiness probes apropiados.
- Establecer resource requests y limits realistas.
- Implementar graceful shutdown en las aplicaciones.
- Usar pod disruption budgets para alta disponibilidad.
- Monitorear restart count y alertar cuando > 3 en 5 minutos.
