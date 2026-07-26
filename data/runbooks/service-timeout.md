---
title: "Timeouts en Comunicación entre Servicios"
service: "microservices"
version: "1.2.0"
last_reviewed: "2026-07-11"
status: "active"
---

## Síntomas

- Respuestas con error "Request Timeout" o "Gateway Timeout" (HTTP 504).
- Latencia de servicios incrementando progresivamente (p99 > 10s).
- Circuit breakers abriéndose entre servicios.
- Conexiones TCP en estado TIME_WAIT acumulándose.
- Logs mostrando "Connection timed out" o "Read timed out".

## Diagnóstico

1. Identificar qué servicio está causando el timeout:
   ```
   # Revisar logs del servicio que reporta timeout
   journalctl -u api-service --since "5 min ago" | grep -i "timeout\|timed out"
   ```

2. Verificar latencia del servicio downstream:
   ```
   curl -w "@curl-format.txt" -o /dev/null -s http://service-downstream:8080/health
   ```

3. Verificar conectividad de red:
   ```
   # DNS resolution
   dig service-downstream.internal
   # TCP connectivity
   nc -zv service-downstream 8080
   ```

4. Verificar carga del servicio destino:
   ```
   curl -s http://service-downstream:8080/metrics | grep "request_duration\|active_connections"
   ```

5. Verificar si hay congestión de red:
   ```
   ss -s
   netstat -an | grep TIME_WAIT | wc -l
   ```

## Resolución

1. Si el servicio downstream está sobrecargado, reducir tráfico:
   ```
   # Activar rate limiting
   # O reducir concurrencia del llamador
   ```

2. Si es un problema de red, verificar y reiniciar interfaces:
   ```
   ip link show
   # Si hay packet loss
   ping -c 10 service-downstream
   ```

3. Incrementar timeouts temporalmente (solo como mitigación):
   ```
   # En configuración del cliente HTTP
   # timeout: 30s -> 60s (temporal, no permanente)
   ```

4. Si el servicio downstream está caído, reiniciarlo:
   ```
   systemctl restart service-downstream
   ```

5. Si hay acumulación de conexiones, limpiar:
   ```
   # Ajustar TCP keepalive
   sysctl -w net.ipv4.tcp_keepalive_time=60
   sysctl -w net.ipv4.tcp_fin_timeout=30
   ```

## Escalamiento

- Si los timeouts persisten después de reiniciar el servicio, escalar al equipo dueño del servicio downstream.
- Si es un problema de red, contactar al equipo de infraestructura/networking.
- Si múltiples servicios están afectados, podría ser un problema del service mesh o DNS.

## Prevención

- Configurar timeouts apropiados por servicio (no usar defaults).
- Implementar circuit breakers con fallback.
- Usar connection pooling con límites configurados.
- Monitorear latencia p95/p99 y alertar en degradación.
- Implementar retry con exponential backoff y jitter.
