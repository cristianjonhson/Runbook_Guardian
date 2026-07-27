---
title: "Alto Consumo de CPU en Servidores Linux"
service: "linux-infrastructure"
version: "1.3.0"
last_reviewed: "2026-07-10"
status: "active"
---

## Síntomas

- Uso de CPU consistentemente por encima del 90% durante más de 5 minutos.
- Tiempos de respuesta lentos en servicios ejecutándose en el host.
- Load average excede la cantidad de núcleos de CPU disponibles.
- Alertas disparadas desde el sistema de monitoreo (CloudWatch, Datadog, Prometheus).

## Diagnóstico

1. Verificar uso actual de CPU y procesos principales:
   ```
   top -bn1 | head -20
   ```

2. Identificar procesos específicos consumiendo CPU:
   ```
   ps aux --sort=-%cpu | head -10
   ```

3. Revisar historial de load average:
   ```
   uptime
   sar -u 1 5
   ```

4. Verificar si el problema es en espacio de usuario o kernel:
   ```
   vmstat 1 5
   ```
   - Alto `us` (user): problema a nivel de aplicación.
   - Alto `sy` (system): problema de kernel o I/O.

5. Buscar procesos descontrolados o fork bombs:
   ```
   ps -eo pid,ppid,%cpu,cmd --sort=-%cpu | head -20
   ```

## Resolución

1. Si una aplicación específica consume CPU excesivo, reiniciar el servicio:
   ```
   systemctl restart <nombre-servicio>
   ```

2. Si se detecta un proceso descontrolado, reducir su prioridad:
   ```
   renice +10 -p <PID>
   ```

3. Si el proceso no responde y no es crítico, terminarlo:
   ```
   kill -15 <PID>
   ```
   Esperar 30 segundos. Si sigue corriendo:
   ```
   kill -9 <PID>
   ```

4. Si el CPU alto se debe a carga legítima, considerar escalar:
   - Horizontal: agregar más instancias detrás del balanceador de carga.
   - Vertical: redimensionar la instancia (requiere downtime).

5. Después de la resolución, verificar que el CPU volvió a la normalidad:
   ```
   top -bn1 | grep "Cpu(s)"
   ```

## Escalamiento

- Si el problema persiste después de reiniciar el servicio, escalar al equipo de aplicación.
- Si múltiples hosts están afectados simultáneamente, verificar problemas de dependencias upstream.
- Si el CPU de kernel es alto, involucrar al equipo de infraestructura para análisis profundo.

## Prevención

- Configurar alertas de uso de CPU al umbral del 80%.
- Implementar políticas de auto-scaling para patrones de carga predecibles.
- Revisar rendimiento de aplicaciones trimestralmente.
