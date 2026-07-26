---
title: "Disco Lleno - Procedimientos de Limpieza de Emergencia"
service: "linux-infrastructure"
version: "2.1.0"
last_reviewed: "2026-07-05"
status: "active"
---

## Síntomas

- Uso de disco al 90% o superior en cualquier partición montada.
- Aplicaciones fallando al escribir logs o archivos temporales.
- Base de datos rechazando escrituras por espacio insuficiente.
- Alerta: "Espacio en disco críticamente bajo en /dev/sda1".

## Diagnóstico

1. Verificar uso de disco en todas las particiones:
   ```
   df -h
   ```

2. Identificar los directorios más grandes consumiendo espacio:
   ```
   du -sh /* 2>/dev/null | sort -rh | head -10
   ```

3. Encontrar archivos grandes modificados en los últimos 7 días:
   ```
   find / -type f -mtime -7 -size +100M -exec ls -lh {} \; 2>/dev/null
   ```

4. Verificar archivos eliminados aún abiertos por procesos:
   ```
   lsof +L1
   ```

5. Revisar estado de rotación de logs:
   ```
   ls -lh /var/log/*.log
   journalctl --disk-usage
   ```

## Resolución

1. Limpiar caché del gestor de paquetes (seguro, recuperable):
   ```
   apt-get clean
   yum clean all
   ```

2. Eliminar journal logs antiguos (mantener últimos 3 días):
   ```
   journalctl --vacuum-time=3d
   ```

3. Comprimir archivos de log grandes:
   ```
   find /var/log -name "*.log" -size +100M -exec gzip {} \;
   ```

4. Eliminar archivos temporales con más de 7 días:
   ```
   find /tmp -type f -atime +7 -delete
   ```

5. Si hay archivos eliminados retenidos por procesos, reiniciar esos servicios:
   ```
   systemctl restart <servicio-con-archivos-eliminados>
   ```

6. ADVERTENCIA: NO ejecutar `rm -rf /` ni eliminar directorios del sistema.
   Solo eliminar archivos que pueda identificar y verificar que son seguros.

7. Después de la limpieza, verificar espacio disponible:
   ```
   df -h
   ```

## Escalamiento

- Si el disco está lleno y no hay archivos seguros para eliminar, escalar al equipo de infraestructura para expansión de volumen.
- Si el disco de base de datos está lleno, contactar al equipo DBA inmediatamente.
- Considerar agregar volúmenes EBS adicionales si está en AWS.

## Prevención

- Configurar alertas de uso de disco al umbral del 80%.
- Implementar rotación de logs con límites de tamaño (logrotate).
- Programar tareas cron semanales de limpieza para /tmp y logs antiguos.
- Monitorear tendencias de crecimiento de disco para planificación de capacidad.
