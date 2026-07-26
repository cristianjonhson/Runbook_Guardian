---
title: "Redis con Memoria Llena"
service: "redis"
version: "1.0.0"
last_reviewed: "2026-07-09"
status: "active"
---

## Síntomas

- Errores "OOM command not allowed when used memory > maxmemory".
- Operaciones de escritura en Redis fallando.
- Aplicaciones reportando errores de cache.
- Latencia de Redis incrementando significativamente.
- Alertas de uso de memoria de Redis > 90%.

## Diagnóstico

1. Verificar uso de memoria de Redis:
   ```
   redis-cli INFO memory | grep -E "used_memory_human|maxmemory_human|mem_fragmentation_ratio"
   ```

2. Identificar las keys más grandes:
   ```
   redis-cli --bigkeys
   ```

3. Verificar política de eviction configurada:
   ```
   redis-cli CONFIG GET maxmemory-policy
   ```

4. Verificar distribución de keys por tipo:
   ```
   redis-cli INFO keyspace
   ```

5. Verificar si hay keys sin TTL que están acumulándose:
   ```
   redis-cli --scan --pattern "*" | head -100 | while read key; do
     ttl=$(redis-cli TTL "$key")
     if [ "$ttl" = "-1" ]; then echo "NO TTL: $key"; fi
   done
   ```

## Resolución

1. Si la política de eviction no está configurada, activarla:
   ```
   redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

2. Eliminar keys expiradas manualmente si están retenidas:
   ```
   redis-cli --scan --pattern "temp:*" | xargs redis-cli DEL
   ```

3. Si hay keys grandes innecesarias, eliminarlas:
   ```
   redis-cli DEL <key-grande-identificada>
   ```

4. Incrementar maxmemory temporalmente (si hay RAM disponible):
   ```
   redis-cli CONFIG SET maxmemory 4gb
   ```

5. Si la fragmentación es alta (> 1.5), reiniciar Redis:
   ```
   redis-cli BGSAVE
   systemctl restart redis
   ```

6. Verificar que la memoria se estabilizó:
   ```
   redis-cli INFO memory | grep used_memory_human
   ```

## Escalamiento

- Si Redis sigue llenándose rápidamente, contactar al equipo de desarrollo para revisar patrones de uso.
- Si se necesita más memoria permanentemente, coordinar con infraestructura para escalar la instancia.
- Si hay datos que no pueden estar en memoria, considerar migrar a Redis Cluster.

## Prevención

- Configurar maxmemory-policy apropiada (allkeys-lru para cache, noeviction para datos).
- Establecer TTL en todas las keys de cache.
- Monitorear uso de memoria con alertas al 70% y 85%.
- Implementar key namespacing para facilitar limpieza.
- Revisar crecimiento de keyspace mensualmente.
