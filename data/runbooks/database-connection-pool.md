---
title: "Database Connection Pool Exhaustion"
service: "postgresql"
version: "1.0.0"
last_reviewed: "2026-06-20"
status: "active"
---

## Symptoms

- Application logs show "connection pool exhausted" or "too many connections".
- Database queries timing out.
- New connections being refused by PostgreSQL.
- Increased latency in API responses.
- Error: "FATAL: too many connections for role".

## Diagnosis

1. Check current connection count in PostgreSQL:
   ```
   SELECT count(*) FROM pg_stat_activity;
   ```

2. Check max allowed connections:
   ```
   SHOW max_connections;
   ```

3. Identify connections by state:
   ```
   SELECT state, count(*)
   FROM pg_stat_activity
   GROUP BY state;
   ```

4. Find idle connections that may be leaked:
   ```
   SELECT pid, usename, application_name, state, query_start
   FROM pg_stat_activity
   WHERE state = 'idle'
   AND query_start < now() - interval '10 minutes'
   ORDER BY query_start;
   ```

5. Check application-side pool configuration:
   ```
   # Review connection pool settings in application config
   # Typical parameters: pool_size, max_overflow, pool_timeout
   ```

## Resolution

1. Terminate idle connections older than 10 minutes:
   ```
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'idle'
   AND query_start < now() - interval '10 minutes'
   AND pid <> pg_backend_pid();
   ```

2. If connections are from a specific application, restart that service:
   ```
   systemctl restart <application-service>
   ```

3. Temporarily increase max_connections (requires superuser):
   ```
   ALTER SYSTEM SET max_connections = 200;
   SELECT pg_reload_conf();
   ```
   Note: This requires PostgreSQL restart to take full effect.

4. If using PgBouncer, check its pool status:
   ```
   psql -p 6432 pgbouncer -c "SHOW POOLS;"
   ```

5. Verify connection count has decreased:
   ```
   SELECT count(*) FROM pg_stat_activity;
   ```

## Escalation

- If connections continue to grow after cleanup, engage the application development team to identify connection leaks.
- If max_connections needs permanent increase, coordinate with the DBA team for capacity planning.
- If PgBouncer is misconfigured, engage the infrastructure team.

## Prevention

- Configure application connection pools with appropriate limits (pool_size <= max_connections / app_instances).
- Set idle connection timeout in the connection pool.
- Monitor active connections with alerts at 80% of max_connections.
- Implement connection health checks in the pool configuration.
- Review connection usage patterns monthly.
