---
title: "Agotamiento del Pool de Conexiones de Base de Datos"
service: "postgresql"
version: "1.0.0"
last_reviewed: "2026-06-20"
status: "active"
---

## Síntomas

- Logs de aplicación muestran "connection pool exhausted" o "too many connections".
- Consultas a la base de datos agotando timeout.
- PostgreSQL rechazando nuevas conexiones.
- Latencia incrementada en respuestas de la API.
- Error: "FATAL: too many connections for role".

## Diagnóstico

1. Verificar conteo actual de conexiones en PostgreSQL:
   ```
   SELECT count(*) FROM pg_stat_activity;
   ```

2. Verificar máximo de conexiones permitidas:
   ```
   SHOW max_connections;
   ```

3. Identificar conexiones por estado:
   ```
   SELECT state, count(*)
   FROM pg_stat_activity
   GROUP BY state;
   ```

4. Encontrar conexiones idle que pueden ser leaks:
   ```
   SELECT pid, usename, application_name, state, query_start
   FROM pg_stat_activity
   WHERE state = 'idle'
   AND query_start < now() - interval '10 minutes'
   ORDER BY query_start;
   ```

5. Revisar configuración del pool de conexiones de la aplicación:
   ```
   # Revisar parámetros: pool_size, max_overflow, pool_timeout
   ```

## Resolución

1. Terminar conexiones idle con más de 10 minutos:
   ```
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'idle'
   AND query_start < now() - interval '10 minutes'
   AND pid <> pg_backend_pid();
   ```

2. Si las conexiones vienen de una aplicación específica, reiniciar ese servicio:
   ```
   systemctl restart <servicio-aplicacion>
   ```

3. Incrementar temporalmente max_connections (requiere superuser):
   ```
   ALTER SYSTEM SET max_connections = 200;
   SELECT pg_reload_conf();
   ```
   Nota: Requiere restart de PostgreSQL para efecto completo.

4. Si usa PgBouncer, verificar estado del pool:
   ```
   psql -p 6432 pgbouncer -c "SHOW POOLS;"
   ```

5. Verificar que el conteo de conexiones disminuyó:
   ```
   SELECT count(*) FROM pg_stat_activity;
   ```

## Escalamiento

- Si las conexiones siguen creciendo después de la limpieza, contactar al equipo de desarrollo para identificar leaks de conexiones.
- Si max_connections necesita aumento permanente, coordinar con el equipo DBA para planificación de capacidad.
- Si PgBouncer está mal configurado, contactar al equipo de infraestructura.

## Prevención

- Configurar pools de conexión con límites apropiados (pool_size <= max_connections / instancias_app).
- Establecer timeout de conexiones idle en la configuración del pool.
- Monitorear conexiones activas con alertas al 80% de max_connections.
- Implementar health checks de conexiones en la configuración del pool.
- Revisar patrones de uso de conexiones mensualmente.
