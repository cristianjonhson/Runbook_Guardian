---
title: "Reinicio de Base de Datos PostgreSQL"
service: "postgresql"
version: "1.1.0"
last_reviewed: "2026-07-12"
status: "active"
---

## Síntomas

- PostgreSQL no responde a conexiones.
- Procesos de postgres en estado zombie o consumiendo 100% CPU.
- Error: "FATAL: the database system is not yet accepting connections".
- Replication lag creciente sin recuperación.
- Shared memory corruption detectada en logs.

## Diagnóstico

1. Verificar estado del servicio PostgreSQL:
   ```
   systemctl status postgresql
   ```

2. Revisar logs recientes de PostgreSQL:
   ```
   tail -100 /var/log/postgresql/postgresql-15-main.log
   ```

3. Verificar si hay procesos postgres activos:
   ```
   ps aux | grep postgres | grep -v grep
   ```

4. Verificar si el archivo PID existe y es válido:
   ```
   cat /var/lib/postgresql/15/main/postmaster.pid
   ```

5. Verificar espacio en disco (causa común de crash):
   ```
   df -h /var/lib/postgresql
   ```

## Resolución

1. Intentar un restart graceful primero:
   ```
   systemctl restart postgresql
   ```

2. Verificar que PostgreSQL acepta conexiones:
   ```
   pg_isready -h localhost -p 5432
   ```

3. Si el restart falla, verificar el archivo PID huérfano:
   ```
   rm /var/lib/postgresql/15/main/postmaster.pid
   systemctl start postgresql
   ```

4. Si hay corrupción de WAL, intentar recovery:
   ```
   sudo -u postgres pg_resetwal -f /var/lib/postgresql/15/main
   ```
   ADVERTENCIA: Esto puede causar pérdida de datos. Solo usar como último recurso.

5. Verificar integridad después del restart:
   ```
   sudo -u postgres psql -c "SELECT pg_is_in_recovery();"
   sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
   ```

## Escalamiento

- Si PostgreSQL no arranca después de 2 intentos, escalar al equipo DBA.
- Si hay corrupción de datos, activar procedimiento de disaster recovery.
- Si es la réplica la que falla, considerar reconstruirla desde el primario.

## Prevención

- Monitorear espacio en disco del directorio de datos.
- Configurar alertas de replication lag > 30 segundos.
- Realizar backups con pg_basebackup diariamente.
- Probar procedimientos de recovery trimestralmente.
- Mantener PostgreSQL actualizado con parches de seguridad.
