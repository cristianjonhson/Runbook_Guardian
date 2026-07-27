---
title: "Reinicio del Servicio Nginx"
service: "nginx"
version: "1.2.0"
last_reviewed: "2026-07-01"
status: "active"
---

## Síntomas

- Errores 502 Bad Gateway reportados por usuarios o monitoreo.
- Respuestas 503 Service Unavailable.
- Conexión rechazada en puerto 80 o 443.
- Fallos en health checks desde el balanceador de carga.
- Procesos worker de Nginx consumiendo memoria excesiva.

## Diagnóstico

1. Verificar el estado del servicio Nginx:
   ```
   systemctl status nginx
   ```

2. Confirmar que Nginx está escuchando en los puertos esperados:
   ```
   ss -tlnp | grep nginx
   ```

3. Revisar los logs de error recientes:
   ```
   tail -50 /var/log/nginx/error.log
   ```

4. Validar la sintaxis de configuración:
   ```
   nginx -t
   ```

5. Verificar si los backends upstream están saludables:
   ```
   curl -I http://localhost:8080/health
   ```

6. Revisar cantidad de procesos worker y conexiones:
   ```
   ps aux | grep nginx
   cat /proc/$(cat /var/run/nginx.pid)/status
   ```

## Resolución

1. Si el test de configuración pasa, intentar un reload graceful primero:
   ```
   systemctl reload nginx
   ```
   Esto recarga la configuración sin cortar conexiones activas.

2. Si el reload no resuelve el problema, realizar un restart completo:
   ```
   systemctl restart nginx
   ```

3. Verificar que el servicio está corriendo después del restart:
   ```
   systemctl status nginx
   curl -I http://localhost
   ```

4. Si el restart falla, verificar conflictos de puerto:
   ```
   ss -tlnp | grep :80
   ss -tlnp | grep :443
   ```

5. Si otro proceso tiene el puerto, identificarlo y detenerlo:
   ```
   fuser -k 80/tcp
   systemctl start nginx
   ```

6. Verificar salud desde la perspectiva del balanceador:
   ```
   curl -I http://localhost/health
   ```

## Escalamiento

- Si Nginx se cae repetidamente después del restart, escalar al equipo de plataforma.
- Si los backends upstream están fallando, contactar al equipo de aplicación.
- Si hay errores de SSL/TLS, verificar expiración de certificados y contactar al equipo de seguridad.

## Prevención

- Monitorear tasas de error y tiempos de respuesta de Nginx.
- Configurar alertas para crashes de procesos worker.
- Implementar restart graceful en los pipelines de despliegue.
- Revisar y probar cambios de configuración en staging antes de producción.
